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
from pathlib import PurePath
from .sys_path import SysPath


class DataType(object):
    """
    Defines a friendly name and relative path for storing types of data within a KiProject.
    """

    def __init__(self, project_local_path, name, rel_path):
        self._project_local_path = project_local_path
        self._name = name
        # Get the rel_path from SysPath so the os.sep is correct.
        self._rel_path = SysPath(rel_path, cwd=project_local_path, rel_start=project_local_path).rel_path

    @property
    def name(self):
        return self._name

    @property
    def rel_path(self):
        return self._rel_path

    @property
    def abs_path(self):
        return os.path.join(self._project_local_path, self.rel_path)

    def to_json(self):
        """
        Serializes self into JSON.

        :return: Hash
        """
        return {
            'name': self.name,
            # Always store the path in Posix format ("/" vs "\").
            'rel_path': PurePath(self.rel_path).as_posix() if self.rel_path else None,
        }

    @staticmethod
    def from_json(json, project_local_path):
        """
        Deserializes JSON into a DataType.

        :param json: The JSON to deserialize.
        :return: DataType
        """
        return DataType(
            project_local_path,
            json.get('name'),
            json.get('rel_path'))

    def __eq__(self, other):
        if isinstance(other, DataType):
            return self.name == other.name and self.rel_path == other.rel_path and self.abs_path == other.abs_path
        else:
            return NotImplemented
