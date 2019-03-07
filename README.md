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

`TBD...`

## KiProject Configuration File

Example File:
```json
{
  "title": "My KiProject",
  "description": "My KiProject Description",
  "project_uri": "syn:syn001",
  "resources": [
    {
      "data_type": "core",
      "remote_uri": "syn:syn002",
      "rel_path": "data/core/file1.csv",
      "name": "file1.csv",
      "version": "2"
    },
    {
      "data_type": "core",
      "remote_uri": "syn:syn003",
      "rel_path": "data/core/study1",
      "name": "study1",
      "version": null
    }
  ]
}
```