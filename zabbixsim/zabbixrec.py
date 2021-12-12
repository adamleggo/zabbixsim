#!/usr/bin/env python3
"""Query a Zabbix Server to generated a ZabbixSim datafile"""
import configparser
import yaml
import zabbix_api


def convert_to_seconds(time):
    """Convert a time string to seconds"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    if time.isnumeric():
        return int(time)

    return int(time[:-1]) * seconds_per_unit[time[-1]]

class Config():
    """ Load config from file """
    def __init__(self):
        """ Initialise the config """
        """Process config from the file"""
        config_file = configparser.ConfigParser()
        config_file.read(DEFAULTS)
        self.server = config_file.get('SETTINGS', 'server')
        self.website = config_file.get('SETTINGS', 'website')
        self.username = config_file.get('SETTINGS', 'username')
        self.password = config_file.get('SETTINGS', 'password')

DEFAULTS = 'zabbixsim.cfg'

def main():
    """Main for Zabbix Recorder"""

    config = Config()

    zapi = zabbix_api.ZabbixAPI(server=config.website)
    zapi.login(config.username, config.password)

    # Get all the hosts
    hosts = zapi.host.get({"output": "extend"})

    for host in hosts:
        hostid = host['hostid']
        hostname = host['host']

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

        # Convert all deplays to seconds
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
        if len(active_items) > 0 or len(passive_items) > 0:
            output = yaml.dump(host_items, Dumper=yaml.Dumper)
            with open(hostname + '.yaml', 'w', encoding="utf8") as writer:
                writer.write(output)

    zapi.logout()

if __name__ == "__main__":
    main()
