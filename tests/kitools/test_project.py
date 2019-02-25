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
import pytest
import os
import json as JSON
import uuid
from src.kitools import Project, ProjectFile, DataType, DataUri


@pytest.fixture(scope='session')
def syn_project_files(syn_project, syn_test_helper, mk_tempfile, write_file):
    """
    Creates 3 files in the root of the Synapse Project with each file having 3 versions.
    """
    syn_files = []

    # Create 3 files in the syn_project.
    for _ in range(3):
        temp_file = mk_tempfile()

        # Create 3 versions of each file.
        syn_file = None

        for version_num in range(1, 4):
            write_file(temp_file, 'version{0}'.format(version_num))

            syn_file = syn_test_helper.create_file(
                path=temp_file,
                parent=syn_project,
                name=os.path.basename(temp_file))

        syn_files.append(syn_file)

    return syn_files


@pytest.fixture(scope='session')
def syn_project_folders(syn_project, syn_test_helper):
    """
    Creates a 3 folder hierarchy in the root of the Synapse Project.
    """
    syn_folders = []

    # Create a folder structure 3 levels deep
    parent = syn_project
    for count in range(1, 4):
        syn_folder = syn_test_helper.create_folder(name='Folder{0}'.format(count), parent=parent)
        parent = syn_folder
        syn_folders.append(syn_folder)

    return syn_folders


@pytest.fixture(scope='session')
def syn_project_folders_and_files(syn_project, syn_test_helper, mk_tempfile, write_file):
    """
    Creates a 3 folder hierarchy in the root of the Synapse Project with each folder
    having one file with 3 versions of the file.
    """
    syn_folders = []
    syn_files = []

    # Create a folder structure 3 levels deep
    parent = syn_project
    for count in range(1, 4):
        syn_folder = syn_test_helper.create_folder(name='Folder{0}'.format(count), parent=parent)

        # Create 3 versions of the file in this folder.
        temp_file = mk_tempfile()

        syn_file = None
        for version_num in range(1, 4):
            write_file(temp_file, 'version{0}'.format(version_num))

            syn_file = syn_test_helper.create_file(
                path=temp_file,
                parent=syn_folder,
                name=os.path.basename(temp_file))
        syn_files.append(syn_file)

        parent = syn_folder
        syn_folders.append(syn_folder)

    return syn_folders, syn_files


def assert_matches_project(projectA, projectB):
    """
    Asserts that two Projects match each other.
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
                      b.rel_path == fileA.rel_path and
                      b.version == fileA.version), None)
        assert fileB


def assert_matches_config(project):
    """
    Asserts that a Project's config matches the Project.
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
                     f.rel_path == jfile['rel_path'] and
                     f.version == jfile['version']), None)
        assert file


def test_it_sets_the_project_paths(mk_project, mk_tempdir):
    temp_dir = mk_tempdir()
    project = mk_project(dir=temp_dir)
    assert project.local_path == temp_dir
    assert project._config_path == os.path.join(temp_dir, Project.CONFIG_FILENAME)


def test_it_creates_a_config_file_from_the_constructor(mk_project):
    project = mk_project(with_fake_project_files=True)

    # Delete the config file
    os.remove(project._config_path)
    assert os.path.exists(project._config_path) is False

    new_project = Project(project.local_path)

    assert os.path.isfile(new_project._config_path)
    assert_matches_config(new_project)


def test_it_loads_the_config_file_from_the_constructor(mk_project):
    project = mk_project(with_fake_project_files=True)
    other_project = Project(project.local_path)
    assert_matches_config(other_project)
    assert_matches_project(other_project, project)


def test_it_loads_the_config_file(mk_project):
    project = mk_project(with_fake_project_files=True)

    other_project = Project(project.local_path)
    other_project.title = None
    other_project.description = None
    other_project.project_uri = None
    other_project.files.clear()

    other_project.load()
    assert_matches_project(other_project, project)


def test_it_loads_the_config_file_when_it_exists(mk_project):
    project = mk_project(with_fake_project_files=True)
    assert os.path.isfile(project._config_path)
    assert project.load() is True


def test_it_does_not_load_the_config_file_when_it_does_not_exist(mk_project):
    project = mk_project(with_fake_project_files=True)
    os.remove(project._config_path)
    assert os.path.isfile(project._config_path) is False
    assert project.load() is False


