import pytest
import os
from src.kitools import DataType


def test_it_json_serializes_rel_path_as_posix_path():
    # NOTE: This test needs to be run in each supported env (Linux/Mac, Windows).
    data_type = DataType('/tmp/a/path', 'test', os.path.join('a', 'b', 'c'))
    json = data_type.to_json()
    assert '\\' not in json['rel_path']
    assert '/' in json['rel_path']


def test___eq__():
    a = DataType('/tmp', 'test', 'test')
    b = DataType('/tmp', 'test', 'test')
    assert a == b

    b = DataType('/tmp_', 'test', 'test')
    assert a != b

    b = DataType('/tmp', 'test_', 'test')
    assert a != b

    b = DataType('/tmp', 'test', 'test_')
    assert a != b
