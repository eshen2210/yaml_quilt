import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)


def remove_key_declaration(data: dict, key: str, declaration: str) -> str:
    """Remove a declaration from a specific key of the YAML data inplace.
       Returns the new key without the declaration"""

    new_key = key.replace(declaration + " ", "")
    new_data = data[key]
    data.pop(key, None)
    data[new_key] = new_data
    return new_key


def remove_all_key_declarations(data, mode: str, declaration: str):
    """Removes all keys and subkeys that declares declaration inplace.
       Mode == "declaration" to remove declaration.
       Mode == "key" to remove entire key."""
    if isinstance(data, dict):
        for key in list(data.keys()):
            if declaration in key:
                if mode == "key":
                    data.pop(key)
                elif mode == "declaration":
                    remove_key_declaration(data, key, declaration)
            else:
                remove_all_key_declarations(data[key], mode, declaration)
    elif isinstance(data, list):
        for item in data:
            remove_all_key_declarations(item, mode, declaration)
    return data
