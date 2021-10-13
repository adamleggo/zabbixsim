# zabbixsim

Zabbix Agent Simulator (active)

The Zabbix Agent Simulator is intended to be used instead of the regular Zabbix agent in scenarios, where the use of the real Zabbix Agnet is not partical or desirable. This includes testing scenarios that are not possible on a live system.

This is works well with the snmpsim to provide simulation data for Zabbix.
<https://github.com/etingof/snmpsim>
<https://pypi.org/project/snmpsim/>

The simulator is based on the protocol documented in the Zabbbix manual.
<https://www.zabbix.com/documentation/current/manual/appendix/items/activepassive>

## Installation

```bash
pip install zabbixsim
```

## Usage

### Record simulation file

Record a simulation file from a Zabbix Server

```bash
zabbixrec
```

### Run simulation file

Run a simulation file with a Zabbix Server

```bash
zabbixsim
```

Copyright (c) 2021, [Adam Leggo](mailto:adam@leggo.id.au). All rights reserved.
