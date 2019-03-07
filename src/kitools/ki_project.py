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
from beautifultable import BeautifulTable
from .ki_project_template import KiProjectTemplate
from .ki_project_resource import KiProjectResource
from .data_type import DataType
from .data_uri import DataUri


class KiProject(object):
    CONFIG_FILENAME = 'kiproject.json'

    def __init__(self, local_path, title=None, description=None, project_uri=None, resources=None):
        if not local_path or local_path.strip() == '':
            raise ValueError('local_path is required.')

        self.local_path = os.path.abspath(local_path)
        self.title = title
        self.description = description
        self.project_uri = project_uri
        self.resources = resources or []

        self._config_path = os.path.join(self.local_path, self.CONFIG_FILENAME)

        self._loaded = False

        if self.load():
            # Ensure the kiproject structure exists
            KiProjectTemplate(self.local_path).write()

            print('KiProject successfully loaded and ready to use.')
            self._loaded = True
        else:
            if self._init_project():
                self._loaded = True
                print('KiProject initialized successfully and ready to use.')
            else:
                print('KiProject initialization failed.')

    def data_add(self, remote_uri_or_local_path, name=None, version=None, data_type=None):
        self._ensure_loaded()

        is_uri = DataUri.is_uri(remote_uri_or_local_path)
        is_local = not is_uri and os.path.exists(remote_uri_or_local_path)

        if not is_uri and not is_local:
            raise ValueError('Please specify a remote URI or a local file or folder.')

        project_resource = None
        if is_uri:
            project_resource = KiProjectResource(kiproject=self,
                                                 data_type=data_type,
                                                 remote_uri=remote_uri_or_local_path,
                                                 name=(name or remote_uri_or_local_path),
                                                 version=version)
        else:
            # Make sure the file is in one of the data directories.
            if not DataType.is_project_data_path(self.local_path, remote_uri_or_local_path):
                raise ValueError('local_path must be in one of the data directories.')

            project_resource = KiProjectResource(kiproject=self,
                                                 data_type=data_type,
                                                 local_path=remote_uri_or_local_path,
                                                 name=(name or os.path.basename(remote_uri_or_local_path)),
                                                 version=version)

        self._add_ki_project_resource(project_resource)
        self.save()
        return project_resource

    def data_pull(self, remote_uri_or_name=None):
        self._ensure_loaded()

        if remote_uri_or_name:
            project_resource = self.find_project_resource_by(remote_uri=remote_uri_or_name) or \
                               self.find_project_resource_by(name=remote_uri_or_name)

            data_uri = DataUri.parse(project_resource.remote_uri)
            remote_entity = data_uri.data_adapter().data_pull(project_resource)
            return remote_entity
        else:
            results = []
            for project_resource in self.resources:
                if not project_resource.remote_uri:
                    # Needs to be pushed
                    print('Resource {0} cannot be pulled until it has been pushed.'.format(project_resource.rel_path))
                    continue

                data_uri = DataUri.parse(project_resource.remote_uri)
                remote_entity = data_uri.data_adapter().data_pull(project_resource)
                results.append(remote_entity)
            return results

    def data_push(self, remote_uri_or_name=None):
        self._ensure_loaded()

        if remote_uri_or_name:
            project_resource = self.find_project_resource_by(remote_uri=remote_uri_or_name) or \
                               self.find_project_resource_by(name=remote_uri_or_name)

            data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
            remote_entity = data_uri.data_adapter().data_push(project_resource)
            return remote_entity
        else:
            results = []
            for project_resource in self.resources:
                # Needs needs to be pulled first.
                if not project_resource.rel_path:
                    print('Resource {0} cannot be pushed until it has been pulled.'.format(project_resource.remote_uri))
                    continue

                data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
                remote_entity = data_uri.data_adapter().data_push(project_resource)
                results.append(remote_entity)
            return results

    def data_list(self):
        """
        Prints out a nice table of all the available KiProject resource entries.
        :return: BeautifulTable
        """
        self._ensure_loaded()

        table = BeautifulTable(max_width=1000)
        table.set_style(BeautifulTable.STYLE_BOX)
        table.column_headers = ['Remote URI', 'Version', 'Path']
        for resource in self.resources:
            table.append_row([resource.remote_uri, resource.version, resource.rel_path])

        print(table)
        return table

    def find_project_resource_by(self, remote_uri=None, abs_path=None, rel_path=None, name=None):
        self._ensure_loaded()

        for resource in self.resources:
            if remote_uri is not None and remote_uri != resource.remote_uri:
                continue

            if abs_path is not None and abs_path != resource.abs_path:
                continue

            if rel_path is not None and rel_path != resource.rel_path:
                continue

            if name is not None and name != resource.name:
                continue

            return resource

    def load(self):
        """
        Loads the KiProject from a config file.
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
        Saves the KiProject to a config file.
        :return: None
        """
        with open(self._config_path, 'w') as f:
            JSON.dump(self._self_to_json(), f, indent=2)

    def _self_to_json(self):
        return {
            'title': self.title,
            'description': self.description,
            'project_uri': self.project_uri,
            'resources': [self._ki_project_resource_to_json(f) for f in self.resources]
        }

    def _json_to_self(self, json):
        self.title = json.get('title')
        self.description = json.get('description')
        self.project_uri = json.get('project_uri')
        self.resources = []

        jresources = json.get('resources')
        for jresource in jresources:
            self.resources.append(self._json_to_ki_project_resource(jresource))

    def _ki_project_resource_to_json(self, ki_project_resource):
        return {
            'data_type': ki_project_resource.data_type,
            'remote_uri': ki_project_resource.remote_uri,
            'rel_path': ki_project_resource.rel_path,
            'name': ki_project_resource.name,
            'version': ki_project_resource.version
        }

    def _json_to_ki_project_resource(self, json):
        return KiProjectResource(self,
                                 data_type=json.get('data_type'),
                                 remote_uri=json.get('remote_uri'),
                                 local_path=json.get('rel_path'),
                                 name=json.get('name'),
                                 version=json.get('version'))

    def _ensure_loaded(self):
        """
        Ensures the KiProject has been successfully loaded and created.
        :return:
        """
        if not self._loaded:
            raise Exception('KiProject configuration not created or loaded.')

    def _init_project(self):
        """
        Configures and creates the KiProject.
        :return:
        """
        if not self._init_local_path():
            return False

        if not self._init_title():
            return False

        if not self._init_project_uri():
            return False

        KiProjectTemplate(self.local_path).write()

        self.save()
        return True

    def _init_local_path(self):
        """
        Ensures the local_path is set.
        :return:
        """
        answer = input('Create KiProject in: {0} [y/n]: '.format(self.local_path))
        return answer and answer.strip().lower() == 'y'

    def _init_title(self):
        """
        Ensure the title is set.
        :return:
        """
        while self.title is None or self.title.strip() == '':
            self.title = input('KiProject title: ')
        return True

    def _init_project_uri(self):
        """
        Ensures the project_uri is set and valid.
        :return:
        """
        if not self.project_uri:
            while True:
                answer = input('Create a remote project or use an existing? [c/e]: ')
                if answer == 'c':
                    return self._init_project_uri_new()
                elif answer == 'e':
                    return self._init_project_uri_existing()
                else:
                    print(
                        'Invalid input. Enter "c" to create a new remote project or "e" to use an existing remote project.')
        else:
            return self._init_project_uri_existing()

    def _init_project_uri_new(self):
        """
        Creates a new remote project and sets the project_uri.
        :return: True or False
        """
        data_uri = DataUri(DataUri.default_scheme(), None)

        while True:
            try:
                project_name = input('Remote project name: ')
                remote_project = data_uri.data_adapter().create_project(project_name)
                self.project_uri = DataUri(DataUri.default_scheme(), remote_project.id).uri
                print('Remote project created at URI: {0}'.format(self.project_uri))
                return True
            except Exception as ex:
                print('Error creating remote project: {0}'.format(str(ex)))
                answer = input('Try again? [y/n]: ')
                if answer == 'n':
                    break

        return False

    def _init_project_uri_existing(self):
        """
        Sets the project_uri to an existing remote project.
        :return:
        """

        if self.project_uri and self._validate_project_uri(self.project_uri):
            return True

        data_uri = DataUri(DataUri.default_scheme(), '{0}123456'.format(DataUri.default_scheme()))

        while True:
            answer = input('Remote project URI (e.g., {0}): '.format(data_uri.uri))
            valid_project = self._validate_project_uri(answer)
            if valid_project:
                self.project_uri = answer
                print('Remote project URI: {0}'.format(self.project_uri))
                return True

        return False

    def _validate_project_uri(self, project_uri):
        """
        Validates that a remote project exists at a specific data URI.
        :param project_uri:
        :return: True or False
        """
        try:
            data_uri = DataUri.parse(project_uri)
            remote_entity = data_uri.data_adapter().get_entity(data_uri.id)
            return remote_entity is not None and remote_entity.is_project
        except Exception as ex:
            print('Invalid remote project URI: {0}'.format(str(ex)))

        return False

    def _add_ki_project_resource(self, project_resource):
        # TODO: ensure it has a name and it's uniq.
        self.resources.append(project_resource)
