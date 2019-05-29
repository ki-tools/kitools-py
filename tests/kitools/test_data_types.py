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
