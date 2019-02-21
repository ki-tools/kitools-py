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


class ProjectFile(object):

    def __init__(self, remote_uri=None, local_path=None, version=None):
        """
        :param remote_uri: The remote URI of the folder or file.
        :param local_path: The relative path from the project root to the folder or file.
        :param version: The version of the file.
        """
        self.remote_uri = remote_uri
        self.local_path = local_path
        self.version = str(version) if version else None

    def to_absolute_path(self, root_path):
        """
        Gets the absolute path from a root path.
        :param root_path:
        :return:
        """
        root_path = os.path.abspath(root_path)
        return os.path.join(root_path, self.local_path)

    @staticmethod
    def to_relative_path(child_path, root_path):
        """
        Gets the relative path of a child file for folder from a root path.
        :param root_path:
        :param child_path:
        :return:
        """
        root_path = os.path.abspath(root_path)
        return os.path.relpath(child_path, start=root_path)
