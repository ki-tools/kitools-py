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
import json as JSON
from .project_file import ProjectFile
from .project_template import ProjectTemplate
from .data_providers import ProviderUri
from .data_type import DataType


class Project(object):
    CONFIG_FILENAME = 'project.json'

    def __init__(self, local_path):
        self.local_path = local_path
        self.title = None
        self.description = None
        self.project_uri = None
        self.files = []

        self._config_path = os.path.join(self.local_path, self.CONFIG_FILENAME)

        if not self.load():
            self.create()

    def create(self, title=None, description=None, project_uri=None):
        # TODO: Prompt for empty param values.

        ProjectTemplate(self.local_path).write()

        self.title = title
        self.description = description
        self.project_uri = project_uri

        self.save()
        return self

    def data_pull(self, remote_uri=None, data_type=None, version=None, get_latest=True):
        """
        Downloads a file or a complete directory from a remote URI.

        :param remote_uri: the URI of the remote file (e.g., syn:syn123456)
        :param data_type: one of {'core', 'discovered', 'derived'}
        :param version: the version of the file to pull
        :param get_latest: pull the latest remote version (cannot be used if version is set)
        :return: absolute path to the local file or folder.
        """
        result = None

        provider_uri = ProviderUri(remote_uri)
        data_provider = provider_uri.data_provider()
        data_type = DataType(data_type)

        self.save()

        return result

    def data_load(self, remote_uri, data_type=None, version=None, get_latest=True):
        """
        Calls data_pull and then loads into memory and returns
        Check the file extension and load a certain set of supported file types
        to start: csv, pickle, json, excel

        :param remote_uri:
        :param data_type:
        :param version:
        :param get_latest:
        :return: the loaded data
        """
        result = None

        provider_uri = ProviderUri(remote_uri)
        data_provider = provider_uri.data_provider()
        data_type = DataType(data_type)

        return result

    def data_save(self, name, data, data_type=None):
        """
        Saves the data locally and pushes it to the remote project (inferring how to save based on file extension).
        (Uses data_push)

        :param name:
        :param data:
        :param data_type:
        :return:
        """
        result = None

        provider_uri = ProviderUri(self.project_uri)
        data_provider = provider_uri.data_provider()
        data_type = DataType(data_type)

        return result

    def data_push(self, local_path=None):
        """
        Takes the file at local_path and uploads it to the remote project,
        or uploads all project files (with changes).

        :param local_path:
        :return:
        """
        result = None

        provider_uri = ProviderUri(self.project_uri)
        data_provider = provider_uri.data_provider()
        data_type = DataType(data_type)

        return result

    def data_list(self):
        """
        Prints out a nice table of all the available project file entries.
        """
        return None

    def load(self):
        """
        Loads the Project from a config file.
        :return: True if the config file exists and was loaded.
        """
        loaded = False
        if os.path.isfile(self._config_path):
            with open(self._config_path) as f:
                self._json_to_self(JSON.load(f))
                loaded = True

        return loaded

    def save(self):
        """
        Saves the Project to a config file.
        :return: None
        """
        with open(self._config_path, 'w') as f:
            JSON.dump(self._self_to_json(), f, indent=2)

    def _self_to_json(self):
        return {
            'title': self.title,
            'description': self.description,
            'project_uri': self.project_uri,
            'files': [self._project_file_to_json(f) for f in self.files]
        }

    def _json_to_self(self, json):
        self.title = json.get('title')
        self.description = json.get('description')
        self.project_uri = json.get('project_uri')
        self.files = []

        jfiles = json.get('files')
        for jfile in jfiles:
            self.files.append(self._json_to_project_file(jfile))

    def _project_file_to_json(self, project_file):
        return {
            'remote_uri': project_file.remote_uri,
            'local_path': project_file.local_path,
            'version': project_file.version
        }

    def _json_to_project_file(self, json):
        return ProjectFile(
            remote_uri=json.get('remote_uri'),
            local_path=json.get('local_path'),
            version=json.get('version')
        )
