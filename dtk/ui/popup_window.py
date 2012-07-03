#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 QiuHailong
# 
# Author:     QiuHailong <qiuhailong@linuxdeepin.com>
# Maintainer: QiuHailong <qiuhailong@linuxdeepin.com>
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
from titlebar import Titlebar
from utils import move_window
from window import Window
import gobject
import gtk

class PopupWindow(Window):
    '''PopupWindow.'''
	
    def __init__(self, parent_widget=None, widget=None, x=None, y=None):
        '''Init PopupWindow.'''        
        Window.__init__(self)
        
        # Init Window.
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_modal(True)
        self.set_size_request(200,300)
        
        self.main_box = gtk.VBox()
        self.titlebar = Titlebar(["close"])
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        self.scrolled_align  = gtk.Alignment()
        self.scrolled_align.set(0.0, 0.0, 1.0, 1.0)
        self.scrolled_window = ScrolledWindow(gtk.POLICY_NEVER)
        self.scrolled_align.add(self.scrolled_window)
        self.scrolled_align.set_padding(10, 10, 10, 10)
        
        if widget:
            self.scrolled_window.add_child(widget)
        else:
            self.buffer = gtk.TextBuffer()
            self.text_view = gtk.TextView(self.buffer)
            self.buffer.set_text("Linux Deepin")
            self.scrolled_window.add_child(self.text_view)
            
        if x and y:
            self.move(x, y)
            
        self.titlebar.drag_box.connect('button-press-event', lambda w, e: move_window(w, e, self))
            
        if parent_widget:
            self.connect("show", lambda w:self.show_window(w, parent_widget))
            
        self.main_box = gtk.VBox()
        self.main_box.pack_start(self.titlebar, False, False)
        self.main_box.pack_start(self.scrolled_align, True, True)
        
        self.window_frame.add(self.main_box)
        
        self.show_all()

    def show_window(self, widget, parent_widget):
        '''Show window'''
        parent_rect = parent_widget.get_toplevel().get_allocation()
        widget.move(parent_rect.x + parent_rect.width/2, parent_rect.y + parent_rect.height/2)
        
gobject.type_register(PopupWindow)
