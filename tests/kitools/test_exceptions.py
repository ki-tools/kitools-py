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
import os
from src.kitools import DataType
from src.kitools.exceptions import InvalidDataTypeError, NotADataTypePathError


def test_InvalidDataTypeError():
    ex = InvalidDataTypeError('test', DataType.ALL)
    assert str(ex) == 'Invalid DataType: {0}. Must of one of: {1}'.format('test', ', '.join(DataType.ALL))


def test_NotADataTypePathError(mk_tempdir, mk_tempfile):
    data_path = mk_tempdir()
    bad_path = mk_tempfile()
    ex = NotADataTypePathError(data_path, bad_path, DataType.ALL)
    assert 'must be in one of the data directories:' in str(ex)
