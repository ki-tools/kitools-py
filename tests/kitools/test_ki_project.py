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
from src.kitools import KiProject, KiProjectResource, DataType, DataUri


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


@pytest.fixture(scope='session')
def syn_project_data_folders_and_files(mk_syn_project, syn_test_helper, mk_tempfile, write_file):
    """
    Creates a 3 folder data hierarchy in the root of the Synapse Project with the last folder
    having one file with 3 versions.
    """
    syn_project = mk_syn_project()
    syn_folders = []
    syn_files = []

    data_folder = syn_test_helper.create_folder(name='data', parent=syn_project)
    syn_folders.append(data_folder)

    core_folder = syn_test_helper.create_folder(name='core', parent=data_folder)
    syn_folders.append(core_folder)

    study_folder = syn_test_helper.create_folder(name='study_one', parent=core_folder)
    syn_folders.append(study_folder)

    # Create 3 versions of the file in the study folder.
    temp_file = mk_tempfile()

    syn_file = None
    for version_num in range(1, 4):
        write_file(temp_file, 'version{0}'.format(version_num))
        syn_file = syn_test_helper.create_file(path=temp_file, parent=study_folder, name=os.path.basename(temp_file))
    syn_files.append(syn_file)

    return syn_project, syn_folders, syn_files


def assert_matches_project(kiprojectA, kiprojectB):
    """
    Asserts that two Projects match each other.
    """
    assert kiprojectA.local_path == kiprojectB.local_path
    assert kiprojectA._config_path == kiprojectB._config_path
    assert kiprojectA.title == kiprojectB.title
    assert kiprojectA.description == kiprojectB.description
    assert kiprojectA.project_uri == kiprojectB.project_uri

    assert len(kiprojectA.resources) == len(kiprojectB.resources)

    for fileA in kiprojectA.resources:
        fileB = next((b for b in kiprojectB.resources if
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

    for jfile in json.get('resources'):
        file = next((f for f in kiproject.resources if
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
    other_project.resources.clear()

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
    kiproject.resources.append(mk_fake_project_file(kiproject))

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


def test_find_project_file_by(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)

    props = ['remote_uri', 'abs_path', 'rel_path', 'name']

    for ki_project_resource in kiproject.resources:
        all_args = {}
        for prop in props:
            all_args[prop] = getattr(ki_project_resource, prop)

        # Finds by all properties
        found = kiproject.find_project_resource_by(**all_args)
        assert found == ki_project_resource

        # Find by each property individually.
        for prop, value in all_args.items():
            single_arg = {
                prop: value
            }
            found = kiproject.find_project_resource_by(**single_arg)
            assert found == ki_project_resource


def test_it_prints_out_all_the_project_files(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True, with_fake_project_files_count=3)
    table = kiproject.data_list()

    index = 0
    for resource in kiproject.resources:
        row = table[index]
        assert row[0] == resource.remote_uri
        assert row[1] == resource.version
        assert row[2] == resource.rel_path
        index += 1


def test_it_creates_a_new_remote_project(mk_mock_kiproject_input, mk_tempdir, syn_test_helper):
    mk_mock_kiproject_input(create_remote_project_or_existing='c')
    kiproject = KiProject(mk_tempdir())

    syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)
    syn_test_helper.dispose_of(syn_project)


def test_it_adds_a_remote_data_structure_file(mk_kiproject, syn_project_data_folders_and_files):
    kiproject = mk_kiproject()
    syn_files = syn_project_data_folders_and_files[2]

    syn_file = syn_files[0]
    syn_file_uri = DataUri('syn', syn_file.id).uri
    ki_project_resource = kiproject.data_add(syn_file_uri)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_adds_a_remote_data_structure_folder(mk_kiproject, syn_project_data_folders_and_files):
    kiproject = mk_kiproject()

    syn_project, syn_folders, syn_files = syn_project_data_folders_and_files

    syn_folder = syn_folders[-1]
    ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_file(mk_kiproject, syn_project_folders_and_files):
    kiproject = mk_kiproject()
    syn_files = syn_project_folders_and_files[1]

    syn_file = syn_files[0]
    syn_file_uri = DataUri('syn', syn_file.id).uri
    ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_folder(mk_kiproject, syn_project_folders_and_files):
    kiproject = mk_kiproject()

    syn_folders, syn_files = syn_project_folders_and_files

    syn_folder = syn_folders[-3]
    ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri, data_type=DataType.CORE)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_file(mk_kiproject, mk_uniq_string, write_file):
    kiproject = mk_kiproject()

    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), filename)
    write_file(file_path, 'version1')

    ki_project_resource = kiproject.data_add(file_path)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_folder(mk_kiproject):
    kiproject = mk_kiproject()

    folder_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), 'study1')
    os.makedirs(folder_path)

    ki_project_resource = kiproject.data_add(folder_path)
    assert ki_project_resource
    # TODO: add remaining assertions


def test_it_pulls_a_file_matching_the_data_structure(mk_kiproject, syn_project_data_folders_and_files):
    kiproject = mk_kiproject()

    syn_project, syn_folders, syn_files = syn_project_data_folders_and_files

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity


