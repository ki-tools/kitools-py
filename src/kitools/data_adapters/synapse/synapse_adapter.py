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


class SynapseAdapter(BaseAdapter):
    DATA_URI_SCHEME = 'syn'
    _client = None

    @classmethod
    def client(cls):
        """
        Gets a new or cached instance of a logged in Synapse client.
        :return:
        """
        if not cls._client:
            cls._client = synapseclient.Synapse()
            cls._client.login(silent=True)
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
        syn_project = SynapseAdapter.client().store(synapseclient.Project(name=name))
        return SynapseRemoteEntity(syn_project)

    def data_pull(self, ki_project_resource):
        if not ki_project_resource.remote_uri:
            raise ValueError('KiProjectResource must have a remote_uri. Try pushing first.')

        data_uri = DataUri.parse(ki_project_resource.remote_uri)
        syn_entity = SynapseAdapter.client().get(data_uri.id, downloadFile=False)

        if not ki_project_resource.abs_path:
            # This is the first pull so figure out where it lives locally.
            self._try_set_abs_path(ki_project_resource, syn_entity)

        download_path = ki_project_resource.abs_path

        if self._is_file(syn_entity):
            download_path = os.path.dirname(download_path)

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
            if not os.path.exists(remote_entity.local_path):
                os.makedirs(remote_entity.local_path)

            assert remote_entity.local_path == ki_project_resource.abs_path

            self._pull_children(entity, ki_project_resource.abs_path)

        return remote_entity

    def _pull_children(self, syn_parent, local_path):

        syn_children = SynapseAdapter.client().getChildren(syn_parent, includeTypes=['folder', 'file'])

        version = None  # TODO: lookup version from the child's KiProjectResource (when/if children are added)?

        for syn_child in syn_children:
            entity = SynapseAdapter.client().get(
                syn_child.get('id'),
                downloadFile=True,
                downloadLocation=local_path,
                ifcollision='overwrite.local',
                version=version
            )

            remote_entity = SynapseRemoteEntity(entity, local_path=os.path.join(local_path, entity.name))

            if remote_entity.is_directory:
                # Create the local directory for the folder.
                if not os.path.exists(remote_entity.local_path):
                    os.makedirs(remote_entity.local_path)

                self._pull_children(entity, remote_entity.local_path)

    def _try_set_abs_path(self, ki_project_resource, syn_entity):
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
            abs_path = os.path.join(DataType(ki_project_resource.data_type).to_project_path(kiproject.local_path), name)

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
            supported_data_type_paths.append('{0}/{1}/'.format(DataType.DATA_DIR_NAME, data_type_name))

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

        rel_path = os.path.relpath(ki_project_resource.abs_path, start=kiproject.local_path)
        rel_dirs = os.path.dirname(rel_path)

        syn_parent = SynapseAdapter.client().get(project_data_uri.id)

        # Get or create the folders in Synapse.
        for segment in rel_dirs.split(os.sep):
            syn_parent = self._find_or_create_syn_folder(syn_parent, segment)

        is_dir = os.path.isdir(ki_project_resource.abs_path)
        syn_entity = None

        if is_dir:
            # Create the folder in Synapse
            folder_name = os.path.basename(ki_project_resource.abs_path)
            syn_entity = self._find_or_create_syn_folder(syn_parent, folder_name)

            # Push the children
            self._push_children(syn_entity, ki_project_resource.abs_path)
        else:
            # Upload the file
            syn_entity = SynapseAdapter.client().store(
                synapseclient.File(path=ki_project_resource.abs_path, parent=syn_parent))

        # If this is the first push then update the KiProjectResource.
        if not ki_project_resource.remote_uri:
            ki_project_resource.remote_uri = DataUri(self.DATA_URI_SCHEME, syn_entity.id).uri
            kiproject.save()

        remote_entity = SynapseRemoteEntity(syn_entity, local_path=ki_project_resource.abs_path)

        assert remote_entity.local_path == ki_project_resource.abs_path

        return remote_entity

    def _push_children(self, syn_parent, local_path):
        dirs, files = self._get_dirs_and_files(local_path)

        for file_entry in files:
            syn_file = SynapseAdapter.client().store(synapseclient.File(path=file_entry.path, parent=syn_parent))

        for dir_entry in dirs:
            folder_name = os.path.basename(dir_entry.path)
            syn_folder = self._find_or_create_syn_folder(syn_parent, folder_name)
            self._push_children(syn_folder, dir_entry.path)

    def _get_dirs_and_files(self, local_path):
        dirs = []
        files = []

        with os.scandir(local_path) as iter:
            for entry in iter:
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

        path_segments = []

        child = syn_entity
        while True:
            syn_parent = SynapseAdapter.client().get(child.get('parentId', None))

            # Stop once we hit the project.
            if self._is_project(syn_parent):
                break
            else:
                path_segments.insert(0, syn_parent.name)
                child = syn_parent

        path_segments.append(syn_entity.name)

        return '/'.join(path_segments)

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
