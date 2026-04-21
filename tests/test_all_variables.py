import pytest
import os
import sys
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TESTS_DIR = os.path.join(BASE_DIR, 'tests')
sys.path.append(BASE_DIR)

from tests.test import assert_result_config
from yaml_quilt.core import stitch
from yaml_quilt.core.custom_errors import (
    AmbiguousVariableException,
    KeySealedException,
    ConflictingDeclarationException,
    NoOverrideException,
    InvalidDeclarationException,
    CircularInheritanceException,
    AbstractKeyNotImplementedException)


def test_variable():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'variable', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'variable', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)
    

def test_list_variable():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'list_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'list_variables', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_multiple_variable():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'multiple_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'multiple_variables', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_instantiation():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'instantiation', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'instantiation', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_multiple_instantiation():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'multiple_instantiation', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'multiple_instantiation', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_abstract_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'abstract_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'abstract_variables', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_failed_abstract_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'failed_abstract_variables', 'sub_config.yaml')
    with pytest.raises(AbstractKeyNotImplementedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is AbstractKeyNotImplementedException


def test_failed_sealed_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'failed_sealed_variables', 'sub_config.yaml')
    with pytest.raises(KeySealedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is KeySealedException


def test_failed_ambiguous_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'failed_ambiguous_variables', 'sub_config.yaml')
    with pytest.raises(AmbiguousVariableException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is AmbiguousVariableException


def test_nested_instantiation():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'nested_instantiation', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'nested_instantiation', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_nested_global_instantiation():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'nested_global_instantiation', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'nested_global_instantiation', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_inject_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'inject_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'inject_variables', 'result_config.yaml')
    variable_injection = {
        'var1': "injected_value",
        'var2': {
            'subkey1': "sub_value1",
            'subkey2': "sub_value2"
        },
        'var3': [1, 2, 3, 4, 5],
        'var4': {
            'subkey3': "sub_value3"
        }
    }
    assert_result_config(input_path, expected_path, TESTS_DIR, variable_injection)


def test_inject_instantiation():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'inject_instantiation', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'inject_instantiation', 'result_config.yaml')
    variable_injection = {
        '<var3>': 'injected_value3',
        '<patch1>': 'test_variables/inject_instantiation/patch1.yaml',
        '<patch2>': 'test_variables/inject_instantiation/patch2.yaml',
        '<patch3>': [{
            '(path)': 'test_variables/inject_instantiation/patch3.yaml',
            '(variables)': {
                '<var1>': 'injected_value1',
                '(carryover) <var3>': ''
            }
        }],
        '<patch4>': [{
            '(path)': 'test_variables/inject_instantiation/patch4.yaml',
            '(variables)': {
                '<var4>': 'injected_value4',
                '<var5>': 'injected_value5',
            }
        }]
    }
    assert_result_config(input_path, expected_path, TESTS_DIR, variable_injection)


def test_global_injection():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'global_injection', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'global_injection', 'result_config.yaml')
    variable_injection = {
        '<patch_injection>': 'test_variables/global_injection/patch_level1.yaml',
        '(global) <var1>': 'injected1',
        '(global) <var2>': 'injected2'
    }
    assert_result_config(input_path, expected_path, TESTS_DIR, variable_injection)


def test_global_injection_abstract_carryover():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'global_injection_abstract_carryover', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'global_injection_abstract_carryover', 'result_config.yaml')
    variable_injection = {
        '<patch>': 'test_variables/global_injection_abstract_carryover/patch_level1.yaml',
        '(global) var1': 'variable1',
        '(global) var2': 'variable2'
    }
    assert_result_config(input_path, expected_path, TESTS_DIR, variable_injection)


def test_default_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'default_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'default_variables', 'result_config.yaml')
    variable_injection = {
        '<injected_val3>': 'injected_val3',
        '<injected_val6>': 'injected_val6',
        '<injected_base_val3>': 'injected_base_val3'
    }
    assert_result_config(input_path, expected_path, TESTS_DIR, variable_injection)


def test_enable_variables():
    input_path = os.path.join(TESTS_DIR, 'test_variables', 'enable_variables', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_variables', 'enable_variables', 'result.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)
