#!/usr/bin/python3
#
# Simulate a Zabbix active agent
#

"""System modules"""
import configparser
import socket
import json
import struct
import logging
import time
import random
import tkinter as tk
from tkinter import ttk
import yaml

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
ACTIVE_PORT = 10051
#ACTIVE_PORT = 10050

class ZabbixActive():
    """ZabbixActive"""
    session_num = random.getrandbits(64)

    server = ""

    def __init__(self, server):
        print("ZabbixActive")
        self.server = server

    def send_message(self, data):
        '''Send the message to the Zabbix server'''
        active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        active_socket.connect(self.server, ACTIVE_PORT)
        logging.debug('packet %s', data)
        active_socket.sendall(data)
        data = active_socket.recv(10000)
        active_socket.close()
        # Print the received message
        receive_message = data[13:]
        parsed = json.loads(receive_message)
        logging.debug(parsed["response"])
        return parsed


    def active_checks(self, host_check: str):
        '''Query the Zabbix server for an active check'''
        data = dict(request="active checks", host=host_check)
        json_data = json.dumps(data, sort_keys=False)
        logging.debug("data %s", json_data)
        packet = b'ZBXD\1' + struct.pack('<Q', len(json_data)) + json_data.encode("utf-8")
        logging.debug("packet %s", packet)
        received_data = self.send_message(packet)

        logging.debug(received_data)
        for value in received_data["data"]:
            logging.debug( "%s %s", str(value["key"]), str(value["delay"]))
        return received_data["data"]


    def agent_data(self, config):
        '''Process the active agent data'''
        logging.debug("agent_data")
        epoch_time = int(time.time())

        item_id = 1
        # Send data for each host
        data_list = []
        for host in config.sections():
            if host != 'SYSTEM':
                metrics = config.items(host)
                logging.info(metrics)
                # Send metrics to Zabbix
                for key, value in metrics:
                    item_data = dict(host=host,
                                    key=key,
                                    value=value,
                                    id=item_id,
                                    clock=epoch_time,
                                    ns=0)
                    data_list.append(item_data)
                    item_id += 1
                    logging.debug(item_data)

        data = dict(request="agent data",
                    session=self.session_num,
                    clock=epoch_time,
                    ns=0,
                    data=data_list)
        logging.debug(data)
        json_data = json.dumps(data, sort_keys=False, indent=2)
        logging.debug("data %s", json_data)
        packet = b'ZBXD\1' + struct.pack('<Q', len(json_data)) + json_data.encode("utf-8")
        received_data = self.send_message(packet)

        logging.debug(received_data["info"])
        self.session_num += 1

#class ZabbixPassive():
#    def __init__(self):
#        print("ZabbixPassive")

class ZabbixSim(tk.Tk):
    """ZabbixSim"""

    # pylint: disable=too-many-instance-attributes
#    server = ""
#    hostname = ""
    sim_data = {}
    hostnames = []
    agent_types = []
    item_names = []
    item_keys = []
    current_item = {}

    def __init__(self):
        """ZabbixSim init"""
        super().__init__()
        self.geometry("400x250")
        self.title('Zabbix Agent Simulator')

        self.init_sim_data()

        # set up option menu variables
        self.option_var = tk.StringVar(self)
        self.var_hostname = tk.StringVar(self)
        self.var_agent_type = tk.StringVar(self)
        self.var_item_name = tk.StringVar(self)
        self.var_item_key = tk.StringVar(self)

        # create widget
        self.create_wigets()

