import os
import uuid


class Utils:
    """Utility methods for the package."""

    @staticmethod
    def is_uuid(value):
        """Gets if the value is a UUID.

        Args:
            value: The value to check.

        Returns:
            True or False
        """
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_dirs_and_files(local_path):
        """Gets all the directories and files in a local path.

        Args:
            local_path: The path to get files and folders for.

        Returns:
            List of directory path, List of file paths.
        """
        dirs = []
        files = []

        entries = list(os.scandir(local_path))
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                dirs.append(entry)
            else:
                files.append(entry)

        dirs.sort(key=lambda f: f.name)
        files.sort(key=lambda f: f.name)

        return dirs, files
