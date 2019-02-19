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

import pytest
from src.kitools.data_providers import ProviderUri, SynapseProvider


def test___init__():
    for scheme in ProviderUri.SCHEMES:
        id = '123456'
        uri = '{0}:{1}'.format(scheme, id).title()

        puri = ProviderUri(uri)
        assert puri.scheme == scheme
        assert puri.id == id

        if scheme == 'syn':
            assert isinstance(puri.data_provider(), SynapseProvider)

    with pytest.raises(ValueError) as ex:
        ProviderUri(None)
    assert str(ex.value) == 'URI must be specified.'

    for bad_uri in ['syn', 'syn123', 'syn:123:abc']:
        with pytest.raises(ValueError) as ex:
            ProviderUri(bad_uri)
        assert str(ex.value) == 'Invalid URI format, cannot parse: {0}'.format(bad_uri)
