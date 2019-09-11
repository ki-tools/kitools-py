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
