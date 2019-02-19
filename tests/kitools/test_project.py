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
from src.kitools import Project, ProjectFile


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
