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

from .project_template import ProjectTemplate
from .project_file import ProjectFile
from .data_type import DataType
from .data_uri import DataUri


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

    def find_project_file(self, remote_uri):
        """
        Gets a ProjectFile by remote_uri
        :param remote_uri:
        :return: ProjectFile or None
        """
        return next((f for f in self.files if f.remote_uri == remote_uri), None)

    def data_pull(self, remote_uri=None, data_type=None, version=None, get_latest=True):
        """
        Downloads a file or a complete directory from a remote URI.

        :param remote_uri: the URI of the remote file (e.g., syn:syn123456)
        :param data_type: one of {'core', 'discovered', 'derived'}
        :param version: the version of the file to pull
        :param get_latest: pull the latest remote version (cannot be used if version is set)
        :return: A single ProviderFile or a list of ProviderFiles if pulling all.
        """
        if remote_uri and not data_type:
            raise ValueError('remote_uri and data_type are required.')

        if version and get_latest:
            raise ValueError('version and get_latest cannot both be set.')

        result = None

        if remote_uri:
            # Pull a specific file
            data_uri = DataUri.parse(remote_uri)
            data_provider = data_uri.data_provider()
            data_type = DataType(data_type)

            project_file = self.find_project_file(remote_uri)

            pull_version = version

            if version is None and project_file is not None:
                pull_version = project_file.version

            provider_file = data_provider.data_pull(
                data_uri.id,
                data_type.to_project_path(self.local_path),
                version=pull_version,
                get_latest=get_latest
            )

            if project_file:
                # Update the version if it changed
                project_file.version = provider_file.version
            else:
                # Add the ProjectFile
                relative_path = os.path.relpath(provider_file.local_path, start=self.local_path)
                project_file = ProjectFile(remote_uri=data_uri.uri(), local_path=relative_path, version=version)
                self.files.append(project_file)

            result = provider_file
        else:
            # Pull all files
            # TODO: implement this
            raise NotImplementedError()

        self.save()

        return result

    def data_push(self, local_path=None, data_type=None, remote_uri=None):
        """
        Takes the file at local_path and uploads it to the remote project,
        or uploads all project files (with changes).

        :param local_path:
        :return:
        """
        result = None

        data_uri = DataUri.parse(remote_uri or self.project_uri)
        data_provider = data_uri.data_provider()
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
