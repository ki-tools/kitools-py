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

import os
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
        try:
            return SynapseProvider.client()._loggedIn() is not False
        except Exception as ex:
            # TODO: log this exception
            pass
        return False

    def create_project(self, name, **kwargs):
        raise NotImplementedError()

    def get_project(self, remote_uri):
        raise NotImplementedError()

    def data_pull(self, remote_id, local_path, version=None, get_latest=True):
        if version and get_latest:
            raise ValueError('version and get_latest cannot both be set.')

        entity = SynapseProvider.client().get(
            remote_id,
            downloadFile=True,
            downloadLocation=local_path,
            ifcollision='overwrite.local',
            version=version
        )

        provider_file = ProviderFile(
            entity.id,
            entity.name,
            entity.get('versionNumber', None),
            is_directory=isinstance(entity, synapseclient.Folder),
            local_path=entity.get('path', os.path.join(local_path, entity.name)),
            raw=entity
        )

        if provider_file.is_directory:
            if version is not None:
                raise ValueError('version cannot be set when pulling a folder.')

            # Create the local directory for the folder.
            if not os.path.exists(provider_file.local_path):
                os.makedirs(provider_file.local_path)

            syn_children = SynapseProvider.client().getChildren(entity, includeTypes=['folder', 'file'])

            for syn_child in syn_children:
                child_local_path = provider_file.local_path if provider_file.is_directory else local_path

                child = self.data_pull(syn_child.get('id'), child_local_path, version=None, get_latest=True)
                provider_file.children.append(child)

        return provider_file

    def data_push(self, remote_id, local_path):
        remote_entity = None
        try:
            remote_entity = SynapseProvider.client().get(remote_id)
        except Exception as ex:
            # TODO: log this
            pass

        syn_parent_id = None

        if isinstance(remote_entity, synapseclient.Project) or isinstance(remote_entity, synapseclient.Folder):
            syn_parent_id = remote_entity.id
        else:
            syn_parent_id = remote_entity.get('parentId')

        entity = SynapseProvider.client().store(synapseclient.File(path=local_path, parent=syn_parent_id))

        provider_file = ProviderFile(
            entity.id,
            entity.name,
            entity.get('versionNumber', None),
            is_directory=isinstance(entity, synapseclient.Folder),
            local_path=entity.get('path', os.path.join(local_path, entity.name)),
            raw=entity
        )

        return provider_file
