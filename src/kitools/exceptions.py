class InvalidDataTypeError(ValueError):
    """Raised on invalid DataType."""

    def __init__(self, invalid_data_type, valid_data_types):
        """Instantiates a new instance.

        Args:
            invalid_data_type: The invalid data types.
            valid_data_types: All the valid data types.
        """
        names = [d.name for d in valid_data_types]
        message = 'Invalid DataType: {0}. Must of one of: {1}'.format(invalid_data_type, ', '.join(names))
        super().__init__(message)


class NotADataTypePathError(ValueError):
    """Raised when a local path is not in one of the KiProject's data directories."""

    def __init__(self, invalid_data_type_path, valid_data_types):
        message = 'Path: {0} must be in one of the data directories: '.format(invalid_data_type_path)

        valid_paths = []
        for data_type in valid_data_types:
            valid_paths.append(data_type.abs_path)

        message += ', '.join(valid_paths)

        super().__init__(message)


class DataTypeMismatchError(ValueError):
    """Raised when a DataType does not match another DataType, or expected DataType."""
    pass


class InvalidDataUriError(ValueError):
    """Raised on invalid DataUris"""
    pass


class KiProjectResourceNotFoundError(ValueError):
    """Raised when a KiProjectResource cannot be found."""
    pass
