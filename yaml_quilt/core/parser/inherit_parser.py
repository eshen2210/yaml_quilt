from typing import Dict, Set
from yaml_quilt.core.custom_errors import (
    KeySealedException,
    NoOverrideException,
    InvalidDeclarationException,
    MismatchedValueTypeException,
    AbstractKeyNotImplementedException
)

import yaml_quilt.core.parser.config_parser as config_parser
import yaml_quilt.core.parser.next_parser as next_parser
from ..declarations import DeclarationType
from .context import ProcessingContext
from .parse_functions import remove_all_key_declarations


def process_inherit(sub_data: dict, base_data: dict, context: ProcessingContext) -> None:

    if DeclarationType.PATCH in base_data:
        config_parser.process_patch_declaration(
            yaml_data=base_data,
            context=context,
        )

    # Map matches the base_data keys to the sub keys with their declarations.
    # sub_key_map Key = parsed key (no declaration)
    # sub_key_map Value = Full key
    sub_key_map = _map_parsed_sub_keys(sub_data)

    # List containing:
    # [base_key (without declarations), full_key (with_declaratios), list of declarations]
    base_key_list = _list_parsed_base_keys(base_data)

    # Iterate through parsed base keys and perform inheritance logic
    for parsed_base_key, full_base_key in base_key_list:
        full_base_key, base_key_declarations = context.extract_base_declarations(base_data, full_base_key)
        if DeclarationType.PRIVATE in base_key_declarations:
            continue  # Do no inherit private keys

        if parsed_base_key not in sub_key_map:
            _process_inherit_missing_sub_key(
                sub_data=sub_data,
                base_data=base_data,
                parsed_base_key=parsed_base_key,
                full_base_key=full_base_key,
                base_key_declarations=base_key_declarations,
                context=context,
            )
            continue

        sub_key = sub_key_map.pop(parsed_base_key)
        _process_inherit_matching_key(
            sub_data=sub_data,
            base_data=base_data,
            sub_key=sub_key,
            full_base_key=full_base_key,
            base_key_declarations=base_key_declarations,
            context=context,
        )

    # Process remaining sub_data keys that did not match base_data keys
    _process_remaining_sub_keys(sub_data, sub_key_map, context)


def _process_inherit_missing_sub_key(sub_data: dict, base_data: dict, parsed_base_key: str, full_base_key: str, 
                                     base_key_declarations: Set[str], context: ProcessingContext) -> None:
    if DeclarationType.ABSTRACT in context.base_declarations or DeclarationType.ABSTRACT in base_key_declarations:
        file_context = f" File: '{context.file_path}'."
        raise AbstractKeyNotImplementedException(
            f"Abstract base key '{parsed_base_key}' is not implemented in sub YAML."
            f"{file_context}"
        )
    if DeclarationType.OVERRIDE in context.sub_declarations:
        # If override was declared for a key.
        # New keys are not inherited.
        return
    
    next_data = next_parser.process_next(
        yaml_data=base_data[full_base_key],
        context=context,
    )
    next_data = next_data if next_data is not None else base_data[full_base_key]
    
    remove_all_key_declarations(next_data, "key", DeclarationType.PRIVATE)
    sub_data[full_base_key] = next_data


def _process_inherit_matching_key(sub_data: dict, base_data: dict, sub_key: str, full_base_key: str,
                                  base_key_declarations: Set[str], context: ProcessingContext) -> None:
    file_context = f" File: '{context.file_path}'."
    sub_key, sub_key_declarations = context.extract_sub_declarations(sub_data, sub_key)
    if sub_key in sub_data and _is_type_mismatch(sub_data[sub_key], base_data[full_base_key]):
        raise MismatchedValueTypeException(
            f"Type mismatch during inheritance for key '{full_base_key}'. "
            f"Base type: {type(base_data[full_base_key])}, sub type: {type(sub_data[sub_key])}."
            f"{file_context}"
        )
    if DeclarationType.SEALED in context.base_declarations or DeclarationType.SEALED in base_key_declarations:
        raise KeySealedException(
            f"Cannot override sealed base key '{full_base_key}'.{file_context}"
        )

    base_value = base_data[full_base_key]
    if isinstance(base_value, dict):
        if sub_data[sub_key] is None:
            sub_data[sub_key] = {}
        inherit_context = ProcessingContext(
            directory=context.directory,
            loader=context.loader,
            variables=context.variables,
            sub_files=context.sub_files.copy(),
            sub_declarations=context.persistent_sub_declarations(sub_key_declarations),
            base_declarations=context.base_declarations.copy() | base_key_declarations,
            file_path=context.file_path
        )
        process_inherit(
            sub_data=sub_data[sub_key],
            base_data=base_data[full_base_key],
            context=inherit_context,
        )
        return
    if isinstance(base_value, list):
        _inherit_list_value(
            sub_data=sub_data,
            base_data=base_data,
            sub_key=sub_key,
            full_base_key=full_base_key,
            sub_key_declarations=sub_key_declarations,
            base_key_declarations=base_key_declarations,
            context=context,
        )
        return
    if base_value is not None:  # Data is scalar
        if DeclarationType.OVERRIDE in sub_key_declarations | context.sub_declarations:
            return  # Maintain sub_data's values.
        raise NoOverrideException(
            f"No override declared for scalar key '{sub_key}' despite matching base key."
            f"{file_context}"
        )


