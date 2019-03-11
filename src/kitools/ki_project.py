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
from .sys_path import SysPath
from .ki_utils import KiUtils


class KiProject(object):
    CONFIG_FILENAME = 'kiproject.json'

    def __init__(self, local_path, title=None, description=None, project_uri=None, resources=None):
        if not local_path or local_path.strip() == '':
            raise ValueError('local_path is required.')

        self.local_path = SysPath(local_path).abs_path
        self.data_path = os.path.join(self.local_path, DataType.DATA_DIR_NAME)
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
        """
        Adds a remote file/folder to local file/folder to the KiProject.
        :param remote_uri_or_local_path:
        :param name:
        :param version:
        :param data_type:
        :return:
        """
        self._ensure_loaded()

        if DataUri.is_uri(remote_uri_or_local_path):
            return self._data_add(data_type=data_type,
                                  remote_uri=remote_uri_or_local_path,
                                  name=(name or remote_uri_or_local_path),
                                  version=version)
        else:
            sys_local_path = SysPath(remote_uri_or_local_path)
            if sys_local_path.exists:
                return self._data_add(data_type=data_type,
                                      local_path=sys_local_path.abs_path,
                                      name=(name or sys_local_path.basename),
                                      version=version)
            else:
                raise ValueError('Please specify a remote URI or a local file or folder.')

    def data_remove(self, resource_or_identifier):
        """
        Removes a KiProjectResource from the KiProject.
        :param resource_or_identifier:
        :return:
        """
        project_resource = self._find_project_resource_by_value(resource_or_identifier)

        if project_resource:
            # Remove any children.
            for child_resource in self.find_project_resources_by(root_id=project_resource.id):
                self.resources.remove(child_resource)

            # Remove the root.
            self.resources.remove(project_resource)
            self.save()
            return project_resource
        else:
            raise ValueError('Could not find resource: {0}'.format(resource_or_identifier))

    def data_change(self, resource_or_identifier, name=None, version=None):
        """
        Changes the name or version on a KiProjectResource.
        :param resource_or_identifier:
        :param name:
        :param version:
        :return:
        """
        self._ensure_loaded()

        project_resource = self._find_project_resource_by_value(resource_or_identifier)

        if not project_resource:
            raise ValueError('No resource found matching: {0}'.format(resource_or_identifier))

        if name is not None:
            project_resource.name = name

        if version is not None:
            project_resource.version = version

        self.save()
        return project_resource

    def data_pull(self, resource_or_identifier=None):
        """

        :param resource_or_identifier:
        :return:
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if not project_resource:
                raise Exception('No resource found matching: {0}'.format(resource_or_identifier))

            data_uri = DataUri.parse(project_resource.remote_uri)
            data_uri.data_adapter().data_pull(project_resource)
            return project_resource.abs_path
        else:
            results = []
            for project_resource in self.resources:
                # Skip any non-root resources since they are children of a parent resource
                # that will handle downloading it.
                if project_resource.root_id:
                    continue

                if not project_resource.remote_uri:
                    # Needs to be pushed
                    print('Resource {0} cannot be pulled until it has been pushed.'.format(project_resource.rel_path))
                    continue

                data_uri = DataUri.parse(project_resource.remote_uri)
                data_uri.data_adapter().data_pull(project_resource)
                results.append(project_resource.abs_path)
            return results

    def data_push(self, resource_or_identifier=None):
        """

        :param resource_or_identifier:
        :return:
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if not project_resource:
                raise Exception('No resource found matching: {0}'.format(resource_or_identifier))

            data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
            data_uri.data_adapter().data_push(project_resource)
            return project_resource.abs_path
        else:
            results = []
            for project_resource in self.resources:
                # Needs needs to be pulled first.
                if not project_resource.rel_path:
                    print('Resource {0} cannot be pushed until it has been pulled.'.format(project_resource.remote_uri))
                    continue

                data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
                data_uri.data_adapter().data_push(project_resource)
                results.append(project_resource.abs_path)
            return results

    def data_list(self, all=False):
        """
        Prints out a nice table of all the available KiProject resource entries.
        :return: BeautifulTable
        """
        self._ensure_loaded()

        table = BeautifulTable(max_width=1000)
        table.set_style(BeautifulTable.STYLE_BOX)
        table.column_headers = ['Remote URI', 'Version', 'Name', 'Path']

        for header in table.column_headers:
            table.column_alignments[header] = BeautifulTable.ALIGN_LEFT

        for resource in self.resources:
            # Only show non-root resources unless requested.
            if resource.root_id and not all:
                continue
            table.append_row([resource.remote_uri, resource.version, resource.name, resource.rel_path])

        print(table)
        return table

    def find_project_resource_by(self, operator='and', **kwargs):
        results = self.find_project_resources_by(operator=operator, **kwargs)
        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            raise Exception('Found more than one matching resource.')

    def find_project_resources_by(self, operator='and', **kwargs):
        results = []

        if operator not in ['and', 'or']:
            raise ValueError('operator must be one of: "and", "or". ')

        for resource in self.resources:
            matches = []

            for attribute, value in kwargs.items():
                if not hasattr(resource, attribute):
                    raise ValueError('{0} does not have attribute: {1}'.format(type(resource), attribute))

                if getattr(resource, attribute) == value:
                    matches.append(attribute)

            if operator == 'and' and len(matches) == len(kwargs):
                results.append(resource)
            elif operator == 'or' and len(matches) > 0:
                results.append(resource)

        return results

    def data_type_to_project_path(self, data_type):
        """
        Gets the full directory path for the data_type.
        :param data_type:
        :return:
        """
        return os.path.join(self.data_path, DataType(data_type).name)

    def data_type_from_project_path(self, local_path):
        """
        Gets the DataType from a local Project path.
        :param local_path:
        :return:
        """
        sys_path = SysPath(local_path, rel_start=self.data_path)

        if len(sys_path.rel_parts) > 0:
            return DataType(sys_path.rel_parts[0])
        else:
            return None

    def is_project_data_path(self, local_path):
        """
        Gets if the local_path is a path within the local data directory.
        :param local_path:
        :return:
        """
        try:
            self.data_type_from_project_path(local_path)
            return True
        except Exception as ex:
            # TODO: log this?
            pass
        return False

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
        # Sort the resources before saving.
        self.resources.sort(key=lambda r: r.rel_path or r.data_type or r.name or r.remote_uri or r.id)

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
            'id': ki_project_resource.id,
            'root_id': ki_project_resource.root_id,
            'data_type': ki_project_resource.data_type,
            'remote_uri': ki_project_resource.remote_uri,
            'rel_path': ki_project_resource.rel_path,
            'name': ki_project_resource.name,
            'version': ki_project_resource.version
        }

    def _json_to_ki_project_resource(self, json):
        return KiProjectResource(self,
                                 id=json.get('id'),
                                 root_id=json.get('root_id'),
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

    def _data_add(self,
                  remote_uri=None,
                  local_path=None,
                  name=None,
                  version=None,
                  data_type=None,
                  root_ki_project_resource=None):
        if local_path:
            # Make sure the file is in one of the data directories.
            if not self.is_project_data_path(local_path):
                raise ValueError('local_path must be in one of the data directories.')

            # TODO: make sure the data_type param matches the local_path.

        # Check for an existing KiProjectResource
        find_args = {}
        if remote_uri:
            find_args['remote_uri'] = remote_uri
        if local_path:
            find_args['abs_path'] = local_path
        if root_ki_project_resource:
            find_args['root_id'] = root_ki_project_resource.id

        project_resource = self.find_project_resource_by(**find_args)

        if project_resource:
            raise ValueError('Resource has already been added')

        # Update a resource.
        project_resource = KiProjectResource(kiproject=self,
                                             root_id=root_ki_project_resource.id if root_ki_project_resource else None,
                                             data_type=data_type,
                                             remote_uri=remote_uri,
                                             local_path=local_path,
                                             name=name,
                                             version=version)

        self.resources.append(project_resource)
        self.save()
        return project_resource

    def _find_project_resource_by_value(self, value):
        """
        Finds a KiProjectResource by a value.
        Value must be one of:
            - KiProjectResource (will be looked up by its id)
            - KiProjectResource.id (UUID)
            - KiProjectResource.remote_uri (DataUri)
            - KiProjectResource.abs_path or rel_path (file/folder that exists at the value path)
            - KiProjectResource.name (string)
        :param value:
        :return:
        """
        if isinstance(value, KiProjectResource):
            return self.find_project_resource_by(id=value.id)
        elif DataUri.is_uri(value):
            return self.find_project_resource_by(remote_uri=value)
        elif KiUtils.is_uuid(value):
            return self.find_project_resource_by(id=value)
        elif SysPath(value).exists:
            sys_path = SysPath(value)
            return self.find_project_resource_by(abs_path=sys_path.abs_path)
        elif isinstance(value, str):
            return self.find_project_resource_by(name=value)
        else:
            raise ValueError('Could not determine value type of: {0}'.format(value))
