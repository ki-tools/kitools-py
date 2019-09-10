class DataTypeTemplate(object):
    """Defines a DataType template.

    The template defines a name and all the paths to the "data" folders in a KiProject.
    """

    _templates = []

    def __init__(self, name, description, paths, is_default=False):
        """Instantiates a new instance.

        Args:
            name: The friendly name of the template.
            description: A description of the template.
            paths: The paths contained in the template.
            is_default: True if this is the default template otherwise False.
        """
        self.name = name
        self.description = description
        self.paths = paths
        self.is_default = is_default

    @classmethod
    def all(cls):
        """Gets all the templates."""
        return cls._templates

    @classmethod
    def default(cls):
        """Gets the default template."""
        return next(d for d in cls._templates if d.is_default)

    @classmethod
    def register(cls, template):
        """Registers a template so it can be used.

        Args:
            template: The template to register.

        Returns:
            None
        """
        cls._templates.append(template)

    @classmethod
    def get(cls, name):
        """Gets a template by name.

        Args:
            name: The name of the template top get.

        Returns:
            The template or None.
        """
        return next((t for t in cls._templates if t.name == name), None)


class DataTypeTemplatePath(object):
    """Defines a name and path in a DataTypeTemplate"""

    def __init__(self, name, rel_path):
        """Instantiates a new instance.

        Args:
            name: The friendly name of the path.
            rel_path: The relative path to the directory for the path.
        """
        self.name = name
        self.rel_path = rel_path
