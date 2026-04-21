class YamlQuiltException(Exception):
    """Base exception for all yaml_quilt-specific errors."""

    def __init__(self, message: str):
        super().__init__(message)


class CircularInheritanceException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class KeySealedException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class ConflictingDeclarationException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class NoOverrideException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


# TO DO
class AmbiguousVariableException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class InvalidInstantiationException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class InvalidDeclarationException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class MismatchedValueTypeException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)


class AbstractKeyNotImplementedException(YamlQuiltException):
    def __init__(self, message):
        super().__init__(message)