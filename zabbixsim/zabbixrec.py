#!/usr/bin/env python3

"""System module"""
import argparse
import configparser
import yaml
import zabbix_api


def convert_to_seconds(time):
    """Convert a time string to seconds"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    if time.isnumeric():
        return int(time)

    return int(time[:-1]) * seconds_per_unit[time[-1]]

DEFAULTS = 'zabbixsim.cfg'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Specify command line arguments.
    parser.add_argument(
        "--server", type=str,
        help="Zabbix Server",
        default=None
        )
    parser.add_argument(
        "--username", type=str,
        help="Zabbix API username",
        default=None
        )
    parser.add_argument(
        "--password", type=str,
        help="Zabbix API password",
        default=None
        )
    parser.add_argument(
        "--hostname", type=str,
        help="Hostname",
        default=None
        )

    # Parse command line arguments.
    argvs = parser.parse_args()

    # Read the config
    config = configparser.ConfigParser()
    config.read(DEFAULTS)
    cfg_server = config.get('SETTINGS', 'server')
    cfg_username = config.get('SETTINGS', 'username')
    cfg_password = config.get('SETTINGS', 'password')
    cfg_hostname = config.get('SETTINGS', 'hostname')

    # Parse parameter overrides specified as command line arguments.
    argvs_server = argvs.server
    argvs_username = argvs.username
    argvs_password = argvs.password
    argvs_hostname = argvs.hostname

    # Bind reference to final parameter values.
    server   = argvs_server if argvs_server else cfg_server
    username = argvs_username if argvs_username else cfg_username
    password = argvs_password if argvs_password else cfg_password
    hostname = argvs_hostname if argvs_hostname else cfg_hostname
    zapi = zabbix_api.ZabbixAPI(server=server + "/zabbix")
    zapi.login(username, password)

    # Get the host
    host = zapi.host.get({ "filter": { "host": [ hostname ] } })

    if host[0]:
        hostid = host[0]['hostid']

        # Get the host items
        # 7 - Zabbix agent (active);
        active_items = zapi.item.get({
            "hostids": hostid,
            "sortfield": "name",
            "filter": {
                "type": "7"
            },
            "output": [ "key_", "name", "type", "value_type", "lastvalue", "delay" ]
        })

        # 0 - Zabbix agent;
        passive_items = zapi.item.get({
            "hostids": hostid,
            "sortfield": "name",
            "filter": {
                "type": "0"
            },
            "output": [ "key_", "name", "value_type", "lastvalue", "delay" ]
        })

        for item in active_items:
            item['delay'] = convert_to_seconds(item['delay'])
            item.pop('itemid')

        for item in passive_items:
            item['delay'] = convert_to_seconds(item['delay'])
            item.pop('itemid')

        # Add the hostname and Zabbix monitoring type to dict.
        host_items = {}
        host_items_type = {}
        if len(active_items) and len(passive_items):
            host_items_type['passive'] = passive_items
            host_items_type['active'] = active_items
            host_items[hostname] = host_items_type
        elif len(passive_items):
            host_items_type['passive'] = passive_items
            host_items[hostname] = host_items_type
        elif len(active_items):
            host_items_type['active'] = active_items
            host_items[hostname] = host_items_type

        # Dump the recorded items as yaml
        output = yaml.dump(host_items, Dumper=yaml.Dumper)
        with open(hostname + '.yaml', 'w', encoding="utf8") as writer:
            writer.write(output)

    zapi.logout()
