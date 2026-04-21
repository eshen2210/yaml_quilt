from typing import Any, Optional

import yaml_quilt.core.parser.config_parser as config_parser
from ..declarations import DeclarationType
from .context import ProcessingContext


def process_next(yaml_data: Any, context: ProcessingContext) -> Optional[Any]:
    """Traverse yaml_data to process patch declarations.
    Returns a replacement node if the current yaml_data should be replaced by another object (e.g., a list).
    Otherwise returns None if yaml_data should be unmodified."""

    if isinstance(yaml_data, list):
        _process_next_list(yaml_data, context)
        return None
    if isinstance(yaml_data, dict):
        return _process_next_dict(yaml_data, context)
    return None


def _process_next_list(yaml_data: list, context: ProcessingContext) -> None:
    # Process (patch) declarations in the list itself first.
    i = 0
    while i < len(yaml_data):
        item = yaml_data[i]
        if isinstance(item, dict) and DeclarationType.PATCH in item:
            base_data = config_parser.process_patch_declaration(
                yaml_data=item,
                context=context,
            )
            yaml_data[i] = base_data if base_data is not None else yaml_data[i]
            if isinstance(yaml_data[i], list):
                yaml_data[i:i + 1] = yaml_data[i]
            continue
        i += 1
    
    # Process non (patch) items later.
    for item in yaml_data:
        process_next(
            yaml_data=item,
            context=context,
        )


def _process_next_dict(yaml_data: dict, context: ProcessingContext) -> Optional[Any]:
    if DeclarationType.PATCH in yaml_data:
        base_data = config_parser.process_patch_declaration(
            yaml_data=yaml_data,
            context=context,
        )
        if base_data is not None:
            return base_data

    for key in list(yaml_data.keys()):
        key, declarations = context.extract_next_declarations(yaml_data, key)
        next_context = ProcessingContext(
            directory=context.directory,
            loader=context.loader,
            variables=context.variables,
            sub_files=context.sub_files.copy(),
            sub_declarations=context.persistent_sub_declarations(declarations),
            base_declarations=set(),
            file_path=context.file_path,
        )
        next_data = process_next(
            yaml_data=yaml_data[key],
            context=next_context,
        )
        yaml_data[key] = next_data if next_data is not None else yaml_data[key]
    return None
