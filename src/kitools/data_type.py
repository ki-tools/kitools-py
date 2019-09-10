import os
from pathlib import PurePath
from .sys_path import SysPath


class DataType(object):
    """Defines a friendly name and relative path for storing types of data within a KiProject."""

    def __init__(self, project_local_path, name, rel_path):
        """Instantiates a new instance.

        Args:
            project_local_path: The local path of the KiProject
            name: The name of the data type.
            rel_path: The relative path of the data type directory.
        """
        self._project_local_path = project_local_path
        self._name = name
        # Get the rel_path from SysPath so the os.sep is correct.
        self._rel_path = SysPath(rel_path, cwd=project_local_path, rel_start=project_local_path).rel_path

    @property
    def name(self):
        return self._name

    @property
    def rel_path(self):
        return self._rel_path

    @property
    def abs_path(self):
        return os.path.join(self._project_local_path, self.rel_path)

    def to_json(self):
        """Serializes self into JSON.

        Returns:
            Primary properties as a Hash.
        """
        return {
            'name': self.name,
            # Always store the path in Posix format ("/" vs "\").
            'rel_path': PurePath(self.rel_path).as_posix() if self.rel_path else None,
        }

    @staticmethod
    def from_json(json, project_local_path):
        """Deserializes JSON into a DataType.

        Args:
            json: The JSON to deserialize.
            project_local_path: The local path of the KiProject.

        Returns:
            DataType
        """
        return DataType(
            project_local_path,
            json.get('name'),
            json.get('rel_path'))

    def __eq__(self, other):
        if isinstance(other, DataType):
            return self.name == other.name and self.rel_path == other.rel_path and self.abs_path == other.abs_path
        else:
            return NotImplemented
