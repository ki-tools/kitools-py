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
from src.kitools import KiProjectResource, DataType


@pytest.fixture()
def kiproject(mk_kiproject):
    return mk_kiproject()


@pytest.fixture()
def fake_uri(mk_fake_uri):
    return mk_fake_uri()


@pytest.fixture()
def file_abs_path(kiproject, write_file):
    path = os.path.join(kiproject.data_type_to_project_path(DataType.CORE), 'test.csv')
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
