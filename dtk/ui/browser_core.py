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

browser_core_path = os.path.realpath(__file__)

class BrowserCore(Gtk.Plug):
    '''Browser core.'''
	
    def __init__(self, uri, socket_id, cookie_file):
        '''Init browser core.'''
        Gtk.Plug.__init__(self)
        print socket_id
        self.uri = uri
        self.socket_id = socket_id
        self.cookie_file = cookie_file
        self.construct(self.socket_id)
        
        self.view = WebKit.WebView()
        self.session = WebKit.get_default_session()
        self.cookie = Soup.CookieJarText.new(cookie_file, False)
        self.session.add_feature(self.cookie)
        
        self.view.load_uri(self.uri)

        self.add(self.view)
        self.connect("delete-event", Gtk.main_quit)
        
if __name__ == "__main__":
    Gdk.threads_init()
    BrowserCore(sys.argv[1], int(sys.argv[2]), sys.argv[3]).show_all()
    Gtk.main()
    print "********************"
