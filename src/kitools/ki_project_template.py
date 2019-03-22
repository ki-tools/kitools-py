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
from .sys_path import SysPath


class KiProjectTemplate:
    """
    Creates the base directories and files for a KiProject.
    """

    def __init__(self, local_path):
        self.local_path = local_path

    def write(self):
        self.create_dirs()
        self.create_gitignore()

    def create_dirs(self):
        SysPath(self.local_path).ensure_dirs()

        for dirname in KiProjectTemplate.project_dir_names():
            full_path = os.path.join(self.local_path, dirname)
            SysPath(full_path).ensure_dirs()

    def create_gitignore(self):
        gitignore_path = os.path.join(self.local_path, '.gitignore')
        if not os.path.isfile(gitignore_path):
            # TODO: implement this
            pass

    @staticmethod
    def project_dir_names():
        return [
            'data',
            'data{0}core'.format(os.sep),
            'data{0}derived'.format(os.sep),
            'data{0}discovered'.format(os.sep),
            'scripts'.format(os.sep),
            'reports'.format(os.sep)]
