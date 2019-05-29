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
from .ki_project import KiProject
from .ki_project_resource import KiProjectResource
from .data_type import DataType
from .data_type_template import DataTypeTemplate, DataTypeTemplatePath
from .data_uri import DataUri
from .sys_path import SysPath
from .utils import Utils
from .env import Env
from .data_adapters import SynapseAdapter
from .exceptions import InvalidDataTypeError, NotADataTypePathError, DataTypeMismatchError, InvalidDataUriError

name = 'kitools'

# Register the Synapse adapter.
DataUri.register_data_adapter(SynapseAdapter.DATA_URI_SCHEME, SynapseAdapter)

# Register the DataType templates.
DataTypeTemplate.register(
    DataTypeTemplate(name='rally',
                     description='Data Types for rally projects.',
                     paths=[
                         DataTypeTemplatePath('core', os.path.join('data', 'core')),
                         DataTypeTemplatePath('auxiliary', os.path.join('data', 'auxiliary')),
                         DataTypeTemplatePath('results', 'results')
                     ],
                     is_default=True)
)

DataTypeTemplate.register(
    DataTypeTemplate(name='generic',
                     description='Data Type for generic projects.',
                     paths=[
                         DataTypeTemplatePath('data', 'data')
                     ],
                     is_default=False)
)
