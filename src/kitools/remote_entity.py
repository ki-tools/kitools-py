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


class RemoteEntity(object):
    """
    Encapsulates a project/file/folder from a data provider.
    """

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self._name = kwargs.get('name')
        self._source = kwargs.get('source')

        self._version = str(kwargs.get('version')) if 'version' in kwargs else None
        self._local_path = kwargs.get('local_path', None)
        self._is_project = kwargs.get('is_project', False)
        self._is_file = kwargs.get('is_file', False)
        self._is_directory = kwargs.get('is_directory', False)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def local_path(self):
        return self._local_path

    @property
    def is_project(self):
        return self._is_project

    @property
    def is_directory(self):
        return self._is_directory

    @property
    def is_file(self):
        return self._is_file

    @property
    def source(self):
        return self._source
