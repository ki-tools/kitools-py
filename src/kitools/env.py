import os
import synapseclient


class Env:
    """Provides access to all the environment variables the package uses."""

    @staticmethod
    def SYNAPSE_CONFIG_PATH():
        """Gets the path to the Synapse Config file.

        Returns:
            String
        """
        return os.environ.get('SYNAPSE_CONFIG_PATH', synapseclient.client.CONFIG_FILE)
