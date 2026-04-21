import copy
import os
import yaml
from typing import Any, Optional, Dict
from yaml_quilt.core.custom_errors import (
    InvalidInstantiationException,
    CircularInheritanceException,
    MismatchedValueTypeException,
    AbstractKeyNotImplementedException,
)

import yaml_quilt.core.parser.inherit_parser as inherit_parser
import yaml_quilt.core.parser.next_parser as next_parser
from yaml_quilt.core.parser.variable_parser import process_variables
from yaml_quilt.core.declarations import DeclarationType
from yaml_quilt.core.parser.context import ProcessingContext
from yaml_quilt.core.parser.parse_functions import remove_all_key_declarations


# To do: test loaders
def process_root_yaml(yaml_data: Any, directory: str, injected_variables: Dict, loader: type, file_path: str) -> Any:
    """Process the root YAML config file inplace."""

    # Root file cannot be abstract file
    if DeclarationType.ABSTRACT_FILE in yaml_data:
        file_context = f" File: '{file_path}'."
        raise AbstractKeyNotImplementedException(
            "Cannot process an abstract YAML file. "
            f"Abstract objects must be inherited in (patch) declarations.{file_context}"
        )

    # Root file is not inheriting, therefore is not sealed
    if DeclarationType.SEALED_FILE in yaml_data:
        yaml_data.pop(DeclarationType.SEALED_FILE)

    _process_file_declarations(yaml_data)
    injected_variables = _process_variables_until_stable(
        yaml_data,
        injected_variables,
        file_path,
    )

    context = ProcessingContext(
        directory=directory,
        loader=loader,
        file_path=file_path,
        variables=injected_variables,
        sub_files=set(),
        sub_declarations=set(),
        base_declarations=set(),
    )
    next_data: Optional[Any] = next_parser.process_next(
        yaml_data=yaml_data,
        context=context)
    yaml_data = next_data if next_data is not None else yaml_data

    # Removes base declarations that are a part of the root config.
    # Removes sub declarations that were not found earlier.
    for declaration in DeclarationType.BASE_KEY_DECLARATIONS | DeclarationType.SUB_KEY_DECLARATIONS:
        remove_all_key_declarations(yaml_data, "declaration", declaration)

    return yaml_data


def _process_variables_until_stable(yaml_data: Any, injected_variables: Dict, file_path: str) -> Dict:
    # In case injected variables contains additional variables, continue processing until file is no longer different
    unprocessed_yaml_data = None
    while yaml_data != unprocessed_yaml_data:
        unprocessed_yaml_data = copy.deepcopy(yaml_data) if isinstance(yaml_data, (dict, list)) else yaml_data
        global_variables = {}
        for key in list(injected_variables.keys()):
            if DeclarationType.GLOBAL in key:
                global_variables[key] = injected_variables.pop(key)
        injected_variables = process_variables(
            data=yaml_data,
            patch={},
            global_variables=global_variables,
            injected_variables=injected_variables,
            file_path=file_path,
        )
    return injected_variables


def process_patch_declaration(yaml_data: dict, context: ProcessingContext) -> Optional[Any]:
    """Find the patch declaration in yaml_data and inherit.
    Returns a replacement node if yaml_data should be replaced by another object (e.g., a list).
    Returns none if yaml_data should remain unmodified."""

    if DeclarationType.PATCH not in yaml_data:
        return

    # Convert patch to list format
    patch_data = yaml_data.pop(DeclarationType.PATCH)
    if isinstance(patch_data, list):
        patches = list(patch_data)
    else:
        patches = [patch_data]

    replacement_data = None
    for index, config_info in enumerate(patches):
        patch_path, base_data, config_info = _load_patch(config_info, context)
        _process_file_declarations(base_data)
        base_file_path = os.path.join(context.directory, patch_path)

        instantiation_variables = _process_patch_variables(
            base_data=base_data,
            config_info=config_info,
            context=context,
            base_file_path=base_file_path,
        )
        new_context = _build_patch_inheritance_context(
            context=context,
            patch_path=patch_path,
            instantiation_variables=instantiation_variables,
            base_file_path=base_file_path,
        )
        replacement_data = _inherit_patch(
            yaml_data=yaml_data,
            base_data=base_data,
            context=new_context,
        )
        if replacement_data is not None and index < len(patches) - 1:
            file_context = f" File: '{context.file_path}'."
            raise InvalidInstantiationException(
                "Multiple inheritance is not supported when a (patch) replaces the node with a list. "
                "Only the last patch can be list-typed. "
                "Use a keyed list with (append)/(prepend)/(merge) to combine lists instead."
                f"{file_context}"
            )
    return replacement_data


