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
import json as JSON
from src.kitools import Project
from src.kitools import DataUri
import synapseclient


def assert_matches_project(projectA, projectB):
    """
    Asserts that two Projects match each other.
    :param projectA:
    :param projectB:
    :return: None
    """
    assert projectA.local_path == projectB.local_path
    assert projectA._config_path == projectB._config_path
    assert projectA.title == projectB.title
    assert projectA.description == projectB.description
    assert projectA.project_uri == projectB.project_uri

    assert len(projectA.files) == len(projectB.files)

    for fileA in projectA.files:
        fileB = next((b for b in projectB.files if
                      b.remote_uri == fileA.remote_uri and
                      b.local_path == fileA.local_path and
                      b.version == fileA.version), None)
        assert fileB


def assert_matches_config(project):
    """
    Asserts that a Project's config matches the Project.
    :param project:
    :return: None
    """
    json = None
    with open(project._config_path) as f:
        json = JSON.load(f)

    assert json.get('title', None) == project.title
    assert json.get('description', None) == project.description
    assert json.get('project_uri', None) == project.project_uri

    for jfile in json.get('files'):
        file = next((f for f in project.files if
                     f.remote_uri == jfile['remote_uri'] and
                     f.local_path == jfile['local_path'] and
                     f.version == jfile['version']), None)
        assert file


def test___init__(new_temp_dir):
    project = Project(new_temp_dir)

    # Sets the paths
    assert project.local_path == new_temp_dir
    assert project._config_path == os.path.join(new_temp_dir, Project.CONFIG_FILENAME)

    # Created the config file.
    assert os.path.isfile(project._config_path)

    # Created the dir structure
    # TODO: test this.

    # Load the project and make sure it matches
    assert_matches_project(project, Project(new_temp_dir))


def test_load(new_test_project):
    # Test loading from the constructor.
    project = Project(new_test_project.local_path)
    assert_matches_project(project, new_test_project)

    # Make sure it loads successfully.
    assert project.load() is True

    os.remove(project._config_path)

    # Does not load since the config file has been deleted.
    assert project.load() is False


def test_save(new_test_project):
    # Remove the config file
    os.remove(new_test_project._config_path)
    assert os.path.isfile(new_test_project._config_path) is False

    new_test_project.save()

    assert os.path.isfile(new_test_project._config_path) is True
    assert_matches_config(new_test_project)


def test_get_project_file(new_test_project):
    assert len(new_test_project.files) > 0

    for project_file in new_test_project.files:
        found = new_test_project.find_project_file(project_file.remote_uri)
        assert found == project_file


def test_data_pull(syn_client, new_syn_project, new_temp_file, new_test_project):
    # Create a Synapse file to pull
    syn_file = syn_client.store(synapseclient.File(path=new_temp_file, parent=new_syn_project))
    data_uri = DataUri(scheme='syn', id=syn_file.id)

    # Pull a file (does not exist in the project)
    new_test_project.files.clear()
    assert len(new_test_project.files) == 0

    abs_path = new_test_project.data_pull(remote_uri=data_uri.uri(), data_type='core', version=None, get_latest=True)

    # File was added to the project
    assert len(new_test_project.files) == 1

    # Can find the project file from data_uri
    project_file = new_test_project.find_project_file(data_uri.uri())

    # Has the correct values
    assert project_file
    assert project_file.local_path == os.path.relpath(abs_path, start=new_test_project.local_path)
    assert project_file.version is None

    # Pull a specific version (does not exist in the project)
    # TODO: test this

    # Pull a file (exists in the project)
    # TODO: test this

    # Pull a specific version (file exist in the project)
    # TODO: test this

    # Pull a folder (does not exist in the project)
    # TODO: test this

    # Pull a folder (exists in the project)
    # TODO: test this
