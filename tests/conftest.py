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


@pytest.fixture()
def new_test_project(mk_tempdir):
    """
    Provides a test Project with one ProjectFile.
    :return: Project
    """
    temp_dir = mk_tempdir()

    project = Project(temp_dir)
    project.title = 'My Project Title'
    project.description = 'My Project Description'
    project.project_uri = 'syn:syn001'
    project.files.append(
        ProjectFile(remote_uri='syn:syn002',
                    local_path=os.path.join('data', 'core', 'file1.csv'),
                    version='1.2'
                    )
    )
    project.save()

    return project


@pytest.fixture()
def mk_project(mk_tempdir, mk_tempfile, write_file, syn_test_helper):
    def _mkproject(
            with_project=False,
            with_project_scheme='syn',
            with_files=False,
            with_files_count=1,
            with_files_versions=1,
            **kwargs):

        if kwargs is None:
            kwargs = {}

        project_path = mk_tempdir()
        provider_project = None
        project_files = []

        if with_project or with_files:
            if isinstance(with_project, bool):
                if with_project_scheme == 'syn':
                    provider_project = syn_test_helper.create_project()
                else:
                    raise ValueError('Invalid scheme: {0}'.format(with_project_scheme))
            else:
                provider_project = with_project

        if with_files:
            if with_project_scheme == 'syn':
                for i in range(with_files_count):

                    syn_file = None
                    temp_file = mk_tempfile(content='version0')

                    for fileversion in range(with_files_versions):
                        write_file(temp_file, 'version{0}'.format(fileversion + 1))
                        syn_file = syn_test_helper.create_file(
                            name=os.path.basename(temp_file),
                            path=temp_file,
                            parent=provider_project)

                    remote_uri = DataUri(scheme='syn', id=syn_file.id).uri()
                    local_path = ProjectFile.to_relative_path(temp_file, project_path)

                    project_files.append(ProjectFile(remote_uri=remote_uri, local_path=local_path))
            else:
                raise ValueError('Invalid scheme: {0}'.format(with_project_scheme))

        project_uri = DataUri(scheme=with_project_scheme)
        if provider_project:
            project_uri.id = provider_project.id
        else:
            project_uri.id = DataUri.parse(kwargs.get('project_uri', '{0}:123456'.format(with_project_scheme))).id

        project = Project(
            project_path,
            title=kwargs.get('title', 'My Project Title'),
            description=kwargs.get('description', 'My Project Description'),
            project_uri=project_uri.uri(),
            files=project_files
        )

        return project

    yield _mkproject


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
def write_file():
    def _write(file, content):
        with open(file, mode='w') as f:
            f.write(content)

    yield _write


@pytest.fixture()
def read_file():
    def _read(file):
        with open(file, mode='r') as f:
            return f.read()

    yield _read


@pytest.fixture()
def delete_file():
    def _delete(file):
        if os.path.isfile(file):
            os.remove(file)

    yield _delete
