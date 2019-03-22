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


from .exceptions import InvalidDataUriError


class DataUri(object):
    """
    Defines a URI format for identifying remote projects, folders, and files.

    URI Format: <scheme>:<id> (e.g., syn:syn123456789, osf:z7s4a)
    """

    SCHEMES = {}

    @classmethod
    def register_data_adapter(cls, scheme, adapter):
        """
        Registers a DataAdapter class for a specific scheme.

        :param scheme: The scheme of the data adapter.
        :param adapter: The data adapter class.
        :return: None
        """
        if scheme not in cls.SCHEMES:
            cls.SCHEMES[scheme] = {
                'data_adapter': adapter
            }

    def __init__(self, scheme, id):
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
        return '{0}:{1}'.format(self.scheme, self.id)

    def data_adapter(self):
        return self.SCHEMES.get(self.scheme).get('data_adapter')()

    @staticmethod
    def default_scheme():
        return 'syn'

    @staticmethod
    def parse(uri):
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
        """
        Gets if a string is a DataUri.
        :param value:
        :return:
        """
        try:
            return DataUri.parse(value) is not None
        except InvalidDataUriError as ex:
            # TODO: log this?
            pass
        return False
