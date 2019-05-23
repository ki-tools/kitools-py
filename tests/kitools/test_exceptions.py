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
from src.kitools.exceptions import InvalidKiDataTypeError, NotAKiDataTypePathError


@pytest.fixture()
def kiproject(mk_kiproject):
    return mk_kiproject()


def test_InvalidDataTypeError(kiproject):
    ex = InvalidKiDataTypeError('test', kiproject.data_types)

    all = [d.name for d in kiproject.data_types]
    assert str(ex) == 'Invalid DataType: {0}. Must of one of: {1}'.format('test', ', '.join(all))


def test_NotADataTypePathError(kiproject, mk_tempdir, mk_tempfile):
    data_path = mk_tempdir()
    bad_path = mk_tempfile()
    ex = NotAKiDataTypePathError(bad_path, kiproject.data_types)
    assert 'must be in one of the data directories:' in str(ex)
