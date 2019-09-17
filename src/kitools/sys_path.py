import os
import shutil
from pathlib import PurePath


class SysPath:
    """Helper class for working with paths."""

    def __init__(self, path, cwd=None, rel_start=None):
        """Instantiates a new instance.

        Args:
            path: The path to manipulate.
            cwd: Optional current working directory.
            rel_start: Optional relative start path.
        """
        self._orig_path = path
        self._cwd = SysPath(cwd).abs_path if cwd else None

        var_path = os.path.expandvars(self._orig_path)
        expanded_path = os.path.expanduser(var_path)

        # Set the current working directory if not an absolute path.
        if not os.path.isabs(expanded_path) and self._cwd:
            expanded_path = os.path.join(self._cwd, expanded_path)

        self._abs_path = os.path.abspath(expanded_path)
        self._rel_start = rel_start

    @property
    def abs_path(self):
        """Gets the absolute path.

        Returns:
            String
        """
        return self._abs_path

    @property
    def abs_parts(self):
        """Gets the parts of the abs_path.

        Returns:
            List if strings.
        """
        return PurePath(self.abs_path).parts

    @property
    def rel_path(self):
        """Gets the relative path.

        Returns:
            String
        """
        return os.path.relpath(self.abs_path, start=self._rel_start)

    @property
    def rel_parts(self):
        """Gets the parts of the rel_path.

        Returns:
            List if strings.
        """
        return PurePath(self.rel_path).parts

    @property
    def exists(self):
        """Gets if the path exists.

        Returns:
            True or False
        """
        return os.path.exists(self.abs_path)

    @property
    def basename(self):
        """Gets the basename of the path.

        Returns:
            String
        """
        return os.path.basename(self.abs_path)

    @property
    def is_dir(self):
        """Gets if the path is a directory.

        Returns:
            True or False
        """
        return os.path.isdir(self.abs_path)

    @property
    def is_file(self):
        """Gets if the path is a file.

        Returns:
            True or False
        """
        return os.path.isfile(self.abs_path)

    def ensure_dirs(self):
        """Ensures all folders exists in the path.

        Returns:
            None
        """
        if not os.path.exists(self.abs_path):
            os.makedirs(self.abs_path)

    def delete(self):
        """Deletes all files and folders in the last path segment.

        Returns:
            None

        Raises:
            Exception: Raised when the path does not point to a file or directory.
        """
        if self.exists:
            if self.is_dir:
                shutil.rmtree(self.abs_path)
            elif self.is_file:
                os.remove(self.abs_path)
            else:
                raise Exception(
                    'Cannot delete: "{0}". Only directories and files can be deleted.'.format(self.abs_path))
