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
    KeySealedException,
    ConflictingDeclarationException,
    NoOverrideException,
    InvalidDeclarationException,
    CircularInheritanceException,
    AbstractKeyNotImplementedException)


def test_override_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'override_config', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_configs', 'override_config', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_failed_abstract_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'failed_abstract_config', 'sub_config.yaml')
    with pytest.raises(AbstractKeyNotImplementedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is AbstractKeyNotImplementedException


def test_abstract_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'abstract_config', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_configs', 'abstract_config', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_sealed_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'sealed_config', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_configs', 'sealed_config', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_failed_sealed_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'failed_sealed_config', 'sub_config.yaml')
    with pytest.raises(KeySealedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is KeySealedException


def test_sealed_override_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'sealed_override_config', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_configs', 'sealed_override_config', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)


def test_failed_sealed_override_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'failed_sealed_override_config', 'sub_config.yaml')
    with pytest.raises(KeySealedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is KeySealedException


def test_failed_nested_sealed_config():
    input_path = os.path.join(TESTS_DIR, 'test_configs', 'failed_nested_sealed_config', 'sub_config.yaml')
    with pytest.raises(KeySealedException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is KeySealedException
