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

import os
import yaml
from .data_providers import DataProviderFactory
from .project_template import ProjectTemplate


class Project:
    CONFIG_FILENAME = '.project.yml'
    CONFIG_PROPERTIES = ['title', 'description', 'synapse_id']
    DATA_TYPES = ['core', 'discovered', 'derived']

    DEFAULT_CONFIG = {
        'title': None,
        'description': None,
        'synapse_id': None,
        'data': {
            'core': {},
            'discovered': {},
            'derived': {}
        }
    }

    def __init__(self, path, **kwargs):
        self.path = path
        self._config_path = os.path.join(self.path, self.CONFIG_FILENAME)
        self._config = dict(self.DEFAULT_CONFIG)
        self._load_config()

        if kwargs:
            for prop_name, prop_value in kwargs.items():
                self._set_config_value(prop_name, prop_value)

    title = property(
        lambda self: self._get_config_value('title'),
        lambda self, value: self._set_config_value('title', value)
    )

    description = property(
        lambda self: self._get_config_value('description'),
        lambda self, value: self._set_config_value('description', value)
    )

    synapse_id = property(
        lambda self: self._get_config_value('synapse_id'),
        lambda self, value: self._set_config_value('synapse_id', value)
    )

    data_core = property(
        lambda self: self._get_config_value('data').get('core')
    )

    data_discovered = property(
        lambda self: self._get_config_value('data').get('discovered')
    )

    data_derived = property(
        lambda self: self._get_config_value('data').get('derived')
    )

    @staticmethod
    def create(path, title=None, description=None, synapse_project_id=None, synapse_user_id=None):
        ProjectTemplate(path).write()

        project = Project(path, title=title, description=description, synapse_id=synapse_project_id)

        return project

    def data_pull(self, source_uri, data_type=None, only_if_changed=True):
        """
        Downloads a file or a complete directory from a source URI.

        Downloads data to self.path/data/data_type/rest_of_path
        Checks if file exists already and checks if it's the latest version (by just getting metadata first and comparing MD5 hashes)
        Download new file
        Update the config and save
        :param source_uri: synapse_id/subdir_1/subdir_2/file.csv or synapse_id/subdir_1/subdir_2/
        :param data_type: must be one of {'core', 'discovered', 'derived'}
        :param only_if_changed: whether to check for update
        :return: path to file or folder
        """
        result = None

        data_provider = DataProviderFactory.get(source_uri)

        self._save_config()

        return result

    def data_load(self, source_uri, data_type=None, only_if_changed=True):
        """
        Calls data_pull and then loads into memory and returns
        Check the file extension and load a certain set of supported file types
        to start: csv, pickle, json, excel,
        :return: the loaded data
        """
        result = None

        data_provider = DataProviderFactory.get(source_uri)

        return result

    def data_save(self, data, target_uri, data_type=None, only_if_changed=True):
        """
        Sends data up to synapse, inferring how to save based on file extension.
        (Uses data_push)
        :param data:
        :param target_uri:
        :param data_type:
        :param only_if_changed:
        :return:
        """
        result = None

        data_provider = DataProviderFactory.get(target_uri)

        return result

    def data_push(self, data_path, target_uri, data_type=None, only_if_changed=True):
        """
        Takes the file at data_path and sends it to target_uri
        :param data_path:
        :param target_uri:
        :param data_type:
        :param only_if_changed:
        :return:
        """
        result = None

        data_provider = DataProviderFactory.get(target_uri)

        return result

    def data_list(self):
        """
        Prints out a nice table of all the available data entries in config.yml + local path
        """
        return None

    def _load_config(self):
        """
        Loads the Project's config file.
        :return: None
        """
        if os.path.isfile(self._config_path):
            with open(self._config_path) as f:
                self._config = yaml.load(f)

    def _save_config(self):
        """
        Saves the Project's config file.
        :return: None
        """
        with open(self._config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
        return self

    def _get_config_value(self, name):
        """
        Gets the value from the config.
        :param name:
        :return: object
        """
        return self._config.get(name, None)

    def _set_config_value(self, name, value):
        """
        Sets a value in the config.
        :param name:
        :param value:
        :return: None
        """
        if name not in self.CONFIG_PROPERTIES:
            raise AttributeError('Invalid config property: {0}'.format(name))

        self._config[name] = value
        self._save_config()

    def _get_config_data(self, data_type, synapse_id=None):
        """
        Gets a data property from the config.
        :param data_type:
        :param synapse_id:
        :return: Dictionary
        """
        data_type = data_type.lower()

        if data_type not in self.DATA_TYPES:
            raise ValueError('Invalid data data_type: {0}'.format(data_type))

        data = getattr(self, 'data_{0}'.format(data_type))

        if synapse_id:
            return data.get(synapse_id, None)
        else:
            return data

    def _set_config_data(self, data_type, synapse_id, path, modified, version):
        """
        Sets a data property in the config.
        :param data_type:
        :param synapse_id:
        :param path:
        :param modified:
        :param version:
        :return: Dictionary
        """
        data = self._get_config_data(data_type, synapse_id)
        if not data:
            data = {}
            data_type = self._get_config_data(data_type)
            data_type[synapse_id] = data

        data['path'] = path
        data['modified'] = modified
        data['version'] = version

        self._save_config()
        return data

    def _delete_config_data(self, data_type, synapse_id):
        """
        Deletes a data property in the config.
        :param data_type:
        :param synapse_id:
        :return:
        """
        data = self._get_config_data(data_type)
        if data.pop(synapse_id, None):
            self._save_config()
