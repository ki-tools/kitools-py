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
import shutil
from src.kitools import KiProject, KiProjectFile, DataType, DataUri


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
    Creates a 3 folder hierarchy in the root of the Synapse project.
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


def assert_matches_project(kiprojectA, kiprojectB):
    """
    Asserts that two Projects match each other.
    """
    assert kiprojectA.local_path == kiprojectB.local_path
    assert kiprojectA._config_path == kiprojectB._config_path
    assert kiprojectA.title == kiprojectB.title
    assert kiprojectA.description == kiprojectB.description
    assert kiprojectA.project_uri == kiprojectB.project_uri

    assert len(kiprojectA.files) == len(kiprojectB.files)

    for fileA in kiprojectA.files:
        fileB = next((b for b in kiprojectB.files if
                      b.remote_uri == fileA.remote_uri and
                      b.rel_path == fileA.rel_path and
                      b.version == fileA.version), None)
        assert fileB


def assert_matches_config(kiproject):
    """
    Asserts that a KiProject's config matches the KiProject.
    """
    json = None
    with open(kiproject._config_path) as f:
        json = JSON.load(f)

    assert json.get('title', None) == kiproject.title
    assert json.get('description', None) == kiproject.description
    assert json.get('project_uri', None) == kiproject.project_uri

    for jfile in json.get('files'):
        file = next((f for f in kiproject.files if
                     f.remote_uri == jfile['remote_uri'] and
                     f.rel_path == jfile['rel_path'] and
                     f.version == jfile['version']), None)
        assert file


def assert_data_type_paths(kiproject, exists=True):
    """
    Asserts that all the data_type directories exist or not.
    :param exists:
    :return:
    """
    for data_type_name in DataType.ALL:
        data_type = DataType(data_type_name)
        assert os.path.isdir(data_type.to_project_path(kiproject.local_path)) is exists


def test_it_sets_the_kiproject_paths(mk_kiproject, mk_tempdir):
    temp_dir = mk_tempdir()
    kiproject = mk_kiproject(dir=temp_dir)
    assert kiproject.local_path == temp_dir
    assert kiproject._config_path == os.path.join(temp_dir, KiProject.CONFIG_FILENAME)


