#!/usr/bin/python3
#
# Simulate a Zabbix active agent
#

"""System modules"""
import configparser
import json
import logging
import os
import glob
import random
import socket
import struct
import sys
import time
import tkinter as tk
from tkinter import ttk
import yaml

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
ZABBIX_ACTIVE_PORT = 10051
#ZABBIX_ACTIVE_PORT = 10050
ZABBIX_REFRESH_ACTIVE_CHECKS = 120
ZABBIX_SEND_ACTIVE = 5

class ZabbixActive():
    """ZabbixActive"""
    # Generate a random 32 character number for the session id
    session_num= random.randrange(1, 10**32)

    server = ""
    active_data = {}

    def __init__(self, server: str, active_data: dict):
        logging.debug("ZabbixActive")
        self.server = server
        self.active_data = active_data

    def send_message(self, data: dict):
        '''Send the message to the Zabbix server'''
        active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        active_socket.connect((self.server, ZABBIX_ACTIVE_PORT))
        logging.debug('packet %s', data)

        # Generate the zabbix formatted message
        json_data = json.dumps(data, sort_keys=False)
        logging.debug("data %s", json_data)
        packet_send = b'ZBXD\1' + struct.pack('<Q', len(json_data)) + json_data.encode("utf-8")
        logging.debug("packet %s", packet_send)

        # send the message and receive the response
        active_socket.sendall(packet_send)
        packet_receive = active_socket.recv(10000)
        active_socket.close()

        # Print the received message
        receive_message = packet_receive[13:]
        parsed = json.loads(receive_message)
        logging.debug(parsed["response"])
        return parsed

    def refresh_checks(self, host_check: str):
        '''Query the Zabbix server for an active check'''
        active_check_msg = dict(request="active checks", host=host_check)
        received_data = self.send_message(active_check_msg)

        for value in received_data["data"]:
            logging.debug( "%s %s", str(value["key"]), str(value["delay"]))
        return received_data["data"]


    def agent_data(self, hostname :str, host_data :dict):
        '''Process the active agent data'''
        logging.debug("agent_data")
        epoch_time = int(time.time())

        # Send active data for each host
        if host_data:
            item_id = 1
            item_data_list = []
            for item in host_data:
                # Send the data when the current delay has been reset
                if item['current_delay'] == item['delay']:
                    item_data = dict(host=hostname,
                                key=item['key_'],
                                value=item['lastvalue'],
                                id=item_id,
                                clock=epoch_time,
                                ns=0)
                    item_data_list.append(item_data)
                    item_id += 1

        # Check if any data to send
        if len(item_data_list) > 0:
            agent_data_msg = dict(request="agent data",
                        session=f'{self.session_num:032}',
                        clock=epoch_time,
                        ns=0,
                        data=item_data_list)
            logging.debug(agent_data_msg)
            received_data = self.send_message(agent_data_msg)

            logging.debug(received_data["info"])
            self.session_num += 1

# TODO
#class ZabbixPassive():
#    def __init__(self):
#        logging.info("ZabbixPassive")

