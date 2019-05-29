# Copyright 2018-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