def test_it_creates_a_config_file_from_the_constructor(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    # Delete the config file
    os.remove(kiproject._config_path)
    assert os.path.exists(kiproject._config_path) is False

    new_project = KiProject(kiproject.local_path)

    assert os.path.isfile(new_project._config_path)
    assert_matches_config(new_project)


def test_it_loads_the_config_file_from_the_constructor(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    other_project = KiProject(kiproject.local_path)
    assert_matches_config(other_project)
    assert_matches_project(other_project, kiproject)


def test_it_loads_the_config_file(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    other_project = KiProject(kiproject.local_path)
    other_project.title = None
    other_project.description = None
    other_project.project_uri = None
    other_project.files.clear()

    other_project.load()
    assert_matches_project(other_project, kiproject)


def test_it_loads_the_config_file_when_it_exists(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    assert os.path.isfile(kiproject._config_path)
    assert kiproject.load() is True


def test_it_does_not_load_the_config_file_when_it_does_not_exist(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    os.remove(kiproject._config_path)
    assert os.path.isfile(kiproject._config_path) is False
    assert kiproject.load() is False


def test_it_creates_a_config_file_when_saved(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    # Delete the config file
    os.remove(kiproject._config_path)
    assert os.path.exists(kiproject._config_path) is False

    # Save a new config file
    kiproject.save()

    assert os.path.isfile(kiproject._config_path)
    assert_matches_config(kiproject)


def test_it_updates_the_config_file_when_saved(mk_kiproject, mk_fake_uri, mk_fake_project_file):
    kiproject = mk_kiproject(with_fake_project_files=True)
    kiproject.title = str(uuid.uuid4())
    kiproject.description = str(uuid.uuid4())
    kiproject.project_uri = mk_fake_uri()
    kiproject.files.append(mk_fake_project_file(kiproject))

    kiproject.save()
    assert_matches_config(kiproject)


def test_it_creates_the_project_dir_structure_on_a_new_project(mk_kiproject):
    kiproject = mk_kiproject()
    assert_data_type_paths(kiproject, exists=True)


def test_it_recreates_the_project_dir_structure_on_an_existing_project(mk_kiproject):
    kiproject = mk_kiproject()
    shutil.rmtree(os.path.join(kiproject.local_path, 'data'))
    assert_data_type_paths(kiproject, exists=False)

    # Reload the kiproject
    kiproject = KiProject(kiproject.local_path)
    assert_data_type_paths(kiproject, exists=True)


def test_it_finds_a_project_file_by_uri(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)
    assert len(kiproject.files) == 3

    for project_file in kiproject.files:
        found = kiproject.find_project_file_by_uri(project_file.remote_uri)
        assert found == project_file


def test_it_finds_a_project_file_by_path(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)
    assert len(kiproject.files) == 3

    for project_file in kiproject.files:
        # Absolute path
        found = kiproject.find_project_file_by_path(project_file.abs_path)
        assert found == project_file

        # Relative path
        found = kiproject.find_project_file_by_path(project_file.rel_path)
        assert found == project_file


def test_it_does_not_find_a_project_file(mk_kiproject, mk_fake_uri):
    kiproject = mk_kiproject()
    assert kiproject.find_project_file_by_uri(mk_fake_uri()) is None


def test_it_pulls_a_file_and_adds_it_to_the_project(mk_kiproject, syn_project_files):
    kiproject = mk_kiproject()
    assert len(kiproject.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # Pull the file.
        kiproject.data_pull(remote_uri=syn_uri, data_type=DataType.CORE)
        project_file = kiproject.find_project_file_by_uri(syn_uri)
        assert project_file

        # Does not add duplicate KiProjectFile
        kiproject.data_pull(remote_uri=syn_uri, data_type=DataType.CORE)

    assert len(kiproject.files) == 3


def test_it_does_not_pull_a_file_unless_the_remote_file_changed():
    # TODO: test this
    pass


def test_it_pulls_a_folder_and_adds_it_to_the_project(mk_kiproject, syn_project_folders):
    kiproject = mk_kiproject()
    assert len(kiproject.files) == 0

    for syn_folder in syn_project_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Pull the folder.
        kiproject.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE)
        project_file = kiproject.find_project_file_by_uri(syn_folder_uri)
        assert project_file

        # Does not add duplicate KiProjectFile
        kiproject.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE)

    assert len(kiproject.files) == 3


def test_it_pulls_the_latest_version_of_a_file(mk_kiproject, syn_project_files, read_file):
    kiproject = mk_kiproject()
    assert len(kiproject.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # None and 'latest' should both pull the latest if a version has not been pinned.
        for version in [None, KiProject.VERSION_LATEST_KEYWORD]:
            # Pull the current version of the file.
            pfile = kiproject.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version=version)
            assert pfile.version == '3'

            project_file = kiproject.find_project_file_by_uri(syn_uri)
            # Version was not specified so it should be None in the KiProjectFile.
            assert project_file.version is None

            assert read_file(pfile.local_path) == 'version3'


def test_it_pulls_a_specific_version_of_a_file(mk_kiproject, syn_project_files, read_file):
    kiproject = mk_kiproject()
    assert len(kiproject.files) == 0

    for syn_file in syn_project_files:
        syn_uri = DataUri('syn', syn_file.id).uri

        # Pull the version 2 of the file.
        pfile = kiproject.data_pull(remote_uri=syn_uri, data_type=DataType.CORE, version='2')
        assert pfile.version == '2'

        project_file = kiproject.find_project_file_by_uri(syn_uri)
        # Version was specified so it should be that version in the KiProjectFile.
        assert project_file.version == '2'

        assert read_file(pfile.local_path) == 'version2'


def test_it_pulls_the_current_version_of_files_in_a_folder(mk_kiproject, syn_project_folders_and_files, read_file):
    kiproject = mk_kiproject()
    assert len(kiproject.files) == 0

    syn_project_folders = syn_project_folders_and_files[0]

    def assert_child_file_version(pfile):
        if not pfile.is_directory:
            assert read_file(pfile.local_path) == 'version3'
        for pchild in pfile.children:
            assert_child_file_version(pchild)

    for syn_folder in syn_project_folders:
        syn_uri = DataUri('syn', syn_folder.id).uri

        # Pull the folder.
        pfile = kiproject.data_pull(remote_uri=syn_uri, data_type=DataType.CORE)
        assert pfile.version is None

        project_file = kiproject.find_project_file_by_uri(syn_uri)
        # Folders never have a version in the KiProjectFile.
        assert project_file.version is None

        # All the pulled files are the latest version.
        assert_child_file_version(pfile)


def test_it_recreates_the_project_dir_structure_when_pulling(mk_kiproject, add_project_file):
    kiproject = mk_kiproject()
    for name in DataType.ALL:
        add_project_file(kiproject, data_type=name)

    # Delete the data directory.
    shutil.rmtree(os.path.join(kiproject.local_path, 'data'))
    assert_data_type_paths(kiproject, exists=False)

    # Reload the kiproject
    kiproject = KiProject(kiproject.local_path)

    # Pull everything
    kiproject.data_pull()
    assert_data_type_paths(kiproject, exists=True)

    # Delete the data directory.
    shutil.rmtree(os.path.join(kiproject.local_path, 'data'))
    assert_data_type_paths(kiproject, exists=False)

    # Reload the kiproject
    kiproject = KiProject(kiproject.local_path)
    # Pull individual files
    for project_file in kiproject.files:
        kiproject.data_pull(project_file.remote_uri, data_type=project_file.data_type, version=project_file.version)
    assert_data_type_paths(kiproject, exists=True)


def test_it_raises_when_pulling_a_specific_version_for_a_folder(mk_kiproject, syn_project_folders):
    kiproject = mk_kiproject()
    syn_folder_uri = DataUri('syn', syn_project_folders[0].id).uri

    # Pull the file.
    with pytest.raises(ValueError) as ex:
        kiproject.data_pull(remote_uri=syn_folder_uri, data_type=DataType.CORE, version='1')
    assert str(ex.value) == 'version cannot be set when pulling a folder.'


def test_it_raises_when_remote_uri_is_present_and_data_type_is_none(mk_kiproject, mk_fake_uri):
    kiproject = mk_kiproject()

    with pytest.raises(ValueError) as ex:
        kiproject.data_pull(remote_uri=mk_fake_uri(), data_type=None)
    assert str(ex.value) == 'data_type is required.'


def test_it_pushes_a_file_to_a_synapse_project(syn_test_helper, mk_kiproject, write_file, mk_uniq_string):
    kiproject = mk_kiproject()
    syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)

    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), filename)
    write_file(file_path, 'version1')

    assert len(kiproject.files) == 0

    pfile = kiproject.data_push(file_path, data_type=DataType.CORE, remote_uri=None)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '1'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(kiproject.files) == 1

    remote_uri = DataUri('syn', pfile.id).uri

    project_file = kiproject.find_project_file_by_uri(remote_uri)
    assert project_file.kiproject == kiproject
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.get('parentId') == syn_project.id


def test_it_does_not_push_a_file_unless_the_local_file_has_changed():
    # TODO: test this
    pass


def test_it_pushes_a_file_to_a_synapse_folder(syn_test_helper, syn_project, mk_kiproject, write_file, mk_uniq_string):
    kiproject = mk_kiproject()
    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), filename)
    write_file(file_path, 'version1')

    syn_folder = syn_test_helper.create_folder(parent=syn_project)

    remote_uri = DataUri('syn', syn_folder.id).uri

    assert len(kiproject.files) == 0

    pfile = kiproject.data_push(file_path, data_type=DataType.CORE, remote_uri=remote_uri)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '1'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(kiproject.files) == 1

    file_remote_uri = DataUri('syn', pfile.id).uri

    project_file = kiproject.find_project_file_by_uri(file_remote_uri)
    assert project_file.kiproject == kiproject
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.get('parentId') == syn_folder.id


