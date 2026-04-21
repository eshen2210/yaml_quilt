# yaml_quilt

A Python library that enables inheritance, variables, and instantiation in YAML files via inline declarations.

## Installation

```bash
pip install yaml_quilt
```

## Overview

YamlQuilt allows templating of YAML files using **inline declarations** and **depth-first search (DFS)** traversal, through three key features: **Variables**, **File Inheritance**, and **Declarative Rules**. The DFS approach allows declarative rules to persist to child elements, even across inherited files.

YamlQuilt aims for yaml readability by avoiding {{ Helm-style }} templating and in-line programming logic:

```python
import yaml
from yaml_quilt import stitch, YamlQuiltException

try:
    result = stitch(
        file_path="root_config.yaml",
        directory="/path/to/config",
        Loader=yaml.SafeLoader,
        variables={"<var1>": "value1"}
    )
except YamlQuiltException as e:
    print(f"Error: {e}")
```

```yaml
# config.yaml
(patch): config_path/patch.yaml
(override) base_key1: <variable1>
---
# patch.yaml
(abstract) base_key1:
base_key2: value2
---
# yaml_quilt output
base_key1: value1
base_key2: value2
```

## Logical Flow

1. **Load YAML** into Python objects (dict/list/scalars) via PyYAML
2. Convert **config-level declarations** (like `(override_file)`) into top-level key declarations
3. Run **variable substitution** using DFS repeatedly until no more substitutions can occur
4. Run **`(patch)` expansion** as a pre-pass: expand all `(patch)` nodes before processing other keys. For each expansion, repeat steps 1–4 and apply inheritance rules via DFS.
5. Strip declaration markers from output keys / variable maps
6. Return Python objects (dict/list/scalars)

## Declaration Syntax

Declarations are inline prefixes. **Spacing matters** — always include a trailing space after the declaration:

✅ `(override) key`  
❌ `(override)key`

Multiple declarations can be combined:

```yaml
(override) (sealed) (optional) key: <variable1>_some_string_<variable2>
```
