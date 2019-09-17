import pytest
import os
import tempfile
import shutil
import json
import uuid
from src.kitools import KiProject, KiProjectResource, DataUri
from src.kitools.data_adapters import SynapseAdapter
from tests.synapse_test_helper import SynapseTestHelper

# Load Environment variables.
module_dir = os.path.dirname(os.path.abspath(__file__))

test_env_file = os.path.join(module_dir, 'private.test.env.json')

if os.path.isfile(test_env_file):
    with open(test_env_file) as f:
        config = json.load(f).get('test')

        for key, value in config.items():
            os.environ[key] = value
else:
    print('WARNING: Test environment file not found at: {0}'.format(test_env_file))


@pytest.fixture(scope='session', autouse=True)
def synapse_test_config():
    """
    Creates a temporary Synapse config file with the test credentials and redirects
    the Synapse client to the temp config file.
    :return:
    """
    syn_username = os.getenv('SYNAPSE_USERNAME', None)
    syn_password = os.getenv('SYNAPSE_PASSWORD', None)

    if not syn_username:
        raise Exception('Missing environment variable: SYNAPSE_USERNAME')

    if not syn_password:
        raise Exception('Missing environment variable: SYNAPSE_PASSWORD')

    syn_cache_path = tempfile.mkdtemp()

    config = """
[authentication]
username = {0}
password = {1}
[cache]
location = {2}
    """.format(syn_username, syn_password, syn_cache_path)

    fd, tmp_filename = tempfile.mkstemp(suffix='.synapseConfig')
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(config)

    os.environ['SYNAPSE_CONFIG_PATH'] = tmp_filename

    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)

    if os.path.isdir(syn_cache_path):
        shutil.rmtree(syn_cache_path)


@pytest.fixture(scope='session')
def syn_test_helper():
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture()
def new_syn_test_helper():
    helper = SynapseTestHelper()
    yield helper
    helper.dispose()


@pytest.fixture(scope='session')
def syn_client(syn_test_helper):
    return syn_test_helper.client()


@pytest.fixture(scope='session')
def syn_project(syn_test_helper):
    return syn_test_helper.create_project()


@pytest.fixture(scope='session')
def syn_project_uri(syn_project):
    return DataUri(SynapseAdapter.DATA_URI_SCHEME, syn_project.id).uri


@pytest.fixture()
def new_syn_project(new_syn_test_helper):
    return new_syn_test_helper.create_project()


@pytest.fixture(scope='session')
def mk_syn_project(syn_test_helper):
    def _mk():
        return syn_test_helper.create_project()

    yield _mk


@pytest.fixture()
def mk_kiproject(syn_dispose_of, mk_mock_kiproject_input, mk_tempdir, mk_uniq_string, mk_fake_project_file):
    def _mk(dir=None,
            data_type_template=None,
            with_fake_project_files=False,
            with_fake_project_files_count=1,
            with_non_root_project_files=False,
            with_non_root_project_files_count=1):

        mk_mock_kiproject_input()

        kiproject = KiProject((dir or mk_tempdir()), data_type_template=data_type_template)

        if with_fake_project_files:
            for _ in range(with_fake_project_files_count):
                fake_resource = mk_fake_project_file(kiproject)
                kiproject.resources.append(fake_resource)

                if with_non_root_project_files:
                    for _ in range(with_non_root_project_files_count):
                        fake_child_resource = mk_fake_project_file(kiproject, root_id=fake_resource.id)
                        kiproject.resources.append(fake_child_resource)

        kiproject.save()

        syn_dispose_of(kiproject)

        return kiproject

    yield _mk


@pytest.fixture()
def syn_dispose_of(syn_test_helper):
    def _sdo(kiproject):
        syn_project = syn_test_helper.client().get(DataUri.parse(kiproject.project_uri).id)
        syn_test_helper.dispose_of(syn_project)
        return syn_project

    yield _sdo


class MockKiProjectInputError(Exception):
    """
    Raised in mk_mock_kiproject_input when specified.
    """
    pass


@pytest.fixture()
def MockKiProjectInputErrorClass():
    return MockKiProjectInputError


