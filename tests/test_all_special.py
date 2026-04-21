import pytest
import os
import sys
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TESTS_DIR = os.path.join(BASE_DIR, 'tests')
sys.path.append(BASE_DIR)

from yaml_quilt.core import stitch
from tests.test import assert_result_config
from yaml_quilt.core.custom_errors import (
    KeySealedException, 
    ConflictingDeclarationException, 
    NoOverrideException, 
    InvalidDeclarationException,
    CircularInheritanceException)


def test_failed_circular_inheritance():
    input_path = os.path.join(TESTS_DIR, 'test_special', 'failed_circular_inheritance', 'sub_config.yaml')
    with pytest.raises(CircularInheritanceException) as executeInfo:
        stitch(file_path=input_path, directory=TESTS_DIR, Loader=yaml.FullLoader)
    assert executeInfo.type is CircularInheritanceException


def test_patch_process_first():
    input_path = os.path.join(TESTS_DIR, 'test_special', 'patch_process_first', 'sub_config.yaml')
    expected_path = os.path.join(TESTS_DIR, 'test_special', 'patch_process_first', 'result_config.yaml')
    assert_result_config(input_path, expected_path, TESTS_DIR)
