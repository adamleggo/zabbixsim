#
# This file is part of zabbixsim software.
#
# Copyright (c) 2021, Adam Leggo <adam@leggo.id.au>
# License: https://github.com/adamleggo/zabbixsim/blob/main/LICENSE
#
"""Zabbix Agent simulator

   Zabbix Agent Simulator is a tool that acts a Zabbix agent (active)
"""
import setuptools

with open("README.md", "r", encoding="utf8") as readme_file:
    readme = readme_file.read()

setuptools.setup(
    name='zabbixsim',
    version='0.2.1',
    author='Adam Leggo',
    author_email='adam@leggo.id.au',
    description='Zabbix Agent simulator',
    long_description=readme,
    maintainer='Adam Leggo <adam@leggo.id.au>',
    url='https://github.com/adamleggo/zabbixsim',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=['zabbix-api>=0.5.4', 'pyyaml'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring"
    ],
    entry_points={
        'console_scripts': [
            'zabbixrec = zabbixsim.zabbixrec:main',
            'zabbixsim = zabbixsim.zabbixsim:main'
        ]
     }
)
