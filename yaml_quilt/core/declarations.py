"""
Declarations (keywords) using in YAML compose processing.
"""

from dataclasses import dataclass, field


class DeclarationType():
    """Types of declarations that can be applied to YAML elements."""

    PATCH = "(patch)"
    PATCH_PATH = "(path)"

    VARIABLES = "(variables)"
    OPTIONAL = "(optional)"
    DEFAULT = "(default)"
    DEFAULT_DELIMITER = " | "
    ENABLE_DELIMITER = " | "
    CARRYOVER = "(carryover)"
    GLOBAL = "(global)"

    ABSTRACT_FILE = "(abstract_file)"
    SEALED_FILE = "(sealed_file)"
    OVERRIDE_FILE = "(override_file)"

    ABSTRACT = "(abstract)"
    SEALED = "(sealed)"
    PRIVATE = "(private)"
    OVERRIDE = "(override)"
    APPEND = "(append)"
    PREPEND = "(prepend)"
    MERGE = "(merge)"
    ENABLE = "(enable)"

    # Convenience sets for different declaration categories

    # Declarations available to keys in base class
    BASE_KEY_DECLARATIONS = {
        ABSTRACT,
        SEALED,
        PRIVATE,
        OPTIONAL,
        DEFAULT
    }

    # Declarations available to keys in sub class
    SUB_KEY_DECLARATIONS = {
        OVERRIDE,
        APPEND,
        PREPEND,
        MERGE,
        OPTIONAL,
        DEFAULT
    }

    # Declarations available to keys in sub class that do not persist to child elements
    NON_PERSISTENT_SUB_KEY_DECLARATIONS = {
        APPEND,
        PREPEND,
        MERGE,
    }

    # Declarations available to variables
    VARIABLE_DECLARATIONS = {
        ABSTRACT,  # Abstract variables cannot be used until overriden.
        SEALED,  # Sealed variables cannot be overriden.
        OVERRIDE,
        CARRYOVER,  # Declared during instantiation. Inherits variables from patch during instantiation.
        GLOBAL,  # Declared anywhere. Inherits variables from patch through all levels of instantiation.
        OPTIONAL,
        DEFAULT,
        ENABLE
    }

    # Declarations for entire file
    FILE_DECLARATIONS = {
        ABSTRACT_FILE,
        SEALED_FILE,
        OVERRIDE_FILE
    }
   

@dataclass(frozen=True)
class Declarations:
    """Represents a declaration (keyword) applied to a YAML element."""
    
    type: DeclarationType
    parsed_key: str
    original_key: str

    
