"""
Parsing context for YAML Compose operations. Essentially a set of variables that are passed around and manipulated during the DFS.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Set
from ..declarations import DeclarationType
from ..custom_errors import (
    ConflictingDeclarationException,
)
from .parse_functions import remove_key_declaration


@dataclass
class ProcessingContext:
    """Context for YAML Compose processing operations."""

    # High level parser information
    directory: str
    loader: type
    file_path: str
    variables: Dict[str, Any] = field(default_factory=dict)
    sub_files: Set[str] = field(default_factory=set)

    # Declarations includes parent declarations and current element declarations
    # When not inheriting, active declarations are stored in sub_declarations while base_declrations should be empty
    sub_declarations: Set[str] = field(default_factory=set)
    base_declarations: Set[str] = field(default_factory=set)

    def extract_base_declarations(self, base_data, base_key: str) -> tuple[str, Set]:
        """Returns the base_key without imported declarations and returns base_declarations from base_key.
        Modifies base_data inplace.
        Checks for conflicting declarations."""
        
        base_declarations: Set[str] = set()

        # Remove sub_declarations from base key as they have already been processed
        for declaration in DeclarationType.SUB_KEY_DECLARATIONS:
            if declaration in base_key:
                base_key = remove_key_declaration(base_data, base_key, declaration)

        # Add base declarations
        for declaration in DeclarationType.BASE_KEY_DECLARATIONS:
            if declaration in base_key:
                base_declarations.add(declaration)
        
        total_base_declarations = self.base_declarations | base_declarations

        # Check conflicting declarations for base key inheritance
        conflicting_base_declarations = {
            DeclarationType.ABSTRACT,
            DeclarationType.SEALED,
            DeclarationType.PRIVATE
        }
        if len(total_base_declarations.intersection(conflicting_base_declarations)) > 1:
            file_context = f" File: '{self.file_path}'."
            raise ConflictingDeclarationException(
                f"Key: '{base_key}' cannot declare more than one of: abstract, sealed, private.{file_context}"
            )

        return base_key, base_declarations

    def extract_sub_declarations(self, sub_data, sub_key: str) -> tuple[str, set]:
        """Returns the sub_key without imported declarations and sub_declarations from sub_key.
        Modifies sub_data inplace.
        Checks for conflicting declarations."""
        
        sub_declarations: Set[str] = set()
        
        # Add sub_declarations
        for declaration in DeclarationType.SUB_KEY_DECLARATIONS:
            if declaration in sub_key:
                sub_declarations.add(declaration)
        
        total_sub_declarations = self.sub_declarations | sub_declarations

        # Check conflicting declarations for list inheritance
        conflicting_sub_list_declarations = {
            DeclarationType.APPEND,
            DeclarationType.PREPEND,
            DeclarationType.MERGE
        }
        if len(total_sub_declarations.intersection(conflicting_sub_list_declarations)) > 1:
            file_context = f" File: '{self.file_path}'."
            raise ConflictingDeclarationException(
                f"Key: '{sub_key}' cannot declare more than one of: append, prepend, merge.{file_context}"
            )

        return sub_key, sub_declarations

    def persistent_sub_declarations(self, sub_declarations: Set[str]) -> Set[str]:
        """Return sub_declarations merged with current context, excluding non-persistent declarations.
           Intended to be called as context is passed down to child depth."""
        merged = self.sub_declarations | sub_declarations
        return merged - DeclarationType.NON_PERSISTENT_SUB_KEY_DECLARATIONS
    
    def extract_next_declarations(self, next_data, next_key: str) -> tuple[str, set]:
        """Returns the next_key without imported declarations and sub_declarations from next_key.
        Modifies next_data inplace.
        Checks for conflicting declarations."""
        
        next_declarations: Set[str] = set()
        
        # Remove sub_declarations
        for declaration in DeclarationType.SUB_KEY_DECLARATIONS:
            if declaration in next_key:
                next_key = remove_key_declaration(next_data, next_key, declaration)
                next_declarations.add(declaration)
        
        # Do not remove base_declarations but track them to catch conflicts
        for declaration in DeclarationType.BASE_KEY_DECLARATIONS:
            if declaration in next_key:
                next_declarations.add(declaration)
        
        total_next_declarations = self.sub_declarations | next_declarations

        # Check conflicting declarations for list inheritance
        conflicting_next_declarations = {
            DeclarationType.ABSTRACT,
            DeclarationType.SEALED,
            DeclarationType.PRIVATE
        }
        if len(total_next_declarations.intersection(conflicting_next_declarations)) > 1:
            file_context = f" File: '{self.file_path}'."
            raise ConflictingDeclarationException(
                f"Key: '{next_key}' cannot declare more than one of: abstract, sealed, private.{file_context}"
            )

        return next_key, next_declarations
