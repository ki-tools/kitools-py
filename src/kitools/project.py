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

    def __init__(self, local_path, title=None, description=None, project_uri=None, files=None):
        self.local_path = local_path
        self.title = title
        self.description = description
        self.project_uri = project_uri
        self.files = files or []

        self._config_path = os.path.join(self.local_path, self.CONFIG_FILENAME)

        if not self.load():
            self.create(title=self.title, description=self.description, project_uri=self.project_uri)

    def create(self, title=None, description=None, project_uri=None):
        # TODO: Prompt for empty param values.

        ProjectTemplate(self.local_path).write()

        self.title = title
        self.description = description
        self.project_uri = project_uri

        self.save()
        return self

    def find_project_file_by_uri(self, remote_uri):
        """
        Gets a ProjectFile by remote_uri
        :param remote_uri:
        :return: ProjectFile or None
        """
        return next((f for f in self.files if f.remote_uri == remote_uri), None)

    def find_project_file_by_path(self, local_path):
        """
        Gets a ProjectFile by remote_uri
        :param remote_uri:
        :return: ProjectFile or None
        """
        return next((f for f in self.files if f.abs_path == local_path or f.rel_path == local_path), None)

    def data_pull(self, remote_uri=None, data_type=None, version=None, get_latest=True):
        """
        Downloads a file or a complete directory from a remote URI and adds
        the folder or file to the project manifest.

        :param remote_uri: the URI of the remote file (e.g., syn:syn123456)
        :param data_type: one of {'core', 'discovered', 'derived'}
        :param version: the version of the file to pull
        :param get_latest: pull the latest remote version (cannot be used if version is set)
        :return: A single ProviderFile or a list of ProviderFiles if pulling all.
        """
        if version and get_latest:
            raise ValueError('version and get_latest cannot both be set.')

        result = None

        if remote_uri:
            # Pull a specific file
            data_uri = DataUri.parse(remote_uri)
            data_provider = data_uri.data_provider()
            data_type = DataType(data_type)

            project_file = self.find_project_file_by_uri(remote_uri)

            pull_version = version

            if version is None and project_file is not None and not get_latest:
                pull_version = project_file.version

            provider_file = data_provider.data_pull(
                data_uri.id,
                data_type.to_project_path(self.local_path),
                version=pull_version,
                get_latest=get_latest
            )

            if project_file:
                # Update the version
                if get_latest:
                    # Set the version to None so we know to always get the latest version.
                    project_file.version = None
                elif version is not None:
                    # Set the version
                    project_file.version = provider_file.version
            else:
                # Add a ProjectFile
                self.__add_project_file(provider_file, data_uri.uri(), version=version)

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
        :param data_type:
        :param remote_uri:
        :return:
        """
        result = None

        if not os.path.isfile(local_path):
            raise ValueError('local_path must be a file.')

        if local_path:
            # Push a specific file
            local_path = os.path.abspath(local_path)

            # Push to a specific remote_uri otherwise push to the main project.
            data_uri = DataUri.parse(remote_uri or self.project_uri)
            data_provider = data_uri.data_provider()
            data_type = DataType(data_type)

            # TODO: Make sure the file is in the correct folder based on the data_type.

            provider_file = data_provider.data_push(data_uri.id, local_path)

            # Update the data_uri now that the file has been stored.
            data_uri = DataUri(scheme=data_uri.scheme, id=provider_file.id)

            # See if the file is already in the project
            project_file = self.find_project_file_by_uri(data_uri.uri()) or self.find_project_file_by_path(local_path)

            if project_file:
                # Make sure it's the same file
                if project_file.abs_path != local_path:
                    raise Exception('Existing project file found but does not match file path: {0} : {1}'.format(
                        project_file.abs_path, local_path))

                if project_file.remote_uri != data_uri.uri():
                    raise Exception('Existing project file found but has different remote_uri: {0} : {1}'.format(
                        project_file.remote_uri, data_uri.uri()))
            else:
                # Add a ProjectFile
                self.__add_project_file(provider_file, data_uri.uri())

            result = provider_file
        else:
            # Push all files
            # TODO: implement this
            raise NotImplementedError()

        return result

    def __add_project_file(self, provider_file, remote_uri, version=None):
        project_file = ProjectFile(self,
                                   remote_uri=remote_uri,
                                   local_path=provider_file.local_path,
                                   version=version)
        self.files.append(project_file)
        return project_file

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
            'rel_path': project_file.rel_path,
            'version': project_file.version
        }

    def _json_to_project_file(self, json):
        return ProjectFile(self,
                           remote_uri=json.get('remote_uri'),
                           local_path=json.get('rel_path'),
                           version=json.get('version'))
