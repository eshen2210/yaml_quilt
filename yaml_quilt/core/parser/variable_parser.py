import ast
from typing import Any, Dict, Optional, Set, Tuple

from yaml_quilt.core.custom_errors import (
    AbstractKeyNotImplementedException,
    AmbiguousVariableException,
    InvalidDeclarationException,
    KeySealedException,
    NoOverrideException,
)

from .parse_functions import remove_key_declaration
from ..declarations import DeclarationType

VariableEntry = Tuple[Any, Set[str]]
VariableMap = Dict[str, VariableEntry]


def process_variables(data: Any, patch: Dict, global_variables: Dict, injected_variables: Dict, file_path: str) -> Dict[str, Any]:
    """Processes variables in data inplace."""
    extracted_injected_variables = _extract_variable_declarations(injected_variables, set())
    extracted_global_variables = _extract_variable_declarations(global_variables, set())

    instantiation_variables, instantiation_declarations = _extract_variables_from_dict(patch)
    extracted_instantiation_variables = _extract_variable_declarations(
        instantiation_variables,
        instantiation_declarations,
    )

    if isinstance(data, dict):
        data_variables, data_declarations = _extract_variables_from_dict(data)
    elif isinstance(data, list):
        data_variables, data_declarations = _extract_variables_from_list(data)
    else:
        return {}  # Scalar data

    extracted_data_variables = _extract_variable_declarations(data_variables, data_declarations)

    # Apply variable precedence (lowest -> highest): local, instantiation, global, injected
    _inherit_variables(extracted_data_variables, extracted_instantiation_variables, file_path)
    _inherit_variables(extracted_data_variables, extracted_global_variables, file_path)
    _inherit_variables(extracted_data_variables, extracted_injected_variables, file_path)

    # Check for abstract variables used before being overriden
    for variable_key, variable_value in extracted_data_variables.items():
        if DeclarationType.ABSTRACT in variable_value[1]:
            file_context = f" File: '{file_path}'."
            raise AbstractKeyNotImplementedException(
                f"Abstract variable '{variable_key}' cannot be used before being overridden.{file_context}"
            )

    # Process data for variable replacement inplace
    if isinstance(data, dict):
        _process_dict(data, extracted_data_variables, False, file_path)
    elif isinstance(data, list):
        _process_list(data, extracted_data_variables, False, file_path)

    return _serialize_variables(extracted_data_variables)


def _extract_variable_declarations(variables: dict, existing_declarations: Set) -> VariableMap:
    """Returns variable dict with keys without declarations and set of declarations as value.
    Appends existing declarations (declarations declared alongside variables declaration) to each variable.
    Return key = key without declaration (key is the substring to be replaced in YAML)
    Return value = (replacement substring, declarations set)"""
    if not variables:
        return {}

    extracted_variables: VariableMap = {}
    for key, value in variables.items():
        declarations, parsed_key = _find_variable_key_declarations(key)
        declarations = declarations.union(existing_declarations)
        # TO DO: Check for conflicting declarations
        extracted_variables[parsed_key] = (value, declarations)
    return extracted_variables


def _extract_variables_from_dict(data: Dict) -> Tuple[Dict[str, Any], Set[str]]:
    for key in list(data.keys()):
        if DeclarationType.VARIABLES in key:
            variables = data[key]
            declarations, _ = _find_variable_key_declarations(key)
            data.pop(key)
            return variables, declarations
    return {}, set()


def _extract_variables_from_list(data: list) -> Tuple[Dict[str, Any], Set[str]]:
    for item in list(data):
        if isinstance(item, dict) and len(item) == 1:
            for key in item:
                if DeclarationType.VARIABLES in key:
                    variables = item[key]
                    declarations, _ = _find_variable_key_declarations(key)
                    data.remove(item)
                    return variables, declarations
    return {}, set()


def _serialize_variables(variables: VariableMap) -> Dict[str, Any]:
    """Transform extracted variables back to dict format."""
    return_variables: Dict[str, Any] = {}
    for key, value in variables.items():
        return_key = ""
        for declaration in value[1]:
            return_key += declaration + " "
        return_key += key
        return_variables[return_key] = value[0]
    return return_variables


