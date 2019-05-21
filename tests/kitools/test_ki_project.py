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
import uuid
import shutil
import synapseclient
from collections import deque
from src.kitools import KiProject, KiProjectResource, DataType, DataUri, SysPath
from src.kitools import NotADataTypePathError, DataTypeMismatchError


@pytest.fixture(scope='session')
def mk_syn_files(syn_test_helper, write_file, mk_tempdir):
    def _mk(syn_parent, file_num=2, versions=2, suffix=''):
        syn_files = []

        temp_dir = mk_tempdir()

        for file_num in range(1, file_num + 1):
            # Create N versions of each file.
            syn_file = None

            temp_file = os.path.join(temp_dir, 'File{0}{1}'.format(file_num, suffix))

            for version_num in range(1, versions + 1):
                write_file(temp_file, 'version{0}'.format(version_num))

                syn_file = syn_test_helper.client().store(synapseclient.File(
                    path=temp_file,
                    parent=syn_parent))

            syn_files.append(syn_file)
        return syn_files

    yield _mk


@pytest.fixture(scope='session')
def mk_syn_folders(syn_test_helper):
    def _mk(syn_parent, count=2, suffix=''):
        syn_folders = []

        for folder_count in range(1, count + 1):
            folder_name = 'Folder{0}{1}'.format(folder_count, suffix)
            syn_folder = syn_test_helper.client().store(synapseclient.Folder(name=folder_name, parent=syn_parent))
            syn_folders.append(syn_folder)
        return syn_folders

    yield _mk


@pytest.fixture(scope='session')
def mk_syn_folders_files(mk_syn_files, mk_syn_folders):
    def _mk(syn_parent):
        root_files = mk_syn_files(syn_parent)
        root_folders = mk_syn_folders(syn_parent)

        for root_folder in root_folders:
            mk_syn_files(root_folder, suffix='_1')

            for level2_folder in mk_syn_folders(root_folder, suffix='_1'):
                mk_syn_files(level2_folder, suffix='_2')

        return syn_parent, root_folders, root_files

    yield _mk


@pytest.fixture(scope='session')
def syn_non_data(mk_syn_project, mk_syn_folders_files):
    """
    Creates this:

    file1
    file2
    folder1/
        file1_1
        file2_1
        Folder1_1/
            file1_2
            file2_2
        Folder2_1/
            file1_2
            file2_2
    folder2/
        file1_1
        file2_1
        Folder1_1/
            file1_2
            file2_2
        Folder2_1/
            file1_2
            file2_2
    """
    syn_project = mk_syn_project()
    return mk_syn_folders_files(syn_project)


@pytest.fixture(scope='session')
def syn_data(mk_syn_project, syn_test_helper, mk_syn_folders_files):
    """
    Creates this:

    data
        /core
            file1
            file2
            folder1/
                file1_1
                file2_1
                Folder1_1/
                    file1_2
                    file2_2
                Folder2_1/
                    file1_2
                    file2_2
            folder2/
                file1_1
                file2_1
                Folder1_1/
                    file1_2
                    file2_2
                Folder2_1/
                    file1_2
                    file2_2
        /artifacts
            <same as core...>
        /discovered
            <same as core...>

    This method will return the root files/folders under data/core, data/artifacts, data/discovered.
    The data and data_type folders are NOT returned.
    """
    syn_project = mk_syn_project()
    root_folders = []
    root_files = []

    syn_data_folder = syn_test_helper.client().store(synapseclient.Folder(name='data', parent=syn_project))

    for data_type_name in DataType.ALL:
        syn_folder = syn_test_helper.client().store(synapseclient.Folder(name=data_type_name, parent=syn_data_folder))
        folder, folders, files = mk_syn_folders_files(syn_folder)
        root_folders += folders
        root_files += files

    return syn_project, root_folders, root_files


