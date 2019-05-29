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
from src.kitools import DataTypeTemplate


def test_it_gets_all_templates():
    all = DataTypeTemplate.all()
    assert len(all) == 2
    for template in all:
        assert template.name in ['rally', 'generic']


def test_it_gets_the_default_template():
    expected_template = next(t for t in DataTypeTemplate.all() if t.is_default)
    template = DataTypeTemplate.default()
    assert template == expected_template


def test_it_gets_a_template_by_name():
    name = DataTypeTemplate.all()[-1].name
    template = DataTypeTemplate.get(name)
    assert template.name == name


def test_it_registers_a_template():
    template = DataTypeTemplate('test', 'test', [])
    DataTypeTemplate.register(template)
    assert template in DataTypeTemplate._templates
