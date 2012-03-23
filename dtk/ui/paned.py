#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Hou Shaohui
# 
# Author:     Wang Yong <manatee.lazycat@gmail.com>
#             Hou ShaoHui <houshao55@gmail.com>
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

import gtk
import cairo


class HPaned(gtk.HPaned):
    
    def __init__(self, *args):
        
        super(HPaned, self).__init__(*args)
        self.connect("button-press-event", self.hpaned_press_cb)
        
    def self.hpaned_press_cb(self, widget, event):    
        if len(widget.get_children()) == 2:
            if widget.get_child1.get_visible():
                widget.get_child1().hide_all()
            else:    
                widget.get_child1().show_all()
            

        

        
        
        