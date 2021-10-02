#
# This file is part of zabbixsim software.
#
# Copyright (c) 2021, Adam Leggo <adam@leggo.id.au>
# License: https://github.com/adamleggo/zabbixsim/blob/main/LICENSE
#
"""Zabbix Agent simulator

   Zabbix Agent Simulator is a tool that acts a Zabbix agent (passive and active)
"""
import glob
import os
import sys
import setuptools

classifiers = """\
"""

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["zabbix-api>=0.5.4"]

setuptools.setup(
    name='zabbixsim',
    version='0.0.1',
    author='Adam Leggo',
    author_email='adam@leggo.id.au',
    description='Zabbix Agent simulator',
    long_description=readme,
    maintainer='Adam Leggo <adam@leggo.id.au>',
    url='https://github.com/adamleggo/zabbixsim',
    license='MIT',
    packages=setuptools.find_packages(),
    include_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring"
    ]
)
