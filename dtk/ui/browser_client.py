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

from scrolled_window import ScrolledWindow
import dbus
import dbus.service
import gtk
import os
import subprocess

class BrowserClientService(dbus.service.Object):
    def __init__(self, client_hash, callbacks, app_bus_name, app_dbus_name):
        # Init.
        self.client_hash = client_hash
        self.callbacks = callbacks
        self.app_object_name = "/com/deepin/browserclient/%s" % self.client_hash
        dbus.service.Object.__init__(self, app_bus_name, self.app_object_name)
        
        # Define DBus method.
        def dbus_callback_wrap(self, name, args):
            if self.callbacks.has_key(name):
                self.callbacks[name](args)
            else:
                print "Don't know how to handle callback: %s" % name
            
        # Below code export dbus method dyanmically.
        # Don't use @dbus.service.method !
        setattr(BrowserClientService, 
                "deepin_browser_client_%s" % self.client_hash,
                dbus.service.method(app_dbus_name, "ss")(dbus_callback_wrap))
        
class BrowserClient(ScrolledWindow):
    '''Browser client.'''
	
    def __init__(self, uri, cookie_file, app_bus_name, app_dbus_name):
        '''Browser client.'''
        # Init.
        ScrolledWindow.__init__(self)
        self.client_hash = self.__hash__()
        self.app_bus_name = app_bus_name
        self.app_dbus_name = app_dbus_name

        self.uri = uri
        self.cookie_file = cookie_file
        
        self.connect("realize", self.realize_browser_client)
        
    def realize_browser_client(self, widget):
        '''Callback for `realize` signal.'''
        # Build dbus service.
        BrowserClientService(
            self.client_hash, 
            {'init_size' : self.init_size,
             'init_plug' : self.init_plug
             },
            self.app_bus_name,
            self.app_dbus_name)
        
        # Open browser core process.
        subprocess.Popen(["python", 
                          os.path.join(os.path.dirname(os.path.realpath(__file__)), "browser_core.py"),
                          self.uri, str(self.client_hash), self.cookie_file, self.app_dbus_name])
        
    def init_size(self, args):
        '''Resize web view.'''
        # Init.
        (width, height) = eval(args) 
        vadjust = self.get_vadjustment()
        hadjust = self.get_hadjustment()
        
        # Adjust upper value.
        hadjust.set_upper(width)
        vadjust.set_upper(height)
        
        # Adjust init value.
        hadjust.set_value(0)
        vadjust.set_value(0)

    def init_plug(self, args):
        '''Init plug widget.'''
        # Extract plug id.
        plug_id = eval(args)
        
        # Add plug to socket.
        # 
        # NOTICIE: 
        # 
        # You must get plug_id in subprocess and send back to parent process,
        # otherwise you will got 'BadWindow' error when socket widget haven't ready complete.
        # 
        # You must create socket widget and add in container after receive plug id.
        # otherwise you will got error "gtk_socket_add_id: GTK_WIDGET_ANCHORED (socket) failed".
        # 
        self.socket = gtk.Socket()
        self.socket.show()      # must show before add to container
        self.add_child(self.socket)
        self.socket.add_id(plug_id)

        # Show socket widget.
        self.show_all()
