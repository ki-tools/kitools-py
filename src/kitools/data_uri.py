from .exceptions import InvalidDataUriError


class DataUri(object):
    """Defines a URI format for identifying remote projects, folders, and files.

    URI Format: <scheme>:<id> (e.g., syn:syn123456789, osf:z7s4a)
    """

    SCHEMES = {}

    def __init__(self, scheme, id):
        """Instantiates a new instance.

        Args:
            scheme: The scheme to use.
            id: The ID of the remote object.
        """
        self._scheme = scheme
        self._id = id

    @property
    def scheme(self):
        return self._scheme

    @property
    def id(self):
        return self._id

    @property
    def uri(self):
        """Gets the full URI.

        Returns:
            Full URI as a string.
        """
        return '{0}:{1}'.format(self.scheme, self.id)

    def data_adapter(self):
        """Gets the data adapter for the current scheme.

        Returns:
            Data adapter.
        """
        return self.SCHEMES.get(self.scheme).get('data_adapter')()

    @staticmethod
    def default_scheme():
        """Gets the default scheme ('syn').

        Returns:
            String.
        """
        return 'syn'

    @staticmethod
    def parse(uri):
        """Parses a string into a DataUri.

        Args:
            uri: The string to parse.

        Returns:
            DataUri

        Raises:
            InvalidDataUriError: Raised when the string cannot be parsed.
        """
        if not uri:
            raise InvalidDataUriError('uri cannot be blank.')

        # Clean up the URI.
        prepared_uri = uri.strip().replace(' ', '')

        parts = prepared_uri.split(':')

        if len(parts) != 2:
            raise InvalidDataUriError('Invalid URI format, cannot parse: {0}'.format(uri))

        scheme = parts[0].lower()
        id = parts[1]

        if scheme not in DataUri.SCHEMES:
            raise InvalidDataUriError('Invalid URI scheme: {0}'.format(scheme))

        if id.strip() == '':
            raise InvalidDataUriError('URI ID must be provided.')

        return DataUri(scheme, id)

    @staticmethod
    def is_uri(value):
        """Gets if a string is a DataUri.

        Args:
            value: The string to check.

        Returns:
            True if the string is a DataUri.
        """
        try:
            return DataUri.parse(value) is not None
        except InvalidDataUriError as ex:
            # TODO: log this?
            pass
        return False

    @classmethod
    def register_data_adapter(cls, scheme, adapter):
        """Registers a DataAdapter class for a specific scheme.

        Args:
            scheme: The scheme of the data adapter.
            adapter: The data adapter class.

        Returns:
            None
        """
        if scheme not in cls.SCHEMES:
            cls.SCHEMES[scheme] = {
                'data_adapter': adapter
            }