class ZabbixSim(tk.Tk):
    """ZabbixSim"""

    # pylint: disable=too-many-instance-attributes
    # data structures
    active_data = {}
    passive_data = {}

    # Lists for the menu options
    hostnames = []
    agent_types = []
    item_names = []
    item_keys = []

    # Current values
    current_hostname = ""
    current_item = {}
    current_type = ""

    zabbix_active = None

    def __init__(self):
        """ZabbixSim init"""
        super().__init__()
        self.geometry("400x250")
        self.title('Zabbix Agent Simulator')

        self.check_service()
        self.init_sim_data()
        self.zabbix_active = ZabbixActive(self.server, self.active_data)

        # set up option menu variables
        self.option_var = tk.StringVar(self)
        self.var_hostname = tk.StringVar(self)
        self.var_agent_type = tk.StringVar(self)
        self.var_item_name = tk.StringVar(self)
        self.var_item_key = tk.StringVar(self)
        self.var_item_delay = tk.IntVar(self)

        # create widget
        self.create_wigets()

    @classmethod
    def check_service(cls):
        """Check if zabbix-agent or zabbix-agent2 services are running"""
        status = os.system('systemctl is-active --quiet zabbix-agent')
        if status == 0:
            print("zabbixsim can't start while zabbix-agent is running")
            sys.exit()

        status = os.system('systemctl is-active --quiet zabbix-agent2')
        if status == 0:
            print("zabbixsim can't start while zabbix-agent2 is running")
            sys.exit()

    def init_sim_data(self):
        """Load the sim data and populate variables"""

        # Get Python Config parser
        config = configparser.ConfigParser()
        default_config = "zabbixsim.cfg"
        logging.debug('ConfigPath = %s', default_config)

        config.read(default_config)

        self.server = config.get('SETTINGS', 'server')

        # Load the recorded items as yaml
        for filename in sorted(glob.glob("*.yaml")):
            with open(os.path.join(os.getcwd(), filename), encoding="utf8") as file:
                loaded_data = yaml.load(file, Loader=yaml.Loader)

                # Add current_delay key to dictionary
                for hostname in loaded_data:
                    if 'active' in loaded_data[hostname]:
                        self.active_data[hostname] = []
                        for item in loaded_data[hostname]['active']:
                            item['current_delay'] = item['delay']
                            self.active_data[hostname].append(item)

                    if 'passive' in loaded_data[hostname]:
                        self.passive_data[hostname] = []
                        for item in loaded_data[hostname]['passive']:
                            self.passive_data[hostname].append(item)

                    # Load the hostnames
                    self.hostnames.append(hostname)

        # Load the agent types
        self.current_hostname = self.hostnames[0]
        self.agent_types = []
        if self.current_hostname in self.active_data:
            self.agent_types.append('active')
        if self.current_hostname in self.passive_data:
            self.agent_types.append('passive')

        self.current_type = self.agent_types[0]

        self.item_names = []
        self.item_keys = []
        if self.current_type == 'active':
            for item in self.active_data[hostname]:
                self.item_names.append(item['name'])
                self.item_keys.append(item['key_'])
            self.current_item = self.active_data[hostname][0]
        elif self.current_type == 'passive':
            for item in loaded_data[self.hostnames[0]][self.current_type]:
                self.item_names.append(item['name'])
                self.item_keys.append(item['key_'])
            self.current_item = self.passive_data[hostname][0]

    def create_wigets(self):
        # pylint: disable=too-many-locals

        """Create wigets"""
        # padding for widgets using the grid layout
        paddings = {'padx': 5, 'pady': 5}

        # label hostname
        lbl_hostname = ttk.Label(self,  text='Hostname:')
        lbl_hostname.grid(column=0, row=0, sticky=tk.W, **paddings)

        # menu hostname
        mnu_hostname = ttk.OptionMenu(
            self,
            self.var_hostname,
            self.hostnames[0],
            *self.hostnames,
            command=self.changed_hostname)
        mnu_hostname.grid(column=1, row=0, sticky=tk.W, **paddings)

        # label agent type
        lbl_agent_type = ttk.Label(self,  text='Agent Type:')
        lbl_agent_type.grid(column=0, row=1, sticky=tk.W, **paddings)

        # menu agent type
        self.mnu_agent_type = ttk.OptionMenu(
            self,
            self.var_agent_type,
            self.agent_types[0],
            *self.agent_types,
            command=self.changed_agent_type)
        self.mnu_agent_type.grid(column=1, row=1, sticky=tk.W, **paddings)

        # label item name
        lbl_item_name = ttk.Label(self,  text='Item Name:')
        lbl_item_name.grid(column=0, row=2, sticky=tk.W, **paddings)

        # menu item name
        self.mnu_item_name = ttk.OptionMenu(
            self,
            self.var_item_name,
            self.item_names[0],
            *self.item_names,
            command=self.changed_item_name)
        self.mnu_item_name.grid(column=1, row=2, sticky=tk.W, **paddings)

        # label item key
        lbl_item_key = ttk.Label(self,  text='Item Key:')
        lbl_item_key.grid(column=0, row=3, sticky=tk.W, **paddings)

        # menu item name
        self.mnu_item_key = ttk.OptionMenu(
            self,
            self.var_item_key,
            self.item_keys[0],
            *self.item_keys,
            command=self.changed_item_key)
        self.mnu_item_key.grid(column=1, row=3, sticky=tk.W, **paddings)

        # label item delay
        lbl_item_delay = ttk.Label(self, text='Item Delay:')
        lbl_item_delay.grid(column=0, row=4, sticky=tk.W, **paddings)

        # value item delay
        self.var_item_delay.set(self.current_item['delay'])
        self.lbl_item_delay_value = ttk.Label(self, textvariable=self.var_item_delay)
        self.lbl_item_delay_value.grid(column=1, row=4, sticky=tk.W, **paddings)

        # label item value
        lbl_item_value = ttk.Label(self,  text='Item Value:')
        lbl_item_value.grid(column=0, row=5, sticky=tk.W, **paddings)

        # value item delay
        self.entry_item_value = ttk.Entry(self)
        self.entry_item_value.insert(0, self.current_item['lastvalue'])
        self.entry_item_value.grid(column=1, row=5, sticky=tk.W, **paddings)

        # apply button
        btn_apply = ttk.Button(self, text='Apply', command=self.apply)
        btn_apply.grid(column=0, row=6, sticky=tk.W, **paddings)

        # refresh checks and send active data
        for hostname, data_items in self.active_data.items():
            self.zabbix_active.refresh_checks(hostname)
            self.zabbix_active.agent_data(hostname, data_items)

        # Start timers
        self.after(ZABBIX_REFRESH_ACTIVE_CHECKS * 1000, self.refresh_active_checks)
        self.after(ZABBIX_SEND_ACTIVE * 1000, self.send_active_data)

    def changed_hostname(self, hostname):
        """hostname changed"""
        logging.debug(hostname)
        self.var_hostname.set(hostname)

        # Delete the agent types
        self.mnu_agent_type['menu'].delete(0, 'end')

        # Load the agent types
        self.current_hostname = hostname
        self.agent_types = []
        if self.current_hostname in self.active_data:
            agent_type = 'active'
            self.agent_types.append(agent_type)
            self.mnu_agent_type['menu'].add_command(label=agent_type, command=tk._setit(self.var_agent_type, agent_type))
        if self.current_hostname in self.passive_data:
            agent_type = 'passive'
            self.agent_types.append(agent_type)
            self.mnu_agent_type['menu'].add_command(label=agent_type, command=tk._setit(self.var_agent_type, agent_type))

        self.current_type = self.agent_types[0]

        self.changed_agent_type(self.current_type)


    def changed_agent_type(self, agent_type):
        """agent type changed"""
        logging.debug('changed_agent_type %s', agent_type)

        # Delete the names and keys from menu
        self.mnu_item_name['menu'].delete(0, 'end')
        self.mnu_item_key['menu'].delete(0, 'end')

        # Load the items
        hostname = self.var_hostname.get()
        self.item_names = []
        self.item_keys = []
        if self.current_type == 'active':
            for item in self.active_data[hostname]:
                self.item_names.append(item['name'])
                self.item_keys.append(item['key_'])
                self.mnu_item_name['menu'].add_command(label=item['name'], command=tk._setit(self.var_item_name, item['name']))
                self.mnu_item_key['menu'].add_command(label=item['key_'], command=tk._setit(self.var_item_key, item['key_']))
            self.current_item = self.active_data[hostname][0]
        elif self.current_type == 'passive':
            for item in self.passive_data[hostname]:
                self.item_names.append(item['name'])
                self.item_keys.append(item['key_'])
                self.mnu_item_name['menu'].add_command(label=item['name'], command=tk._setit(self.var_item_name, item['name']))
                self.mnu_item_key['menu'].add_command(label=item['key_'], command=tk._setit(self.var_item_key, item['key_']))
            self.current_item = self.passive_data[hostname][0]

        self.changed_item_name(self.current_item['name'])

    def update_item_detail(self, item):
        """Update the item details when new item selected"""
        logging.debug('update_item_detail %s', str(item))
        self.var_item_name.set(item['name'])
        self.var_item_key.set(item['key_'])
        self.var_item_delay.set(item['delay'])
        self.entry_item_value.delete(0, tk.END)
        self.entry_item_value.insert(0, item['lastvalue'])


    def changed_item_name(self, item_name):
        """item name changed"""
        logging.debug('changed_item_name %s', item_name)

        # Load the item details
        hostname = self.var_hostname.get()
        if self.current_type == 'active':
            for item in self.active_data[hostname]:
                if item_name == item['name']:
                    self.update_item_detail(item)
        elif self.current_type == 'passive':
            for item in self.passive_data[hostname]:
                if item_name == item['name']:
                    self.update_item_detail(item)

    def changed_item_key(self, item_key):
        """item key changed"""
        logging.debug('changed_item_key %s', item_key)
        # Load the item details
        hostname = self.var_hostname.get()
        if self.current_type == 'active':
            for item in self.active_data[hostname]:
                if item_key == item['key_']:
                    self.update_item_detail(item)
        elif self.current_type == 'passive':
            for item in self.passive_data[hostname]:
                if item_key == item['key_']:
                    self.update_item_detail(item)

    def apply(self):
        """Apply the change in value and send update"""
        self.current_item['lastvalue'] = self.entry_item_value.get()
        self.current_item['current_delay'] = self.current_item['delay']
        for hostname, item_data in self.active_data.items():
            self.zabbix_active.agent_data(hostname, item_data)

    def refresh_active_checks(self):
        """Refresh active checks"""
        logging.debug('refresh active checks')
        for hostname in self.active_data:
            self.zabbix_active.refresh_checks(hostname)
        self.after(ZABBIX_REFRESH_ACTIVE_CHECKS * 1000, self.refresh_active_checks)

    def send_active_data(self):
        """Send active data"""
        logging.debug('send active data')
        for hostname, item_data in self.active_data.items():
            for item in item_data:
                # Update the current delay, so data is sent after the proper delay
                if item['current_delay'] <= 0:
                    item['current_delay'] = \
                        item['delay']
                else:
                    item['current_delay'] = \
                        item['current_delay'] - int(ZABBIX_SEND_ACTIVE)
            self.zabbix_active.agent_data(hostname, item_data)
        self.after(ZABBIX_SEND_ACTIVE * 1000, self.send_active_data)

def main():
    """Main for Zabbix Simulator"""
    zabbixsim = ZabbixSim()
    zabbixsim.mainloop()

if __name__ == "__main__":
    main()
