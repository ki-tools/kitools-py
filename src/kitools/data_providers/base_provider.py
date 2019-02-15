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
    def login(self, username, password, **kwargs):
        """
        Logs into the data provider.
        :param username:
        :param password:
        :param kwargs:
        :return:
        """
        pass

    @abc.abstractmethod
    def create_project(self, name, **kwargs):
        """
        Creates a new project.
        :param name:
        :param kwargs:
        :return:
        """
        pass

    @abc.abstractmethod
    def get_project(self, source_uri):
        """
        Gets a project.
        :param source_uri:
        :return:
        """
        pass

    @abc.abstractmethod
    def pull_data(self, source_uri, target_path, only_if_changed=True):
        """
        Downloads a file for folder from a data provider into a local directory.
        :param source_uri:
        :param target_path:
        :param only_if_changed:
        :return:
        """
        pass

    @abc.abstractmethod
    def push_data(self, target_uri, source_path, only_if_changed=True):
        """
        Uploads a file for folder to a data provider from a local directory.
        :param target_uri:
        :param source_path:
        :param only_if_changed:
        :return:
        """
        pass
