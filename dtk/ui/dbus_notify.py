#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Hou ShaoHui
#
# Author:     Hou ShaoHui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
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

NOTIFICATIONS_SERVICE_NAME = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"

def check_dbus(bus, interface):
    obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    dbus_iface = dbus.Interface(obj, 'org.freedesktop.DBus')
    avail = dbus_iface.ListNames()
    return interface in avail

DEFAULT_TIMEOUT = 3

class DbusNotify(object):
    '''
    Dbus notify interface.

    @undocumented: set_icon_from_pixbuf
    @undocumented: pixbuf_to_dbus
    '''

    def __init__(self,
                 app_name,
                 icon=None,
                 timeout=None,
                 ):
        '''
        Initialize DbusNotify class.

        @param app_name: The name of application.
        @param icon: The name of icon, default is None, it will use app_name as icon name if set `icon` with None.
        @param timeout: The timeout of disappear (in seconds), default is None.
        '''
        self.app_name = app_name
        self.icon = icon or app_name
        self.summary = ""
        self.body = ""
        self.hints = {}
        self.actions = []
        self.timeout = timeout or DEFAULT_TIMEOUT

    def set_summary(self, summary):
        '''
        Set summary of notify message.

        @param summary: Summary string.
        '''
        self.summary = summary

    def set_body(self, body):
        '''
        Set body of notify message.

        @param body: Body string.
        '''
        self.body = body

    def set_icon_from_pixbuf(self, pixbuf):
        pass

    def pixbuf_to_dbus(self, pixbuf):
        pass

    def set_icon_from_path(self, image_path):
        '''
        Set icon file path.

        @param image_path: The filepath of image.
        '''
        self.hints["image-path"] = image_path

    def notify(self):
        '''
        Call notifications dbus service to display notify message.
        '''
        bus = dbus.SessionBus()
        # if not check_dbus(bus, NOTIFICATIONS_SERVICE_NAME):
        #     return False
        try:

            proxy = bus.get_object(NOTIFICATIONS_SERVICE_NAME,
                                   NOTIFICATIONS_PATH)
            notify_interface = dbus.Interface(proxy, NOTIFICATIONS_SERVICE_NAME)
            notify_interface.Notify(self.app_name, 0, self.icon, self.summary, self.body,
                                    self.actions, self.hints, self.timeout)
        except:
            pass
