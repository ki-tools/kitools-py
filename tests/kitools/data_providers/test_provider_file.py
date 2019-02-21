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
from src.kitools.data_providers import ProviderFile


def test___init__():
    test_id = 'syn001'
    test_name = 'test name'
    test_version = '1'
    test_local_path = '/tmp'
    test_raw = {'name': 'a object'}
    test_is_directory = True
    test_children = [ProviderFile('id', 'name', '1')]

    project_file = ProviderFile(
        test_id,
        test_name,
        test_version,
        local_path=test_local_path,
        raw=test_raw,
        is_directory=test_is_directory,
        children=test_children
    )

    assert project_file.id == test_id
    assert project_file.name == test_name
    assert project_file.version == test_version
    assert project_file.local_path == test_local_path
    assert project_file.raw == test_raw
    assert project_file.is_directory == test_is_directory
    assert project_file.children == test_children

    # Ensure version is a string
    assert ProviderFile('id', 'name', version=None).version is None
    assert ProviderFile('id', 'name', version=1).version == '1'
    assert ProviderFile('id', 'name', version='').version is None
