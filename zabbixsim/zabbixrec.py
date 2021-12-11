#!/usr/bin/env python3
"""Query a Zabbix Server to generated a ZabbixSim datafile"""
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

class ConfigArgs():
    """ Load config from command line """
    def __init__(self):
        """Process config from the command line"""
        parser = argparse.ArgumentParser()
        # Specify command line arguments.
        parser.add_argument(
            "--server", type=str,
            help="Zabbix Server",
            default=None
            )
        parser.add_argument(
            "--https", type=str,
            help="Server supports TLS [true|false]",
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

        # Parse parameter overrides specified as command line arguments.
        self.argvs_server = argvs.server
        self.argvs_https = argvs.https
        self.argvs_username = argvs.username
        self.argvs_password = argvs.password

class ConfigFile():
    """ Load config from file """
    def __init__(self):
        """Process config from the file"""
        config_file = configparser.ConfigParser()
        config_file.read(DEFAULTS)
        self.cfg_server = config_file.get('SETTINGS', 'server')
        self.cfg_https = config_file.getboolean('SETTINGS', 'https')
        self.cfg_username = config_file.get('SETTINGS', 'username')
        self.cfg_password = config_file.get('SETTINGS', 'password')


class Config():
    """ Load config from command line and file """
    def __init__(self):
        """ Initialise the config """
        self.config_args = ConfigArgs()
        self.config_file = ConfigFile()
        self.process_final_values()

    def process_final_values(self):
        """ Bind reference to final parameter values """
        self.server   = self.config_args.argvs_server \
                            if self.config_args.argvs_server else self.config_file.cfg_server
        self.https = (self.config_args.argvs_https.lower() == 'true') \
                            if self.config_args.argvs_https else self.config_file.cfg_https
        self.username = self.config_args.argvs_username \
                            if self.config_args.argvs_username else self.config_file.cfg_username
        self.password = self.config_args.argvs_password \
                            if self.config_args.argvs_password else self.config_file.cfg_password

DEFAULTS = 'zabbixsim.cfg'

def main():
    """Main for Zabbix Recorder"""

    config = Config()

    if config.https:
        zapi = zabbix_api.ZabbixAPI(server="https://" + config.server + "/zabbix")
    else:
        zapi = zabbix_api.ZabbixAPI(server="http://" + config.server + "/zabbix")
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
