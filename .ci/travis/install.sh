#!/usr/bin/env bash
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

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    # Install custom requirements for macOS
    brew update

    case "${PYENV}" in
        py35)
            # Python 3.5
            brew install python35
            ;;
        py36)
            # Python 3.6
            brew install python36
            ;;
    esac

else
    # Install custom requirements for Linux
    :
fi

python --version
python -m pip install -U pip
pip install -r requirements.txt
pip install coveralls
