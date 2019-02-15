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
from src.kitools.data_providers import DataProviderFactory, SynapseProvider


def test_create():
    # Parses the source_uri
    for source_uri in ['syn123', 'SyN123', 'syn123/dir', 'syn123/dir/file.txt']:
        dp = DataProviderFactory.get(source_uri)
        assert isinstance(dp, SynapseProvider)

    # Raises an error
    with pytest.raises(ValueError):
        DataProviderFactory.get('unsupported-uri')

    # Returns the same instance
    dp1 = DataProviderFactory.get('syn1')
    dp2 = DataProviderFactory.get('syn2')
    assert id(dp1) == id(dp2)