def _process_dict(data: dict, variables: VariableMap, is_patch: bool, file_path: str):
    """Processes a dict for variable DFS replacement inplace.
       If None is returned, then pop non-root parent element."""
    if not _process_enable_in_dict(data, variables, file_path):
        # (enable) if False, clear dict
        return
    _process_enable_in_key(data, variables, file_path)

    for key in list(data.keys()):
        if key == DeclarationType.PATCH:
            is_patch = True
        if not data.get(key):
            continue

        if is_patch and DeclarationType.VARIABLES in key:
            _process_carryover_variables(data, key, variables)
            continue

        if DeclarationType.OPTIONAL in key:
            _process_optional_dict_key(data, key, variables, file_path)
            continue

        if DeclarationType.DEFAULT in key:
            _process_default_dict_key(data, key, variables, file_path)
            continue

        if isinstance(data[key], dict):
            _process_dict(data[key], variables.copy(), is_patch, file_path)
            if not data[key]:
                data.pop(key)
        elif isinstance(data[key], list):
            _process_list(data[key], variables.copy(), is_patch, file_path)
            if not data[key]:
                data.pop(key)
        else:  # Scalar value
            _replace_value(data, key, variables, file_path)


def _process_enable_in_dict(data: dict, variables: VariableMap, file_path: str) -> bool:
    """Apply (enable) semantics to a dict. Returns False if the dict is cleared."""
    if DeclarationType.ENABLE not in data:
        return True
    _replace_value(data, DeclarationType.ENABLE, variables, file_path)
    if data[DeclarationType.ENABLE] is not True:
        data.clear()
        return False
    data.pop(DeclarationType.ENABLE)
    return True


def _process_enable_in_key(data: dict, variables: VariableMap, file_path: str) -> None:
    """Apply (enable) semantics to a dict key. Deletes the key in the data if removed."""
    for key in list(data.keys()):
        if DeclarationType.ENABLE not in key or\
           key == DeclarationType.ENABLE:  # Whole key is (enable) means dict-level enable
            continue
        
        delimited_key = key.split(DeclarationType.ENABLE_DELIMITER)
        if len(delimited_key) != 2:
            file_context = f" File: '{file_path}'."
            raise InvalidDeclarationException(
                f"Key-level (enable) must contain exactly one delimiter '{DeclarationType.ENABLE_DELIMITER}'. "
                f"Key '{key}' instead has value: {key}.{file_context}"
            )
    
        enable_variables = delimited_key[0].replace(DeclarationType.ENABLE + " ", "")
        if not enable_variables:
            file_context = f" File: '{file_path}'."
            raise InvalidDeclarationException(
                f"Key-level (enable) must have a variable key before the delimiter '{DeclarationType.ENABLE_DELIMITER}'. "
                f"Key '{key}' instead has value: {key}.{file_context}"
            )
    
        if enable_variables not in variables:
            data.pop(key)
            return
        else:
            value = data.pop(key)
            data[delimited_key[1]] = value


def _process_carryover_variables(data: dict, key: str, variables: VariableMap) -> None:
    """Process carryover variables declared inside (patch) instantiations."""
    variables_block = data[key]
    carryover_keys = [
        variable_key for variable_key in variables_block
        if DeclarationType.CARRYOVER in variable_key
    ]
    for carryover_key in carryover_keys:
        carryover_key_declarations, parsed_carryover_key = _find_variable_key_declarations(carryover_key)
        if DeclarationType.OPTIONAL in carryover_key_declarations:
            if parsed_carryover_key not in variables:
                variables_block.pop(carryover_key)
                continue
        if parsed_carryover_key in variables:
            if DeclarationType.GLOBAL in variables[parsed_carryover_key][1]:
                # Do not instantiation with carryover key if key is in global
                # This prevents the same variable key from appearing twice in nested inheritance
                # Falsely triggering NoOverride errors
                variables_block.pop(carryover_key)
                continue
            variables_block[carryover_key] = variables[parsed_carryover_key][0]
            carryover_key = remove_key_declaration(variables_block, carryover_key, DeclarationType.CARRYOVER)
            if DeclarationType.ABSTRACT in carryover_key_declarations:
                remove_key_declaration(variables_block, carryover_key, DeclarationType.ABSTRACT)


