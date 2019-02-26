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

import pytest
import os
import tempfile
import shutil
import json
import uuid
from src.kitools import Project, ProjectFile, DataUri, DataType
from tests.synapse_test_helper import SynapseTestHelper
import synapseclient

# Load Environment variables.
module_dir = os.path.dirname(os.path.abspath(__file__))

test_env_file = os.path.join(module_dir, 'private.test.env.json')

if os.path.isfile(test_env_file):
    with open(test_env_file) as f:
        config = json.load(f).get('test')

        # Validate required properties are present
        for prop in ['SYNAPSE_USERNAME', 'SYNAPSE_PASSWORD']:
            if prop not in config or not config[prop]:
                raise Exception('Property: "{0}" is missing in {1}'.format(prop, test_env_file))

        for key, value in config.items():
            os.environ[key] = value
else:
    print('WARNING: Test environment file not found at: {0}'.format(test_env_file))


@pytest.fixture(scope='session')
def synapse_test_config():
    """
    Creates a temporary Synapse config file with the test credentials and redirects
    the Synapse client to the temp config file.
    :return:
    """

    config = """
[authentication]
username = {0}
password = {1}
    """.format(os.getenv('SYNAPSE_USERNAME'), os.getenv('SYNAPSE_PASSWORD'))

    fd, tmp_filename = tempfile.mkstemp(suffix='.synapseConfig')
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(config)

    synapseclient.client.CONFIG_FILE = tmp_filename

    yield tmp_filename

    if os.path.isfile(tmp_filename):
        os.remove(tmp_filename)


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


@pytest.fixture()
def new_syn_project(new_syn_test_helper):
    return new_syn_test_helper.create_project()


@pytest.fixture()
def mk_project(mocker, syn_project, mk_tempdir, mk_uniq_string, mk_fake_project_file):
    def _input_mock(prompt):
        if 'Create project in:' in prompt:
            return 'y'
        elif 'Project title:' in prompt:
            return mk_uniq_string()
        elif 'Create remote project or use existing? [c/e]' in prompt:
            return 'e'
        elif 'Remote project name:' in prompt:
            return mk_uniq_string()
        elif 'Remote project URI (e.g.,' in prompt:
            return DataUri('syn', syn_project.id).uri
        elif 'Try again? [y/n]:' in prompt:
            return 'y'
        else:
            raise Exception('Unsupported mock input prompt: {0}'.format(prompt))

    def _mk(dir=None,
            with_fake_project_files=False,
            with_fake_project_files_count=1):

        # Mock the user input
        mock_input = mocker.MagicMock('input')
        mock_input.side_effect = _input_mock
        mocker.patch('builtins.input', new=mock_input)

        project = Project((dir or mk_tempdir()),
                          project_uri=DataUri('syn', syn_project.id).uri,
                          title=mk_uniq_string(),
                          description=mk_uniq_string())

        if with_fake_project_files:
            for _ in range(with_fake_project_files_count):
                project.files.append(mk_fake_project_file(project))

        project.save()
        return project

    yield _mk


@pytest.fixture(scope='session')
def mk_uniq_string():
    def _mk():
        return str(uuid.uuid4()).replace('-', '_')

    yield _mk


@pytest.fixture(scope='session')
def mk_uniq_integer():
    def _mk():
        return str(uuid.uuid4().int)

    yield _mk


@pytest.fixture(scope='session')
def mk_fake_uri(mk_uniq_integer):
    def _mk(scheme='syn'):
        return DataUri(scheme, '{0}{1}'.format(scheme, mk_uniq_integer())).uri

    yield _mk


@pytest.fixture(scope='session')
def mk_fake_project_file(mk_tempdir, mk_fake_uri, mk_uniq_string, write_file):
    def _mk(project, data_type=DataType.CORE):
        file_path = os.path.join(DataType(data_type).to_project_path(project.local_path),
                                 '{0}.csv'.format(mk_uniq_string()))

        write_file(file_path, mk_uniq_string())

        return ProjectFile(project, remote_uri=mk_fake_uri(), local_path=file_path, version='1')

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
