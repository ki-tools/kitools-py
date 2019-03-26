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
from .exceptions import NotADataTypePathError, DataTypeMismatchError, KiProjectResourceNotFoundError


class KiProject(object):
    CONFIG_FILENAME = 'kiproject.json'

    def __init__(self,
                 local_path,
                 title=None,
                 description=None,
                 project_uri=None,
                 init_no_prompt=False):
        """
        Instantiates the KiProject.

        :param local_path: The local path to where the KiProject resides or will reside.
        :param title: The title of the KiProject.
        :param description: The description of the KiProject.
        :param project_uri: The remote URI of the project that will hold the KiProject resources.
        """

        if not local_path or local_path.strip() == '':
            raise ValueError('local_path is required.')

        self._init_no_prompt = init_no_prompt

        self.local_path = SysPath(local_path).abs_path
        self.data_path = os.path.join(self.local_path, DataType.DATA_DIR_NAME)
        self.title = title
        self.description = description
        self.project_uri = project_uri
        self.resources = []

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
        Adds a new resource to the KiProject. The resource can be a remote or local file or directory.
        If the resource already exists it will be updated with the provided parameters.

        Examples:
            import kitools
            kiproject = kitools.KiProject('/tmp/my_project')
            kiproject.data_add('syn:syn123456', name='my dataset')
            kiproject.data_add('/home/me/file1.csv')
            kiproject.data_add('syn:syn123457', data_type='core', version='2')

        :param remote_uri_or_local_path: The remote URI (e.g., syn:syn123456) or local path of the directory for file.
        :param name: A user friendly name for the resource.
        :param version: The version of the file to add.
        :param data_type: The DataType of the file. This is only required when a remote_uri is provided and the remote
                          folder structure does not match the KiProject's "data" structure.
        :return: KiProjectResource
        """
        self._ensure_loaded()

        if DataUri.is_uri(remote_uri_or_local_path):
            return self._data_add(data_type=data_type,
                                  remote_uri=remote_uri_or_local_path,
                                  name=(name or remote_uri_or_local_path),
                                  version=version)
        else:
            sys_local_path = SysPath(remote_uri_or_local_path, cwd=self.local_path)
            if sys_local_path.exists:
                return self._data_add(data_type=data_type,
                                      local_path=sys_local_path.abs_path,
                                      name=(name or sys_local_path.basename),
                                      version=version)
            else:
                raise ValueError('Please specify a remote URI or a local file or folder path that exists.')

    def data_remove(self, resource_or_identifier):
        """
        Removes a resource from the KiProject. This does not delete the file locally or remotely, it is only
        removed from the KiProject manifest.

        :param resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).
        :return: KiProjectResource
        """
        project_resource = self._find_project_resource_by_value(resource_or_identifier)

        # Remove any children.
        for child_resource in self.find_project_resources_by(root_id=project_resource.id):
            self.resources.remove(child_resource)

        # Remove the root.
        self.resources.remove(project_resource)
        self.save()
        return project_resource

    def data_change(self, resource_or_identifier, name=None, version=None):
        """
        Changes the name or version on a KiProjectResource.

        :param resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).
        :param name: The new name.
        :param version: The new version (or 'None' to clear the version).
        :return: KiProjectResource
        """
        self._ensure_loaded()

        project_resource = self._find_project_resource_by_value(resource_or_identifier)

        if name is not None:
            project_resource.name = name

        if version is not None:
            project_resource.version = version

        self.save()
        return project_resource

    def data_pull(self, resource_or_identifier=None):
        """
        Downloads a specific resource or all resources in the KiProject.

        :param resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).
        :return: The absolute path to the pulled resource or a list of absolute paths for all pulled resources.
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if project_resource.remote_uri is None:
                print('Resource {0} cannot be pulled until it has been pushed.'.format(resource_or_identifier))
                return None

            data_uri = DataUri.parse(project_resource.remote_uri)
            data_uri.data_adapter().data_pull(project_resource)
            return project_resource.abs_path
        else:
            results = []
            for project_resource in self.resources:
                # Skip any non-root resources. The root resource will handle pulling the child.
                if project_resource.root_id:
                    continue

                results.append(self.data_pull(project_resource))
            return results

    def data_push(self, resource_or_identifier=None):
        """
        Uploads a specific resource or all local non-pushed resources.

        :param resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).
        :return: The absolute path to the pushed resource or a list of absolute paths for all pushed resources.
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if project_resource.abs_path is None:
                print('Resource {0} cannot be pushed until it has been pulled.'.format(resource_or_identifier))
                return None

            data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
            data_uri.data_adapter().data_push(project_resource)
            return project_resource.abs_path
        else:
            print('Pushing all resources that have not been pushed.')
            results = []
            for project_resource in self.resources:
                # Only push resources that have not been pushed yet.
                if project_resource.remote_uri:
                    continue

                # Skip any non-root resources unless the root resource has already been pushed.
                # The root resource will handle pushing the child.
                if project_resource.root_id and project_resource.root_resource.remote_uri is None:
                    continue

                results.append(self.data_push(project_resource))
            return results

    def data_list(self, all=False):
        """
        Prints out a table of all the resources in the KiProject.

        :param all: Set to True to include all child resources.
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
        """
        Finds a single resource in the KiProject by any of KiProjectResource attributes.

        :param operator: The operator to use when finding by more than one attribute. Must be one of: 'and', 'or'.
        :param kwargs: KiProjectResource attributes and values to find by.
        :return: KiProjectResource or None
        """
        results = self.find_project_resources_by(operator=operator, **kwargs)
        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            raise Exception('Found more than one matching resource.')

    def find_project_resources_by(self, operator='and', **kwargs):
        """
        Finds all resources in the KiProject by any of KiProjectResource attributes.

        :param operator: The operator to use when finding by more than one attribute. Must be one of: 'and', 'or'.
        :param kwargs: KiProjectResource attributes and values to find by.
        :return: List of KiProjectResources or an empty list.
        """
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
        Gets the absolute path to the DataType directory in the KiProject.

        :param data_type: The DataType to get the path for.
        :return: Absolute path to the local directory as a string.
        """
        return os.path.join(self.data_path, DataType(data_type).name)

    def data_type_from_project_path(self, local_path):
        """
        Gets the DataType from a local path. The local path must be in one of the KiProject's DataType directories.

        :param local_path: Path to get the DataType from.
        :return: The DataType or None.
        """
        sys_path = SysPath(local_path, cwd=self.local_path, rel_start=self.data_path)

        if len(sys_path.rel_parts) > 0:
            return DataType(sys_path.rel_parts[0])
        else:
            return None

    def is_project_data_type_path(self, local_path):
        """
        Gets if the local_path is in one of the DataType directories.

        :param local_path: Path to check.
        :return: True or False
        """
        try:
            is_data_path = self.data_type_from_project_path(local_path) is not None
            is_root_data_path = is_data_path and local_path in self._root_data_paths()

            if is_data_path and not is_root_data_path:
                return True
            else:
                return False
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
        """
        Serializes the KiProject to JSON.

        :return: Hash
        """
        return {
            'title': self.title,
            'description': self.description,
            'project_uri': self.project_uri,
            'resources': [self._ki_project_resource_to_json(f) for f in self.resources]
        }

    def _json_to_self(self, json):
        """
        Deserializes JSON into the KiProject.

        :param json: The JSON to deserialize.
        :return: None
        """
        self.title = json.get('title')
        self.description = json.get('description')
        self.project_uri = json.get('project_uri')
        self.resources = []

        jresources = json.get('resources')
        for jresource in jresources:
            self.resources.append(self._json_to_ki_project_resource(jresource))

    def _ki_project_resource_to_json(self, ki_project_resource):
        """
        Serializes a KiProjectResource into JSON.

        :param ki_project_resource: The KiProjectResource to serialize.
        :return: Hash
        """
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
        """
        Deserializes JSON into the KiProjectResource.

        :param json: The JSON to deserialize.
        :return: KiProjectResource
        """
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

        :return: None or raise an exception.
        """
        if not self._loaded:
            raise Exception('KiProject configuration not created or loaded.')

    def _init_project(self):
        """
        Configures and creates the KiProject.

        :return: True or False
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

        :return: True or False
        """
        if self._init_no_prompt:
            return True
        else:
            answer = input('Create KiProject in: {0} [y/n]: '.format(self.local_path))
            return answer and answer.strip().lower() == 'y'

    def _init_title(self):
        """
        Ensure the title is set.

        :return: True or False
        """
        if self._init_no_prompt:
            if self.title and self.title.strip() != '':
                return True
            else:
                print('title is required.')
                return False
        else:
            while self.title is None or self.title.strip() == '':
                self.title = input('KiProject title: ')
            return True

    def _init_project_uri(self):
        """
        Ensures the project_uri is set and valid.

        :return: True or False
        """
        if self.project_uri:
            return self._init_project_uri_existing()
        else:
            if self._init_no_prompt:
                print('project_uri is required.')
                return False

            while True:
                answer = input('Create a remote project or use an existing? [c/e]: ')
                if answer == 'c':
                    return self._init_project_uri_new()
                elif answer == 'e':
                    return self._init_project_uri_existing()
                else:
                    print(
                        'Invalid input. Enter "c" to create a new remote project or "e" to use an existing remote project.')

    def _init_project_uri_new(self):
        """
        Creates a new remote project and sets the project_uri.

        :return: True or False
        """
        data_uri = DataUri(DataUri.default_scheme(), None)

        while True:
            try:
                project_name = self.title

                if not self._init_no_prompt:
                    project_name = input('Remote project name: ')

                remote_project = data_uri.data_adapter().create_project(project_name)
                self.project_uri = DataUri(DataUri.default_scheme(), remote_project.id).uri
                print('Remote project created at URI: {0}'.format(self.project_uri))
                return True
            except Exception as ex:
                print('Error creating remote project: {0}'.format(str(ex)))
                if self._init_no_prompt:
                    break
                else:
                    answer = input('Try again? [y/n]: ')
                    if answer == 'n':
                        break

        return False

    def _init_project_uri_existing(self):
        """
        Sets the project_uri to an existing remote project.

        :return: True or False
        """

        if self.project_uri and self._validate_project_uri(self.project_uri):
            return True

        if self._init_no_prompt:
            print('project_uri: {0} not set or could not be validated.'.format(self.project_uri))
            return False

        example_data_uri = DataUri(DataUri.default_scheme(), '{0}123456'.format(DataUri.default_scheme())).uri

        while True:
            answer = input('Remote project URI (e.g., {0}): '.format(example_data_uri))
            if self._validate_project_uri(answer):
                self.project_uri = answer
                print('Remote project URI: {0}'.format(self.project_uri))
                return True

        return False

    def _validate_project_uri(self, project_uri):
        """
        Validates that a remote project exists at a specific data URI.

        :param project_uri: The remote URI to validate.
        :return: True or False
        """
        try:
            data_uri = DataUri.parse(project_uri)
            remote_entity = data_uri.data_adapter().get_entity(data_uri.id)
            return remote_entity is not None and remote_entity.is_project
        except Exception as ex:
            print('Invalid remote project URI: {0}'.format(ex))

        return False

    def _data_add(self,
                  remote_uri=None,
                  local_path=None,
                  name=None,
                  version=None,
                  data_type=None,
                  root_ki_project_resource=None):
        """
        Adds or updates a resource. Must have remote_uri or local_path specified.

        :param remote_uri: The remote URI to add.
        :param local_path: The local path to a file or directory to add.
        :param name: The friendly name of the resource.
        :param version: The version to lock on the resource.
        :param data_type: The data_type of the resource (only needed for remote_uris that do not match
               the DataType structure).
        :param root_ki_project_resource: The root KiProjectResource. Only needed when auto adding children of a directory.
        :return: KiProjectResource
        """

        if not remote_uri and not local_path:
            raise ValueError('remote_uri or local_path must be supplied.')

        if local_path:
            # Make sure the file is in one of the data directories.
            if not self.is_project_data_type_path(local_path):
                raise NotADataTypePathError(self.data_path, local_path, DataType.ALL)

            # Make sure the data_type param matches the local_path.
            if data_type:
                local_path_data_type = self.data_type_from_project_path(local_path)
                if local_path_data_type is None or data_type != local_path_data_type.name:
                    raise DataTypeMismatchError(
                        'data_type: {0} does not match local_path: {1}.'.format(data_type, local_path))

        root_id = root_ki_project_resource.id if root_ki_project_resource else None

        # Check for an existing KiProjectResource
        find_args = {}
        if remote_uri:
            find_args['remote_uri'] = remote_uri
        if local_path:
            find_args['abs_path'] = local_path
        if root_id:
            find_args['root_id'] = root_id

        project_resource = self.find_project_resource_by(**find_args)

        if project_resource:
            # Update the resource and warn about any changes.
            changes = []

            change_map = {
                'remote_uri': {'value': remote_uri, 'allow_none': False},
                'abs_path': {'value': local_path, 'allow_none': False},
                'name': {'value': name, 'allow_none': False},
                'version': {'value': version, 'allow_none': True},
                'data_type': {'value': data_type, 'allow_none': False},
                'root_id': {'value': root_id, 'allow_none': False}
            }

            for attr, config in change_map.items():
                old_value = getattr(project_resource, attr)
                new_value = config.get('value')
                allow_none = config.get('allow_none')

                if new_value != old_value:
                    if new_value is None and not allow_none:
                        print('WARNING: Cannot set {0} to None. {0} already has value: {1}'.format(attr, old_value))
                        continue

                    changes.append('{0} changed from: {1} to: {2}'.format(attr.title(), old_value, new_value))
                    setattr(project_resource, attr, new_value)

            if len(changes) > 0:
                print('WARNING: Resource already exists and has been updated with the following changes:')
                for change in changes:
                    print('  - {0}'.format(change))
        else:
            # Add the resource.
            project_resource = KiProjectResource(kiproject=self,
                                                 root_id=root_id,
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
        Finds a KiProjectResource by a unique value.

        Value must be one of:
            - KiProjectResource (will be looked up by its id)
            - KiProjectResource.id (UUID)
            - KiProjectResource.remote_uri (DataUri)
            - KiProjectResource.abs_path or rel_path (file/folder that exists at the value path)
            - KiProjectResource.name (string)
        :param value: The value to find by.
        :return: KiProjectResource or None
        """
        result = None

        if isinstance(value, KiProjectResource):
            result = self.find_project_resource_by(id=value.id)
        elif DataUri.is_uri(value):
            result = self.find_project_resource_by(remote_uri=value)
        elif KiUtils.is_uuid(value):
            result = self.find_project_resource_by(id=value)
        elif SysPath(value, cwd=self.local_path).exists:
            sys_path = SysPath(value, cwd=self.local_path)
            result = self.find_project_resource_by(abs_path=sys_path.abs_path)
        elif isinstance(value, str):
            result = self.find_project_resource_by(name=value)
        else:
            raise ValueError('Could not determine value type of: {0}'.format(value))

        if result is None:
            raise KiProjectResourceNotFoundError('No project resource found matching: {0}'.format(value))

        return result

    def _root_data_paths(self):
        """
        Gets all the DataType root paths for the project (e.g., /home/user/my_project/data/core)

        :return: List of absolute paths.
        """
        paths = []
        for data_type in DataType.ALL:
            paths.append(os.path.join(self.data_path, data_type))
        return paths
