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

import gtk
import os
from utils import *
from scrolled_window import *

class BrowserClient(ScrolledWindow):
    '''Browser client.'''
	
    def __init__(self, uri, cookie_file):
        '''Browser client.'''
        # Init.
        ScrolledWindow.__init__(self)

        self.socket = gtk.Socket()
        self.uri = uri
        self.cookie_file = cookie_file
        
        self.add_child(self.socket)
        
        self.socket.connect("realize", self.realize_browser_client)
        
    def realize_browser_client(self, widget):
        '''Callback for `realize` signal.'''
        # Connect browser core.
        self.socket_id = int(self.socket.get_id())
        subprocess.Popen(["python", 
                          os.path.join(os.path.dirname(os.path.realpath(__file__)), "browser_core.py"),
                          self.uri, str(self.socket_id), self.cookie_file])        
        
