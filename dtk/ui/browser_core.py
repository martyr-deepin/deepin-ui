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

from gi.repository import WebKit
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Soup
import sys
import os
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

browser_core_path = os.path.realpath(__file__)

class BrowserCoreService(dbus.service.Object):
    '''Browser core service.'''
	
    def __init__(self, plug_id, callbacks):
        '''Init browser core service.'''
        # Init.
        self.plug_id = plug_id
        self.callbacks = callbacks
        self.browser_core_dbus_name = "com.deepin.browser_core_%s" % self.plug_id
        self.browser_core_object_name = "/com/deepin/browser_core/%s" % self.plug_id
        self.browser_core_bus_name = dbus.service.BusName(self.browser_core_dbus_name, bus=dbus.SessionBus())
        dbus.service.Object.__init__(
            self, 
            self.browser_core_bus_name,
            self.browser_core_object_name)
        
        # Define DBus method.
        def dbus_callback_wrap(self, name, args):
            if self.callbacks.has_key(name):
                self.callbacks[name](args)
            else:
                print "BrowserCoreService, Don't know how to handle callback: %s" % name
                
        # Below code export dbus method dyanmically.
        # Don't use @dbus.service.method !
        setattr(BrowserCoreService, 
                "deepin_browser_core_%s" % self.plug_id,
                dbus.service.method(self.browser_core_dbus_name, "ss")(dbus_callback_wrap))

class BrowserCore(Gtk.Plug):
    '''Browser core.'''
	
    def __init__(self, uri, client_id, cookie_file, app_dbus_name):
        '''Init browser core.'''
        # Init.
        DBusGMainLoop(set_as_default=True) # WARING: only use once in one process
        Gtk.Plug.__init__(self)
        self.construct(0)
        self.uri = uri
        self.client_id = client_id
        self.cookie_file = cookie_file
        self.app_dbus_name = app_dbus_name
        
        # Build web view.
        self.view = WebKit.WebView()
        self.view.get_settings().set_property("enable-plugins", False) # this is binding bug that should set with `True`
        self.view.get_settings().set_property("enable-scripts", True)
        self.session = WebKit.get_default_session()
        self.cookie = Soup.CookieJarText.new(cookie_file, False)
        self.session.add_feature(self.cookie)
        self.view.load_uri(self.uri)
        self.add(self.view)
        self.view.connect("create-web-view", self.browser_core_open_link)
        
        # Handle signal.
        self.connect("realize", self.realize_browser_core)
        self.connect("delete-event", self.recevie_delete_event)
        self.view.connect("load-finished", self.browser_core_load_finished)
        self.view.connect("notify::load-status", self.browser_core_load_status)
        self.view.connect("load-error", self.browser_core_load_error)
        
        # Build service.
        BrowserCoreService(
            self.get_id(), 
            {"exit" : self.browser_core_exit}
            )
        
    def browser_core_open_link(self, view, frame):
        '''Open link when request new window.'''
        # Return current view to open link in current view.
        return self.view
                
    def browser_core_exit(self, args):
        '''Exit browser core progress.'''
        Gtk.main_quit()
        
    def recevie_delete_event(self, widget, event):
        '''Receive delete event.'''
        print "Receive delete-event."
        
        return True
        
    def realize_browser_core(self, widget):
        '''Realize browser core.'''
        self.send_message_to_client("init_plug", str(self.get_id()))
        
    def execute_script(self, script):
        '''Execute script.'''
        self.view.execute_script('oldtitle=document.title;%s' % script)
        result = self.view.get_title()
        self.view.execute_script('document.title=oldtitle;')
        
        return result
        
    def browser_core_load_finished(self, view, frame):
        '''Callback for `load-finished` signal.'''
        try:
            # Get new width.
            width = eval(self.execute_script("document.title=document.body.offsetWidth;"))
            height = eval(self.execute_script("document.title=document.body.offsetHeight;"))
            
            # Set web view size.
            self.view.set_size_request(width, height)
            
            # Adjust scroll window's size.
            self.send_message_to_client("init_size", str((width, height)))
        except Exception, e:
            print "browser_core_load_finished got error: %s" % (e)
            
    def browser_core_load_status(self, view, status):
        '''Print status.'''
        pass
        
    def browser_core_load_error(self, *error):
        '''Print error.'''
        print error
        
    def send_message_to_client(self, method_name, method_args):
        '''Send message to browser client.'''
        bus = dbus.SessionBus()
        self.app_object_name = "/com/deepin/browser_client/%s" % self.client_id
        if bus.request_name(self.app_dbus_name) != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            method = bus.get_object(
                self.app_dbus_name, 
                self.app_object_name).get_dbus_method('deepin_browser_client_%s' % self.client_id)
            method(method_name, method_args)
        
if __name__ == "__main__":
    Gdk.threads_init()
    BrowserCore(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]).show_all()
    Gtk.main()
    print "Exit from webkit subprocess."
