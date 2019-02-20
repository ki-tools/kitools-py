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


def test_data_pull(syn_client, new_syn_project, new_temp_file):
    # Create a Synapse file to pull
    syn_file = syn_client.store(synapseclient.File(path=new_temp_file, parent=new_syn_project))

    local_path = os.path.dirname(new_temp_file)

    # Pull the latest file
    provider_file = SynapseProvider().data_pull(syn_file.id, local_path, version=None, get_latest=True)
    assert provider_file
    assert provider_file.id == syn_file.id

    # Pull a specific version of the file
    # TODO: test this

    # Pull the latest folder
    # TODO: test this

    # Pull a specific version of a folder
    # TODO: folders don't support versions, can this be tested?
