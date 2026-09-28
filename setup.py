#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from distutils.core import setup
from DistUtilsExtra.command import *

setup(name='unity-scope-virtualbox',
      version='0.1',
      author='David Callé',
      author_email='davidc@framli.eu',
      url='http://launchpad.net/ubuntu-scopes',
      license='GNU General Public License (GPL)',
      data_files=[
    ('share/dbus-1/services', ['data/unity-scope-virtualbox.service']),
    ('share/unity-scopes/virtualbox', ['src/unity_virtualbox_daemon.py']),
    ('share/unity-scopes/virtualbox', ['src/__init__.py']),
    ], cmdclass={'build':  build_extra.build_extra,
                 'build_i18n': build_i18n.build_i18n,})
