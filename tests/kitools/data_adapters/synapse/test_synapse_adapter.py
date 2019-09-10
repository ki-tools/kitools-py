import pytest
import responses
from src.kitools.data_adapters import SynapseAdapter
import synapseclient


def test_name():
    assert SynapseAdapter().name() == 'Synapse'


def test_client():
    client = SynapseAdapter.client()
    assert client
    assert isinstance(client, synapseclient.Synapse)
    assert client._loggedIn() is not False

    # Returns the same client
    client2 = SynapseAdapter.client()
    assert client2 == client
    assert client2._loggedIn() is not False


def test_connected():
    assert SynapseAdapter().connected() is True

    with responses.RequestsMock() as rsps:
        # Unauthorized
        rsps.add(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=401)
        assert SynapseAdapter().connected() is False

        # General error
        rsps.replace(responses.GET, 'https://repo-prod.prod.sagebase.org/repo/v1/userProfile', status=418)
        assert SynapseAdapter().connected() is False

# TODO: add remaining tests.
