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
import responses
from src.kitools.data_providers import SynapseProvider
import synapseclient


def test_name(synapse_test_config):
    assert SynapseProvider().name() == 'Synapse'


def test_client(synapse_test_config):
    client = SynapseProvider.client()
    assert client
    assert isinstance(client, synapseclient.Synapse)
    assert client._loggedIn() is not False

    # Returns the same client
    client2 = SynapseProvider.client()
    assert client2 == client
    assert client2._loggedIn() is not False


def test_connected(synapse_test_config):
    assert SynapseProvider().connected() is True

    with responses.RequestsMock() as rsps:
        # Unauthorized
        rsps.add(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=401)
        assert SynapseProvider().connected() is False

        # General error
        rsps.replace(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=418)
        assert SynapseProvider().connected() is False


def test_data_pull(syn_client, new_syn_project, mk_tempdir):
    syn_folder = syn_client.store(synapseclient.Folder(name='folder', parent=new_syn_project))

    download_dir = mk_tempdir()

    # Pull a specific version of a folder
    with pytest.raises(ValueError) as ex:
        SynapseProvider().data_pull(syn_folder.id, download_dir, version='1', get_latest=False)
    assert str(ex.value) == 'version cannot be set when pulling a folder.'

    # Get version and latest
    with pytest.raises(ValueError) as ex:
        SynapseProvider().data_pull(syn_folder.id, download_dir, version='1', get_latest=True)
    assert str(ex.value) == 'version and get_latest cannot both be set.'


def test_data_pull_file(syn_client, new_syn_project, mk_tempdir, mk_tempfile, write_file, read_file):
    # Make 2 versions of a file
    temp_file = mk_tempfile(content='version1')
    syn_file = syn_client.store(synapseclient.File(path=temp_file, parent=new_syn_project))
    write_file(temp_file, 'version2')
    syn_file = syn_client.store(synapseclient.File(path=temp_file, parent=new_syn_project))

    download_dir = os.path.join(mk_tempdir(), 'my_data')
    assert os.path.exists(download_dir) is False

    # Pulls the latest version
    pfile = SynapseProvider().data_pull(syn_file.id, download_dir, version=None, get_latest=True)
    assert pfile.is_directory is False
    assert pfile.id == syn_file.id
    assert pfile.name == syn_file.name
    assert pfile.version == '2'
    assert pfile.local_path == os.path.join(download_dir, pfile.name)
    assert len(pfile.children) == 0
    assert os.path.isfile(pfile.local_path)
    assert read_file(pfile.local_path) == 'version2'
    assert os.path.exists(download_dir) is True

    # Pulls a specific version
    pfile = SynapseProvider().data_pull(syn_file.id, download_dir, version='1', get_latest=False)
    assert pfile.id == syn_file.id
    assert pfile.version == '1'
    assert read_file(pfile.local_path) == 'version1'


def test_data_pull_folder(syn_client, new_syn_project, mk_tempdir, mk_tempfile, write_file, read_file):
    temp_file1 = mk_tempfile(content='folder1_file_version0')
    temp_file2 = mk_tempfile(content='folder1_file_version0')
    temp_file3 = mk_tempfile(content='folder1_file_version0')

    for i in range(1, 3):
        # Create some folders and files in Synapse
        syn_folder1 = syn_client.store(synapseclient.Folder(name='folder1', parent=new_syn_project))
        write_file(temp_file1, 'folder1_file_version{0}'.format(i))
        syn_file1 = syn_client.store(synapseclient.File(path=temp_file1, parent=syn_folder1))

        syn_folder2 = syn_client.store(synapseclient.Folder(name='folder2', parent=syn_folder1))
        write_file(temp_file2, 'folder2_file_version{0}'.format(i))
        syn_file2 = syn_client.store(synapseclient.File(path=temp_file2, parent=syn_folder2))

        syn_folder3 = syn_client.store(synapseclient.Folder(name='folder3', parent=syn_folder2))
        write_file(temp_file3, 'folder3_file_version{0}'.format(i))
        syn_file3 = syn_client.store(synapseclient.File(path=temp_file3, parent=syn_folder3))

        download_dir = os.path.join(mk_tempdir(), 'my_data')

        # Pull the latest folders and files

        # folder1
        pfolder1 = SynapseProvider().data_pull(syn_folder1.id, download_dir, version=None, get_latest=True)
        assert pfolder1.is_directory is True
        assert os.path.isdir(pfolder1.local_path)
        assert pfolder1.id == syn_folder1.id
        assert pfolder1.name == syn_folder1.name
        assert pfolder1.version is None
        assert len(pfolder1.children) == 2

        # file1
        pfile1 = pfolder1.children[1]
        assert pfile1.is_directory is False
        assert os.path.isfile(pfile1.local_path)
        assert pfile1.id == syn_file1.id
        assert pfile1.name == syn_file1.name
        assert pfile1.version == str(i)
        assert len(pfile1.children) == 0
        assert read_file(pfile1.local_path) == 'folder1_file_version{0}'.format(i)

        # folder2
        pfolder2 = pfolder1.children[0]
        assert pfolder2.is_directory is True
        assert os.path.isdir(pfolder2.local_path)
        assert pfolder2.id == syn_folder2.id
        assert pfolder2.name == syn_folder2.name
        assert pfolder2.version is None
        assert len(pfolder2.children) == 2

        # file2
        pfile2 = pfolder2.children[1]
        assert pfile2.is_directory is False
        assert os.path.isfile(pfile2.local_path)
        assert pfile2.id == syn_file2.id
        assert pfile2.name == syn_file2.name
        assert pfile2.version == str(i)
        assert len(pfile2.children) == 0
        assert read_file(pfile2.local_path) == 'folder2_file_version{0}'.format(i)

        # folder3
        pfolder3 = pfolder2.children[0]
        assert pfolder3.is_directory is True
        assert os.path.isdir(pfolder3.local_path)
        assert pfolder3.id == syn_folder3.id
        assert pfolder3.name == syn_folder3.name
        assert pfolder3.version is None
        assert len(pfolder3.children) == 1

        # file3
        pfile3 = pfolder3.children[0]
        assert pfile3.is_directory is False
        assert os.path.isfile(pfile3.local_path)
        assert pfile3.id == syn_file3.id
        assert pfile3.name == syn_file3.name
        assert pfile3.version == str(i)
        assert len(pfile3.children) == 0
        assert read_file(pfile3.local_path) == 'folder3_file_version{0}'.format(i)