@pytest.fixture()
def mk_mock_kiproject_input(mocker, syn_test_helper, mk_uniq_string):
    """
    Mocks out the prompts during KiProject initialization.
    """

    def _mk(create_project_in=None,
            raise_on_create_project_in=False,
            project_title=None,
            raise_on_project_title=False,
            project_description=None,
            raise_on_project_description=False,
            create_remote_project_or_existing=None,
            raise_on_create_remote_project_or_existing=False,
            remote_project_name=None,
            raise_on_remote_project_name=False,
            remote_project_uri=None,
            raise_on_remote_project_uri=False,
            try_again=None,
            raise_on_try_again=False):

        def _input_mock(prompt):
            if 'Create KiProject in:' in prompt:
                if raise_on_create_project_in:
                    raise MockKiProjectInputError(prompt)
                else:
                    return create_project_in or 'y'
            elif 'KiProject title:' in prompt:
                if raise_on_project_title:
                    raise MockKiProjectInputError(prompt)
                else:
                    return project_title or mk_uniq_string()
            elif 'KiProject description:' in prompt:
                if raise_on_project_description:
                    raise MockKiProjectInputError(prompt)
                else:
                    return project_description or mk_uniq_string()
            elif 'Create a remote project or use an existing? [c/e]:' in prompt:
                if raise_on_create_remote_project_or_existing:
                    raise MockKiProjectInputError(prompt)
                else:
                    return create_remote_project_or_existing or 'c'
            elif 'Remote project name:' in prompt:
                if raise_on_remote_project_name:
                    raise MockKiProjectInputError(prompt)
                else:
                    return remote_project_name or mk_uniq_string()
            elif 'Remote project URI (e.g.,' in prompt:
                if raise_on_remote_project_uri:
                    raise MockKiProjectInputError(prompt)
                else:
                    return remote_project_uri
            elif 'Try again? [y/n]:' in prompt:
                if raise_on_try_again:
                    raise MockKiProjectInputError(prompt)
                else:
                    return try_again or 'n'
            else:
                raise Exception('Unsupported mock input prompt: {0}'.format(prompt))

        # Mock the user input
        mock_input = mocker.MagicMock('input')
        mock_input.side_effect = _input_mock
        mocker.patch('builtins.input', new=mock_input)

    # Catch any new Synapse Projects that are created so they can be cleaned up.
    real_create_project = SynapseAdapter.create_project

    def _mock_create_project(self, project_name):
        remote_project = real_create_project(self, project_name)
        syn_test_helper.dispose_of(remote_project.source)
        return remote_project

    mocker.patch('src.kitools.data_adapters.SynapseAdapter.create_project', new=_mock_create_project)

    yield _mk

    SynapseAdapter.create_project = real_create_project


@pytest.fixture(scope='session')
def mk_uniq_string():
    def _mk():
        return str(uuid.uuid4()).replace('-', '_')

    yield _mk


@pytest.fixture(scope='session')
def mk_uniq_integer():
    def _mk():
        return uuid.uuid4().int

    yield _mk


@pytest.fixture(scope='session')
def mk_fake_uri(mk_uniq_integer):
    def _mk(scheme='syn'):
        return DataUri(scheme, '{0}{1}'.format(scheme, mk_uniq_integer())).uri

    yield _mk


@pytest.fixture(scope='session')
def mk_fake_project_file(mk_fake_uri, mk_uniq_string, write_file):
    def _mk(kiproject, data_type=None, root_id=None):
        if not data_type:
            data_type = kiproject.data_types[0]

        file_path = os.path.join(data_type.abs_path, '{0}.csv'.format(mk_uniq_string()))

        write_file(file_path, mk_uniq_string())

        return KiProjectResource(kiproject=kiproject,
                                 remote_uri=mk_fake_uri(),
                                 local_path=file_path,
                                 name=mk_uniq_string(),
                                 version='1',
                                 root_id=root_id)

    yield _mk


@pytest.fixture(scope='session')
def add_project_file(mk_fake_uri, mk_uniq_string, write_file):
    def _mk(kiproject, data_type=None):
        if not data_type:
            data_type = kiproject.data_types[0]

        file_path = os.path.join(data_type.abs_path, '{0}.csv'.format(mk_uniq_string()))

        write_file(file_path, mk_uniq_string())

        kiproject.data_push(file_path, data_type=data_type)
        return kiproject.find_project_resource_by(abs_path=file_path)

    yield _mk


@pytest.fixture(scope='session')
def mk_tempdir():
    created = []

    def _mk():
        path = tempfile.mkdtemp()
        created.append(path)
        return path

    yield _mk

    for path in created:
        if os.path.isdir(path):
            shutil.rmtree(path)


@pytest.fixture(scope='session')
def mk_tempfile(mk_tempdir, syn_test_helper):
    temp_dir = mk_tempdir()

    def _mk(content=syn_test_helper.uniq_name()):
        fd, tmp_filename = tempfile.mkstemp(dir=temp_dir)
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
        return tmp_filename

    yield _mk

    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture(scope='session')
def write_file():
    def _write(file, content):
        # Create the directory if it doesn't exist.
        if not os.path.exists(os.path.dirname(file)):
            os.makedirs(os.path.dirname(file))

        with open(file, mode='w') as f:
            f.write(content)

    yield _write


@pytest.fixture(scope='session')
def read_file():
    def _read(file):
        with open(file, mode='r') as f:
            return f.read()

    yield _read


@pytest.fixture(scope='session')
def delete_file():
    def _delete(file):
        if os.path.isfile(file):
            os.remove(file)

    yield _delete
