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
from src.kitools.sys_path import SysPath


@pytest.fixture(scope='session')
def mk_test_dirs(mk_tempdir, write_file):
    def _mk():
        temp_dir = mk_tempdir()
        child_dir = os.path.join(temp_dir, 'dir1')
        os.makedirs(child_dir)
        child_file = os.path.join(child_dir, 'file1.csv')
        write_file(child_file, content='test')

        return temp_dir, child_dir, child_file

    yield _mk


@pytest.fixture(scope='session')
def test_dirs(mk_test_dirs):
    return mk_test_dirs()


def test_it_expands_user():
    syspath = SysPath('~')
    assert syspath.abs_path == os.path.expanduser('~')


def test_it_expands_vars():
    # TODO: test this
    pass


def test_it_sets_the_cwd(test_dirs):
    temp_dir, child_dir, child_file = test_dirs

    assert SysPath(temp_dir, cwd=temp_dir).abs_path == temp_dir

    temp_dir_path = os.path.dirname(temp_dir)
    temp_dir_name = os.path.basename(temp_dir)

    assert SysPath(temp_dir_name, cwd=temp_dir_path)._cwd == temp_dir_path
    assert SysPath(temp_dir_name, cwd=temp_dir_path).abs_path == temp_dir
    file_path = os.path.join('dir1', 'file1.csv')
    assert SysPath(file_path, cwd=temp_dir, rel_start=temp_dir).rel_path == file_path


def test_it_sets_the_abs_path(test_dirs):
    temp_dir, child_dir, child_file = test_dirs

    # From absolute path
    assert SysPath(temp_dir).abs_path == temp_dir
    assert SysPath(temp_dir, cwd=temp_dir).abs_path == temp_dir

    # From relative path
    file_path = os.path.join('dir1', 'file1.csv')
    assert SysPath(file_path, cwd=temp_dir).abs_path == child_file
    assert SysPath(file_path).abs_path != child_file


def test_it_sets_the_rel_path(test_dirs):
    temp_dir, child_dir, child_file = test_dirs

    file_path = os.path.join('dir1', 'file1.csv')
    assert SysPath(temp_dir, rel_start=temp_dir).rel_path == '.'
    assert SysPath(temp_dir, cwd=temp_dir, rel_start=temp_dir).rel_path == '.'
    assert SysPath(child_file, rel_start=temp_dir).rel_path == file_path
    assert SysPath(child_file, cwd=temp_dir, rel_start=temp_dir).rel_path == file_path


def test_it_deletes_a_file(mk_test_dirs):
    temp_dir, child_dir, child_file = mk_test_dirs()
    assert os.path.isfile(child_file)

    sys_path = SysPath(child_file)
    assert sys_path.is_file
    assert sys_path.exists

    sys_path.delete()
    assert sys_path.exists is False
    assert os.path.exists(child_file) is False
    assert os.path.exists(temp_dir) is True
    assert os.path.exists(child_dir) is True


def test_it_deletes_a_folder_with_children(mk_test_dirs):
    temp_dir, child_dir, child_file = mk_test_dirs()
    assert os.path.isdir(child_dir)

    sys_path = SysPath(child_dir)
    assert sys_path.is_dir
    assert sys_path.exists

    sys_path.delete()
    assert sys_path.exists is False
    assert os.path.exists(child_dir) is False
    assert os.path.exists(child_file) is False
    assert os.path.exists(temp_dir) is True


def test_it_does_not_raise_an_error_if_the_file_doesnt_exist(mk_tempdir):
    temp_dir = mk_tempdir()
    fake_path = os.path.join(temp_dir, 'nope')
    sys_path = SysPath(fake_path)
    assert sys_path.exists is False
    sys_path.delete()
