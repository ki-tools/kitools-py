import pytest
from src.kitools.exceptions import InvalidDataTypeError, NotADataTypePathError


@pytest.fixture()
def data_types(mk_kiproject):
    return mk_kiproject().data_types


def test_InvalidDataTypeError(data_types):
    ex = InvalidDataTypeError('test', data_types)

    all = [d.name for d in data_types]
    assert str(ex) == 'Invalid DataType: {0}. Must of one of: {1}'.format('test', ', '.join(all))


def test_NotADataTypePathError(data_types):
    ex = NotADataTypePathError('/tmp/a/path', data_types)
    assert 'must be in one of the data directories:' in str(ex)
