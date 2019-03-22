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

import abc


class BaseAdapter(object):
    """
    Base class for data adapters.
    """

    @abc.abstractmethod
    def name(self):
        """
        Returns the name of the Data Adapter(e.g., Synapse).

        :return: String
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def connected(self):
        """
        Gets if the provider is up and accessible.

        :return: True if successful
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_entity(self, remote_id, version=None, local_path=None):
        """
        Gets a remote entity (Project, Folder, File).

        :param remote_id: The ID of the remote entity.
        :param version: The version to get, or None for the latest version.
        :param local_path: If getting a file then set the local path to download the file to.
        :return: RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def create_project(self, name):
        """
        Creates a new remote project.

        :param name:
        :param kwargs:
        :return: RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_pull(self, ki_project_resource):
        """
        Pulls a KiProjectResource.

        :param ki_project_resource: The KiProjectResource to pull.
        :return: RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_push(self, ki_project_resource):
        """
        Pushes a KiProjectResource.

        :param ki_project_resource: The KiProjectResource to push.
        :return: RemoteEntity
        """
        raise NotImplementedError()
