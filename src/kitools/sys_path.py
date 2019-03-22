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


class SysPath:
    """
    Helper class for working with paths.
    """

    def __init__(self, path, rel_start=None):
        self._orig_path = path

        var_path = os.path.expandvars(self._orig_path)
        expanded_path = os.path.expanduser(var_path)
        self._abs_path = os.path.abspath(expanded_path)
        self._rel_start = rel_start

    @property
    def abs_path(self):
        return self._abs_path

    @property
    def abs_parts(self):
        return PurePath(self.abs_path).parts

    @property
    def rel_path(self):
        return os.path.relpath(self.abs_path, start=self._rel_start)

    @property
    def rel_parts(self):
        return PurePath(self.rel_path).parts

    @property
    def exists(self):
        return os.path.exists(self.abs_path)

    @property
    def basename(self):
        return os.path.basename(self.abs_path)

    @property
    def is_dir(self):
        return os.path.isdir(self.abs_path)

    @property
    def is_file(self):
        return os.path.isfile(self.abs_path)

    def ensure_dirs(self):
        if not os.path.exists(self.abs_path):
            os.makedirs(self.abs_path)
