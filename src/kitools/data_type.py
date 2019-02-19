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


class DataType(object):
    CORE = 'core'
    DISCOVERED = 'discovered'
    DERIVED = 'derived'
    ALL = [CORE, DISCOVERED, DERIVED]

    def __init__(self, name):
        if not name:
            raise ValueError('Name must be specified.')

        name = name.lower()
        if name not in self.ALL:
            raise ValueError('Invalid data type: {0}'.format(name))

        self.name = name
