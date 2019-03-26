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
import synapseclient
from ..base_adapter import BaseAdapter
from .synapse_remote_entity import SynapseRemoteEntity
from ...data_type import DataType
from ...data_uri import DataUri
from ...sys_path import SysPath
from ...ki_env import KiEnv
from ...ki_project_resource import KiProjectResource


class SynapseAdapter(BaseAdapter):
    """
    Data Adapter for Synapse.
    """

    DATA_URI_SCHEME = 'syn'
    _client = None

    @classmethod
    def client(cls):
        """
        Gets a new or cached instance of a logged in Synapse client.
        :return:
        """
        if not cls._client:
            cls._client = synapseclient.Synapse(configPath=KiEnv.SYNAPSE_CONFIG_PATH())
            cls._client.login(forced=True, silent=True, rememberMe=False)
        return cls._client

    def name(self):
        return 'Synapse'

    def connected(self):
        try:
            return SynapseAdapter.client()._loggedIn() is not False
        except Exception as ex:
            # TODO: log this exception
            pass
        return False

    def get_entity(self, remote_id, version=None, local_path=None):
        entity = SynapseAdapter.client().get(
            remote_id,
            downloadFile=local_path is not None,
            downloadLocation=local_path,
            ifcollision='overwrite.local',
            version=version
        )

        remote_entity = SynapseRemoteEntity(entity)

        return remote_entity

    def create_project(self, name):
        # Check if the project already exists.
        syn_project_id = SynapseAdapter.client().findEntityId(name=name)
        if syn_project_id:
            raise Exception('Synapse project already exists for name: {0}'.format(name))

        syn_project = SynapseAdapter.client().store(synapseclient.Project(name=name))
        return SynapseRemoteEntity(syn_project)

    def data_pull(self, ki_project_resource):
        data_uri = DataUri.parse(ki_project_resource.remote_uri)
        syn_entity = SynapseAdapter.client().get(data_uri.id, downloadFile=False)

        if not ki_project_resource.abs_path:
            # This is the first pull so figure out where it lives locally.
            self._set_abs_path_from_entity(ki_project_resource, syn_entity)

        download_path = ki_project_resource.abs_path

        if self._is_file(syn_entity):
            download_path = os.path.dirname(download_path)

        # Make sure a version didn't get set on a folder.
        # Synapse will blow up when requesting a version on a folder.
        if self._is_folder(syn_entity) and ki_project_resource.version:
            ki_project_resource.version = None
            ki_project_resource.kiproject.save()

        entity = SynapseAdapter.client().get(
            data_uri.id,
            downloadFile=True,
            downloadLocation=download_path,
            ifcollision='overwrite.local',
            version=ki_project_resource.version
        )

        remote_entity = SynapseRemoteEntity(entity, local_path=download_path)

        assert remote_entity.local_path == ki_project_resource.abs_path

        if remote_entity.is_directory:
            # Create the local directory for the folder.
            SysPath(remote_entity.local_path).ensure_dirs()
            self._pull_children(ki_project_resource.root_resource or ki_project_resource,
                                remote_entity.source,
                                remote_entity.local_path)

        return remote_entity

    def _pull_children(self, root_ki_project_resource, syn_parent, download_path):
        kiproject = root_ki_project_resource.kiproject
        syn_children = SynapseAdapter.client().getChildren(syn_parent, includeTypes=['folder', 'file'])

        for syn_child in syn_children:
            child_data_uri = DataUri(SynapseAdapter.DATA_URI_SCHEME, syn_child.get('id')).uri
            child_name = syn_child.get('name')
            child_local_path = os.path.join(download_path, child_name)
            child_data_type = kiproject.data_type_from_project_path(child_local_path).name

            child_resource = kiproject.find_project_resource_by(data_type=child_data_type,
                                                                remote_uri=child_data_uri,
                                                                abs_path=child_local_path,
                                                                root_id=root_ki_project_resource.id)

            if not child_resource:
                child_resource = kiproject._data_add(data_type=child_data_type,
                                                     remote_uri=child_data_uri,
                                                     local_path=child_local_path,
                                                     name=child_name,
                                                     root_ki_project_resource=root_ki_project_resource)

            self.data_pull(child_resource)

    def _set_abs_path_from_entity(self, ki_project_resource, syn_entity):
        """
        Tries to figure out where a file/folder lives with in a KiProject data directory.
        :param ki_project_resource:
        :param syn_entity:
        :return:
        """
        kiproject = ki_project_resource.kiproject

        abs_path = self._find_abs_path_from_remote_path(kiproject, syn_entity)

        if not abs_path and ki_project_resource.data_type:
            # Figure out the path from the data_type
            name = syn_entity.name
            abs_path = os.path.join(kiproject.data_type_to_project_path(ki_project_resource.data_type), name)

        if abs_path:
            ki_project_resource.abs_path = abs_path
            kiproject.save()
        else:
            raise Exception('Could not determine local file path for: {0}'.format(ki_project_resource.remote_uri))

    def _find_abs_path_from_remote_path(self, kiproject, entity):
        """
        Tries to find the absolute path within a KiProject for a Synapse File/Folder.
        :param kiproject:
        :param entity:
        :return:
        """
        remote_path = self._get_full_remote_path(entity)

        # Get a list of the supported DataType paths (e.g., 'data/core/', etc.)
        supported_data_type_paths = []

        for data_type_name in DataType.ALL:
            supported_data_type_paths.append('{0}/{1}'.format(DataType.DATA_DIR_NAME, data_type_name))

        # Make sure the remote path conforms to the data_types directory structure.
        remote_data_type = None

        for path in supported_data_type_paths:
            if remote_path.startswith(path):
                remote_data_type = DataType(path.split('/')[1])
                break

        if remote_data_type:
            os_path = remote_path.replace('/', os.sep)
            return os.path.join(kiproject.local_path, os_path)

        return None

    def data_push(self, ki_project_resource):
        kiproject = ki_project_resource.kiproject

        project_data_uri = DataUri.parse(kiproject.project_uri)

        syn_parent = SynapseAdapter.client().get(project_data_uri.id)

        sys_path = SysPath(ki_project_resource.abs_path, rel_start=kiproject.local_path)

        # Get or create the folders in Synapse.
        for part in sys_path.rel_parts:
            # Break when we hit the filename.
            if part == sys_path.basename:
                break
            syn_parent = self._find_or_create_syn_folder(syn_parent, part)

        return self._data_push(ki_project_resource, syn_parent)

    def _data_push(self, ki_project_resource, syn_parent):
        kiproject = ki_project_resource.kiproject
        sys_path = SysPath(ki_project_resource.abs_path, rel_start=kiproject.local_path)
        syn_entity = None

        if sys_path.is_dir:
            # Find or create the folder in Synapse.
            syn_entity = self._find_or_create_syn_folder(syn_parent, sys_path.basename)

            # Push the children
            self._push_children(ki_project_resource.root_resource or ki_project_resource, syn_entity, sys_path.abs_path)
        else:
            # Upload the file
            syn_entity = SynapseAdapter.client().store(
                synapseclient.File(path=sys_path.abs_path, parent=syn_parent),
                forceVersion=False)

        has_changes = False

        # If this is the first push then update the KiProjectResource.
        if ki_project_resource.remote_uri is None:
            has_changes = True
            ki_project_resource.remote_uri = DataUri(self.DATA_URI_SCHEME, syn_entity.id).uri

        # Clear the version when pushing
        if ki_project_resource.version is not None:
            has_changes = True
            ki_project_resource.version = None

        if has_changes:
            kiproject.save()

        remote_entity = SynapseRemoteEntity(syn_entity, local_path=sys_path.abs_path)

        assert remote_entity.local_path == ki_project_resource.abs_path

        return remote_entity

    def _push_children(self, root_ki_project_resource, syn_parent, local_path):
        kiproject = root_ki_project_resource.kiproject

        dirs, files = self._get_dirs_and_files(local_path)

        for entry in files + dirs:
            sys_path = SysPath(entry.path)
            child_data_type = kiproject.data_type_from_project_path(sys_path.abs_path).name

            child_resource = kiproject.find_project_resource_by(data_type=child_data_type,
                                                                abs_path=sys_path.abs_path,
                                                                root_id=root_ki_project_resource.id)
            if not child_resource:
                child_resource = kiproject._data_add(data_type=child_data_type,
                                                     local_path=sys_path.abs_path,
                                                     name=sys_path.basename,
                                                     root_ki_project_resource=root_ki_project_resource)

            self._data_push(child_resource, syn_parent)

    def _get_dirs_and_files(self, local_path):
        dirs = []
        files = []

        entries = list(os.scandir(local_path))
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                dirs.append(entry)
            else:
                files.append(entry)

        dirs.sort(key=lambda f: f.name)
        files.sort(key=lambda f: f.name)

        return dirs, files

    def _get_full_remote_path(self, syn_entity):
        """
        Gets the full remote path for a Synapse Folder or File (e.g., folder1/folder2/file1.csv)
        :param syn_entity:
        :return: String
        """
        if syn_entity.get('parentId', None) is None:
            return None

        path_parts = []

        child = syn_entity
        while True:
            syn_parent = SynapseAdapter.client().get(child.get('parentId', None))

            # Stop once we hit the project.
            if self._is_project(syn_parent):
                break
            else:
                path_parts.insert(0, syn_parent.name)
                child = syn_parent

        path_parts.append(syn_entity.name)

        return '/'.join(path_parts)

    def _find_or_create_syn_folder(self, syn_parent, folder_name):
        # TODO: can any of this be cached?
        syn_entity_id = SynapseAdapter.client().findEntityId(folder_name, parent=syn_parent)

        if syn_entity_id:
            syn_entity = SynapseAdapter.client().get(syn_entity_id)
            if self._is_folder(syn_entity):
                return syn_entity
            else:
                raise Exception(
                    'Cannot create folder, name: {0} already take by another entity: {1}'.format(folder_name,
                                                                                                 syn_entity.id))

        return SynapseAdapter.client().store(synapseclient.Folder(name=folder_name, parent=syn_parent))

    def _is_project(self, syn_entity):
        return isinstance(syn_entity, synapseclient.Project)

    def _is_folder(self, syn_entity):
        return isinstance(syn_entity, synapseclient.Folder)

    def _is_file(self, syn_entity):
        return isinstance(syn_entity, synapseclient.File)

    def _is_project_folder_file(self, syn_entity):
        return self._is_project(syn_entity) or self._is_folder(syn_entity) or self._is_file(syn_entity)
