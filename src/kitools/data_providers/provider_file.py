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


class ProviderFile(object):
    """
    Encapsulates a file/folder from a provider.
    """

    def __init__(self, id, name, version, local_path=None, raw=None, is_directory=False, children=None):
        self._id = id
        self._name = name
        self._version = str(version) if version else None
        self._local_path = local_path
        self._is_directory = is_directory
        self._children = children or []
        self._raw = raw

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
    def is_directory(self):
        return self._is_directory

    @property
    def children(self):
        return self._children

    @property
    def raw(self):
        return self._raw
