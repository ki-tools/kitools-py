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

from .exceptions import InvalidDataTypeError


class DataType(object):
    """
    Defines a standard set of names which are mapped to directories within the KiProject's 'data' directory.
    """
    DATA_DIR_NAME = 'data'

    CORE = 'core'
    DISCOVERED = 'discovered'
    ARTIFACTS = 'artifacts'
    ALL = [CORE, DISCOVERED, ARTIFACTS]

    def __init__(self, name):
        prepared_name = name.lower().strip() if name else None
        if prepared_name not in self.ALL:
            raise InvalidDataTypeError(name, DataType.ALL)

        self._name = prepared_name

    @property
    def name(self):
        return self._name
