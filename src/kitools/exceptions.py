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


class InvalidKiDataTypeError(ValueError):
    """
    Raised on invalid KiDataType.
    """

    def __init__(self, invalid_data_type, valid_ki_data_types):
        names = [d.name for d in valid_ki_data_types]
        message = 'Invalid DataType: {0}. Must of one of: {1}'.format(invalid_data_type, ', '.join(names))
        super().__init__(message)


class NotAKiDataTypePathError(ValueError):
    """
    Raised when a local path is not in one of the KiProject's data directories.
    """

    def __init__(self, invalid_data_type_path, valid_ki_data_types):
        message = 'Path: {0} must be in one of the data directories: '.format(invalid_data_type_path)

        valid_paths = []
        for ki_data_type in valid_ki_data_types:
            valid_paths.append(ki_data_type.abs_path)

        message += ', '.join(valid_paths)

        super().__init__(message)


class KiDataTypeMismatchError(ValueError):
    """
    Raised when a KiDataType does not match another KiDataType, or expected KiDataType.
    """
    pass


class InvalidDataUriError(ValueError):
    """
    Raised on invalid DataUris
    """
    pass


class KiProjectResourceNotFoundError(ValueError):
    """
    Raised when a KiProjectResource cannot be found.
    """
    pass
