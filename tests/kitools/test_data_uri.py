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
from src.kitools.data_adapters import SynapseAdapter
from src.kitools import DataUri


@pytest.fixture()
def bad_uris():
    return [
        None,
        '',
        'sn:syn123',
        '/tmp',
        '/tmp:/file',
        '/tmp/file.csv',
        'syn',
        'syn:  ',
        'syn123',
        'syn:123:abc'
    ]


def test___init__(bad_uris):
    for scheme in DataUri.SCHEMES:
        id = '123456'
        uri = '{0}:{1}'.format(scheme, id).title()

        duri = DataUri.parse(uri)
        assert duri.scheme == scheme
        assert duri.id == id
        assert duri.uri == uri.lower()

        if scheme == 'syn':
            assert isinstance(duri.data_adapter(), SynapseAdapter)

    with pytest.raises(ValueError) as ex:
        DataUri.parse(None)
    assert str(ex.value) == 'uri must be specified.'

    for bad_uri in bad_uris:
        with pytest.raises(ValueError) as ex:
            DataUri.parse(bad_uri)
        assert ('Invalid URI format, cannot parse:' in str(ex.value) or
                str(ex.value) == 'uri must be specified.' or
                'Invalid URI scheme:' in str(ex.value) or
                str(ex.value) == 'URI ID must be provided.')


def test_parse():
    # TODO: test this
    pass


def test_is_uri(bad_uris):
    for scheme in DataUri.SCHEMES:
        id = '123456'
        uri = '{0}:{1}'.format(scheme, id).title()
        assert DataUri.is_uri(uri) is True

    for bad_uri in bad_uris:
        assert DataUri.is_uri(bad_uri) is False
