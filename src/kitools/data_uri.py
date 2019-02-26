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

from .data_providers import SynapseProvider


class DataUri(object):
    """
    Data URI parsing.

    URI Format: <scheme>:<id> (e.g., syn:syn123456789, osf:z7s4a)
    """

    SCHEMES = {
        'syn': {
            'data_provider': SynapseProvider
        }
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

    def data_provider(self):
        return self.SCHEMES.get(self.scheme).get('data_provider')()

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

        return DataUri(scheme, id)
