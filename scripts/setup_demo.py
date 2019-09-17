#!/usr/bin/env python3

import argparse
import sys
import os
import uuid
import tempfile
import random
import synapseclient as syn

script_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(script_dir, '..', 'src'))

try:
    from kitools import KiProject, DataUri, SysPath, DataTypeTemplate
except Exception as ex:
    print('WARNING: Failed to load kitools: {0}'.format(ex))


def gen_id():
    return str(uuid.uuid4())[:8]


def mk_dirs(*args):
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def write_random_data_to_file(file_path):
    with open(file_path, mode='w') as f:
        for _ in range(1, random.randrange(2, 10)):
            f.write(str(uuid.uuid4()))


def mk_local_files_and_folders(start_path,
                               prefix='',
                               depth=3,
                               file_count=3,
                               folder_count=3,
                               current_depth=0,
                               syn_client=None,
                               syn_parent=None):
    current_depth += 1

    local_results = []
    remote_results = []

    for _ in range(0, file_count):
        filename = '{0}test_file_{1}_{2}.dat'.format(prefix, current_depth, gen_id())
        file_path = os.path.join(start_path, filename)

        # Fill the file with random data.
        write_random_data_to_file(file_path)
        local_results.append(file_path)

        # Store the file in Synapse
        if syn_parent:
            syn_file = syn_client.store(syn.File(path=file_path, parent=syn_parent))
            remote_results.append(syn_file)

    if current_depth < depth:
        # Create the folders.
        for _ in range(0, folder_count):
            foldername = '{0}test_folder_{1}_{2}'.format(prefix, current_depth, gen_id())
            folder_path = mk_dirs(start_path, foldername)
            local_results.append(folder_path)
            # Create the folder in Synapse
            if syn_parent:
                syn_folder = syn_client.store(syn.Folder(name=foldername, parent=syn_parent))
                remote_results.append(syn_folder)
            more_locals, more_remotes = mk_local_files_and_folders(folder_path,
                                                                   prefix=prefix,
                                                                   depth=depth,
                                                                   current_depth=current_depth,
                                                                   syn_client=syn_client,
                                                                   syn_parent=syn_folder)
            local_results += more_locals
            remote_results += more_remotes

    return local_results, remote_results


def create_demo_curator():
    """
    1. Creates a new Synapse Project.
    2. Creates the data/[core, artifacts, discovered] folders in Synapse.
    3. Creates and uploads files and folders into Synapse.
    4. Creates a new KiProject.
    5. data_adds each of the root data folders (core, artifacts, discovered) that were created in Synapse.
    6. data_pulls all the remote files and folders from Synapse.
    7. Creates one new file in each of the local data/[core, artifacts, discovered] folders.
    8. data_pushes each of the newly added local files.
    9. Changes 3 of the files that were pulled from the Synapse Project and data_pushes them to Synapse.
    10. Prints out the commands to load the project, data_add/data_pull the new and changed files.
    """
    print('Creating Demo for curator...')

    demo_id = gen_id()
    demo_commands = []

    demo_commands.append('')
    demo_commands.append('# Import the KiProject class:')
    demo_commands.append('from kitools import KiProject')

    kiproject_path = mk_dirs(tempfile.gettempdir(), 'demo_curator_{0}'.format(demo_id))

    syn_client = syn.login(silent=True)

    # Create the Synapse project
    syn_project = syn_client.store(syn.Project(name='Ki Tools Curator Demo - {0}'.format(demo_id)))

    kiproject = KiProject(kiproject_path,
                          no_prompt=True,
                          title='Demo KiProject {0}'.format(demo_id),
                          project_uri=DataUri('syn', syn_project.id).uri,
                          data_type_template=DataTypeTemplate.default().name)

    demo_commands.append('')
    demo_commands.append('# Open the KiProject:')
    demo_commands.append(
        'kiproject = KiProject({0}"{1}")'.format(('r' if os.sep == '\\' else ''), kiproject.local_path))

    # Add the synapse project files/folders.
    syn_temp_dir = mk_dirs(kiproject_path, '.demo-data')

    # Create files and folders in each DataType directory.
    for data_type in kiproject.data_types:
        parent = syn_project

        dt_folder_path = mk_dirs(os.path.join(syn_temp_dir, data_type.rel_path))

        for name in SysPath(data_type.rel_path).rel_parts:
            parent = syn_client.store(syn.Folder(name=name, parent=parent))

        kiproject.data_add(DataUri('syn', parent.id).uri, name=parent.name)

        mk_local_files_and_folders(dt_folder_path,
                                   depth=3,
                                   prefix='{0}_'.format(data_type.name),
                                   syn_client=syn_client,
                                   syn_parent=parent)
    kiproject.data_pull()

    # Create some new files for data_add/data_push
    demo_commands.append('')
    demo_commands.append('# Add some new files and push them:')
    for data_type in kiproject.data_types:
        dt_folder_path = mk_dirs(data_type.abs_path)

        local_results, _ = mk_local_files_and_folders(dt_folder_path, prefix='new_study_file_', depth=0, file_count=1)

        for new_filename in local_results:
            demo_commands.append('kiproject.data_add({0}"{1}")'.format(
                ('r' if os.sep == '\\' else ''), SysPath(new_filename, rel_start=kiproject.local_path).rel_path))

    demo_commands.append('kiproject.data_push()')

    # Create a change in some files for data_push
    demo_commands.append('')
    demo_commands.append('# Push some changed files:')
    change_count = 0
    for resource in kiproject.resources:
        if change_count >= 3:
            break

        if resource.abs_path and resource.abs_path.endswith('.dat'):
            change_count += 1
            file_path = resource.abs_path
            write_random_data_to_file(file_path)
            demo_commands.append('kiproject.data_push("{0}")'.format(os.path.basename(resource.name)))

    print('')
    print('Demo project created in: {0}'.format(kiproject_path))
    print('Synapse Project: {0} ({1})'.format(syn_project.name, syn_project.id))

    print('')
    print('Python Script:')
    for command in demo_commands:
        print(command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('demo', nargs='?', help='Which demo to create.', choices=['curator'], default='curator')
    args = parser.parse_args()

    if args.demo == 'curator':
        create_demo_curator()


if __name__ == "__main__":
    main()