def test_it_pushes_a_file_to_a_synapse_file(syn_test_helper, syn_project, mk_kiproject, write_file, mk_uniq_string):
    kiproject = mk_kiproject()
    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), filename)
    write_file(file_path, 'version1')

    syn_file = syn_test_helper.create_file(name=filename, path=file_path, parent=syn_project)

    # Write a new version is it gets uploaded
    write_file(file_path, 'version2')

    remote_uri = DataUri('syn', syn_file.id).uri

    assert len(kiproject.files) == 0

    pfile = kiproject.data_push(file_path, data_type=DataType.CORE, remote_uri=remote_uri)
    assert pfile.name == filename
    assert pfile.local_path == file_path
    assert pfile.version == '2'
    assert pfile.is_directory is False
    assert len(pfile.children) == 0

    assert len(kiproject.files) == 1

    project_file = kiproject.find_project_file_by_uri(remote_uri)
    assert project_file.kiproject == kiproject
    assert project_file.version is None
    assert project_file.abs_path == file_path
    assert project_file.rel_path == 'data{0}core{0}{1}'.format(os.sep, filename)

    syn_entity = syn_test_helper.client().get(DataUri.parse(project_file.remote_uri).id)
    assert syn_entity.id == syn_file.id
    assert syn_entity.get('parentId') == syn_project.id


