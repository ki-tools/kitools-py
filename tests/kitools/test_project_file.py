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
from src.kitools import ProjectFile


def test__init__():
    test_remote_uri = 'syn:syn123'
    test_path = '/tmp/test.csv'
    test_version = '1.2'
    project_file = ProjectFile(remote_uri=test_remote_uri, local_path=test_path, version=test_version)

    assert project_file.remote_uri == test_remote_uri
    assert project_file.local_path == test_path
    assert project_file.version == test_version