def _inherit_list_value(sub_data: dict, base_data: dict, sub_key: str, full_base_key: str, 
                        sub_key_declarations: Set[str], base_key_declarations: Set[str], context: ProcessingContext) -> None:
    base_list = base_data[full_base_key]
    if DeclarationType.APPEND in sub_key_declarations:
        sub_data[sub_key] = _process_append_prepend(sub_data[sub_key], base_list, "append", context)
        return
    if DeclarationType.PREPEND in sub_key_declarations:
        sub_data[sub_key] = _process_append_prepend(sub_data[sub_key], base_list, "prepend", context)
        return
    if DeclarationType.MERGE in sub_key_declarations:
        sub_data[sub_key] = _process_merge(sub_data[sub_key], base_list, context)
        return
    if DeclarationType.OVERRIDE not in sub_key_declarations | context.sub_declarations and \
       DeclarationType.ABSTRACT not in base_key_declarations | context.base_declarations:
        file_context = f" File: '{context.file_path}'."
        raise NoOverrideException(
            f"No override declared for list key '{sub_key}' despite matching base key."
            f"{file_context}"
        )


def _process_remaining_sub_keys(sub_data: dict, sub_key_map: dict, context: ProcessingContext) -> None:
    for sub_key in sub_key_map.values():
        sub_key, sub_key_declarations = context.extract_sub_declarations(sub_data, sub_key)
        if {
            DeclarationType.APPEND,
            DeclarationType.PREPEND,
            DeclarationType.MERGE,
        }.intersection(sub_key_declarations):
            file_context = f" File: '{context.file_path}'."
            raise InvalidDeclarationException(
                f"Key: '{sub_key}' cannot declare append, prepend, or merge without an immediate base key to inherit from."
                f"{file_context}"
            )
        next_context = ProcessingContext(
            directory=context.directory,
            loader=context.loader,
            variables=context.variables,
            sub_files=context.sub_files.copy(),
            sub_declarations=context.persistent_sub_declarations(sub_key_declarations),
            base_declarations=set(),
            file_path=context.file_path,
        )
        next_data = next_parser.process_next(
            yaml_data=sub_data[sub_key],
            context=next_context,
        )
        sub_data[sub_key] = next_data if next_data is not None else sub_data[sub_key]


def _process_append_prepend(sub_data, base_data, mode: str, context: ProcessingContext):
    """Append sub_data's values to base_data's values and return new list."""

    remove_all_key_declarations(base_data, "key", DeclarationType.PRIVATE)
    next_parser.process_next(
        yaml_data=base_data,
        context=context,
    )

    # Catch case where appending into empty key
    base_data = base_data if base_data is not None else []
    sub_data = sub_data if sub_data is not None else []
    
    # Append or prepend
    if mode == "append":
        return base_data + sub_data
    elif mode == "prepend":
        return sub_data + base_data
    else:
        # Should not reach this point
        file_context = f" File: '{context.file_path}'."
        raise Exception(
            f"Invalid append/prepend mode '{mode}' while processing list inheritance."
            f"{file_context} Please open a Github issue with your given input."
        )


def _process_merge(sub_data, base_data, context: ProcessingContext):
    """Merge base_data's list values into sub_data's list values and return new list.
       Merging involving applying inheritance rules to each item of matching index in sub and base lists."""

    total_length = max(len(sub_data), len(base_data))
    for i in range(total_length):
        if i >= len(sub_data):
            sub_data.append(base_data[i])
        elif i >= len(base_data):
            pass
        elif sub_data[i] is None:
            sub_data[i] = base_data[i]
        elif base_data[i] is None:
            pass
        else:
            # Sub and base both have values, so apply inheritance rules
            # Apply inheritance rules only if both sub and base are dicts
            if (not isinstance(sub_data[i], dict) and base_data[i] is not None) or \
               (not isinstance(base_data[i], dict) and sub_data[i] is not None):
                file_context = f" File: '{context.file_path}'."
                raise MismatchedValueTypeException(
                    f"Cannot merge list items at index {i} because one or both items are not dictionaries. "
                    f"Sub type: {type(sub_data[i])}, base type: {type(base_data[i])}."
                    f"{file_context}"
                )
            process_inherit(
                sub_data=sub_data[i],
                base_data=base_data[i],
                context=ProcessingContext(
                    directory=context.directory,
                    loader=context.loader,
                    variables=context.variables,
                    sub_files=context.sub_files.copy(),
                    file_path=context.file_path,
                )
            )
    return sub_data


def _map_parsed_sub_keys(sub_data: dict) -> dict:
    """Map parsed sub keys to their declaration and full key.
       Key = parsed key (no declaration)
       Value = full key."""
    key_map = {}
    for full_key in sub_data:
        parsed_key = _key_without_declaration(full_key)
        key_map[parsed_key] = full_key
    return key_map


def _list_parsed_base_keys(base_data: dict) -> list:
    """List parsed base keys to their declaration and full key.
       Value = parsed key, full key."""
    key_list = []
    for full_key in base_data:
        parsed_key = _key_without_declaration(full_key)
        key_list.append((parsed_key, full_key))
    return key_list


def _key_without_declaration(key: str) -> str:
    """Returns the key without any declarations."""
    if key == "" or key is None:
        return ""
    return " ".join([
        item for item in key.split()
        if item not in DeclarationType.BASE_KEY_DECLARATIONS and item not in DeclarationType.SUB_KEY_DECLARATIONS
    ])


def _is_type_mismatch(sub_data, base_data) -> bool:
    """Returns true if types of base and sub prevent inheritance."""
    if sub_data is None or base_data is None:
        return False
    # Empty dicts or lists are essentially None
    elif not sub_data or not base_data:
        return False
    elif type(base_data) is not type(sub_data):
        return True
    # sub and base are both non-empty dicts or non-empty lists
    return False
