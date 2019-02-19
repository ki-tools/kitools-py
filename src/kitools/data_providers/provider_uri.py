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

from . import SynapseProvider


class ProviderUri(object):
    """
    Data provider URI parsing.

    URI Format: <scheme>:<id> (e.g., syn:syn123456789, osf:z7s4a)
    """

    SCHEMES = {
        'syn': {
            'data_provider': SynapseProvider
        }
    }

    def __init__(self, uri):
        self.uri = uri
        self.scheme = None
        self.id = None
        self._parse()

    def data_provider(self):
        return self.SCHEMES.get(self.scheme).get('data_provider')()

    def _parse(self):
        if not self.uri:
            raise ValueError('URI must be specified.')

        # Clean up the URI.
        self.uri = self.uri.strip().replace(' ', '')

        segments = self.uri.split(':')

        if len(segments) != 2:
            raise ValueError('Invalid URI format, cannot parse: {0}'.format(self.uri))

        tscheme = segments[0].lower()
        tid = segments[1]

        if tscheme not in self.SCHEMES:
            raise ValueError('Invalid scheme: {0}'.format(tscheme))

        self.scheme = tscheme
        self.id = tid
