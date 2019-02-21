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


def test___init__():
    for type in DataType.ALL:
        dt = DataType(type)
        assert dt.name == type

    with pytest.raises(ValueError) as ex:
        DataType(None)
    assert str(ex.value) == 'Name must be specified.'

    with pytest.raises(ValueError) as ex:
        DataType('not-a-valid-type')
    assert str(ex.value) == 'Invalid data type: not-a-valid-type'


def test_to_project_path(mk_tempdir):
    temp_dir = mk_tempdir()
    for type in DataType.ALL:
        dt = DataType(type)
        assert dt.to_project_path(temp_dir) == os.path.join(temp_dir, 'data', dt.name)
