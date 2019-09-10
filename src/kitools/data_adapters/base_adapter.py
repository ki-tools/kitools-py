import abc


class BaseAdapter(object):
    """Base class for data adapters."""

    @abc.abstractmethod
    def name(self):
        """Returns the name of the Data Adapter(e.g., Synapse).

        Returns:
            String
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def connected(self):
        """Gets if the provider is up and accessible.

        Returns:
            True if successful
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_entity(self, remote_id, version=None, local_path=None):
        """Gets a remote entity (Project, Folder, File).

        Args:
            remote_id: The ID of the remote entity.
            version: The version to get, or None for the latest version.
            local_path: If getting a file then set the local path to download the file to.

        Returns:
            RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def create_project(self, name):
        """Creates a new remote project.

        Args:
            name: The name of the project to create.

        Returns:
            RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_pull(self, ki_project_resource):
        """Pulls a KiProjectResource.

        Args:
            ki_project_resource: The KiProjectResource to pull.

        Returns:
            RemoteEntity
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data_push(self, ki_project_resource):
        """Pushes a KiProjectResource.

        Args:
            ki_project_resource: The KiProjectResource to push.

        Returns:
            RemoteEntity
        """
        raise NotImplementedError()
