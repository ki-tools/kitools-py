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
from src.kitools.sys_path import SysPath


def test_it_expands_user():
    syspath = SysPath('~')
    assert syspath.abs_path == os.path.expanduser('~')


def test_it_expands_vars():
    # TODO: test this
    pass


def test_it_sets_the_abs_path():
    # TODO: test this
    pass


def test_it_sets_the_rel_path():
    # TODO: test this
    pass
