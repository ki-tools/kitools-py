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


class BaseProvider(object):

    @abc.abstractmethod
    def name(self):
        """
        Returns the name of the Data Provider (e.g., Synapse).
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
    def create_project(self, name, **kwargs):
        """
        Creates a new project.
        :param name:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_project(self, remote_uri):
        """
        Gets a project.
        :param remote_uri:
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_pull(self, remote_id, local_path, version=None, get_latest=True):
        """
        Downloads a file for folder from a data provider into a local directory.
        :param remote_id:
        :param local_path:
        :param version:
        :param get_latest:
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_push(self, local_path):
        """
        Uploads a file for folder to a data provider from a local directory.
        :param local_path:
        :return:
        """
        raise NotImplementedError()
