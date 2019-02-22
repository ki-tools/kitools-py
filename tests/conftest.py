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


@pytest.fixture(scope='session')
def mk_tempdir():
    created = []

    def _mktempdir():
        path = tempfile.mkdtemp()
        created.append(path)
        return path

    yield _mktempdir

    for path in created:
        if os.path.isdir(path):
            shutil.rmtree(path)


@pytest.fixture(scope='session')
def mk_tempfile(mk_tempdir, syn_test_helper):
    temp_dir = mk_tempdir()

    def _mktempfile(content=syn_test_helper.uniq_name()):
        fd, tmp_filename = tempfile.mkstemp(dir=temp_dir)
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
        return tmp_filename

    yield _mktempfile

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