def _process_optional_dict_key(data: dict, key: str, variables: VariableMap, file_path: str) -> None:
    key = remove_key_declaration(data, key, DeclarationType.OPTIONAL)
    if isinstance(data[key], (dict, list)):
        file_context = f" File: '{file_path}'."
        raise InvalidDeclarationException(
            f"Optional declaration must be associated with a scalar value. "
            f"Key '{key}' is type: {type(data[key])}.{file_context}"
        )
    if data[key] in variables:
        _replace_value(data, key, variables, file_path)
    else:
        data.pop(key)


def _process_default_dict_key(data: dict, key: str, variables: VariableMap, file_path: str) -> None:
    key = remove_key_declaration(data, key, DeclarationType.DEFAULT)
    if not isinstance(data[key], str):
        file_context = f" File: '{file_path}'."
        raise InvalidDeclarationException(
            f"Default declaration must be associated with a string value. "
            f"Key '{key}' is type: {type(data[key])}.{file_context}"
        )
    delimited_value: list = data[key].split(DeclarationType.DEFAULT_DELIMITER)
    if len(delimited_value) != 2:
        file_context = f" File: '{file_path}'."
        raise InvalidDeclarationException(
            f"Default declaration value must contain exactly one delimiter '{DeclarationType.DEFAULT_DELIMITER}'. "
            f"Key '{key}' instead has value: {data[key]}.{file_context}"
        )
    value = delimited_value[0]
    default_value = _convert_string_to_literal(delimited_value[1])
    if value in variables:
        data[key] = value
        _replace_value(data, key, variables, file_path)
    else:
        data[key] = default_value


def _process_list(data: list, variables: VariableMap, is_patch: bool, file_path: str):
    """Processes a list for variable DFS replacement inplace.
       If None is returned, then pop non-root parent element."""
    if not _process_enable_in_list(data, variables, file_path):
        return

    i = 0
    while i < len(data):
        item = data[i]
        if not item:
            i += 1
            continue

        next_index = _process_optional_list_item(data, i, variables, file_path)
        if next_index is not None:
            i = next_index
            continue

        next_index = _process_default_list_item(data, i, variables, file_path)
        if next_index is not None:
            i = next_index
            continue

        if isinstance(item, dict):
            _process_dict(item, variables.copy(), is_patch, file_path)
            if not item:
                data.pop(i)
            else:
                i += 1
        elif isinstance(item, list):
            _process_list(item, variables.copy(), is_patch, file_path)
            if not item:
                data.pop(i)
            else:
                i += 1
        else:  # Scalar value
            _replace_value(data, i, variables, file_path)
            i += 1


def _process_enable_in_list(data: list, variables: VariableMap, file_path: str) -> bool:
    """Apply list-level (enable) gates. Returns False if the list is cleared."""
    for item in data:
        if isinstance(item, dict) and len(item) == 1 and DeclarationType.ENABLE in item:
            _replace_value(item, DeclarationType.ENABLE, variables, file_path)
            if item[DeclarationType.ENABLE] is not True:
                data.clear()
                return False
    return True


def _process_optional_list_item(data: list, index: int, variables: VariableMap, file_path: str) -> Optional[int]:
    """Handle a list item with (optional). Returns next index or None if not handled."""
    item = data[index]
    if not isinstance(item, str) or DeclarationType.OPTIONAL not in item:
        return None

    data[index] = item.replace(DeclarationType.OPTIONAL + " ", "")
    if data[index] in variables:
        _replace_value(data, index, variables, file_path)
        return index + 1
    data.pop(index)
    return index