def test_it_pulls_a_folder_matching_the_data_structure(mk_kiproject, syn_project_data_folders_and_files):
    kiproject = mk_kiproject()

    syn_project, syn_folders, syn_files = syn_project_data_folders_and_files

    for syn_folder in syn_folders:
        if syn_folder.name == 'data' or syn_folder.name == 'core':
            continue

        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_file_not_matching_the_data_structure(mk_kiproject, syn_project_folders_and_files):
    kiproject = mk_kiproject()

    syn_folders, syn_files = syn_project_folders_and_files

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_folder_not_matching_the_data_structure(mk_kiproject, syn_project_folders_and_files):
    kiproject = mk_kiproject()

    syn_folders, syn_files = syn_project_folders_and_files

    for syn_folder in syn_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_does_not_pull_a_file_unless_the_remote_file_changed_TODO():
    raise NotImplementedError()


def test_it_pushes_a_file_matching_the_data_structure(mk_kiproject, mk_uniq_string, write_file):
    kiproject = mk_kiproject()

    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), filename)
    write_file(file_path, 'version1')

    ki_project_resource = kiproject.data_add(file_path)

    # Push the file
    remote_entity = kiproject.data_push(ki_project_resource.remote_uri)
    assert remote_entity
    # TODO: check that file/folders were pushed


def test_it_pushes_a_folder_matching_the_data_structure(mk_kiproject, mk_uniq_string, write_file):
    kiproject = mk_kiproject()

    filename = '{0}.csv'.format(mk_uniq_string())
    file_path = os.path.join(DataType(DataType.CORE).to_project_path(kiproject.local_path), 'study1', filename)
    write_file(file_path, 'version1')

    # Add another file and folder
    child_filename = '{0}.csv'.format(mk_uniq_string())
    child_path = os.path.join(os.path.dirname(file_path), 'folder1', child_filename)
    write_file(child_path, 'version1')

    ki_project_resource = kiproject.data_add(os.path.dirname(file_path))

    # Push the file
    remote_entity = kiproject.data_push(ki_project_resource.remote_uri)
    assert remote_entity
    # TODO: check that file/folders were pushed


def test_it_does_not_push_a_file_unless_the_local_file_changed_TODO():
    raise NotImplementedError()


@pytest.fixture(scope='session')
def mk_local_data_dir(mk_uniq_string, write_file):
    def _mk(root_path):
        core_data_path = DataType(DataType.CORE).to_project_path(root_path)
        derived_data_path = DataType(DataType.DERIVED).to_project_path(root_path)
        discovered_data_path = DataType(DataType.DISCOVERED).to_project_path(root_path)
        all_data_paths = [core_data_path, derived_data_path, discovered_data_path]

        # Create some local data files.
        local_data_files = []
        for data_path in all_data_paths:
            filename = '{0}_file_{1}.csv'.format(os.path.basename(data_path), mk_uniq_string())
            file_path = os.path.join(data_path, filename)
            write_file(file_path, 'version1')
            local_data_files.append(file_path)

        # Create some local data folders.
        local_data_folders = []
        for data_path in all_data_paths:
            folder_name = '{0}_folder_{1}'.format(os.path.basename(data_path), mk_uniq_string())
            folder_path = os.path.join(data_path, folder_name)
            os.makedirs(folder_path)
            local_data_folders.append(folder_path)

            # Create some files in the folder
            for count in range(1, 4):
                filename = 'file_{0}.csv'.format(mk_uniq_string())
                file_path = os.path.join(folder_path, filename)
                write_file(file_path, 'version1')

        return local_data_folders, local_data_files

    yield _mk


def test_it_tests_the_new_workflow(mk_kiproject,
                                   mk_local_data_dir,
                                   syn_project_data_folders_and_files,
                                   syn_project_folders_and_files):
    kiproject = mk_kiproject()
    local_data_folders, local_data_files = mk_local_data_dir(kiproject.local_path)

    # Add/Push local files
    for local_file in local_data_files:
        name = os.path.basename(local_file)
        kiproject.data_add(local_file, name=name)
        kiproject.data_push(name)

    # Add/Push local folders
    for local_folder in local_data_folders:
        name = os.path.basename(local_folder)
        kiproject.data_add(local_folder, name=name)
        kiproject.data_push(name)

    _, syn_data_folders, syn_data_files = syn_project_data_folders_and_files

    # Add/Push remote data files
    for syn_file in syn_data_files:
        remote_uri = DataUri('syn', syn_file.id).uri
        kiproject.data_add(remote_uri)
        kiproject.data_pull(remote_uri)

    # Add/Pull remote data folders
    for syn_folder in syn_data_folders:
        # Skip the data/core folders
        if syn_folder.name == 'data' or syn_folder.name == 'core':
            continue
        remote_uri = DataUri('syn', syn_folder.id).uri
        kiproject.data_add(remote_uri)
        kiproject.data_pull(remote_uri)

    syn_non_data_folders, syn_non_data_files = syn_project_folders_and_files

    # Add/Pull remote non-data files
    for syn_non_data_file in syn_non_data_files:
        remote_uri = DataUri('syn', syn_non_data_file.id).uri
        kiproject.data_add(remote_uri, data_type=DataType.CORE)
        kiproject.data_pull(remote_uri)

    # Add/Pull remote non-data folders
    for syn_non_data_folder in syn_non_data_folders:
        remote_uri = DataUri('syn', syn_non_data_folder.id).uri
        kiproject.data_add(remote_uri, data_type=DataType.CORE)
        kiproject.data_pull(remote_uri)

    assert True
