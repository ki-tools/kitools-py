class RemoteEntity(object):
    """Encapsulates a project/file/folder from a data provider."""

    def __init__(self, **kwargs):
        """Instantiates a new instance.

        Args:
            **kwargs: Hash of attributes.
        """

        self._id = kwargs.get('id')
        self._name = kwargs.get('name')
        self._source = kwargs.get('source')

        self._version = str(kwargs.get('version')) if 'version' in kwargs else None
        self._local_path = kwargs.get('local_path', None)
        self._is_project = kwargs.get('is_project', False)
        self._is_file = kwargs.get('is_file', False)
        self._is_directory = kwargs.get('is_directory', False)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def local_path(self):
        return self._local_path

    @property
    def is_project(self):
        return self._is_project

    @property
    def is_directory(self):
        return self._is_directory

    @property
    def is_file(self):
        return self._is_file

    @property
    def source(self):
        return self._source