def _process_default_list_item(data: list, index: int, variables: VariableMap, file_path: str) -> Optional[int]:
    """Handle a list item with (default). Returns next index or None if not handled."""
    item = data[index]
    if not isinstance(item, str) or DeclarationType.DEFAULT not in item:
        return None

    data[index] = item.replace(DeclarationType.DEFAULT + " ", "")
    delimited_value: list = data[index].split(DeclarationType.DEFAULT_DELIMITER)
    if len(delimited_value) != 2:
        file_context = f" File: '{file_path}'."
        raise InvalidDeclarationException(
            f"Default declaration value must contain exactly one delimiter '{DeclarationType.DEFAULT_DELIMITER}'. "
            f"List item at index {index} instead has value: {data[index]}.{file_context}"
        )
    value = delimited_value[0]
    default_value = _convert_string_to_literal(delimited_value[1])
    if value in variables:
        data[index] = value
        _replace_value(data, index, variables, file_path)
    else:
        data[index] = default_value
    return index + 1


def _inherit_variables(variables: VariableMap, new_variables: VariableMap, file_path: str) -> None:
    """Inherits variables from new_variables to variables inplace."""
    for new_key, new_value in new_variables.items():
        if new_key in variables and \
           DeclarationType.OVERRIDE not in new_value[1] and \
           DeclarationType.ABSTRACT not in variables[new_key][1]:
            file_context = f" File: '{file_path}'."
            raise NoOverrideException(
                f"Cannot override variable '{new_key}' because the new value does not declare (override)."
                f"{file_context}"
            )
        if new_key in variables and DeclarationType.SEALED in variables[new_key][1]:
            file_context = f" File: '{file_path}'."
            raise KeySealedException(
                f"Cannot override sealed variable '{new_key}'.{file_context}"
            )
        variables[new_key] = new_value


def _replace_value(data: Any, key_or_index: Any, variables: VariableMap, file_path: str) -> None:
    """For string value in data, replaces any matching substring of data_value with variable value inplace.
       Returns replaced value."""
    value = data[key_or_index]
    if isinstance(value, str):
        _check_ambiguous_variables(value, variables, file_path)
        for variable_key, variable_value in variables.items():
            if not isinstance(value, str):
                break  # value was replaced with a non-string; multiple replacements not possible
            if variable_key in value:
                # Note: This abstract check is redundant with earlier abstract checks, but kept for safety.
                if DeclarationType.ABSTRACT in variable_value[1]:
                    file_context = f" File: '{file_path}'."
                    raise AbstractKeyNotImplementedException(
                        f"Abstract variable '{variable_key}' cannot be used before being overridden.{file_context}"
                    )
                if isinstance(variable_value[0], str):  # TO DO: Multiple string replacements possible. But what if string replacements are ambiguous?
                    value = value.replace(variable_key, variable_value[0])
                else:
                    value = variable_value[0]
                    break  # value was replaced with a non-string; multiple replacements not possible
        data[key_or_index] = value
        return


def _find_variable_key_declarations(key: str) -> tuple[set, str]:
    """Returns all declarations and key with no declarations within a variable key."""
    if not key:
        return set(), key
    else:
        declarations = set()
        for item in key.split(" "):
            if item in DeclarationType.VARIABLE_DECLARATIONS:
                declarations.add(item)
                key = key.replace(item + " ", "")
        return declarations, key


def _convert_string_to_literal(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def _check_ambiguous_variables(value: str, variables: VariableMap, file_path: str) -> None:
    matches = []
    for variable_key in variables.keys():
        if not isinstance(variable_key, str) or variable_key == "":
            continue
        key_len = len(variable_key)
        if key_len == 0:
            continue
        last_start = len(value) - key_len
        index = 0
        while index <= last_start:
            if value[index:index + key_len] == variable_key:
                matches.append((index, index + key_len, variable_key))
            index += 1

    if len(matches) < 2:
        return

    matches.sort()
    for i in range(1, len(matches)):
        prev_start, prev_end, prev_var = matches[i - 1]
        curr_start, curr_end, curr_var = matches[i]
        if curr_start < prev_end:
            file_context = f" File: '{file_path}'."
            raise AmbiguousVariableException(
                f"Ambiguous variable replacement in value '{value}': "
                f"'{prev_var}' overlaps with '{curr_var}'.{file_context}"
            )
