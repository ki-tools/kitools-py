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

    def __init__(self, project, remote_uri, local_path, version=None):
        """
        :param remote_uri: The remote URI of the folder or file.
        :param local_path: The relative (from the project root) or absolute path to the folder or file.
        :param version: The version of the file.
        """
        self._project = project
        self._remote_uri = remote_uri
        self._local_path = None

        if os.path.exists(local_path):
            self._local_path = local_path
        else:
            full_path = os.path.join(self.project.local_path, local_path)
            if os.path.exists(full_path):
                self._local_path = full_path
            else:
                raise FileNotFoundError('Could not find file: {0}'.format(local_path))

        self._version = str(version) if version else None

    @property
    def project(self):
        return self._project

    @property
    def remote_uri(self):
        return self._remote_uri

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def abs_path(self):
        """
        Gets the absolute path to the file.
        :return:
        """
        return os.path.join(self.project.local_path, self.rel_path)

    @property
    def rel_path(self):
        """
        Gets the path of the file relative to the project's root directory.
        :return:
        """
        return os.path.relpath(self._local_path, start=self.project.local_path)