def test_it_raises_an_error_if_the_local_path_does_not_exist(mk_kiproject, mk_tempfile):
    kiproject = mk_kiproject()

    temp_file = mk_tempfile()
    os.remove(temp_file)
    assert os.path.exists(temp_file) is False

    with pytest.raises(ValueError) as ex:
        kiproject.data_push(temp_file, data_type=DataType.CORE, remote_uri=None)
    assert str(ex.value) == 'local_path must be a file.'


def test_it_raises_an_error_if_the_local_path_is_not_file(mk_kiproject, mk_tempdir):
    kiproject = mk_kiproject()

    temp_dir = mk_tempdir()
    shutil.rmtree(temp_dir)
    assert os.path.exists(temp_dir) is False

    with pytest.raises(ValueError) as ex:
        kiproject.data_push(temp_dir, data_type=DataType.CORE, remote_uri=None)
    assert str(ex.value) == 'local_path must be a file.'


def test_it_raises_an_error_if_the_local_is_not_in_one_of_the_data_type_dirs():
    # TODO: test this
    pass


def test_it_prints_out_all_the_project_files(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)
    table = kiproject.data_list()

    index = 0
    for pf in kiproject.files:
        row = table[index]
        assert row[0] == pf.remote_uri
        assert row[1] == pf.version
        assert row[2] == pf.rel_path
        index += 1


def test_it_creates_a_new_remote_project(mk_mock_kiproject_input, mk_tempdir, syn_test_helper):
    mk_mock_kiproject_input(create_remote_project_or_existing='c')
    kiproject = KiProject(mk_tempdir())

    syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)
    syn_test_helper.dispose_of(syn_project)


def test_it_tests_the_workflow(mk_mock_kiproject_input, mk_tempdir, mk_uniq_string, write_file):
    mk_mock_kiproject_input()

    ###############################################################################################
    # KiProject Creation
    ###############################################################################################
    kiproject = KiProject(mk_tempdir())
    data_path = os.path.join(kiproject.local_path, 'data')

    def rm_data_dir():
        if os.path.isdir(data_path):
            shutil.rmtree(data_path)

    # Push one file per DataType.
    for data_type in DataType.ALL:
        file_path = os.path.join(DataType(data_type).to_project_path(kiproject.local_path),
                                 '{0}.csv'.format(mk_uniq_string()))
        # Create 2 versions of the file
        for count in range(1, 3):
            write_file(file_path, 'version{0}'.format(count))
            kiproject.data_push(file_path, data_type=data_type)

    assert len(kiproject.files) == len(DataType.ALL)

    # Pull all the files (this will be the latest version)
    kiproject.data_pull()
    for project_file in kiproject.files:
        assert project_file.version is None
        assert os.path.isfile(project_file.abs_path)

    # Pull a specific version of each file
    for project_file in kiproject.files:
        pfile = kiproject.data_pull(project_file.remote_uri, version='1')
        assert pfile.version == '1'
        assert project_file.version == '1'
        assert os.path.isfile(project_file.abs_path)

    # Pull each latest version of a file
    for project_file in kiproject.files:
        pfile = kiproject.data_pull(project_file.remote_uri, version=KiProject.VERSION_LATEST_KEYWORD)
        assert pfile.version == '2'
        assert project_file.version is None
        assert os.path.isfile(project_file.abs_path)

    ###############################################################################################
    # KiProject usage
    ###############################################################################################

    # Clean out the KiProject dir.
    rm_data_dir()

    # Reload the KiProject
    kiproject = KiProject(kiproject.local_path)
    assert len(kiproject.files) == len(DataType.ALL)

    # Pull all the files
    kiproject.data_pull()
    for project_file in kiproject.files:
        assert project_file.version is None
        assert os.path.isfile(project_file.abs_path)

    # Pull each version of a file
    for project_file in kiproject.files:
        pfile = kiproject.data_pull(project_file.remote_uri, version='1')
        assert pfile.version == '1'
        assert project_file.version == '1'
        assert os.path.isfile(project_file.abs_path)

    # Pull each latest version of a file
    for project_file in kiproject.files:
        pfile = kiproject.data_pull(project_file.remote_uri)
        assert pfile.version == '2'
        assert project_file.version is None
        assert os.path.isfile(project_file.abs_path)
