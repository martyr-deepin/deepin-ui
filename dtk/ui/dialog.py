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
from label import Label
from button import Button
from constant import ALIGN_MIDDLE

class ConfirmDialog(Window):
    '''Confir dialog.'''
	
    def __init__(self, 
                 title, 
                 message, 
                 default_width,
                 default_height,
                 confirm_callback=None, 
                 cancel_callback=None):
        '''Init confirm dialog.'''
        # Init.
        Window.__init__(self)
        self.default_width = default_width
        self.default_height = default_height
        self.set_default_size(self.default_width, self.default_height)
        self.set_geometry_hints(None, self.default_width, self.default_height, -1, -1, -1, -1, -1, -1, -1, -1)
        
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            title)
        
        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 1, 1)
        self.label_align.set_padding(0, 0, 10, 10)
        self.label = Label(message, text_x_align=ALIGN_MIDDLE)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 5, 5)
        self.button_box = gtk.HBox()
        
        self.confirm_button = Button("确认")
        self.cancel_button = Button("取消")
        
        # Connect widgets.
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.label_align, True, True)
        self.window_frame.pack_start(self.button_align, False, False)
        
        self.label_align.add(self.label)
        
        self.button_align.add(self.button_box)        
        self.button_box.pack_start(self.confirm_button, False, False, 5)
        self.button_box.pack_start(self.cancel_button, False, False, 5)
        
        # Add move action.
        self.add_move_event(self.titlebar)
        
gobject.type_register(ConfirmDialog)

if __name__ == '__main__':
    dialog = ConfirmDialog("确认对话框", "你确定吗？", 200, 100)
    dialog.show_all()
    
    gtk.main()
