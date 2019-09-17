import os
import json
import glob
from collections import deque
from beautifultable import BeautifulTable
from .ki_project_resource import KiProjectResource
from .data_type import DataType
from .data_type_template import DataTypeTemplate
from .data_uri import DataUri
from .sys_path import SysPath
from .utils import Utils
from .exceptions import NotADataTypePathError, DataTypeMismatchError, KiProjectResourceNotFoundError, \
    InvalidDataTypeError


class KiProject(object):
    """Primary class for interacting with KI Projects."""

    CONFIG_FILENAME = 'kiproject.json'

    DEFAULT_LINUX_DATA_IGNORES = frozenset([
        '*~',
        '.Trash-*',
        '.directory',
        '.fuse_hidden*',
        '.nfs*'
    ])

    DEFAULT_OSX_DATA_IGNORES = frozenset([
        '.DS_Store',
        '.AppleDouble',
        '.LSOverride',
        '._*',
        '.DocumentRevisions-V100',
        '.fseventsd',
        '.Spotlight-V100',
        '.TemporaryItems',
        '.Trashes',
        '.VolumeIcon.icns',
        '.com.apple.timemachine.donotpresent',
        '.AppleDB',
        '.AppleDesktop',
        '.apdisk'
    ])

    DEFAULT_WINDOWS_DATA_IGNORES = frozenset([
        'Thumbs.db',
        'ehthumbs.db',
        'ehthumbs_vista.db',
        '*.stackdump',
        '[Dd]esktop.ini',
        '$RECYCLE.BIN/',
        '*.lnk'
    ])

    DEFAULT_DATA_IGNORES = frozenset.union(DEFAULT_LINUX_DATA_IGNORES,
                                           DEFAULT_OSX_DATA_IGNORES,
                                           DEFAULT_WINDOWS_DATA_IGNORES)

    def __init__(self, local_path, **kwargs):
        """Instantiates the KiProject.

        Args:
            local_path: The local path to where the KiProject resides (or will reside if creating a new KiProject).
            **kwargs: Keyword arguments.

        Kwargs:
            title: The title for the new KiProject.
            description: The description for the new KiProject.
            project_uri: The remote URI of the remote project that will hold the new KiProject resources.
                If this is set an existing remote project will be used.
            project_name: The name of the remote project that will hold the new KiProject resources.
                If this is set a new remote project will be created with this name.
            data_type_template: The name of the DataTypeTemplate to create the project with.
            no_prompt: Suppress all prompts during KiProject initialization.
        """
        if not local_path or local_path.strip() == '':
            raise ValueError('local_path is required.')

        self.local_path = SysPath(local_path).abs_path
        self.title = None
        self.description = None
        self.project_uri = None
        self.project_name = None
        self.data_types = []
        self.resources = []

        self._data_ignores = list(self.DEFAULT_DATA_IGNORES)

        self._config_path = os.path.join(self.local_path, self.CONFIG_FILENAME)

        self._loaded = False

        if self.load():
            self._ensure_project_structure()
            self._loaded = True
            self.show_missing_resources()
            print('KiProject successfully loaded and ready to use.')
        else:
            if self._init_project(**kwargs):
                self._loaded = True
                self.show_missing_resources()
                print('KiProject initialized successfully and ready to use.')
            else:
                print('KiProject initialization failed.')

    def data_add(self, remote_uri_or_local_path, name=None, version=None, data_type=None):
        """Adds a new resource to the KiProject.

        A resource can be a remote or local file or directory.
        If the resource already exists it will be updated with the provided parameters.

        Examples:
            >>> import kitools
            >>> kiproject = kitools.KiProject('/tmp/my_project')
            >>> kiproject.data_add('syn:syn123456', name='my dataset')
            >>> kiproject.data_add('/home/me/file1.csv')
            >>> kiproject.data_add('syn:syn123457', data_type='core', version='2')

        Args:
            remote_uri_or_local_path: The remote URI (e.g., syn:syn123456) or local path of the directory for file.
            name: A user friendly name for the resource.
            version: The version of the file to add.
            data_type: The DataType of the file. This is only required when a remote_uri is provided
                and the remote folder structure does not match the KiProject's "data" structure.

        Returns:
            KiProjectResource
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
        """Removes a resource from the KiProject.

        This does not delete the file locally or remotely, it is only removed from the KiProject manifest.

        Args:
            resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).

        Returns:
            KiProjectResource
        """
        self._ensure_loaded()

        project_resource = self._find_project_resource_by_value(resource_or_identifier)

        # Remove any children.
        for child_resource in self.find_project_resources_by(root_id=project_resource.id):
            self.resources.remove(child_resource)

        # Remove the root.
        self.resources.remove(project_resource)
        self.save()
        return project_resource

    def data_change(self, resource_or_identifier, name=None, version=None):
        """Changes the name or version on a KiProjectResource.

        Args:
            resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).
            name: The new name.
            version: The new version (or 'None' to clear the version).

        Returns:
            KiProjectResource
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
        """Downloads a specific resource or all resources in the KiProject.

        Args:
            resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).

        Returns:
            The absolute path to the pulled resource or a list of absolute paths for all pulled resources.
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if project_resource.remote_uri is None:
                print('Resource cannot be pulled until it has been pushed:{0}{1}'.format(os.linesep, project_resource))
                return None

            data_uri = DataUri.parse(project_resource.remote_uri)
            data_uri.data_adapter().data_pull(project_resource)
            return project_resource
        else:
            results = []
            for project_resource in self.resources:
                # Skip any non-root resources. The root resource will handle pulling the child.
                if project_resource.root_id:
                    continue

                results.append(self.data_pull(project_resource))
            return results

    def data_push(self, resource_or_identifier=None):
        """Uploads a specific resource or all local non-pushed resources.

        Args:
            resource_or_identifier: KiProjectResource object or a valid identifier (local path, remote URI, name).

        Returns:
            The absolute path to the pushed resource or a list of absolute paths for all pushed resources.
        """
        self._ensure_loaded()

        if resource_or_identifier:
            project_resource = self._find_project_resource_by_value(resource_or_identifier)

            if project_resource.abs_path is None:
                print('Source cannot be pushed until it has been pulled:{0}{1}'.format(os.linesep, project_resource))
                return None

            data_uri = DataUri.parse(project_resource.remote_uri or self.project_uri)
            data_uri.data_adapter().data_push(project_resource)
            return project_resource
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
        """Prints out a table of all the resources in the KiProject.

        Args:
            all: Set to True to include all child resources.

        Returns:
            BeautifulTable
        """
        self._ensure_loaded()

        # Only show non-root resources unless requested.
        scoped_resources = self.resources if all else self.find_project_resources_by(root_id=None)

        col_action_needed = 'Action Needed'
        col_remote_uri = 'Remote URI'
        col_root_uri = 'Root URI'
        col_version = 'Version'
        col_name = 'Name'
        col_path = 'Path'

        column_headers = [col_action_needed, col_remote_uri, col_root_uri, col_version, col_name, col_path]

        table = BeautifulTable(max_width=1000)
        table.set_style(BeautifulTable.STYLE_BOX)
        # Remove the row separator.
        table.row_separator_char = ''
        table.column_headers = column_headers

        for header in table.column_headers:
            table.column_alignments[header] = BeautifulTable.ALIGN_LEFT

        for resource in scoped_resources:
            row_data = ['' for _ in column_headers]
            actions_needed = []

            # remote_uri
            if resource.remote_uri:
                row_data[column_headers.index(col_remote_uri)] = resource.remote_uri
            else:
                actions_needed.append('data_push()')

            # root_id
            if resource.root_id:
                root_resource = self.find_project_resource_by(id=resource.root_id)
                row_data[column_headers.index(col_root_uri)] = root_resource.remote_uri

            # version
            if resource.version:
                row_data[column_headers.index(col_version)] = resource.version

            # name
            if resource.name:
                row_data[column_headers.index(col_name)] = resource.name

            # rel_path
            if resource.rel_path:
                row_data[column_headers.index(col_path)] = resource.rel_path
            else:
                actions_needed.append('data_pull()')

            # action needed
            row_data[column_headers.index(col_action_needed)] = ', '.join(actions_needed)

            table.append_row(row_data)

        # Remove the root uri column unless we are showing all.
        if all is not True:
            table.pop_column(col_root_uri)

        # Remove the actions needed column if there are no actions needed.
        if not list(filter(None, table[col_action_needed])):
            table.pop_column(col_action_needed)

        print(table)

    @property
    def data_ignores(self):
        """Ges the ignored data patterns."""
        return self._data_ignores

    def add_data_ignore(self, pattern):
        """Add a glob pattern to ignore data files.

        Args:
            pattern: A glob pattern to match files to be ignored.

        Returns:
            None
        """
        if pattern not in self._data_ignores:
            self._data_ignores.append(pattern)
            self.save()

    def remove_data_ignore(self, pattern):
        """Remove a glob pattern that ignores data files.

        Args:
            pattern: The glob pattern to remove.

        Returns:
            None
        """
        if pattern in self._data_ignores:
            self._data_ignores.remove(pattern)
            self.save()

    def show_missing_resources(self):
        """Shows all local DataType directories and files that have not been added to the KiProject resources.

        Returns:
            None
        """
        self._ensure_loaded()

        missing = self.find_missing_resources()
        if missing:
            print('WARNING: The following local resources have not been added to this KiProject.')
            for path in missing:
                print(' - {0}'.format(SysPath(path, rel_start=self.local_path).rel_path))

    def find_missing_resources(self):
        """Finds all local DataType directories and files that have not been added to the KiProject resources.

        Returns:
            List of paths
        """
        missing = []

        paths = deque(self._root_data_paths())

        ignored_paths = self._get_data_ignored_paths()

        while paths:
            path = paths.popleft()
            dirs, files = Utils.get_dirs_and_files(path)

            for entry in (dirs + files):
                if entry.path in ignored_paths:
                    continue

                resources = self.find_project_resources_by(abs_path=entry.path)
                if not resources:
                    missing.append(entry.path)

                if entry.is_dir():
                    paths.append(entry.path)

        return missing

    def find_project_resource_by(self, operator='and', **kwargs):
        """Finds a single resource in the KiProject by any of KiProjectResource attributes.

        Args:
            operator: The operator to use when finding by more than one attribute. Must be one of: 'and', 'or'.
            **kwargs: KiProjectResource attributes and values to find by.

        Returns:
            KiProjectResource or None

        Raises:
            Exception: Raised if more than one result is found.
        """
        results = self.find_project_resources_by(operator=operator, **kwargs)
        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            raise Exception('Found more than one matching resource.')

    def find_project_resources_by(self, operator='and', **kwargs):
        """Finds all resources in the KiProject by any of KiProjectResource attributes.

        Args:
            operator: The operator to use when finding by more than one attribute. Must be one of: 'and', 'or'.
            **kwargs: KiProjectResource attributes and values to find by.

        Returns:
            List of KiProjectResources or an empty list.

        Raises:
            ValueError: Raised on invalid 'operator' or invalid KiProjectResources property.
        """
        results = []

        if operator not in ['and', 'or']:
            raise ValueError('operator must be one of: "and", "or". ')

        for resource in self.resources:
            matches = []

            for attribute, attribute_value in kwargs.items():
                if not hasattr(resource, attribute):
                    raise ValueError('{0} does not have attribute: {1}'.format(type(resource), attribute))

                resource_value = getattr(resource, attribute)

                if resource_value == attribute_value:
                    matches.append(attribute)
                elif isinstance(resource_value, DataType) and isinstance(attribute_value, str):
                    # Handle searching by DataType Name.
                    if resource_value.name == attribute_value:
                        matches.append(attribute)

            if operator == 'and' and len(matches) == len(kwargs):
                results.append(resource)
            elif operator == 'or' and len(matches) > 0:
                results.append(resource)

        return results

    def find_data_type(self, name_or_data_type, raise_on_missing=True):
        """Finds a DataType by it's name.

        Args:
            name_or_data_type: The DataType name to find.
            raise_on_missing: Whether or not to raise an error if not found.

        Returns:
            DataType or None
        """
        if isinstance(name_or_data_type, DataType):
            name_or_data_type = name_or_data_type.name

        for data_type in self.data_types:
            if data_type.name == name_or_data_type:
                return data_type

        if raise_on_missing:
            raise InvalidDataTypeError(name_or_data_type, self.data_types)
        else:
            return None

    def get_data_type_from_path(self, path):
        """Gets the DataType from a path.

        The path must be in one of the KiProject's DataType directories.

        Args:
            path: Path to get the DataType from.

        Returns:
            The DataType or None.
        """
        sorted_data_types = sorted(self.data_types, reverse=True, key=lambda d: len(d.rel_path))
        sys_path = SysPath(path, cwd=self.local_path, rel_start=self.local_path)

        for data_type in sorted_data_types:
            if sys_path.rel_path.startswith(data_type.rel_path):
                return data_type

        return None

    def is_data_type_path(self, local_path):
        """Gets if the local_path is in one of the DataType directories.

        Args:
            local_path: Path to check.

        Returns:
            True or False
        """
        try:
            is_data_path = self.get_data_type_from_path(local_path) is not None
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
        """Loads the KiProject from a config file.

        Returns:
            True if the config file exists and was loaded.
        """
        loaded = False
        if os.path.isfile(self._config_path):
            with open(self._config_path) as f:
                self.from_json(json.load(f))
                loaded = True

        return loaded

    def save(self):
        """Saves the KiProject to a config file.

        Returns:
            None
        """
        # Sort the resources before saving.
        self.resources.sort(
            key=lambda r: r.rel_path or (r.data_type.name if r.data_type else None) or r.name or r.remote_uri or r.id)

        with open(self._config_path, 'w') as f:
            json.dump(self.to_json(), f, indent=2)

    def to_json(self):
        """Serializes the KiProject to JSON.

        Returns:
            Hash
        """
        return {
            'title': self.title,
            'description': self.description,
            'project_uri': self.project_uri,
            'data_ignores': self.data_ignores,
            'data_types': [item.to_json() for item in self.data_types],
            'resources': [item.to_json() for item in self.resources]
        }

    def from_json(self, json):
        """Deserializes JSON into the KiProject.

        Args:
            json: The JSON to deserialize.

        Returns:
            None
        """
        self.title = json.get('title')
        self.description = json.get('description')
        self.project_uri = json.get('project_uri')
        self._data_ignores = json.get('data_ignores', list(self.DEFAULT_DATA_IGNORES))
        self.data_types = []
        self.resources = []

        for jdata_type in json.get('data_types'):
            self.data_types.append(DataType.from_json(jdata_type, self.local_path))

        for jresource in json.get('resources'):
            self.resources.append(KiProjectResource.from_json(jresource, self))

    def _ensure_loaded(self):
        """Ensures the KiProject has been successfully loaded and created.

        Returns:
            None or raise an exception.
        """
        if not self._loaded:
            raise Exception('KiProject configuration not created or loaded.')

    def _init_project(self, **kwargs):
        """Configures and creates the KiProject.

        Args:
            **kwargs: Keyword arguments.

        Kwargs:
            title: The title for the new KiProject.
            description: The description for the new KiProject.
            project_uri: The remote URI of the remote project that will hold the new KiProject resources.
                If this is set an existing remote project will be used.
            project_name: The name of the remote project that will hold the new KiProject resources.
                If this is set a new remote project will be created with this name.
            data_type_template: The name of the DataTypeTemplate to create the project with.
            no_prompt: Suppress all prompts during KiProject initialization.

        Returns:
            True or False
        """
        title = kwargs.get('title')
        description = kwargs.get('description')
        project_uri = kwargs.get('project_uri')
        project_name = kwargs.get('project_name')
        data_type_template = kwargs.get('data_type_template')
        no_prompt = kwargs.get('no_prompt')

        if project_uri and project_name:
            print('ERROR: project_uri and project_name cannot both be set.')
            return False

        if project_uri and not DataUri.is_uri(project_uri):
            print('ERROR: Invalid project_uri: {0}'.format(project_uri))
            return False

        if data_type_template:
            data_type_template = DataTypeTemplate.get(data_type_template)
        else:
            data_type_template = DataTypeTemplate.default()

        if not self._init_local_path(no_prompt):
            return False

        if not self._init_title(no_prompt, title):
            return False

        if not self._init_description(no_prompt, description):
            return False

        if not self._init_project_uri(no_prompt, project_uri, project_name):
            return False

        self._set_data_types_from_template(data_type_template)

        self._ensure_project_structure()

        self.save()
        return True

    def _init_local_path(self, no_prompt):
        """Ensures the local_path is set.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.

        Returns:
            True or False
        """
        if no_prompt:
            print('KiProject path: {0}'.format(self.local_path))
            return True
        else:
            answer = input('Create KiProject in: {0} [y/n]: '.format(self.local_path))
            return answer and answer.strip().lower() == 'y'

    def _init_title(self, no_prompt, title):
        """Ensures the title is set.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.
            title: The title for the new KiProject.

        Returns:
            True or False
        """
        if title:
            self.title = title
        elif not no_prompt:
            while self.title is None:
                answer = input('KiProject title: ')
                self.title = answer

        if self.title:
            print('KiProject title: {0}'.format(self.title))

        return self.title is not None

    def _init_description(self, no_prompt, description):
        """Ensures the description is set.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.
            description: The description for the new KiProject.

        Returns:
            True or False
        """
        if description:
            self.description = description
        elif not no_prompt:
            while self.description is None:
                answer = input('KiProject description: ')
                self.description = answer

        if self.description:
            print('KiProject description: {0}'.format(self.description))

        # Description is optional so always return True.
        return True

    def _init_project_uri(self, no_prompt, project_uri, project_name):
        """Ensures the project_uri is set and valid.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.
            project_uri: The remote URI of the remote project that will hold the new KiProject resources.
                If this is set an existing remote project will be used.
            project_name: The name of the remote project that will hold the new KiProject resources.
                If this is set a new remote project will be created with this name.

        Returns:
            True or False
        """
        if project_uri:
            return self._init_project_uri_existing(no_prompt, project_uri=project_uri)
        elif project_name:
            return self._init_project_uri_new(no_prompt, project_name=project_name)
        elif not no_prompt:
            while self.project_uri is None:
                answer = input('Create a remote project or use an existing? [c/e]: ')
                if answer == 'c':
                    return self._init_project_uri_new(no_prompt)
                elif answer == 'e':
                    return self._init_project_uri_existing(no_prompt)
                else:
                    print('Enter "c" to create a new remote project or "e" to use an existing remote project.')
        else:
            return False

    def _init_project_uri_new(self, no_prompt, project_name=None):
        """Creates a new remote project and sets the project_uri.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.
            project_name: The name of the remote project that will hold the new KiProject resources.
                If this is set a new remote project will be created with this name.

        Returns:
            True or False
        """
        data_uri = DataUri(DataUri.default_scheme(), None)

        while not self.project_uri:
            try:
                project_name = project_name

                if not project_name and not no_prompt:
                    project_name = input('Remote project name: ')

                if project_name:
                    remote_project = data_uri.data_adapter().create_project(project_name)
                    self.project_uri = DataUri(data_uri.scheme, remote_project.id).uri
                    print('Remote project: "{0}" created at URI: {1}'.format(remote_project.name, self.project_uri))
            except Exception as ex:
                print('Error creating remote project: {0}'.format(str(ex)))
                if no_prompt:
                    break
                else:
                    answer = input('Try again? [y/n]: ')
                    if answer == 'n':
                        break

        return self.project_uri is not None

    def _init_project_uri_existing(self, no_prompt, project_uri=None):
        """Sets the project_uri to an existing remote project.

        Args:
            no_prompt: Suppress all prompts during KiProject initialization.
            project_uri: The remote URI of the remote project that will hold the new KiProject resources.
                If this is set an existing remote project will be used.

        Returns:
            True or False
        """
        if project_uri:
            if self._validate_project_uri(project_uri):
                self.project_uri = project_uri
            else:
                print('project_uri: {0} could not be validated.'.format(project_uri))
        elif not no_prompt:
            example_data_uri = DataUri(DataUri.default_scheme(), '{0}123456'.format(DataUri.default_scheme())).uri

            while not self.project_uri:
                answer = input('Remote project URI (e.g., {0}): '.format(example_data_uri))
                if answer and self._validate_project_uri(answer):
                    self.project_uri = answer

        if self.project_uri:
            print('Remote project URI: {0}'.format(self.project_uri))

        return self.project_uri is not None

    def _validate_project_uri(self, project_uri):
        """Validates that a remote project exists at a specific data URI.

        Args:
            project_uri: The remote URI to validate.

        Returns:
            True or False
        """
        remote_entity = None
        try:
            data_uri = DataUri.parse(project_uri)
            remote_entity = data_uri.data_adapter().get_entity(data_uri.id)
        except Exception as ex:
            print('Invalid remote project URI: {0}'.format(ex))

        return remote_entity is not None and remote_entity.is_project

    def _set_data_types_from_template(self, name_or_template):
        """Sets the data_types from a template.

        Args:
            name_or_template: The name or the DataTypeTemplate template.

        Returns:
            None
        """
        if isinstance(name_or_template, DataTypeTemplate):
            name_or_template = name_or_template.name

        template = DataTypeTemplate.get(name_or_template)
        if not template:
            raise Exception('Data type template: {0} not found.'.format(name_or_template))

        self.data_types = []

        for template_path in template.paths:
            self.data_types.append(DataType(self.local_path, template_path.name, template_path.rel_path))

    def _ensure_project_structure(self):
        """Ensures the KiProject structure has been created.

        Returns:
            None
        """
        # Project root
        SysPath(self.local_path).ensure_dirs()

        # Data types
        for data_type in self.data_types:
            SysPath(data_type.abs_path).ensure_dirs()

        # Other supporting directories
        for dir_name in ['scripts', 'reports']:
            SysPath(os.path.join(self.local_path, dir_name)).ensure_dirs()

        # Git ignore
        gitignore_path = os.path.join(self.local_path, '.gitignore')
        if not os.path.isfile(gitignore_path):
            # TODO: implement this
            pass

    def _data_add(self,
                  remote_uri=None,
                  local_path=None,
                  name=None,
                  version=None,
                  data_type=None,
                  root_ki_project_resource=None):
        """Adds or updates a resource.

        Must have remote_uri or local_path specified.

        Args:
            remote_uri: The remote URI to add.
            local_path: The local path to a file or directory to add.
            name: The friendly name of the resource.
            version: The version to lock on the resource.
            data_type: The data_type of the resource (only needed for remote_uris that do not match the DataType structure).
            root_ki_project_resource: The root KiProjectResource. Only needed when auto adding children of a directory.

        Returns:
            KiProjectResource
        """
        if not remote_uri and not local_path:
            raise ValueError('remote_uri or local_path must be supplied.')

        if data_type:
            # Get the DataType
            data_type = self.find_data_type(data_type)

        if local_path:
            # Make sure the file is in one of the data directories.
            if not self.is_data_type_path(local_path):
                raise NotADataTypePathError(local_path, self.data_types)

            # Make sure the data_type param matches the local_path.
            if data_type:
                local_path_data_type = self.get_data_type_from_path(local_path)
                if local_path_data_type is None or data_type != local_path_data_type:
                    raise DataTypeMismatchError(
                        'data_type: {0} does not match local_path: {1}.'.format(data_type.name, local_path))

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
        """Finds a KiProjectResource by a unique value.

        Value must be one of:
            - KiProjectResource (will be looked up by its id)
            - KiProjectResource.id (UUID)
            - KiProjectResource.remote_uri (DataUri)
            - KiProjectResource.abs_path or rel_path (file/folder that exists at the value path)
            - KiProjectResource.name (string)

        Args:
            value: The value to find by.

        Returns:
            KiProjectResource or None
        """
        result = None

        if isinstance(value, KiProjectResource):
            result = self.find_project_resource_by(id=value.id)
        elif DataUri.is_uri(value):
            result = self.find_project_resource_by(remote_uri=value)
        elif Utils.is_uuid(value):
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
        """Gets all the DataType root paths for the project (e.g., /home/user/my_project/data/core)

        Returns:
            List of absolute paths.
        """
        paths = []
        for data_type in self.data_types:
            paths.append(data_type.abs_path)
        return paths

    def _get_data_ignored_paths(self):
        """Gets the absolute paths of all files and directories to ignore.

        Returns:
            List of absolute paths to ignore from the data directory.
        """
        ignored = []
        for pattern in self.data_ignores:
            for data_type in self.data_types:
                ignored += glob.glob(os.path.join(data_type.abs_path, '**', pattern), recursive=True)
        return ignored
