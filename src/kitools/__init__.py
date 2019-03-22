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

from .ki_project import KiProject
from .ki_project_resource import KiProjectResource
from .data_type import DataType
from .data_uri import DataUri
from .sys_path import SysPath
from .ki_utils import KiUtils
from .ki_env import KiEnv
from .data_adapters import SynapseAdapter
from .exceptions import InvalidDataTypeError, NotADataTypePathError, DataTypeMismatchError, InvalidDataUriError

name = 'kitools'

DataUri.register_data_adapter(SynapseAdapter.DATA_URI_SCHEME, SynapseAdapter)