@pytest.fixture(scope='session')
def mk_local_data_dir(mk_uniq_string, write_file):
    def _mk(kiproject, return_all=False):
        all_data_paths = kiproject._root_data_paths()

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
                if return_all:
                    local_data_files.append(file_path)

        return local_data_folders, local_data_files

    yield _mk


def assert_matches_project(kiprojectA, kiprojectB):
    """
    Asserts that two Projects match each other.
    """
    assert kiprojectA.local_path == kiprojectB.local_path
    assert kiprojectA._config_path == kiprojectB._config_path
    assert kiprojectA.title == kiprojectB.title
    assert kiprojectA.description == kiprojectB.description
    assert kiprojectA.project_uri == kiprojectB.project_uri
    assert kiprojectA.data_ignores == kiprojectB.data_ignores

    assert len(kiprojectA.resources) == len(kiprojectB.resources)

    for fileA in kiprojectA.resources:
        fileB = next((b for b in kiprojectB.resources if
                      b.remote_uri == fileA.remote_uri and
                      (SysPath(b.rel_path).rel_parts if b.rel_path else b.rel_path) ==
                      (SysPath(fileA.rel_path).rel_parts if fileA.rel_path else fileA.rel_path) and
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
    assert json.get('data_ignores', None) == kiproject.data_ignores

    for jfile in json.get('resources'):
        file = next((f for f in kiproject.resources if
                     f.remote_uri == jfile['remote_uri'] and
                     (SysPath(f.rel_path).rel_parts if f.rel_path else f.rel_path) ==
                     (SysPath(jfile['rel_path']).rel_parts if jfile['rel_path'] else jfile['rel_path']) and
                     f.version == jfile['version']), None)
        assert file


def assert_data_type_paths(kiproject, exists=True):
    """
    Asserts that all the data_type directories exist or not.
    :param exists:
    :return:
    """
    for data_type_name in DataType.ALL:
        assert os.path.isdir(kiproject.data_type_to_project_path(data_type_name)) is exists


@pytest.fixture()
def kiproject(mk_kiproject):
    return mk_kiproject()


def test_it_sets_the_kiproject_paths(mk_kiproject, mk_tempdir):
    temp_dir = mk_tempdir()
    kiproject = mk_kiproject(dir=temp_dir)
    assert kiproject.local_path == temp_dir
    assert kiproject.data_path == os.path.join(temp_dir, DataType.DATA_DIR_NAME)
    assert kiproject._config_path == os.path.join(temp_dir, KiProject.CONFIG_FILENAME)


def test_it_expands_user_dir_in_local_path():
    # TODO: test this.
    pass


def test_it_expands_vars_in_local_path():
    # TODO: test this.
    pass


def test_it_does_not_prompt_for_create_project_in_when_init_no_prompt(mk_tempdir,
                                                                      mk_mock_kiproject_input,
                                                                      syn_project_uri,
                                                                      MockKiProjectInputErrorClass):
    mk_mock_kiproject_input(raise_on_create_project_in=True)

    with pytest.raises(MockKiProjectInputErrorClass):
        kiproject = KiProject(mk_tempdir(), init_no_prompt=False)

    kiproject = KiProject(mk_tempdir(), init_no_prompt=True, title='test', project_uri=syn_project_uri)
    kiproject._ensure_loaded()


def test_it_does_not_prompt_for_project_title_when_init_no_prompt(mk_tempdir,
                                                                  mk_mock_kiproject_input,
                                                                  syn_project_uri,
                                                                  MockKiProjectInputErrorClass):
    mk_mock_kiproject_input(raise_on_project_title=True)

    with pytest.raises(MockKiProjectInputErrorClass):
        kiproject = KiProject(mk_tempdir(), init_no_prompt=False)

    kiproject = KiProject(mk_tempdir(), init_no_prompt=True, title='test', project_uri=syn_project_uri)
    kiproject._ensure_loaded()
    assert kiproject.title == 'test'


def test_it_does_not_prompt_for_create_remote_project_or_existing_when_init_no_prompt(mk_tempdir,
                                                                                      mk_mock_kiproject_input,
                                                                                      syn_project_uri,
                                                                                      MockKiProjectInputErrorClass):
    mk_mock_kiproject_input(raise_on_create_remote_project_or_existing=True)

    with pytest.raises(MockKiProjectInputErrorClass):
        kiproject = KiProject(mk_tempdir(), init_no_prompt=False)

    kiproject = KiProject(mk_tempdir(), init_no_prompt=True, title='test', project_uri=syn_project_uri)
    kiproject._ensure_loaded()
    assert kiproject.project_uri == syn_project_uri


def test_it_does_not_prompt_for_remote_project_name_when_init_no_prompt(mk_tempdir,
                                                                        mk_mock_kiproject_input,
                                                                        syn_project_uri,
                                                                        MockKiProjectInputErrorClass):
    mk_mock_kiproject_input(raise_on_remote_project_name=True, create_remote_project_or_existing='c')

    kiproject = KiProject(mk_tempdir(), init_no_prompt=True, title='test')

    with pytest.raises(Exception) as ex:
        kiproject._ensure_loaded()
    assert str(ex.value) == 'KiProject configuration not created or loaded.'


def test_it_does_not_prompt_for_remote_project_uri_init_no_prompt(mk_tempdir,
                                                                  mk_mock_kiproject_input,
                                                                  syn_project_uri,
                                                                  MockKiProjectInputErrorClass):
    mk_mock_kiproject_input(raise_on_remote_project_uri=True, create_remote_project_or_existing='e')

    with pytest.raises(MockKiProjectInputErrorClass):
        kiproject = KiProject(mk_tempdir(), init_no_prompt=False)

    kiproject = KiProject(mk_tempdir(), init_no_prompt=True, title='test', project_uri=syn_project_uri)
    kiproject._ensure_loaded()
    assert kiproject.project_uri == syn_project_uri


def test_it_creates_a_config_file_from_the_constructor(mk_kiproject, mk_mock_kiproject_input):
    kiproject = mk_kiproject(with_fake_project_files=True)

    # Delete the config file
    os.remove(kiproject._config_path)
    assert os.path.exists(kiproject._config_path) is False

    mk_mock_kiproject_input(create_remote_project_or_existing='e', remote_project_uri=kiproject.project_uri)
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


def test_it_saves_resource_rel_paths_as_posix_paths(mk_kiproject):
    # NOTE: This test needs to be run in each supported env (Linux/Mac, Windows).
    kiproject = mk_kiproject(with_fake_project_files=True)

    with open(kiproject._config_path) as f:
        json = JSON.load(f)

    jresources = json['resources']
    assert len(jresources) > 0

    for jresource in jresources:
        assert '\\' not in jresource['rel_path']
        assert '/' in jresource['rel_path']


def test_it_creates_the_project_dir_structure_on_a_new_project(kiproject):
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

    props = ['id', 'root_id', 'remote_uri', 'abs_path', 'rel_path', 'name', 'version', 'data_type']
    uniq_props = ['id', 'remote_uri', 'abs_path', 'rel_path']

    for ki_project_resource in kiproject.resources:
        all_args = {}
        for prop in props:
            value = getattr(ki_project_resource, prop)
            if value:
                all_args[prop] = value

        # Finds by all properties
        found = kiproject.find_project_resource_by(**all_args)
        assert found == ki_project_resource

        # Find by each unique property individually.
        for prop, value in all_args.items():
            if prop not in uniq_props:
                continue

            single_arg = {
                prop: value
            }
            found = kiproject.find_project_resource_by(**single_arg)
            assert found == ki_project_resource

    # TODO: test "and"/"or" operator.


def test__find_project_resource_by_value(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)
    resource = kiproject.resources[0]

    # Find by the KiProject instance
    assert kiproject._find_project_resource_by_value(resource) == resource

    # Find by ID
    assert kiproject._find_project_resource_by_value(resource.id) == resource

    # Find by remote_uri
    assert kiproject._find_project_resource_by_value(resource.remote_uri) == resource

    # Find by abs_path
    assert kiproject._find_project_resource_by_value(resource.abs_path) == resource

    # Find by rel_path
    assert kiproject._find_project_resource_by_value(resource.rel_path) == resource

    # Find by name
    assert kiproject._find_project_resource_by_value(resource.name) == resource


def test_it_prints_out_the_root_project_resources(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True,
                             with_fake_project_files_count=3,
                             with_non_root_project_files=True)

    kiproject.data_list()
    # TODO: Figure out how to test this.

    # Adjust the resources to be in a non pushed/pulled state.
    kiproject.resources[0].abs_path = None
    kiproject.resources[1].remote_uri = None
    kiproject.resources[2].version = None

    kiproject.data_list()
    # TODO: Figure out how to test this.


def test_it_prints_out_the_all_project_resources(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True,
                             with_fake_project_files_count=3,
                             with_non_root_project_files=True)

    kiproject.data_list(all=True)
    # TODO: Figure out how to test this.

    # Adjust the resources to be in a non pushed/pulled state.
    kiproject.resources[0].abs_path = None
    kiproject.resources[1].remote_uri = None
    kiproject.resources[2].version = None

    kiproject.data_list(all=True)
    # TODO: Figure out how to test this.


def test_it_creates_a_new_remote_project(mk_mock_kiproject_input, mk_tempdir, syn_test_helper):
    mk_mock_kiproject_input(create_remote_project_or_existing='c')
    kiproject = KiProject(mk_tempdir())

    syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)
    syn_test_helper.dispose_of(syn_project)


def test_it_finds_a_resource_to_add_by_its_attributes(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        resource = kiproject.data_add(file_path)
        # Push it so all the attributes are set.
        kiproject.data_push(resource)

        assert kiproject.data_add(resource.remote_uri) == resource
        assert kiproject.data_add(resource.abs_path) == resource
        assert kiproject.data_add(resource.rel_path) == resource


def test_it_adds_a_remote_data_structure_file(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri
        ki_project_resource = kiproject.data_add(syn_file_uri)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_data_structure_folder(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_folder in syn_folders:
        ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_file(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri
        ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_remote_non_data_structure_folder(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_folder in syn_folders:
        ki_project_resource = kiproject.data_add(DataUri('syn', syn_folder.id).uri, data_type=DataType.CORE)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_file(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        ki_project_resource = kiproject.data_add(file_path)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_adds_a_local_data_structure_folder(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for folder_path in local_data_folders:
        ki_project_resource = kiproject.data_add(folder_path)
        assert ki_project_resource
        # TODO: add remaining assertions


def test_it_errors_when_adding_a_local_path_that_is_not_in_the_data_directories(kiproject, mk_tempfile):
    temp_file = mk_tempfile()

    bad_paths = [temp_file, kiproject.data_path]
    for data_type in DataType.ALL:
        bad_paths.append(os.path.join(kiproject.data_path, data_type))

    for bad_path in bad_paths:
        with pytest.raises(NotADataTypePathError):
            kiproject.data_add(bad_path)


def test_it_errors_when_adding_a_data_type_that_does_not_match_the_local_path(kiproject, mk_local_data_dir):
    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for local_path in local_data_folders + local_data_files:
        actual_data_type = kiproject.data_type_from_project_path(local_path).name

        dts = DataType.ALL.copy()
        dts.remove(actual_data_type)
        wrong_data_type = dts[0]

        with pytest.raises(DataTypeMismatchError):
            kiproject.data_add(local_path, data_type=wrong_data_type)


def test_it_finds_a_resource_to_pull_by_its_attributes(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    file_path = local_data_files[0]
    resource = kiproject.data_add(file_path)
    # Push everything so it can be pulled.
    kiproject.data_push(resource)

    assert kiproject.data_pull(resource) == resource.abs_path
    assert kiproject.data_pull(resource.id) == resource.abs_path
    assert kiproject.data_pull(resource.name) == resource.abs_path
    assert kiproject.data_pull(resource.remote_uri) == resource.abs_path
    assert kiproject.data_pull(resource.abs_path) == resource.abs_path
    assert kiproject.data_pull(resource.rel_path) == resource.abs_path


def test_it_pulls_a_file_matching_the_data_structure(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file exist locally


def test_it_pulls_a_folder_matching_the_data_structure(mk_kiproject, syn_data):
    kiproject = mk_kiproject()
    syn_project, syn_folders, syn_files = syn_data

    for syn_folder in syn_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_file_not_matching_the_data_structure(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_file in syn_files:
        syn_file_uri = DataUri('syn', syn_file.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_pulls_a_folder_not_matching_the_data_structure(mk_kiproject, syn_non_data):
    kiproject = mk_kiproject()
    syn_parent, syn_folders, syn_files = syn_non_data

    for syn_folder in syn_folders:
        syn_folder_uri = DataUri('syn', syn_folder.id).uri

        # Add the folder to the KiProject
        ki_project_resource = kiproject.data_add(syn_folder_uri, data_type=DataType.CORE)

        # Pull the folder.
        remote_entity = kiproject.data_pull(ki_project_resource.remote_uri)
        assert remote_entity
        # TODO: check that file/folders exist locally


def test_it_does_not_pull_a_file_unless_the_remote_file_changed():
    # TODO: test this.
    pass


def test_it_finds_a_resource_to_push_by_its_attributes(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    file_path = local_data_files[0]
    resource = kiproject.data_add(file_path)

    assert kiproject.data_push(resource) == resource.abs_path
    assert kiproject.data_push(resource.id) == resource.abs_path
    assert kiproject.data_push(resource.name) == resource.abs_path
    assert kiproject.data_push(resource.remote_uri) == resource.abs_path
    assert kiproject.data_push(resource.abs_path) == resource.abs_path
    assert kiproject.data_push(resource.rel_path) == resource.abs_path


def test_it_pushes_a_file_matching_the_data_structure(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        ki_project_resource = kiproject.data_add(file_path)

        # Push the file
        remote_entity = kiproject.data_push(ki_project_resource.name)
        assert remote_entity
        # TODO: check that file/folders were pushed


def test_it_pushes_a_folder_matching_the_data_structure(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for folder_path in local_data_folders:
        ki_project_resource = kiproject.data_add(folder_path)

        # Push the file
        remote_entity = kiproject.data_push(ki_project_resource.name)
        assert remote_entity
        # TODO: check that file/folders were pushed


def test_it_pushes_a_file_to_a_different_remote_project(syn_client, mk_kiproject, mk_syn_project, mk_syn_files,
                                                        write_file, read_file):
    kiproject = mk_kiproject()

    other_syn_project = mk_syn_project()

    syn_file = mk_syn_files(other_syn_project, file_num=1, versions=1, suffix='')[0]

    syn_file_uri = DataUri('syn', syn_file.id).uri
    kiproject.data_add(syn_file_uri, data_type=DataType.CORE)
    local_file_path = kiproject.data_pull(syn_file_uri)

    new_file_contents = str(uuid.uuid4())
    write_file(local_file_path, new_file_contents)

    kiproject.data_push(syn_file_uri)

    updated_syn_file = syn_client.get(syn_file.id, downloadFile=True)
    assert read_file(updated_syn_file.path) == new_file_contents


def test_it_pushes_a_folder_to_a_different_remote_project():
    # TODO: test this
    pass


def test_it_does_not_push_a_file_unless_the_local_file_changed(mk_kiproject, mk_syn_files, syn_client, mocker):
    kiproject = mk_kiproject()

    # Get the Synapse project for the KiProject
    syn_project = syn_client.get(DataUri.parse(kiproject.project_uri).id)

    syn_data_folder = syn_client.store(synapseclient.Folder(name='data', parent=syn_project))
    syn_core_folder = syn_client.store(synapseclient.Folder(name='core', parent=syn_data_folder))

    # Create a Synapse file to add/pull/push
    syn_file = mk_syn_files(syn_core_folder, file_num=1, versions=1, suffix='')[0]

    syn_file_uri = DataUri('syn', syn_file.id).uri
    resource = kiproject.data_add(syn_file_uri, data_type=DataType.CORE)
    kiproject.data_pull()

    # The file exists in the Synapse project and has been pulled locally.
    # Pushing again should NOT upload the file again.
    mocker.spy(synapseclient.client, 'upload_file_handle')
    kiproject.data_push(syn_file_uri)
    # NOTE: This will fail until this issue is fixed: https://sagebionetworks.jira.com/browse/SYNPY-946
    # TODO: Uncomment this when the synapseclient bug is fixed.
    # assert synapseclient.client.upload_file_handle.call_count == 0


def test_it_tests_the_workflow(mk_kiproject,
                               mk_local_data_dir,
                               mk_uniq_string,
                               syn_data,
                               syn_non_data):
    kiproject = mk_kiproject()
    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    ###########################################################################
    # Add/Push Local Files and Folders
    ###########################################################################

    # Files
    for local_file in local_data_files:
        resource = kiproject.data_add(local_file)
        abs_path = kiproject.data_push(resource)
        assert abs_path == resource.abs_path
        # Re-add it
        resource_count = len(kiproject.resources)
        resource = kiproject.data_add(local_file)
        assert len(kiproject.resources) == resource_count
        # Re-add with a change
        new_name = mk_uniq_string()
        resource = kiproject.data_add(local_file, name=new_name, version='1')
        assert len(kiproject.resources) == resource_count
        assert resource.version == '1'
        assert resource.name == new_name
        resource = kiproject.data_add(local_file)
        assert len(kiproject.resources) == resource_count
        assert resource.version is None
        assert resource.name == os.path.basename(local_file)

    # Folders
    for local_folder in local_data_folders:
        resource = kiproject.data_add(local_folder)
        abs_path = kiproject.data_push(resource)
        assert abs_path == resource.abs_path

    ###########################################################################
    # Add/Pull Remote Data Files and Folders
    ###########################################################################
    _, syn_data_folders, syn_data_files = syn_data

    # Files
    for syn_file in syn_data_files:
        remote_uri = DataUri('syn', syn_file.id).uri
        resource = kiproject.data_add(remote_uri)
        abs_path = kiproject.data_pull(remote_uri)
        # Lock the version
        resource = kiproject.data_change(remote_uri, version='2')
        assert resource.version == '2'
        abs_path = kiproject.data_pull(remote_uri)

    # Folders
    for syn_folder in syn_data_folders:
        remote_uri = DataUri('syn', syn_folder.id).uri
        resource = kiproject.data_add(remote_uri)
        abs_path = kiproject.data_pull(remote_uri)

    ###########################################################################
    # Add/Pull Remote non-Data Files and Folders
    ###########################################################################
    _, syn_non_data_folders, syn_non_data_files = syn_non_data

    # Files
    for syn_non_data_file in syn_non_data_files:
        remote_uri = DataUri('syn', syn_non_data_file.id).uri
        resource = kiproject.data_add(remote_uri, data_type=DataType.CORE)
        abs_path = kiproject.data_pull(remote_uri)

    # Folders
    for syn_non_data_folder in syn_non_data_folders:
        remote_uri = DataUri('syn', syn_non_data_folder.id).uri
        resource = kiproject.data_add(remote_uri, data_type=DataType.CORE)
        abs_path = kiproject.data_pull(remote_uri)

    ###########################################################################
    # Push/Pull Everything
    ###########################################################################
    kiproject.data_push()
    kiproject.data_pull()

    ###########################################################################
    # data_list
    ###########################################################################
    kiproject.data_list()
    kiproject.data_list(all=True)

    ###########################################################################
    # data_remove
    ###########################################################################
    for resource in kiproject.resources.copy():
        if resource.root_id:
            continue
        kiproject.data_remove(resource.remote_uri or resource.abs_path)

    assert len(kiproject.resources) == 0


def test_it_finds_a_resource_to_remove_by_its_attributes(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        resource = kiproject.data_add(file_path)
        # Push it so all the attributes are set.
        kiproject.data_push(resource)

        assert kiproject.data_remove(resource.remote_uri) == resource
        kiproject.resources.append(resource)

        assert kiproject.data_remove(resource.abs_path) == resource
        kiproject.resources.append(resource)

        assert kiproject.data_remove(resource.rel_path) == resource
        kiproject.resources.append(resource)


def test_it_removes_resources(mk_kiproject):
    kiproject = mk_kiproject(with_fake_project_files=True)

    for resource in kiproject.resources.copy():
        if resource.root_id:
            continue

        kiproject.data_remove(resource.remote_uri or resource.abs_path)

    assert len(kiproject.resources) == 0


def test_data_type_to_project_path(kiproject):
    for data_type in DataType.ALL:
        assert kiproject.data_type_to_project_path(data_type) == os.path.join(kiproject.data_path, data_type)


def test_data_type_from_project_path(kiproject):
    for data_type_name in DataType.ALL:
        path = kiproject.data_type_to_project_path(data_type_name)
        assert kiproject.data_type_from_project_path(path).name == data_type_name

        other_paths = []
        for other_path in ['one', 'two', 'three', 'file.csv']:
            other_paths.append(other_path)
            new_path = os.path.join(path, *other_paths)
            assert kiproject.data_type_from_project_path(new_path).name == data_type_name


def test_is_project_data_type_path(kiproject, mk_tempdir):
    temp_dir = mk_tempdir()

    assert kiproject.is_project_data_type_path(temp_dir) is False

    for root_data_path in kiproject._root_data_paths():
        assert kiproject.is_project_data_type_path(root_data_path) is False

        data_type_child_path = os.path.join(root_data_path, 'test.csv')
        assert kiproject.is_project_data_type_path(data_type_child_path) is True

    # TODO: add more tests


def test_data_pull_non_data_folder(syn_test_helper, mk_tempfile, mk_uniq_string, mk_kiproject):
    syn_project = syn_test_helper.create_project()

    syn_folder1 = syn_test_helper.client().store(synapseclient.Folder(name='Folder1', parent=syn_project))
    syn_test_helper.client().store(synapseclient.File(path=mk_tempfile(), parent=syn_folder1))

    syn_folder2 = syn_test_helper.client().store(synapseclient.Folder(name='Folder2', parent=syn_folder1))
    syn_test_helper.client().store(synapseclient.File(path=mk_tempfile(), parent=syn_folder2))

    syn_folder3 = syn_test_helper.client().store(synapseclient.Folder(name='Folder3', parent=syn_folder2))
    syn_test_helper.client().store(synapseclient.File(path=mk_tempfile(), parent=syn_folder3))

    syn_folder4 = syn_test_helper.client().store(synapseclient.Folder(name='Folder4', parent=syn_folder3))
    syn_test_helper.client().store(synapseclient.File(path=mk_tempfile(), parent=syn_folder4))

    syn_folder5 = syn_test_helper.client().store(synapseclient.Folder(name='Folder5', parent=syn_folder4))
    syn_test_helper.client().store(synapseclient.File(path=mk_tempfile(), parent=syn_folder5))

    kiproject = mk_kiproject()
    kiproject.data_add(DataUri('syn', syn_folder1.id).uri, data_type=DataType.CORE)
    kiproject.data_pull()


def test_data_push_folder(mk_uniq_string, write_file, mk_kiproject):
    kiproject = mk_kiproject()

    for data_type_name in DataType.ALL:
        path = kiproject.data_type_to_project_path(data_type_name)

        write_file(os.path.join(path, mk_uniq_string()), 'version1')

        folder1 = SysPath(os.path.join(path, 'Folder1'))
        folder1.ensure_dirs()
        write_file(os.path.join(folder1.abs_path, mk_uniq_string()), 'version1')

        folder2 = SysPath(os.path.join(folder1.abs_path, 'Folder2'))
        folder2.ensure_dirs()
        write_file(os.path.join(folder2.abs_path, mk_uniq_string()), 'version1')

        folder3 = SysPath(os.path.join(folder2.abs_path, 'Folder3'))
        folder3.ensure_dirs()
        write_file(os.path.join(folder3.abs_path, mk_uniq_string()), 'version1')

        folder4 = SysPath(os.path.join(folder3.abs_path, 'Folder4'))
        folder4.ensure_dirs()
        write_file(os.path.join(folder4.abs_path, mk_uniq_string()), 'version1')

        folder5 = SysPath(os.path.join(folder4.abs_path, 'Folder5'))
        folder5.ensure_dirs()
        write_file(os.path.join(folder5.abs_path, mk_uniq_string()), 'version1')

        kiproject.data_add(folder1.abs_path)
        kiproject.data_push()


def test_it_finds_a_resource_to_change_by_its_attributes(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject)

    for file_path in local_data_files:
        resource = kiproject.data_add(file_path)
        # Push it so all the attributes are set.
        kiproject.data_push(resource)

        assert kiproject.data_change(resource) == resource
        assert kiproject.data_change(resource.id) == resource
        assert kiproject.data_change(resource.name) == resource
        assert kiproject.data_change(resource.remote_uri) == resource
        assert kiproject.data_change(resource.abs_path) == resource
        assert kiproject.data_change(resource.rel_path) == resource


def test_it_finds_local_files_and_folders_not_in_the_manifest(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject, return_all=True)
    paths = deque(local_data_folders + local_data_files)

    assert sorted(kiproject.find_missing_resources()) == sorted(paths)

    while paths:
        path = paths.popleft()
        kiproject.data_add(path)
        assert sorted(kiproject.find_missing_resources()) == sorted(paths)

    assert sorted(kiproject.find_missing_resources()) == []


def test_it_excludes_local_files_and_folders_from_the_manifest(mk_kiproject, mk_local_data_dir):
    kiproject = mk_kiproject()

    local_data_folders, local_data_files = mk_local_data_dir(kiproject, return_all=True)
    all_paths = (local_data_folders + local_data_files)

    assert sorted(kiproject.find_missing_resources()) == sorted(all_paths)

    for path in all_paths:
        basename = os.path.basename(path)

        patterns = []

        # Match on absolute path
        patterns.append(path)

        # Match on the basename
        patterns.append(basename)

        # Match on partial basename
        patterns.append(basename[:round(len(basename) / 2)] + '*')

        for pattern in patterns:
            assert path in kiproject.find_missing_resources()
            kiproject.add_data_ignore(pattern)
            assert path not in kiproject.find_missing_resources()
            kiproject.remove_data_ignore(pattern)


def test_it_can_add_and_remove_a_data_ignore_pattern(kiproject):
    pattern = 'test.txt'
    assert pattern not in kiproject.data_ignores

    kiproject.add_data_ignore(pattern)
    assert pattern in kiproject.data_ignores
    assert_matches_config(kiproject)

    kiproject.remove_data_ignore(pattern)
    assert pattern not in kiproject.data_ignores
    assert_matches_config(kiproject)
