[![Build Status](https://travis-ci.org/ki-tools/kitools-py.svg?branch=master)](https://travis-ci.org/ki-tools/kitools-py)
[![Build status](https://ci.appveyor.com/api/projects/status/307n6qcdywewtext/branch/master?svg=true)](https://ci.appveyor.com/project/Patrick33219/kitools-py/branch/master)
[![Coverage Status](https://coveralls.io/repos/github/ki-tools/kitools-py/badge.svg?branch=master)](https://coveralls.io/github/ki-tools/kitools-py?branch=master)

# kitools-py

Tools for working with data in [Ki](https://kiglobalhealth.org) analyses.

## Installation

`pip install kitools`


## Usage

Coming soon...


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