def test_it_creates_a_config_file_when_saved(mk_project):
    project = mk_project(with_fake_project_files=True)

    # Delete the config file
    os.remove(project._config_path)
    assert os.path.exists(project._config_path) is False

    # Save a new config file
    project.save()

    assert os.path.isfile(project._config_path)
    assert_matches_config(project)


def test_it_updates_the_config_file_when_saved(mk_project, mk_fake_uri, mk_fake_project_file):
    project = mk_project(with_fake_project_files=True)
    project.title = str(uuid.uuid4())
    project.description = str(uuid.uuid4())
    project.project_uri = mk_fake_uri()
    project.files.append(mk_fake_project_file(project))

    project.save()
    assert_matches_config(project)


def test_it_creates_the_project_dir_structure(mk_project):
    # TODO: Test this.
    pass


def test_it_finds_a_project_file_by_uri(mk_project):
    project = mk_project(with_fake_project_files=True, with_fake_project_files_count=3)
    assert len(project.files) == 3

    for project_file in project.files:
        found = project.find_project_file_by_uri(project_file.remote_uri)
        assert found == project_file


def test_it_finds_a_project_file_by_path(mk_project):
    project = mk_project(with_fake_project_files=True, with_fake_project_files_count=3)
    assert len(project.files) == 3

    for project_file in project.files:
        # Absolute path
        found = project.find_project_file_by_path(project_file.abs_path)
        assert found == project_file

        # Relative path
        found = project.find_project_file_by_path(project_file.rel_path)
        assert found == project_file


def test_it_does_not_find_a_project_file(mk_project, mk_fake_uri):
    project = mk_project()
    assert project.find_project_file_by_uri(mk_fake_uri()) is None


def test_it_pulls_a_file_and_adds_it_to_the_project(mk_project, syn_project_files):
    project = mk_project()
    assert len(project.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # Pull the file.
        project.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version=None, get_latest=True)
        project_file = project.find_project_file_by_uri(syn_uri)
        assert project_file

        # Does not add duplicate ProjectFile
        project.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version=None, get_latest=True)

    assert len(project.files) == 3


def test_it_does_not_pull_a_file_unless_the_remote_file_changed():
    # TODO: test this
    pass


def test_it_pulls_a_folder_and_adds_it_to_the_project(mk_project, syn_project_folders):
    project = mk_project()
    assert len(project.files) == 0

    for syn_folder in syn_project_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Pull the folder.
        project.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE, version=None, get_latest=True)
        project_file = project.find_project_file_by_uri(syn_folder_uri)
        assert project_file

        # Does not add duplicate ProjectFile
        project.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE, version=None, get_latest=True)

    assert len(project.files) == 3


def test_it_pulls_the_current_version_of_a_file(mk_project, syn_project_files, read_file):
    project = mk_project()
    assert len(project.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # Pull the current version of the file.
        pfile = project.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version=None, get_latest=True)
        assert pfile.version == '3'

        project_file = project.find_project_file_by_uri(syn_uri)
        # Version was not specified so it should be None in the ProjectFile.
        assert project_file.version is None

        assert read_file(pfile.local_path) == 'version3'


def test_it_pulls_a_specific_version_of_a_file(mk_project, syn_project_files, read_file):
    project = mk_project()
    assert len(project.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # Pull the version 2 of the file.
        pfile = project.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version='2', get_latest=False)
        assert pfile.version == '2'

        project_file = project.find_project_file_by_uri(syn_uri)
        # Version was specified so it should be that version in the ProjectFile.
        assert project_file.version == '2'

        assert read_file(pfile.local_path) == 'version2'


def test_it_pulls_the_current_version_of_files_in_a_folder(mk_project, syn_project_folders_and_files, read_file):
    project = mk_project()
    assert len(project.files) == 0

    syn_project_folders = syn_project_folders_and_files[0]

    def assert_child_file_version(pfile):
        if not pfile.is_directory:
            assert read_file(pfile.local_path) == 'version3'
        for pchild in pfile.children:
            assert_child_file_version(pchild)

    for syn_folder in syn_project_folders:
        syn_uri = DataUri('syn', syn_folder.id).uri

        # Pull the folder.
        pfile = project.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version=None, get_latest=True)
        assert pfile.version is None

        project_file = project.find_project_file_by_uri(syn_uri)
        # Folders never have a version in the ProjectFile.
        assert project_file.version is None

        # All the pulled files are the latest version.
        assert_child_file_version(pfile)


