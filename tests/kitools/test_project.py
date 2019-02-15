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
from src.kitools import Project


def test___init__(temp_dir):
    project = Project(temp_dir)

    # Paths
    assert project.path == temp_dir
    assert project._config_path == os.path.join(temp_dir, Project.CONFIG_FILENAME)

    # Default config
    assert project._config == project.DEFAULT_CONFIG
    for data_type in project.DATA_TYPES:
        assert project._get_config_data(data_type) == {}
        assert project._get_config_data(data_type, source_id='syn000') is None

    # kwargs
    project = Project(temp_dir, title='title1', synapse_id='syn1')
    assert project.title == 'title1'
    assert project.synapse_id == 'syn1'

    # Invalid properties
    with pytest.raises(AttributeError) as ex:
        # On __init__
        Project(temp_dir, not_a_real_prop_name='test')
    assert str(ex.value) == 'Invalid config property: not_a_real_prop_name'

    with pytest.raises(AttributeError) as ex:
        # On _set_config_value
        project = Project(temp_dir)
        project._set_config_value('not_a_real_prop_name', 'test')
    assert str(ex.value) == 'Invalid config property: not_a_real_prop_name'


def test_set_get_delete_config_data(temp_dir):
    project = Project(temp_dir)

    for data_type in project.DATA_TYPES:
        source_id = 'syn001'
        path = os.path.join(temp_dir, data_type, 'testfile1.txt')
        modified = '2019-02-15T20:09:38.167Z'
        version = 1.2

        assert project._get_config_data(data_type) == {}
        assert project._get_config_data(data_type, source_id=source_id) is None

        project._set_config_data(data_type, source_id, path, modified, version)

        data = project._get_config_data(data_type, source_id=source_id)
        assert data is not None
        assert data['path'] == path
        assert data['modified'] == modified
        assert data['version'] == version

        project._delete_config_data(data_type, source_id)
        data = project._get_config_data(data_type, source_id=source_id)
        assert data is None

    # Invalid data types
    with pytest.raises(ValueError) as ex:
        project._set_config_data('not_a_real_data_type', '', '', '', '')
    assert str(ex.value) == 'Invalid data data_type: not_a_real_data_type'

    with pytest.raises(ValueError) as ex:
        project._get_config_data('not_a_real_data_type')
    assert str(ex.value) == 'Invalid data data_type: not_a_real_data_type'


def test__load_config(temp_dir):
    title = 'title1'
    synapse_id = 'syn1'

    # Create a config file
    Project(temp_dir, title=title, synapse_id=synapse_id)

    # Load the config
    project = Project(temp_dir)

    assert project.title == title
    assert project.synapse_id == synapse_id

    # Loads if the config file doesn't exist and saves once a prop is set
    os.remove(project._config_path)
    project = Project(temp_dir)
    assert os.path.isfile(project._config_path) is False
    project.title = 'test'
    assert project.title == 'test'
    assert os.path.isfile(project._config_path) is True


def test__save_config(temp_dir):
    project = Project(temp_dir)

    # Auto saving
    for prop in project.CONFIG_PROPERTIES:
        value = 'test'
        setattr(project, prop, value)
        saved_config = Project(temp_dir)
        assert getattr(saved_config, prop) == value


def test_create(temp_dir):
    project = Project.create(temp_dir, title='title1', description='description1', synapse_project_id='syn123')
    # TODO: finish this test.
