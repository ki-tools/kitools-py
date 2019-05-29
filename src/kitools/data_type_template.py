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


class DataTypeTemplate(object):
    _templates = []

    @classmethod
    def all(cls):
        return cls._templates

    @classmethod
    def default(cls):
        return next(d for d in cls._templates if d.is_default)

    @classmethod
    def register(cls, template):
        cls._templates.append(template)

    @classmethod
    def get(cls, name):
        return next((t for t in cls._templates if t.name == name), None)

    def __init__(self, name, description, paths, is_default=False):
        self.name = name
        self.description = description
        self.paths = paths
        self.is_default = is_default


class DataTypeTemplatePath(object):
    def __init__(self, name, rel_path):
        self.name = name
        self.rel_path = rel_path
