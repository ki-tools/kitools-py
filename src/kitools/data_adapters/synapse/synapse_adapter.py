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
from ...data_uri import DataUri
from ...sys_path import SysPath
from ...env import Env
from ...utils import Utils
from ...ki_project_resource import KiProjectResource
from ...data_type import DataType


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
            cls._client = synapseclient.Synapse(configPath=Env.SYNAPSE_CONFIG_PATH())
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

        # Compare path parts until this is fixed: https://github.com/Sage-Bionetworks/synapsePythonClient/issues/678
        assert SysPath(remote_entity.local_path).abs_path.lower() == \
               SysPath(ki_project_resource.abs_path).abs_path.lower()

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
            child_data_type = kiproject.get_data_type_from_path(child_local_path).name

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
        Tries to figure out where a file/folder lives with in a KiProject data directories.
        :param ki_project_resource:
        :param syn_entity:
        :return:
        """
        kiproject = ki_project_resource.kiproject

        remote_path = self._get_remote_path(syn_entity)

        # Always use the resource's data_type if available.
        data_type = ki_project_resource.data_type or kiproject.get_data_type_from_path(remote_path)

        if data_type is None:
            raise Exception(
                'Could not determine local file path for: {0}, try setting the data_type on this resource'.format(
                    ki_project_resource.remote_uri))

        local_rel_path = remote_path

        if local_rel_path.startswith(data_type.rel_path):
            local_rel_path = local_rel_path.replace(data_type.rel_path, '', 1)

        if local_rel_path.startswith(os.sep):
            local_rel_path = local_rel_path[1:]

        abs_path = os.path.join(kiproject.local_path, data_type.rel_path, local_rel_path)

        ki_project_resource.abs_path = abs_path
        assert ki_project_resource.data_type is not None

        kiproject.save()

    def data_push(self, ki_project_resource):
        kiproject = ki_project_resource.kiproject

        project_data_uri = DataUri.parse(kiproject.project_uri)

        resource_belongs_to_ki_project = True
        syn_parent = None

        # Check if the synapse entity belongs to the KiProject's remote project
        # and get the correct synapse parent if it doesn't.
        if ki_project_resource.remote_uri is not None:
            resource_data_uri = DataUri.parse(ki_project_resource.remote_uri)

            syn_entity = SynapseAdapter.client().get(resource_data_uri.id, downloadFile=False)

            syn_parents = [syn_entity] if self._is_project(syn_entity) else list(SynapseParentIter(syn_entity))

            # The last item will always be a Synapse Project.
            resource_syn_project = syn_parents[-1]
            assert self._is_project(resource_syn_project)

            if resource_syn_project.id != project_data_uri.id:
                # The resource does not belong to the same Synapse project so get its parent.
                resource_belongs_to_ki_project = False
                syn_parent = syn_parents[0]
            else:
                syn_parent = resource_syn_project
                assert project_data_uri.id == syn_parent.id

        # If the resource belongs to the KiProject's remote project then get or create the remote folder structure.
        if resource_belongs_to_ki_project:
            if syn_parent is None:
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
            syn_entity = SynapseAdapter.client().store(synapseclient.File(path=sys_path.abs_path, parent=syn_parent),
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

        # Compare path parts until this is fixed: https://github.com/Sage-Bionetworks/synapsePythonClient/issues/678
        assert SysPath(remote_entity.local_path).abs_path.lower() == \
               SysPath(ki_project_resource.abs_path).abs_path.lower()

        return remote_entity

    def _push_children(self, root_ki_project_resource, syn_parent, local_path):
        kiproject = root_ki_project_resource.kiproject

        dirs, files = Utils.get_dirs_and_files(local_path)

        for entry in files + dirs:
            sys_path = SysPath(entry.path)
            child_data_type = kiproject.get_data_type_from_path(sys_path.abs_path).name

            child_resource = kiproject.find_project_resource_by(data_type=child_data_type,
                                                                abs_path=sys_path.abs_path,
                                                                root_id=root_ki_project_resource.id)
            if not child_resource:
                child_resource = kiproject._data_add(data_type=child_data_type,
                                                     local_path=sys_path.abs_path,
                                                     name=sys_path.basename,
                                                     root_ki_project_resource=root_ki_project_resource)

            self._data_push(child_resource, syn_parent)

    def _get_remote_path(self, syn_entity):
        """
        Gets the remote path for a Synapse Folder or File (e.g., folder1/folder2/file1.csv)
        :param syn_entity: The Synapse entity to get the path for.
        :return: String
        """
        if not (self._is_folder(syn_entity) or self._is_file(syn_entity)):
            return ''

        path_parts = [syn_entity.name]

        for e in SynapseParentIter(syn_entity):
            if self._is_project(e):
                break
            path_parts.insert(0, e.name)

        # Return the path matching the OS's separator.
        return os.sep.join(path_parts)

    def _find_or_create_syn_folder(self, syn_parent, folder_name):
        # TODO: can any of this be cached?
        syn_entity_id = SynapseAdapter.client().findEntityId(folder_name, parent=syn_parent)

        if syn_entity_id:
            syn_entity = SynapseAdapter.client().get(syn_entity_id)
            if self._is_folder(syn_entity):
                return syn_entity
            else:
                raise Exception(
                    'Cannot create folder, name: {0} already taken by another entity: {1}'.format(folder_name,
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


class SynapseParentIter:
    def __init__(self, syn_entity):
        self._current_entity = syn_entity

    def __iter__(self):
        return self

    def __next__(self):
        if isinstance(self._current_entity, synapseclient.Project):
            raise StopIteration()

        self._current_entity = SynapseAdapter.client().get(self._current_entity.get('parentId', None))

        return self._current_entity
