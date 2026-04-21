# Variables

Variables substitute scalar string values across the YAML file.

Variables can be added as Python arguments:

```python
injected_variables = {
    "<name>": "my_service",
    "<port>": 8080
}

result = stitch(
    file_path="root_config.yaml",
    directory="/path/to/config",
    Loader=yaml.SafeLoader,
    variables=injected_variables
)
```

And/or as `(patch)` instantiation parameters:

```yaml
(patch):
  - (path): /path/to/config/config.yaml
  - (variables):
      <name>: my_service
      <port>: 8080
```

And/or as a `(variables)` definition in the root of your dict YAML:

```yaml
(variables):
  <name>: my_service
  <port>: 8080
```

If the root of your YAML is a list, declare `(variables)` as a list item instead:

```yaml
- (variables):
    <var1>: my_service
    <var2>: 8080
```

Then reference them anywhere in scalar (sub)string values:

```yaml
service:
  name: <name>
  port: <port>
```

It's recommended to use distinct variable tokens (e.g., `<variable>` with angle brackets) to avoid accidental substring replacement. If two variable keys overlap inside the same string, `stitch()` will raise `AmbiguousVariableException`.

---

## Replacement Behavior

A scalar variable can be substituted into a YAML string value:

```yaml
(variables):
  <int-var>: 1
  <string-var>: value

full_replacement: <int-var>
substring_replacement: prefix-<string-var>
multiple_substring_replacement: prefix-<string-var>-<string-var>
```

Renders to:

```yaml
full_replacement: 1
substring_replacement: prefix-value
multiple_substring_replacement: prefix-value-value
```

If a variable value is a **dict or list**, it replaces the **entire YAML node**, not a substring.

- ✅ Allowed: `key: <some_dict_or_list>`
- ❌ Not allowed: `key: "prefix-<some_dict_or_list>"`

Example:

```yaml
(variables):
  <variable_dict>:
    replaced_key1: replaced_value1
    replaced_key2:
      - replaced_item1
  <var1>: val1
  <var2>: val2

root:
  key: <variable_dict>
  key2: <var1>-string-<var2>
```

Renders to:

```yaml
root:
  key:
    replaced_key1: replaced_value1
    replaced_key2:
      - replaced_item1
  key2: val1-string-val2
```

---

## Precedence

Variables are applied in this order (earlier sources have higher priority):

1. **`variables=` passed to `stitch()`** *(only for the root YAML load)*
2. **Instantiation variables** from the `(variables)` block under the `(patch)` that loaded the current YAML
3. **`(global)` variables**
4. **The local `(variables)` block at the root of the current YAML**

Variable scope is limited to the YAML file it is applied to, with the exception of `(global)` and `(carryover)` variables which can persist through nested `(patch)` calls.

---

## `(global)`

`(global)` variables are visible to the local YAML scope and all nested `(patch)` YAMLs.

```yaml
# Sub YAML
(variables):
  (global) <env>: prod
config:
  (patch):
    (path): path/to/baselevel1.yaml
    (variables):
      (global) <api>: v1
---
# Base YAML Level 1
# path/to/baselevel1.yaml
(patch): path/to/baselevel2.yaml
---
# Base YAML Level 2
# path/to/baselevel2.yaml
api: <api>
env: <env>
```

Renders to:

```yaml
config:
  api: v1
  env: prod
```

---

## `(override)`, `(abstract)`, `(sealed)` on Variables

These keywords modify the behavior of variables defined under `(variables)`.

- `(override)`: A higher-priority scope overrides the value of the same key in a lower-priority scope.
- `(abstract)`: The higher-priority source **must** implement this key, or `stitch()` throws `AbstractKeyNotImplementedException`.
- `(sealed)`: Lower-priority sources may not override this variable, or `stitch()` throws `KeySealedException`.

These keywords persist to all child elements, including `(patch)` YAMLs within those child elements.

```yaml
# Base YAML
(variables):
  (abstract) <required_var>:
  (sealed) <locked_var>: base_sealed
  <shared_var>: base_value

dict:
  required: <required_var>
  locked: <locked_var>
  shared: <shared_var>
---
# Sub YAML
(patch):
  (path): path/to/base.yaml
  (variables):
    <required_var>: provided_by_sub
    # (override) <locked_var>: sub_locked   # Would throw KeySealedException
    (override) <shared_var>: sub_overriden
```

Renders to:

```yaml
dict:
  required: provided_by_sub
  locked: base_sealed
  shared: sub_overriden
```

---

## `(optional)`

For `(optional)` keys, if its value is not a variable reference the key is removed. `(optional)` values must be a scalar or `stitch()` will throw `InvalidDeclarationException`.

```yaml
(variables):
  <defined>: ok

dict:
  (optional) keep_me: <defined>
  (optional) drop_me: <missing>
list:
  - (optional) <defined>
  - (optional) <missing>
```

Renders to:

```yaml
dict:
  keep_me: ok
list:
  - ok
```

---

## `(default)`

The value must contain the delimiter ` | ` (whitespace on both sides). If the left substring is a variable reference, the entire value is replaced by the variable. Otherwise, the entire value is replaced by the right substring.

```yaml
(variables):
  <val1>: replaced_val1

dict:
  (default) key1: <val1> | default_val1
  (default) key2: <val2> | default_val2
list:
  - (default) <val1> | default_val1
  - (default) <val2> | default_val2
```

Renders to:

```yaml
dict:
  key1: replaced_val1
  key2: default_val2
list:
  - replaced_val1
  - default_val2
```

The default value is parsed as a Python literal when possible (e.g., `2` becomes an int).

---

## `(enable)`

`(enable)` keeps its parent block if its value == `True`, otherwise deletes it.

- Parent is a **dict**: keeps or deletes the parent key and entire dict.
- Parent is a **list** and `(enable)` is the only list item: keeps or deletes the entire list.
- Parent is a **list** and `(enable)` is a key within a dict list item: keeps or deletes only that item.

```yaml
(variables):
  <enable_dict>: true
  <enable_list>: true
  <enable_list_item>: true

root:
  enabled_dict:
    (enable): <enable_dict>
    key1: value1
    key2: value2
  disabled_dict:
    (enable): <missing_or_false>
    key3: value3
    key4: value4
  enabled_list:
    - (enable): <enable_list>
    - item1
    - item2
  disabled_list:
    - (enable): <missing_or_false>
    - itemA
    - itemB
  list_of_dicts:
    - (enable): <enable_list_item>
      enabled_key1: value1
      enabled_key2: value2
    - (enable): <missing_or_false>
      disabled_keyA: valueA
      disabled_keyB: valueB
```

Renders to:

```yaml
root:
  enabled_dict:
    key1: value1
    key2: value2
  enabled_list:
    - item1
    - item2
  list_of_dicts:
    - enabled_key1: value1
      enabled_key2: value2
```

---

## `(carryover)`

A `(carryover)` variable is a valueless key used inside `(patch)` variables to pull a variable from the sub YAML scope into the base YAML scope.

```yaml
# Sub YAML
(variables):
  <var>: sub_value
(patch):
  (path): path/to/base.yaml
  (variables):
    (carryover) <var>:
---
# Base YAML
base_key: <var>
```

Renders to:

```yaml
base_key: sub_value
```
