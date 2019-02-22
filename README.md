# kitools

## Development Setup

```bash
git clone https://github.com/ki-tools/kitools-py.git
cd kitools-py
python3 -m venv .venv
source .venv/bin/activate
make init_dev
cp tests/templates/private.test.env.json tests/private.test.env.json
# Set the test values in: private.test.env.json
make test
```


## Usage

Create a new Project with an existing Synapse Project and add two files:
```text
project = Project('/path/to/my/project')

Creating new Project...
Project Name (required): My New Project
Project Description (optional): My example project.

Remote Project: [C]reate or Use [E]xisting [c/e]: e 
Remote Project URI (required): syn:syn001

Checking Synapse connectivity...
Connected to Synapse.

Checking remote project...
Remote project exists and accessible.

Project successfully setup and ready to use.

project.data_pull('syn:syn0020', data_type='core')
project.data_pull('syn:syn0021', data_type='core', version='2')
```

Create a new Project, create a new Synapse Project and add two files:
```text
project = Project('/path/to/my/project')

Creating new Project...
Project Name (required): My New Project
Project Description (optional): My example project.

Remote Project: [C]reate or Use [E]xisting [c/e]: c
 
Data Providers:
  1. Synapse
Enter the number of the data provider to use (required): 1

Checking Synapse connectivity...
Connected to Synapse.

Creating remote project...
Remote project created.

Project successfully setup and ready to use.

project.data_pull('syn:syn0020', data_type='core')
project.data_pull('syn:syn0021', data_type='core', version='2')
```

Pull all the data for an existing Project:
```python
project = Project('/path/to/my/project')
project.data_pull()
```

Push Data to the remote Project:
```python
project = Project('/path/to/my/project')
project.data_push('core/my-data.csv', data_type='core', remote_uri=None)
```

Push Data to the different Project:
```python
project = Project('/path/to/my/project')
project.data_push('core/my-data.csv', data_type='core', remote_uri='syn:syn123456')
```

Push All Data to the remote Project:
```python
project = Project('/path/to/my/project')
project.data_push()
```

## Project Configuration File

Example File:
```json
{
  "title": "My Project",
  "description": "My Project Description",
  "project_uri": "syn:syn001",
  "files": [
    {
      "remote_uri": "syn:syn002",
      "local_path": "data/core/file1.csv",
      "version": "1.2"
    },
    {
      "remote_uri": "syn:syn003",
      "local_path": "data/core/study1",
      "version": null
    }
  ]
}
```