def test_it_raises_when_pulling_a_specific_version_for_a_folder(mk_project, syn_project_folders):
    project = mk_project()
    syn_folder_uri = DataUri('syn', syn_project_folders[0].id).uri

    # Pull the file.
    with pytest.raises(ValueError) as ex:
        project.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE, version='1', get_latest=False)
    assert str(ex.value) == 'version cannot be set when pulling a folder.'


def test_it_raises_when_remote_uri_is_present_and_data_type_is_none(mk_project, mk_fake_uri):
    project = mk_project()

    with pytest.raises(ValueError) as ex:
        project.data_pull(remote_uri=mk_fake_uri(), data_type=None)
    assert str(ex.value) == 'Invalid data type: None'


def test_it_raises_when_version_and_get_latest_are_set(mk_project, mk_fake_uri):
    project = mk_project()
    with pytest.raises(ValueError) as ex:
        project.data_pull(remote_uri=mk_fake_uri(), data_type='core', version='1', get_latest=True)
    assert str(ex.value) == 'version and get_latest cannot both be set.'


def test_it_pushes_a_file_to_a_synapse_project(syn_test_helper, syn_project, mk_project, write_file, mk_uniq_string):
    project = mk_project()
    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(project.local_path), filename)
    write_file(file_path, 'version1')

    assert len(project.files) == 0

    pfile = project.data_push(file_path, data_type=DataType.CORE, remote_uri=None)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '1'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(project.files) == 1

    remote_uri = DataUri('syn', pfile.id).uri

    project_file = project.find_project_file_by_uri(remote_uri)
    assert project_file.project == project
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.get('parentId') == syn_project.id


def test_it_does_not_push_a_file_unless_the_local_file_has_changed():
    # TODO: test this
    pass


def test_it_pushes_a_file_to_a_synapse_folder(syn_test_helper, syn_project, mk_project, write_file, mk_uniq_string):
    project = mk_project()
    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(project.local_path), filename)
    write_file(file_path, 'version1')

    syn_folder = syn_test_helper.create_folder(parent=syn_project)

    remote_uri = DataUri('syn', syn_folder.id).uri

    assert len(project.files) == 0

    pfile = project.data_push(file_path, data_type=DataType.CORE, remote_uri=remote_uri)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '1'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(project.files) == 1

    file_remote_uri = DataUri('syn', pfile.id).uri

    project_file = project.find_project_file_by_uri(file_remote_uri)
    assert project_file.project == project
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.get('parentId') == syn_folder.id


def test_it_pushes_a_file_to_a_synapse_file(syn_test_helper, syn_project, mk_project, write_file, mk_uniq_string):
    project = mk_project()
    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(project.local_path), filename)
    write_file(file_path, 'version1')

    syn_file = syn_test_helper.create_file(name=filename, path=file_path, parent=syn_project)

    # Write a new version is it gets uploaded
    write_file(file_path, 'version2')

    remote_uri = DataUri('syn', syn_file.id).uri

    assert len(project.files) == 0

    pfile = project.data_push(file_path, data_type=DataType.CORE, remote_uri=remote_uri)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '2'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(project.files) == 1

    project_file = project.find_project_file_by_uri(remote_uri)
    assert project_file.project == project
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.id == syn_file.id
    assert syn_entity.get('parentId') == syn_project.id


def test_it_raises_an_error_if_the_local_path_does_not_exist(mk_project, mk_tempfile):
    project = mk_project()

    temp_file = mk_tempfile()
    os.remove(temp_file)
    assert os.path.exists(temp_file) is False

    with pytest.raises(ValueError) as ex:
        project.data_push(temp_file, data_type=DataType.CORE, remote_uri=None)
    assert str(ex.value) == 'local_path must be a file.'


def test_it_raises_an_error_if_the_local_path_is_not_file(mk_project, mk_tempdir):
    project = mk_project()

    temp_dir = mk_tempdir()
    os.rmdir(temp_dir)
    assert os.path.exists(temp_dir) is False

    with pytest.raises(ValueError) as ex:
        project.data_push(temp_dir, data_type=DataType.CORE, remote_uri=None)
    assert str(ex.value) == 'local_path must be a file.'


def test_it_raises_an_error_if_the_local_is_not_in_one_of_the_data_type_dirs():
    # TODO: test this
    pass


def test_it_prints_out_all_the_project_files(mk_project):
    project = mk_project(with_fake_project_files=True, with_fake_project_files_count=3)
    table = project.data_list()

    index = 0
    for pf in project.files:
        row = table[index]
        assert row[0] == pf.remote_uri
        assert row[1] == pf.version
        assert row[2] == pf.rel_path
        index += 1
