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

class BrowserCore(Gtk.Plug):
    '''Browser core.'''
	
    def __init__(self, uri, socket_id, cookie_file):
        '''Init browser core.'''
        # Init.
        Gtk.Plug.__init__(self)
        print socket_id
        self.uri = uri
        self.socket_id = socket_id
        self.cookie_file = cookie_file
        self.construct(self.socket_id)
        
        # Build web view.
        self.view = WebKit.WebView()
        self.session = WebKit.get_default_session()
        self.cookie = Soup.CookieJarText.new(cookie_file, False)
        self.session.add_feature(self.cookie)
        self.view.load_uri(self.uri)
        self.add(self.view)
        
        # Handle signal.
        self.connect("delete-event", Gtk.main_quit)
        self.view.connect("load-finished", self.load_finished_browser_core)
        
    def execute_script(self, script):
        '''Execute script.'''
        self.view.execute_script('oldtitle=document.title;%s' % script)
        result = self.view.get_main_frame().get_title()
        self.view.execute_script('document.title=oldtitle;')
        
        return result
        
    def load_finished_browser_core(self, view, frame):
        '''Callback for `load-finished` signal.'''
        width = int(self.execute_script("document.title=document.body.offsetWidth;"))
        height = int(self.execute_script("document.title=document.body.offsetHeight;"))
        
        self.view.set_size_request(width, height)
        
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        self.app_dbus_name = "com.deepin.browserclient%s" % self.socket_id
        self.app_service_name = "com.deepin.browserclient%s" % self.socket_id
        self.app_object_name = "/com/deepin/browserclient/%s" % self.socket_id
        if bus.request_name(self.app_dbus_name) != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            # Call 'show_window` method when have exist instance.
            method = bus.get_object(
                self.app_service_name, 
                self.app_object_name).get_dbus_method('deepin_browser_client_%s' % self.socket_id)
            method("init-size", (width, height))
        
if __name__ == "__main__":
    Gdk.threads_init()
    BrowserCore(sys.argv[1], int(sys.argv[2]), sys.argv[3]).show_all()
    Gtk.main()
    print "********************"
