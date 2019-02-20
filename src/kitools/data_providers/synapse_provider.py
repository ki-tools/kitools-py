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

from .base_provider import BaseProvider
from .provider_file import ProviderFile
import synapseclient


class SynapseProvider(BaseProvider):
    _client = None

    @classmethod
    def client(cls):
        """
        Gets a new or cached instance of a logged in Synapse client.
        :return:
        """
        if not cls._client:
            cls._client = synapseclient.Synapse()
            cls._client.login(silent=True)
        return cls._client

    def name(self):
        return 'Synapse'

    def connected(self):
        return SynapseProvider.client()._loggedIn() is not False

    def create_project(self, name, **kwargs):
        pass

    def get_project(self, remote_uri):
        pass

    def data_pull(self, remote_id, local_path, version=None, get_latest=True):
        if version and get_latest:
            raise ValueError('version and get_latest cannot both be set.')

        entity = SynapseProvider.client().get(
            remote_id,
            downloadFile=True,
            downloadLocation=local_path,
            version=version
        )

        if isinstance(entity, synapseclient.Folder):
            # TODO: download all the files/folders
            pass

        return ProviderFile(entity.id, entity.name, str(entity.versionNumber), entity)

    def data_push(self, local_path):
        pass
