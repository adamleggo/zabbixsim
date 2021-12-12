# zabbixsim

Zabbix Agent Simulator (active)

## Setup

```bash
sudo yum install python3-tkinter python3-pyyaml
python3 -m venv zabbixsim
source zabbixsim/bin/activate
pip install -r requirements_dev.txt
pip install -r requirements.txt
```

## Build

```bash
python setup.py sdist bdist_wheel
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## Release

```bash
twine upload dist/*
```

Copyright (c) 2021, [Adam Leggo](mailto:adam@leggo.id.au). All rights reserved.
