#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Hou ShaoHui
# 
# Author:     Hou ShaoHui <houshao55@gmail.com>
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

from window import Window
from utils import get_screen_size
from new_treeview import TreeView
from constant import ALIGN_START, ALIGN_MIDDLE
import gobject
import gtk
from popup_grab_window import PopupGrabWindow, wrap_grab_window

class AbstractPoplist(Window):
    '''
    class docs
    '''
	
    def __init__(self,
                 items,
                 max_height=None,
                 shadow_visible=True,
                 shape_frame_function=None,
                 expose_frame_function=None,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 min_width=80,
                 align_size=0,
                 grab_window=None,
                 window_type=gtk.WINDOW_TOPLEVEL,
                 ):
        '''
        init docs
        '''
        # Init.
        Window.__init__(self, 
                        shadow_visible=shadow_visible,
                        window_type=window_type,
                        shape_frame_function=shape_frame_function,
                        expose_frame_function=expose_frame_function)
        self.max_height = max_height
        self.x_align = x_align
        self.y_align = y_align
        self.min_width = min_width
        self.align_size = align_size
        self.window_width = self.window_height = 0
        self.treeview_align = gtk.Alignment()
        self.treeview_align.set(0.5, 0.5, 1, 1)
        self.treeview_align.set_padding(self.align_size, self.align_size, self.align_size, self.align_size)
        self.treeview = TreeView(items,
                                 enable_highlight=False,
                                 enable_multiple_select=False,
                                 enable_drag_drop=False)
        
        # Connect widgets.
        self.treeview_align.add(self.treeview)
        self.window_frame.pack_start(self.treeview_align, True, False)
        
        self.connect("realize", self.realize_poplist)
        
        # Wrap self in poup grab window.
        if grab_window:
            wrap_grab_window(grab_window, self)
        else:
            wrap_grab_window(poplist_grab_window, self)
        
    def get_scrolledwindow(self):
        return self.treeview.scrolled_window
    
    def set_size(self, width, max_height=None, min_height=100):
        adjust_height = int(self.treeview.scrolled_window.get_vadjustment().get_upper())
        if max_height != None:
            adjust_height = min(adjust_height, max_height)
                
        if adjust_height <= 0:    
            adjust_height = min_height
        self.window_height = adjust_height    
        self.window_width = width
        
    def realize_poplist(self, widget):
        (shadow_padding_x, shadow_padding_y) = self.get_shadow_size()
        self.treeview.set_size_request(self.window_width - self.align_size * 2 - shadow_padding_x * 2,
                                       self.window_height)
        max_height = self.window_height + self.align_size * 2 + shadow_padding_x * 2
        self.set_default_size(self.window_width, max_height)
        self.set_geometry_hints(
            None,
            self.window_width,       # minimum width
            max_height,       # minimum height
            self.window_width,
            max_height,
            -1, -1, -1, -1, -1, -1
            )
        
    def show(self, (expect_x, expect_y), (offset_x, offset_y)=(0, 0)):
        (screen_width, screen_height) = get_screen_size(self)
        
        if not self.get_realized():
            self.realize()
        
        if self.x_align == ALIGN_START:
            dx = expect_x
        elif self.x_align == ALIGN_MIDDLE:
            dx = expect_x - self.window_width / 2
        else:
            dx = expect_x - self.window_width
            
        if self.y_align == ALIGN_START:
            dy = expect_y
        elif self.y_align == ALIGN_MIDDLE:
            dy = expect_y - self.window_height / 2
        else:
            dy = expect_y - self.window_height

        if expect_x + self.window_width > screen_width:
            dx = expect_x - self.window_width + offset_x
        if expect_y + self.window_height > screen_height:
            dy = expect_y - self.window_height + offset_y
            
        self.move(dx, dy)
        
        self.show_all()
                            
gobject.type_register(AbstractPoplist)        

poplist_grab_window = PopupGrabWindow(AbstractPoplist)
