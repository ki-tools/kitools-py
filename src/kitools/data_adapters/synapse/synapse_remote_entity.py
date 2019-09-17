from ...remote_entity import RemoteEntity
import synapseclient


class SynapseRemoteEntity(RemoteEntity):
    """RemoteEntity wrapper for Synapse entities."""

    def __init__(self, entity, local_path=None):
        """Instantiates a new instance.

        Args:
            entity: The Synapse entity object.
            local_path: The local path where the entity was downloaded to (when applicable).
        """
        super().__init__(
            id=entity.get('id'),
            name=entity.get('name'),
            version=entity.get('versionNumber', None),
            is_project=isinstance(entity, synapseclient.Project),
            is_directory=isinstance(entity, synapseclient.Folder),
            is_file=isinstance(entity, synapseclient.File),
            local_path=entity.get('path', local_path),
            source=entity
        )
