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
import gobject
from window import Window
from titlebar import Titlebar
from button import Button

class HSV(gtk.ColorSelection):
    '''HSV.'''
	
    def __init__(self):
        '''Init color selection.'''
        gtk.ColorSelection.__init__(self)
        
        # Remove right buttons.
        self.get_children()[0].remove(self.get_children()[0].get_children()[1])
        
        # Remove bottom color pick button.
        self.get_children()[0].get_children()[0].remove(self.get_children()[0].get_children()[0].get_children()[1])

gobject.type_register(HSV)

class ColorSelectDialog(Window):
    '''Color select dialog.'''
	
    def __init__(self, confirm_callback=None, cancel_callback=None):
        '''Init color select dialog.'''
        Window.__init__(self)
        self.set_modal(True)                                # grab focus to avoid build too many skin window
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_skip_taskbar_hint(True)                    # skip taskbar
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.titlebar = Titlebar(["close"], None, None, "颜色选择")
        self.add_move_event(self.titlebar)
        
        self.color_box = gtk.HBox()
        self.color_hsv = HSV()
        self.color_box.pack_start(self.color_hsv, False, False)
        
        self.color_right_box = gtk.VBox()
        self.color_info_box = gtk.HBox()
        self.color_rgb_box = gtk.VBox()
        
        self.confirm_button = Button("确定")
        self.cancel_button = Button("取消")
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 5, 5)
        self.button_box = gtk.HBox()
        
        self.button_align.add(self.button_box)        
        self.button_box.pack_start(self.confirm_button, False, False, 5)
        self.button_box.pack_start(self.cancel_button, False, False, 5)
        
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.color_box, False, False)
        self.window_frame.pack_start(self.button_align, False, False)
        
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        self.connect("destroy", lambda w: self.destroy())
        
    def click_confirm_button(self):
        '''Click confirm button.'''
        if self.confirm_callback != None:
            self.confirm_callback()        
        
        self.destroy()
        
    def click_cancel_button(self):
        '''Click cancel button.'''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.destroy()
        
gobject.type_register(ColorSelectDialog)
