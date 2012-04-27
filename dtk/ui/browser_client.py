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
from utils import container_remove_all
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
        self.app_object_name = "/com/deepin/browser_client/%s" % self.client_hash
        dbus.service.Object.__init__(self, app_bus_name, self.app_object_name)
        
        # Define DBus method.
        def dbus_callback_wrap(self, name, args):
            if self.callbacks.has_key(name):
                self.callbacks[name](args)
            else:
                print "BrowserClientService, Don't know how to handle callback: %s" % name
            
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
        self.plug_id = None
        self.hadjust_value_histroy = 0
        self.vadjust_value_history = 0
        self.hadjust_upper_history = 0
        self.vadjust_upper_history = 0
        self.app_bus_name = app_bus_name
        self.app_dbus_name = app_dbus_name
        self.exit_signal_id = None

        self.uri = uri
        self.cookie_file = cookie_file
        
        self.connect("realize", self.realize_browser_client)
        
    def realize_browser_client(self, widget):
        '''Callback for `realize` signal.'''
        if self.plug_id == None:
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
        else:
            self.insert_plug(self.plug_id)
            
    def init_size(self, args):
        '''Resize web view.'''
        # Init.
        (width, height) = eval(args) 
        
        # Adjust viewport size.
        self.socket.set_size_request(width, height)
        
        # Get adjustment.
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
        self.insert_plug(eval(args))
        
    def insert_plug(self, plug_id):
        '''Insert plug.'''
        self.plug_id = plug_id
        
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
        container_remove_all(self)
        self.socket = gtk.Socket()
        self.socket.show()      # must show before add to container
        self.add_child(self.socket)
        self.socket.add_id(self.plug_id)
        
        # Save value of adjustment when socket remove from container.
        self.socket.connect("hierarchy-changed", self.save_adjust_value)
        
        # Reset vadjust value.
        self.get_vadjustment().set_upper(self.vadjust_upper_history)
        self.get_hadjustment().set_upper(self.hadjust_upper_history)
        self.get_vadjustment().set_value(self.vadjust_value_history)
        self.get_hadjustment().set_value(self.hadjust_value_histroy)
        
        # Show.
        self.show_all()
        
        # Exit browser core when browser client destroy.
        if self.exit_signal_id == None and self.plug_id:
            self.exit_signal_id = self.connect("destroy", self.browser_client_exit_core)
            
    def browser_client_exit_core(self, widget):
        '''Send 'exit' signal to core process.'''
        bus = dbus.SessionBus()
        browser_core_dbus_name = "com.deepin.browser_core_%s" % self.plug_id
        browser_core_object_name = "/com/deepin/browser_core/%s" % self.plug_id
        if bus.request_name(browser_core_dbus_name) != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            method = bus.get_object(
                browser_core_dbus_name,
                browser_core_object_name).get_dbus_method('deepin_browser_core_%s' % self.plug_id)
            method("exit", "")
            
        print "Send exit signal to webkit subprocess."
        
    def save_adjust_value(self, widget, previous_toplevel):
        '''Save value of adjustment.'''
        # Save value.
        self.vadjust_upper_history = self.get_vadjustment().get_upper()
        self.hadjust_upper_history = self.get_hadjustment().get_upper()
        self.vadjust_value_history = self.get_vadjustment().get_value()
        self.hadjust_value_histroy = self.get_hadjustment().get_value()
        
        # Remove socket widget.
        container_remove_all(self)
