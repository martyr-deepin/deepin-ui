#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import dbus
import sys
from network_state import *

if sys.version_info >= (3,0):
    basestring = str

class NMDbusInterface(object):
    bus = dbus.SystemBus()
    dbus_service = 'org.freedesktop.NetworkManager'
    object_path = None

    def __init__(self, object_path=None):
        if isinstance(object_path, NMDbusInterface):
            object_path = object_path.object_path
        self.object_path = self.object_path or object_path
        self.proxy = self.bus.get_object(self.dbus_service, self.object_path)
        self.interface = dbus.Interface(self.proxy, self.interface_name)

        properties = []
        try:
            properties = self.proxy.GetAll(self.interface_name,
                                           dbus_interface='org.freedesktop.DBus.Properties')
        except dbus.exceptions.DBusException as e:
            if e.get_dbus_name() != 'org.freedesktop.DBus.Error.UnknownMethod':
                raise
        for p in properties:
            p = str(p)
            if not hasattr(self.__class__, p):
                setattr(self.__class__, p, self._make_property(p))

    def _make_property(self, name):
        def get(self):
            return self.unwrap(self.proxy.Get(self.interface_name, name,
                                  dbus_interface='org.freedesktop.DBus.Properties'))
        def set(self, value):
            return self.proxy.Set(self.interface_name, name, self.wrap(value),
                                  dbus_interface='org.freedesktop.DBus.Properties')
        return property(get, set)

    def unwrap(self, val):
        if isinstance(val, dbus.ByteArray):
            return "".join([str(x) for x in val])
        if isinstance(val, (dbus.Array, list, tuple)):
            return [self.unwrap(x) for x in val]
        if isinstance(val, (dbus.Dictionary, dict)):
            return dict([(self.unwrap(x), self.unwrap(y)) for x,y in val.items()])
        if isinstance(val, dbus.ObjectPath):
            if val.startswith('/org/freedesktop/NetworkManager/'):
                classname = val.split('/')[4]
                classname = {
                   'Settings': 'Connection',
                   'Devices': 'Device',
                }.get(classname, classname)
                return globals()[classname](val)
        if isinstance(val, (dbus.Signature, dbus.String)):
            return str(val)
        if isinstance(val, dbus.Boolean):
            return bool(val)
        if isinstance(val, (dbus.Int16, dbus.UInt16, dbus.Int32, dbus.UInt32, dbus.Int64, dbus.UInt64)):
            return int(val)
        return val
    
    def wrap(self, val):
        if isinstance(val, NMDbusInterface):
            return val.object_path
        if hasattr(val, '__iter__') and not isinstance(val, basestring):
            if hasattr(val, 'items'):
                return dict([(x, self.wrap(y)) for x, y in val.items()])
            else:
                return [self.wrap(x) for x in val]
        return val

    def  __getattr__(self, name):
        try:
            return super(NMDbusInterface, self).__getattribute__(name)
        except AttributeError:
            def proxy_call(*args, **kwargs):
                func = getattr(self.interface, name)
                args = self.wrap(args)
                kwargs = self.wrap(kwargs)
                ret = func(*args, **kwargs)
                return self.unwrap(ret)
            return proxy_call

    def connect_to_signal(self, signal, handler, *args, **kwargs):
        def helper(*args, **kwargs):
            args = [self.unwrap(x) for x in args]
            handler(*args, **kwargs)
        args = self.wrap(args)
        kwargs = self.wrap(kwargs)
        return self.proxy.connect_to_signal(signal, helper, *args, **kwargs)

class NetworkManager(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager'
    object_path = '/org/freedesktop/NetworkManager'
NetworkManager = NetworkManager()

class Settings(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Settings'
    object_path = '/org/freedesktop/NetworkManager/Settings'
Settings = Settings()

class Connection(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Settings.Connection'

class ActiveConnection(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Connection.Active'

class Device(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device'

    def SpecificDevice(self):
        return {
            NM_DEVICE_TYPE_ETHERNET: Wired,
            NM_DEVICE_TYPE_WIFI: Wireless,
            NM_DEVICE_TYPE_BT: Bluetooth,
            NM_DEVICE_TYPE_OLPC_MESH: OlpcMesh,
            NM_DEVICE_TYPE_WIMAX: Wimax,
            NM_DEVICE_TYPE_MODEM: Modem,
        }[self.DeviceType](self.object_path)

class AccessPoint(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.AccessPoint'

class Wired(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.Wired'

class Wireless(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.Wireless'

class Modem(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.Modem'

class Bluetooth(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.Bluetooth'

class Wimax(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.Wimax'

class OlpcMesh(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.Device.OlpcMesh'

class IP4Config(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.IP4Config'

class IP6Config(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.IP6Config'

class VPNConnection(NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.VPN.Connection'


def const(prefix, val):
    prefix = 'NM_' + prefix.upper() + '_'
    for key, vval in globals().items():
        if 'REASON' in key and 'REASON' not in prefix:
            continue
        if key.startswith(prefix) and val == vval:
            return key.replace(prefix,'').lower()
    raise ValueError("No constant found for %s* with value %d", (prefix, val))

def is_connected():
    '''Is connected.'''
    return NetworkManager.Enable and NetworkManager.State in [NM_STATE_CONNECTED_LOCAL, NM_STATE_CONNECTED_SITE, NM_STATE_CONNECTED_GLOBAL]

if __name__ == "__main__":
    print NetworkManager.State
