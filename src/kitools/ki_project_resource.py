import os
import uuid
from pathlib import PurePath
from .sys_path import SysPath
from .data_type import DataType


class KiProjectResource(object):
    """Defines a resource in a KiProject.

    A resource can be a directory or a file.
    """

    def __init__(self,
                 kiproject,
                 id=None,
                 root_id=None,
                 data_type=None,
                 remote_uri=None,
                 local_path=None,
                 name=None,
                 version=None):
        """
        Instantiates a new instance.

        Args:
            kiproject: The KiProject the resource belongs to.
            id: The ID of the resource.
            root_id: The ID of the root KiProjectResource (if the resource is a child).
            data_type: The data type of the resource.
            remote_uri: The remote URI of the resource.
            local_path: The local path of the resource.
            name: The friendly name of the resource.
            version: The locked version of the resource.
        """
        self._id = id if id else str(uuid.uuid4())
        self._root_id = root_id
        self._kiproject = kiproject
        self._remote_uri = remote_uri
        self._name = name

        self._data_type = None
        self._set_data_type(data_type)

        self._local_path = None
        self._set_local_path(local_path)

        self._version = None
        self._set_version(version)

    def _set_data_type(self, value):
        if value:
            if isinstance(value, DataType):
                value = value.name

            # Validate the value.
            value = self.kiproject.find_data_type(value)
        self._data_type = value

    def _set_local_path(self, value):
        if value:
            sys_path = SysPath(value, cwd=self.kiproject.local_path)
            value = sys_path.abs_path

        self._local_path = value

        if self.abs_path:
            data_type = self.kiproject.get_data_type_from_path(self.abs_path)
            self._set_data_type(data_type)

    def _set_version(self, value):
        self._version = str(value) if value else None

    @property
    def kiproject(self):
        return self._kiproject

    @property
    def id(self):
        return self._id

    @property
    def root_id(self):
        return self._root_id

    @root_id.setter
    def root_id(self, value):
        self._root_id = value

    @property
    def root_resource(self):
        if self.root_id is not None:
            return self.kiproject.find_project_resource_by(id=self.root_id)
        else:
            return None

    @property
    def remote_uri(self):
        return self._remote_uri

    @remote_uri.setter
    def remote_uri(self, value):
        self._remote_uri = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        self._set_data_type(value)

    @property
    def abs_path(self):
        """Gets the absolute path to the file.

        Returns:
            String of the absolute path or None.
        """
        if self.rel_path:
            return os.path.join(self.kiproject.local_path, self.rel_path)
        else:
            return None

    @abs_path.setter
    def abs_path(self, value):
        self._set_local_path(value)

    @property
    def rel_path(self):
        """Gets the path of the file relative to the KiProject's root directory.

        Returns:
            String of the relative path or None.
        """
        if self._local_path:
            return SysPath(self._local_path, rel_start=self.kiproject.local_path).rel_path
        else:
            return None

    @rel_path.setter
    def rel_path(self, value):
        self._set_local_path(value)

    def __str__(self):
        details = []
        details.append('Name: {0}'.format(self.name if self.name else '[not set]'))
        details.append('Date Type: {0}'.format(
            self.data_type if self.data_type else '[has not been pulled... use data_pull() to pull this dataset]'))
        details.append('Version: {0}'.format(self.version if self.version else '[latest]'))
        details.append('Remote URI: {0}'.format(
            self.remote_uri if self.remote_uri else '[has not been pushed... use data_push() to push this dataset]'))
        details.append('Absolute Path: {0}'.format(
            self.abs_path if self.abs_path else '[has not been pulled... use data_pull() to pull this dataset]'))
        return os.linesep.join(details)

    def to_json(self):
        """Serializes self into JSON.

        Returns:
            Hash
        """
        return {
            'id': self.id,
            'root_id': self.root_id,
            'data_type': self.data_type.name if self.data_type else None,
            'remote_uri': self.remote_uri,
            # Always store the path in Posix format ("/" vs "\").
            'rel_path': PurePath(self.rel_path).as_posix() if self.rel_path else None,
            'name': self.name,
            'version': self.version
        }

    @staticmethod
    def from_json(json, kiproject):
        """Deserializes JSON into a KiProjectResource.

        Args:
            json: The JSON to deserialize.
            kiproject: The KiProject the resource belongs to.

        Returns:
            KiProjectResource
        """
        return KiProjectResource(kiproject,
                                 id=json.get('id'),
                                 root_id=json.get('root_id'),
                                 data_type=json.get('data_type'),
                                 remote_uri=json.get('remote_uri'),
                                 local_path=json.get('rel_path'),
                                 name=json.get('name'),
                                 version=json.get('version'))
