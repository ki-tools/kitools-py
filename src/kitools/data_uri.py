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


class DataUri(object):
    """
    Data URI parsing.

    URI Format: <scheme>:<id> (e.g., syn:syn123456789, osf:z7s4a)
    """

    SCHEMES = {}

    @classmethod
    def register(cls, scheme, adapter):
        """
        Registers a DataAdapter.
        :param scheme:
        :param adapter:
        :return:
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
            raise ValueError('uri must be specified.')

        # Clean up the URI.
        uri = uri.strip().replace(' ', '')

        segments = uri.split(':')

        if len(segments) != 2:
            raise ValueError('Invalid URI format, cannot parse: {0}'.format(uri))

        scheme = segments[0].lower()
        id = segments[1]

        if scheme not in DataUri.SCHEMES:
            raise ValueError('Invalid URI scheme: {0}'.format(scheme))

        if id.strip() == '':
            raise ValueError('URI ID must be provided.')

        return DataUri(scheme, id)

    @staticmethod
    def is_uri(uri):
        """
        Gets if a string is a DataUri.
        :param uri:
        :return:
        """
        try:
            return DataUri.parse(uri) is not None
        except Exception as ex:
            # TODO: log this?
            pass
        return False
