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
from src.kitools import KiProjectResource


@pytest.fixture()
def kiproject(mk_kiproject):
    return mk_kiproject()


@pytest.fixture()
def fake_uri(mk_fake_uri):
    return mk_fake_uri()


@pytest.fixture()
def file_abs_path(kiproject, write_file):
    path = os.path.join(kiproject.data_types[0].abs_path, 'test.csv')
    write_file(path, 'test file')
    return path


@pytest.fixture()
def file_rel_path(kiproject, file_abs_path):
    return os.path.relpath(file_abs_path, start=kiproject.local_path)


def test_it_parses_abs_path(kiproject, fake_uri, file_abs_path, file_rel_path):
    ki_project_resource = KiProjectResource(kiproject=kiproject,
                                            remote_uri=fake_uri,
                                            local_path=file_abs_path,
                                            name=os.path.basename(file_abs_path))
    assert ki_project_resource.abs_path == file_abs_path
    assert ki_project_resource.rel_path == file_rel_path


def test_it_parses_rel_path(kiproject, fake_uri, file_abs_path, file_rel_path):
    ki_project_resource = KiProjectResource(kiproject=kiproject,
                                            remote_uri=fake_uri,
                                            local_path=file_rel_path,
                                            name=os.path.basename(file_rel_path))
    assert ki_project_resource.abs_path == file_abs_path
    assert ki_project_resource.rel_path == file_rel_path


def test_it_converts_version_to_a_string(kiproject, fake_uri, file_abs_path):
    name = os.path.basename(file_abs_path)
    assert KiProjectResource(kiproject=kiproject,
                             remote_uri=fake_uri,
                             local_path=file_abs_path,
                             name=name,
                             version=None).version is None

    assert KiProjectResource(kiproject=kiproject,
                             remote_uri=fake_uri,
                             local_path=file_abs_path,
                             name=name,
                             version=1).version == '1'

    assert KiProjectResource(kiproject=kiproject,
                             remote_uri=fake_uri,
                             local_path=file_abs_path,
                             name=name,
                             version='').version is None


def test_it_json_serializes_rel_path_as_posix_path(kiproject, fake_uri, file_abs_path):
    # NOTE: This test needs to be run in each supported env (Linux/Mac, Windows).
    resource = KiProjectResource(kiproject=kiproject, remote_uri=fake_uri, local_path=file_abs_path)
    json = resource.to_json()
    assert '\\' not in json['rel_path']
    assert '/' in json['rel_path']


def assert___str__(ki_project_resource):
    details = str(ki_project_resource)

    if ki_project_resource.name:
        assert 'Name: {0}'.format(ki_project_resource.name) in details
    else:
        assert 'Name: {0}'.format('[not set]') in details

    if ki_project_resource.data_type:
        assert 'Date Type: {0}'.format(ki_project_resource.data_type) in details
    else:
        assert 'Date Type: {0}'.format('[has not been pulled... use data_pull() to pull this dataset]') in details

    if ki_project_resource.version:
        assert 'Version: {0}'.format(ki_project_resource.version) in details
    else:
        assert 'Version: {0}'.format('[latest]') in details

    if ki_project_resource.remote_uri:
        assert 'Remote URI: {0}'.format(ki_project_resource.remote_uri) in details
    else:
        assert 'Remote URI: {0}'.format('[has not been pushed... use data_push() to push this dataset]') in details

    if ki_project_resource.abs_path:
        assert 'Absolute Path: {0}'.format(ki_project_resource.abs_path) in details
    else:
        assert 'Absolute Path: {0}'.format('[has not been pulled... use data_pull() to pull this dataset]') in details

    print(ki_project_resource)


def test___str__returns_the_resource_details(kiproject, fake_uri, file_abs_path):
    ki_project_resource = KiProjectResource(kiproject=kiproject,
                                            remote_uri=None,
                                            local_path=None,
                                            version=None,
                                            name=None)
    assert___str__(ki_project_resource)

    ki_project_resource = KiProjectResource(kiproject=kiproject,
                                            remote_uri=fake_uri,
                                            local_path=file_abs_path,
                                            version='1',
                                            name=os.path.basename(file_abs_path))
    assert___str__(ki_project_resource)