#        checks = active_checks("Zabbix server")

    def init_sim_data(self):
        """Load the sim data and populate variables"""

        # Get Python Config parser
        config = configparser.ConfigParser()
        default_config = "zabbixsim.cfg"
        logging.info('ConfigPath = %s', default_config)
        logging.basicConfig(level=logging.INFO)

        config.read(default_config)

        self.server = config.get('SETTINGS', 'server')
        self.hostname = config.get('SETTINGS', 'hostname')

        # Load the recorded items as yaml
        with open(self.hostname + '.yaml', encoding="utf8") as file:
            self.sim_data = yaml.load(file, Loader=yaml.Loader)

        # Load the hostnames
        for hostname in self.sim_data:
            self.hostnames.append(hostname)

        self.current_hostname = self.hostnames[0]

        # Load the agent types
        for agent_type in self.sim_data[self.current_hostname]:
            self.agent_types.append(agent_type)

        self.current_type = self.agent_types[0]

        # Load the items
        for item in self.sim_data[self.current_hostname][self.current_type]:
            self.item_names.append(item['name'])
            self.item_keys.append(item['key_'])

        self.current_item = self.sim_data[self.current_hostname][self.current_type][0]
        self.current_name = self.current_item['name']
        self.current_key = self.current_item['key_']

    def update_type_data(self):
        """Update type data"""
        self.item_names = []
        self.item_keys = []

    def update_item_data(self):
        """Update item data"""
        self.item_names = []
        self.item_keys = []
        #for type in self.sim_data[self.option_hostname.get()]:
        #    print(hostname)
        #    self.hostnames.append(hostname)

        #hostname_default = tk.StringVar(self)
        #hostname_default.set(hostnames[0]) # default value

        #for item in host_items[hostname]['active']:
        #    print(item)
        #    print(item['name'])
        #    print(item['key_'])
        #    item_names.append(item['name'])
        #    item_keys.append(item['key_'])

        #self.item_name_default = tk.StringVar(self)
        #self.item_name_default.set(item_names[0]) # default value

    def create_wigets(self):
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
        mnu_agent_type = ttk.OptionMenu(
            self,
            self.var_agent_type,
            self.agent_types[0],
            *self.agent_types,
            command=self.changed_agent_type)
        mnu_agent_type.grid(column=1, row=1, sticky=tk.W, **paddings)

        # label item name
        lbl_item_name = ttk.Label(self,  text='Item Name:')
        lbl_item_name.grid(column=0, row=2, sticky=tk.W, **paddings)

        # menu item name
        mnu_item_name = ttk.OptionMenu(
            self,
            self.var_item_name,
            self.item_names[0],
            *self.item_names,
            command=self.changed_item_name)
        mnu_item_name.grid(column=1, row=2, sticky=tk.W, **paddings)

        # label item key
        lbl_item_key = ttk.Label(self,  text='Item Key:')
        lbl_item_key.grid(column=0, row=3, sticky=tk.W, **paddings)

        # menu item name
        mnu_item_key = ttk.OptionMenu(
            self,
            self.var_item_key,
            self.item_keys[0],
            *self.item_keys,
            command=self.changed_item_key)
        mnu_item_key.grid(column=1, row=3, sticky=tk.W, **paddings)

        # label item delay
        lbl_item_delay = ttk.Label(self, text='Item Delay:')
        lbl_item_delay.grid(column=0, row=4, sticky=tk.W, **paddings)

        # value item delay
        lbl_item_delay_value = ttk.Label(self, text=self.current_item['delay'])
        lbl_item_delay_value.grid(column=1, row=4, sticky=tk.W, **paddings)

        # label item value
        lbl_item_value = ttk.Label(self,  text='Item Value:')
        lbl_item_value.grid(column=0, row=5, sticky=tk.W, **paddings)

        # value item delay
        entry_item_value = ttk.Entry(self)
        entry_item_value.insert(0, self.current_item['lastvalue'])
        entry_item_value.grid(column=1, row=5, sticky=tk.W, **paddings)

        # apply button
        btn_apply = ttk.Button(self, text='Apply', command=self.apply)
        btn_apply.grid(column=2, row=5, sticky=tk.W, **paddings)

    def changed_hostname(self, hostname):
        """hostname changed"""
        print(hostname)

    def changed_agent_type(self, agent_type):
        """agent type changed"""
        print(agent_type)

    def changed_item_name(self, item_name):
        """item name changed"""
        print(item_name)

    def changed_item_key(self, item_key):
        """item key changed"""
        print(item_key)

    def apply(self):
        """Apply the change in value and send update"""
        print("Apply pressed")

    @classmethod
    def send_active_data(cls): #, *args):
        """Send active data"""
        print('send active data')
        # my_button.after(5000, self.send_active_data)


if __name__ == "__main__":
    zabbixsim = ZabbixSim()
    zabbixsim.mainloop()
