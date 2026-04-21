import pytest
import os
import sys
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TESTS_DIR = os.path.join(BASE_DIR, 'tests')
sys.path.append(BASE_DIR)

from yaml_quilt.core import stitch


def assert_result_config(input_path, expected_path, directory, variables=None):
    if variables is None:
        variables = {}
    input_data = stitch(file_path=input_path, directory=directory, Loader=yaml.FullLoader, variables=variables)

    try:
        with open(expected_path, 'r') as file:
            expected_data = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as e:
        raise Exception(f"Error reading YAML file: {e}")
    
    if input_data is None or input_data == {}:
        pytest.fail("Could not load input and result YAML files")
    assert input_data == expected_data, f"Expected {expected_data}, but got {input_data}"
