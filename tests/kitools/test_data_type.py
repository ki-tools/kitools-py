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
    assert str(ex.value) == 'Invalid data type: None'

    with pytest.raises(ValueError) as ex:
        DataType('not-a-valid-type')
    assert str(ex.value) == 'Invalid data type: not-a-valid-type'


def test_to_project_path(mk_tempdir):
    temp_dir = mk_tempdir()
    for type in DataType.ALL:
        dt = DataType(type)
        assert dt.to_project_path(temp_dir) == os.path.join(temp_dir, DataType.DATA_DIR_NAME, dt.name)


@pytest.fixture()
def mk_data_dir(mk_tempdir):
    def _mk():
        project_path = mk_tempdir()
        data_path = os.path.join(project_path, DataType.DATA_DIR_NAME)
        os.mkdir(data_path)
        return project_path, data_path

    yield _mk


def test_from_project_path(mk_data_dir):
    project_path, data_path = mk_data_dir()

    for data_type_name in DataType.ALL:
        data_type = DataType(data_type_name)
        path = data_type.to_project_path(project_path)
        assert DataType.from_project_path(project_path, path).name == data_type_name

        other_paths = []
        for other_path in ['one', 'two', 'three', 'file.csv']:
            other_paths.append(other_path)
            new_path = os.path.join(path, *other_paths)
            assert DataType.from_project_path(project_path, new_path).name == data_type_name

    with pytest.raises(ValueError) as ex:
        DataType.from_project_path(project_path, data_path)
    assert 'Invalid data type:' in str(ex.value)


def test_is_project_data_path(mk_data_dir):
    project_path, data_path = mk_data_dir()

    assert DataType.is_project_data_path(data_path, data_path) is False
    # TODO: add more tests
