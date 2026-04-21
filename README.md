# yaml_quilt

A Python library that enables inheritance, variables, and instantiation in YAML files via inline declarations.

## Installation

```bash
pip install yaml_quilt
```

## Overview

YamlQuilt is a Python library that allows templating of YAML files using **inline declarations** and **depth-first search (DFS)** traversal. This is accomplished through three key features: **Variables**, **File Inheritance**, and **Declarative Rules**. These declaration rules include inheritance rules such as abstract, sealed, private, etc and variable replacement rules such as default, optional, global, etc. The DFS approach allows declarative rules to persist to child elements, even across inherited files. 

YamlQuilt aims for yaml readability by avoiding {{ Helm-style }} templating and in-line programming logic. YamlQuilt's in-line declarations use a minimal format that always places declaration in the beginning of an element. YamlQuilt eliminates templating logic in Python and and calls YAML files the same way you would pyyaml's load():

```python
import yaml
from yaml_quilt import stitch, YamlQuiltException

# Define variables in Python code
injected_variables = {
    "<var1>": "value1"
}

# Process YAML with injected variables
try:
  result = stitch(
      file_path="root_config.yaml",
      directory="/path/to/config",
      Loader=yaml.SafeLoader,
      variables=injected_variables
  )
except YamlQuiltException as e:
   print(f"Error: {e}")
```

Processing behavior is defined within the Yaml file via in-line declarations.

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

## Documentation

Full documentation is available at **https://eshen2210.github.io/yaml_quilt/**.

## License

MIT License
