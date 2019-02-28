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


class RemoteProject(object):
    """
    Encapsulates a project from a provider.
    """

    def __init__(self, id, name, source=None):
        self._id = id
        self._name = name
        self._source = source

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source
