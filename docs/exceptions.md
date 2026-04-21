# Exceptions

All exceptions raised by yaml_quilt use a base exception class: `YamlQuiltException`.

| Exception | Cause |
|-----------|-------|
| `NoOverrideException` | Tried to override a key without `(override)` |
| `AbstractKeyNotImplementedException` | Sub YAML did not implement an `(abstract)` key |
| `KeySealedException` | Attempted to override a `(sealed)` key or variable |
| `ConflictingDeclarationException` | Incompatible declarations applied together |
| `InvalidInstantiationException` | Bad `(patch)` structure |
| `CircularInheritanceException` | Cyclic `(patch)` references |
| `InvalidDeclarationException` | Declaration with incorrect key/value content or format |
| `MismatchedValueTypeException` | Declaration used with incorrect value type (e.g., `(append)` expects a list but received a dict) |
| `AmbiguousVariableException` | Overlapping variable keys detected in the same string |
