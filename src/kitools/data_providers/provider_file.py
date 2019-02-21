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
        self.id = id
        self.name = name
        self.version = str(version) if version else None
        self.local_path = local_path
        self.raw = raw
        self.is_directory = is_directory
        self.children = children or []