def _load_patch(config_info: Any, context: ProcessingContext) -> tuple[str, Any, Dict]:
    if isinstance(config_info, str):  # Only file path
        patch_path: str = config_info
        base_data = _read_yaml(
            file_path=os.path.join(context.directory, patch_path),
            loader=context.loader,
        )
        return patch_path, base_data, {}

    if isinstance(config_info, dict):  # File path and variables
        if (DeclarationType.PATCH_PATH not in config_info.keys() or
            len(config_info.keys()) != 2 or not
            any(DeclarationType.VARIABLES in key for key in config_info)):
            _raise_invalid_instantiation(
                context=context,
                config_info=config_info,
                reason="Expected keys: '(path)' and '(variables)' only."
            )
        patch_path: str = config_info[DeclarationType.PATCH_PATH]
        if not isinstance(patch_path, str):
            _raise_invalid_instantiation(
                context=context,
                config_info=config_info,
                reason=f"(path) must be a string, got {type(patch_path)}.",
            )
        base_data = _read_yaml(
            file_path=os.path.join(context.directory, patch_path),
            loader=context.loader,
        )
        return patch_path, base_data, config_info

    _raise_invalid_instantiation(
        context=context,
        config_info=config_info,
        reason=f"Expected a string or dict, got {type(config_info)}.",
    )


def _raise_invalid_instantiation(context: ProcessingContext, config_info: Any, reason: str) -> None:
    file_context = f" File: '{context.file_path}'."
    info_context = f" Config info: {config_info}." if config_info is not None else ""
    raise InvalidInstantiationException(
        f"Instantiation with {DeclarationType.PATCH} must include only "
        f"{DeclarationType.PATCH_PATH} key with string value and "
        f"{DeclarationType.VARIABLES} key with a dict value. "
        f"Reason: {reason}.{file_context}{info_context}"
    )


def _process_patch_variables(base_data: Any, config_info: Dict, context: ProcessingContext, base_file_path: str) -> Dict[str, Any]:
    global_variables = {
        key: value for key, value in context.variables.items()
        if DeclarationType.GLOBAL in key}
    return process_variables(
        data=base_data,
        patch=config_info,
        global_variables=global_variables,
        injected_variables={},
        file_path=base_file_path,
    )


def _build_patch_inheritance_context(context: ProcessingContext, patch_path: str, instantiation_variables: Dict[str, Any], base_file_path: str) -> ProcessingContext:
    # Catch circular inheritance
    new_sub_files = context.sub_files.copy()
    if patch_path in new_sub_files:
        file_context = f" Parent file: '{context.file_path}'."
        chain_context = f" Loaded patches: {sorted(new_sub_files)}." if new_sub_files else ""
        raise CircularInheritanceException(
            f"Circular inheritance detected while loading '{patch_path}'."
            f"{file_context}{chain_context}"
        )
    new_sub_files.add(patch_path)
    return ProcessingContext(
        directory=context.directory,
        loader=context.loader,
        variables=instantiation_variables,
        sub_files=new_sub_files,
        file_path=base_file_path,
    )


def _inherit_patch(yaml_data: dict, base_data: Any, context: ProcessingContext) -> Optional[Any]:
    if not base_data:
        base_data = {}
    if isinstance(base_data, list) and isinstance(yaml_data, dict) and yaml_data != {}:
        base_context = f" Base file: '{context.file_path}'."
        raise MismatchedValueTypeException(
            "Type mismatch while inheriting patch. "
            f"Patch data is a list, but sub data is a dictionary.{base_context}"
        )
    if isinstance(base_data, dict) and isinstance(yaml_data, dict):
        inherit_parser.process_inherit(
            sub_data=yaml_data,
            base_data=base_data,
            context=context,
        )
        return None
    if isinstance(base_data, list) and yaml_data == {}:
        return base_data
    # Should not reach this point
    base_context = f" Base file: '{context.file_path}'."
    raise MismatchedValueTypeException(
        f"Type mismatch while inheriting patch. Patch type: {type(base_data)}."
        f"{base_context}"
    )


def _read_yaml(file_path: str, loader: type) -> Any:
    """Read a YAML file and return its content."""

    yaml_data: Any = {}
    try:
        with open(file_path, 'r') as file:
            yaml_data = yaml.load(file, Loader=loader)
    except Exception as e:
        raise Exception(f"Error reading YAML file '{file_path}': {e}")
    return yaml_data


def _process_file_declarations(yaml_data: Any) -> None:
    """Replaces all yaml_file's (..._file) declarations to key declarations inplace."""
    
    if not isinstance(yaml_data, dict):
        return

    abstract_config: bool
    sealed_config: bool
    override_config: bool
    abstract_config, sealed_config, override_config = False, False, False
    if DeclarationType.ABSTRACT_FILE in yaml_data:
        abstract_config = True
        yaml_data.pop(DeclarationType.ABSTRACT_FILE)
    if DeclarationType.SEALED_FILE in yaml_data:
        sealed_config = True
        yaml_data.pop(DeclarationType.SEALED_FILE)
    if DeclarationType.OVERRIDE_FILE in yaml_data:
        override_config = True
        yaml_data.pop(DeclarationType.OVERRIDE_FILE)

    for key in list(yaml_data.keys()):
        if key == DeclarationType.PATCH:
            continue
        if key == DeclarationType.VARIABLES:
            continue

        if abstract_config:
            key = _add_key_declaration(yaml_data, key, DeclarationType.ABSTRACT)
        if sealed_config:
            key = _add_key_declaration(yaml_data, key, DeclarationType.SEALED)
        if override_config:
            key = _add_key_declaration(yaml_data, key, DeclarationType.OVERRIDE)


def _add_key_declaration(data: dict, key: str, declaration: str): 
    """Adds a declaration to a key in the YAML data."""
    new_key = declaration + " " + key
    new_data = data[key]
    data.pop(key)
    data[new_key] = new_data
    return new_key
