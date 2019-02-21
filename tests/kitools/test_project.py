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


def test___init__(mk_tempdir):
    temp_dir = mk_tempdir()

    project = Project(temp_dir)

    # Sets the paths
    assert project.local_path == temp_dir
    assert project._config_path == os.path.join(temp_dir, Project.CONFIG_FILENAME)

    # Created the config file.
    assert os.path.isfile(project._config_path)

    # Created the dir structure
    # TODO: test this.

    # Load the project and make sure it matches
    assert_matches_project(project, Project(temp_dir))


def test_load(mk_project):
    test_project = mk_project()

    # Test loading from the constructor.
    project = Project(test_project.local_path)
    assert_matches_project(project, test_project)

    # Make sure it loads successfully.
    assert project.load() is True

    os.remove(project._config_path)

    # Does not load since the config file has been deleted.
    assert project.load() is False


def test_save(mk_project):
    test_project = mk_project()

    # Remove the config file
    os.remove(test_project._config_path)
    assert os.path.isfile(test_project._config_path) is False

    test_project.save()

    assert os.path.isfile(test_project._config_path) is True
    assert_matches_config(test_project)


def test_get_project_file(mk_project):
    test_project = mk_project(with_files=True)

    assert len(test_project.files) > 0

    for project_file in test_project.files:
        found = test_project.find_project_file(project_file.remote_uri)
        assert found == project_file


def test_data_pull_exceptions(syn_client, new_syn_project, mk_project, mk_tempdir):
    test_project = mk_project(with_project=new_syn_project)

    syn_folder = syn_client.store(synapseclient.Folder(name='folder', parent=new_syn_project))
    syn_folder_uri = DataUri(scheme='syn', id=syn_folder.id).uri()

    # Pull a remote_uri with no data_type specified
    with pytest.raises(ValueError) as ex:
        test_project.data_pull(remote_uri=syn_folder_uri, data_type=None)
    assert str(ex.value) == 'remote_uri and data_type are required.'

    # Pull a specific version of a folder
    with pytest.raises(ValueError) as ex:
        test_project.data_pull(remote_uri=syn_folder_uri, data_type='core', version='1', get_latest=False)
    assert str(ex.value) == 'version cannot be set when pulling a folder.'

    # Get version and latest
    with pytest.raises(ValueError) as ex:
        test_project.data_pull(remote_uri=syn_folder_uri, data_type='core', version='1', get_latest=True)
    assert str(ex.value) == 'version and get_latest cannot both be set.'


def test_data_pull_adds_file_to_project(syn_test_helper, syn_project, mk_project):
    test_project = mk_project(with_project=syn_project, with_files=True)

    syn_file_uri = test_project.files[0].remote_uri

    test_project.files.clear()

    assert len(test_project.files) == 0

    presult = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version=None, get_latest=True)

    assert len(test_project.files) == 1

    project_file = test_project.find_project_file(syn_file_uri)

    # Has the correct values
    assert project_file.remote_uri == syn_file_uri
    assert project_file.local_path == ProjectFile.to_relative_path(presult.local_path, test_project.local_path)
    assert project_file.version is None

    # Does not duplicate the ProjectFile
    test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version=None, get_latest=True)
    assert len(test_project.files) == 1


def test_data_pull_adds_folder_to_project(syn_test_helper, syn_project, mk_project, mk_tempfile, write_file):
    test_project = mk_project(with_project=syn_project)

    temp_file1 = mk_tempfile()
    syn_folder1 = syn_test_helper.create_folder(name='folder1', parent=syn_project)
    syn_file1 = syn_test_helper.create_file(path=temp_file1, parent=syn_folder1)

    temp_file2 = mk_tempfile()
    syn_folder2 = syn_test_helper.create_folder(name='folder2', parent=syn_folder1)
    syn_file2 = syn_test_helper.create_file(path=temp_file2, parent=syn_folder2)

    temp_file3 = mk_tempfile()
    syn_folder3 = syn_test_helper.create_folder(name='folder3', parent=syn_folder2)
    syn_file3 = syn_test_helper.create_file(path=temp_file3, parent=syn_folder3)

    syn_folder_uri = DataUri(scheme='syn', id=syn_folder1.id).uri()

    test_project.files.clear()
    assert len(test_project.files) == 0

    pfolder1 = test_project.data_pull(remote_uri=syn_folder_uri, data_type='core', version=None, get_latest=True)

    assert len(test_project.files) == 1

    project_file = test_project.find_project_file(syn_folder_uri)

    assert project_file.remote_uri == syn_folder_uri
    assert project_file.local_path == ProjectFile.to_relative_path(pfolder1.local_path, test_project.local_path)
    assert project_file.version is None

    assert os.path.isdir(project_file.to_absolute_path(test_project.local_path))

    # Does not duplicate the ProjectFile
    pfolder1 = test_project.data_pull(remote_uri=syn_folder_uri, data_type='core', version=None, get_latest=True)
    assert len(test_project.files) == 1

    # Downloaded all the files and folders
    # file1
    pfile1 = next((f for f in pfolder1.children if f.id == syn_file1.id), None)
    assert os.path.isfile(pfile1.local_path)

    # folder2
    pfolder2 = pfolder1.children[1]
    assert os.path.isdir(pfolder2.local_path)
    assert pfolder2.id == syn_folder2.id

    # file2
    pfile2 = pfolder2.children[0]
    assert os.path.isfile(pfile2.local_path)
    assert pfile2.id == syn_file2.id

    # folder3
    pfolder3 = pfolder2.children[1]
    assert os.path.isdir(pfolder3.local_path)
    assert pfolder3.id == syn_folder3.id

    # file3
    pfile3 = pfolder3.children[0]
    assert os.path.isfile(pfile3.local_path)
    assert pfile3.id == syn_file3.id


def test_data_pull_get_latest_version(syn_test_helper, syn_project, mk_project):
    test_project = mk_project(with_project=syn_project, with_files=True, with_files_versions=2)

    syn_file_uri = test_project.files[0].remote_uri

    test_project.files.clear()

    pfile = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version=None, get_latest=True)
    assert pfile.version == '2'

    project_file = test_project.find_project_file(syn_file_uri)
    assert project_file.version is None


def test_data_pull_get_specific_version(syn_test_helper, syn_project, mk_project):
    test_project = mk_project(with_project=syn_project, with_files=True, with_files_versions=3)

    syn_file_uri = test_project.files[0].remote_uri

    test_project.files.clear()

    # Get version and set the version in the ProjectFile
    pfile = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version='2', get_latest=False)
    assert pfile.version == '2'
    project_file = test_project.find_project_file(syn_file_uri)
    assert project_file.version == '2'

    # Gets the version from the ProjectFile
    pfile = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version=None, get_latest=False)
    assert pfile.version == '2'
    project_file = test_project.find_project_file(syn_file_uri)
    assert project_file.version == '2'

    # Get version 1 and update the version in the ProjectFile
    pfile = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version='1', get_latest=False)
    assert pfile.version == '1'
    project_file = test_project.find_project_file(syn_file_uri)
    assert project_file.version == '1'

    # Get the latest version (3) and clear the version on the ProjectFile
    # so we always get the latest version when pulling.
    pfile = test_project.data_pull(remote_uri=syn_file_uri, data_type='core', version=None, get_latest=True)
    assert pfile.version == '3'
    project_file = test_project.find_project_file(syn_file_uri)
    assert project_file.version is None


def test_data_pull_folder():
    # TODO:
    pass


def test_data_all():
    # TODO:
    pass
