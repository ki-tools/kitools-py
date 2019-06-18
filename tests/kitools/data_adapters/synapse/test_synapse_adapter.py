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
from src.kitools.data_adapters import SynapseAdapter
from src.kitools.data_adapters.synapse.exceptions import InvalidNameError
from src.kitools.ki_project_resource import KiProjectResource
import synapseclient

from ...test_ki_project import kiproject


def test_name():
    assert SynapseAdapter().name() == 'Synapse'


def test_client():
    client = SynapseAdapter.client()
    assert client
    assert isinstance(client, synapseclient.Synapse)
    assert client._loggedIn() is not False

    # Returns the same client
    client2 = SynapseAdapter.client()
    assert client2 == client
    assert client2._loggedIn() is not False


def test_connected():
    assert SynapseAdapter().connected() is True

    with responses.RequestsMock() as rsps:
        # Unauthorized
        rsps.add(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=401)
        assert SynapseAdapter().connected() is False

        # General error
        rsps.replace(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=418)
        assert SynapseAdapter().connected() is False


@pytest.mark.xfail(raises=InvalidNameError)
def test_it_fails_with_invalid_filename(tmp_path, kiproject):
    f = tmp_path / 'il^egal.dat'
    f.write_text(u'\x00')
    kiproject_resource = KiProjectResource(kiproject, local_path=str(f))
    SynapseAdapter().data_push(ki_project_resource=kiproject_resource)

# TODO: add remaining tests.
