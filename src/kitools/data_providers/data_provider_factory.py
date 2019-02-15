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

import os
from .synapse_provider import SynapseProvider


class DataProviderFactory:
    _providers = {}

    @classmethod
    def get(cls, uri):
        """
        Gets a data provider.
        :param uri:
        :return:
        """
        protocol = uri.lower().split(os.sep)[0]

        provider_class = None

        if protocol.startswith('syn'):
            provider_class = SynapseProvider

        if provider_class:
            if provider_class not in cls._providers:
                cls._providers[provider_class] = provider_class()
            return cls._providers[provider_class]

        raise ValueError('Cannot find data provider for uri: {0}'.format(uri))
