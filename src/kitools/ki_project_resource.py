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
import uuid
from .data_type import DataType
from .sys_path import SysPath


class KiProjectResource(object):

    def __init__(self,
                 kiproject,
                 id=None,
                 root_id=None,
                 data_type=None,
                 remote_uri=None,
                 local_path=None,
                 name=None,
                 version=None):
        """

        :param kiproject:
        :param id:
        :param root_id:
        :param data_type:
        :param remote_uri:
        :param local_path:
        :param name:
        :param version:
        """
        self._id = id if id else str(uuid.uuid4())
        self._root_id = root_id
        self._kiproject = kiproject
        self._remote_uri = remote_uri
        self._name = name

        self._data_type = None
        self._set_data_type(data_type)

        self._local_path = None
        self._set_local_path(local_path)

        self._version = None
        self._set_version(version)

    def _set_data_type(self, value):
        if value:
            # Validate the value.
            value = DataType(value).name
        self._data_type = value

    def _set_local_path(self, value):
        if value:
            if not os.path.exists(value):
                full_path = os.path.join(self.kiproject.local_path, value)
                value = full_path

        self._local_path = value

        if self.rel_path:
            self.data_type = SysPath(self.rel_path).rel_parts[1]

    def _set_version(self, value):
        self._version = str(value) if value else None

    @property
    def kiproject(self):
        return self._kiproject

    @property
    def id(self):
        return self._id

    @property
    def root_id(self):
        return self._root_id

    @root_id.setter
    def root_id(self, value):
        self._root_id = value

    @property
    def root_resource(self):
        if self.root_id is not None:
            return self.kiproject.find_project_resource_by(id=self.root_id)
        else:
            return None

    @property
    def remote_uri(self):
        return self._remote_uri

    @remote_uri.setter
    def remote_uri(self, value):
        self._remote_uri = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        self._set_data_type(value)

    @property
    def abs_path(self):
        """
        Gets the absolute path to the file.
        :return:
        """
        if self.rel_path:
            return os.path.join(self.kiproject.local_path, self.rel_path)
        else:
            return None

    @abs_path.setter
    def abs_path(self, value):
        self._set_local_path(value)

    @property
    def rel_path(self):
        """
        Gets the path of the file relative to the KiProject's root directory.
        :return:
        """
        if self._local_path:
            return SysPath(self._local_path, rel_start=self.kiproject.local_path).rel_path
        else:
            return None

    @rel_path.setter
    def rel_path(self, value):
        self._set_local_path(value)
