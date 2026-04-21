# Inheritance

`(patch)` loads another YAML file and **inherits** it into the current node while preserving depth hierarchy.

```yaml
(patch): path/to/base.yaml
```

Inherit with variables:

```yaml
(patch):
  (path): path/to/base.yaml
  (variables):
    <name>: service_a
    <port>: 8080
```

Inherit multiple files (applied top to bottom):

```yaml
(patch):
  - path/to/base1.yaml
  - path/to/base2.yaml
  - (path): path/to/base3.yaml
    (variables):
      <name>: base_name3
```

Variables are scoped locally to each YAML file unless `(global)` or `(carryover)` is used. `(variables)` in the sub YAML do not pass to base YAMLs, and `(variables)` declared within `(patch)` are scoped only to that base YAML.

Example:

```yaml
# Sub YAML
(variables):
  <name>: sub_name
sub_name: <name>
sub_key: sub_value
services:
  base_service1:
    (patch):
      (path): path/to/base.yaml
      (variables):
        <name>: service_a
        <port>: 8080
  base_service2:
    (patch):
      (path): path/to/base.yaml
      (variables):
        <name>: service_b
        <port>: 8080
---
# Base YAML
base_name: <name>
base_port: <port>
```

Renders to:

```yaml
sub_name: sub_name
sub_key: sub_value
services:
  base_service1:
    base_name: service_a
    base_port: 8080
  base_service2:
    base_name: service_b
    base_port: 8080
```

---

## `(override)`, `(abstract)`, `(sealed)`, `(private)`

These keywords modify the behavior of `(patch)` inheritance.

- `(override)`: When the same key exists in both sub and base, the sub value is used.
- `(abstract)`: The sub YAML must implement this key at the same depth, or `stitch()` throws `AbstractKeyNotImplementedException`.
- `(sealed)`: A sub key may not `(override)` this key, or `stitch()` throws `KeySealedException`.
- `(private)`: The key is deleted before the `(patch)` inheritance process.

These keywords persist to all child elements, including `(patch)` YAMLs within those child elements.

```yaml
# Base YAML
(abstract) required_key:
(sealed) locked_key: base_locked
(private) internal_only: should_not_render
shared_key: base_shared
```

```yaml
# Sub YAML
(patch): base.yaml
required_key: provided_by_sub
# (override) locked_key: sub_locked  # Would throw KeySealedException
(override) shared_key: sub_shared
```

Renders to:

```yaml
required_key: provided_by_sub
locked_key: base_locked
shared_key: sub_shared
```

---

## `(append)`, `(prepend)`, `(merge)`

These keywords modify `(patch)` inheritance when both the sub and base values are sequences.

- `(append)`: Appends the sub sequence after the base sequence.
- `(prepend)`: Inserts the sub sequence before the base sequence.
- `(merge)`: Each index of the sub sequence applies inheritance rules against the matching index of the base sequence.

These keywords **do not persist** to child elements and only apply to matching keys at the same depth. If either value is not a sequence, `stitch()` throws `MismatchedValueTypeException`.

```yaml
# Base YAML
append_key:
  - base_key3: data3
  - base_key4: data4
prepend_key:
  - base_key3: data3
  - base_key4: data4
merge_key:
  - base_key3: data3
  - base_key4: data4
override_key:
  - base_key3: data3
  - base_key4: data4
---
# Sub YAML
(patch): path/to/base.yaml
(append) append_key:
  - sub_key1: data1
  - sub_key2: data2
(prepend) prepend_key:
  - sub_key1: data1
  - sub_key2: data2
(merge) merge_key:
  - sub_key1: data1
    (override) base_key3: overriden_data
  - sub_key2: data2
(override) override_key:
  - sub_key1: data1
  - sub_key2: data2
```

Renders to:

```yaml
append_key:
  - base_key3: data3
  - base_key4: data4
  - sub_key1: data1
  - sub_key2: data2
prepend_key:
  - sub_key1: data1
  - sub_key2: data2
  - base_key3: data3
  - base_key4: data4
merge_key:
  - sub_key1: data1
    base_key3: overriden_data
  - sub_key2: data2
    base_key4: data4
override_key:
  - sub_key1: data1
  - sub_key2: data2
```

---

## File-wide Keywords: `(abstract_file)`, `(sealed_file)`, `(override_file)`

File keywords apply a keyword to every top-level key in the file.

```yaml
(abstract_file)
abstract_key1: must_be_implemented
  abstract_subkey: must_be_implemented
abstract_key2: must_be_implemented
```

Is equivalent to:

```yaml
(abstract) abstract_key1: must_be_implemented
  abstract_subkey: must_be_implemented  # Also abstract — abstract persists to child elements
(abstract) abstract_key2: must_be_implemented
```
