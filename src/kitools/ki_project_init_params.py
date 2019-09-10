from .data_uri import DataUri


class KiProjectInitParams:
    """Defines initialization parameters for a KiProject.

    Use this class to define how a new KiProject should be initialized.
    """

    def __init__(self,
                 title=None,
                 description=None,
                 project_uri=None,
                 project_name=None,
                 data_type_template=None,
                 no_prompt=False):
        """Instantiates a new instance.

        Args:
            title: The title of the KiProject.
            description: The description of the KiProject.
            project_uri: The remote URI of the project that will hold the KiProject resources (for an existing project).
            project_name: The name of the project that will hold the KiProject resources (for a new project).
            data_type_template: The name of the DataTypeTemplate to create the project with.
            no_prompt: Suppress all prompts during KiProject initialization.
        """
        if project_uri and project_name:
            raise ValueError('project_uri and project_name cannot both be set.')

        if project_uri and not DataUri.is_uri(project_uri):
            raise ValueError('Invalid project_uri: {0}'.format(project_uri))
        
        self.title = title
        self.description = description
        self.data_type_template = data_type_template
        self.no_prompt = no_prompt
        self.prompt = not self.no_prompt
        self.project_uri = project_uri
        self.project_name = project_name
