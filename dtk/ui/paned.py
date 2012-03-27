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
from theme import *
from box import *



class HPaned(gtk.HBox):
    '''HPand.'''
	
    def __init__(self):
        '''Init.'''
        super(HPaned, self).__init__()
        
        # Init.
        self.drag_flag = False
        self.left_child = None
        self.right_child = None
        
        self.control_button = ImageBox (ui_theme.get_pixbuf("paned/v_control.png"))
        self.control_button.connect("button-press-event", self.button_press_cb)
        self.control_button.connect("motion-notify-event", self.button_motion_cb)
        self.control_button.connect("button-release-event", self.button_release_cb)
        
        self.__left_box = gtk.VBox()
        self.__right_box = gtk.VBox()
        self.pack_start(self.__left_box)
        self.pack_start(self.control_button, False, False)
        self.pack_end(self.__right_box)
        
    def add1(self, child):    
        self.left_child = child
        self.__left_box.pack_start(child)
        
    def add2(self, child):    
        self.right_child = child
        self.__right_box.pack_start(child)
        
    def pack1(self, child, resize=False, shrink=True):
        child.set_property("resizable", resize)
        child.set_property("allow-shrink", shrink)
        self.left_child = child
        self.__left_box.pack_start(child)
        
    def pack2(self, child, resize=True, shrink=True):    
        child.set_property("resizable", resize)
        child.set_property("allow-shrink", shrink)
        self.right_child = child
        self.__right_box.pack_start(child)
        
    def button_press_cb(self, widget, event):    
        self.drag_flag = True
        
    def button_motion_cb(self, widget, event):    
        
        '''Motion notify.'''
        if self.drag_flag:
            if event.x > 0:
                rect = self.left_child.get_allocation()
                new_rect = gtk.gdk.Rectangle(int(rect.x) , int(rect.y), int(rect.width + event.x), int(rect.height))
                self.left_child.set_allocation(new_rect)
        self.queue_draw()        
        
    def button_release_cb(self, widget, event):    
        pass
        