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
from box import EventBox
from utils import container_remove_all, get_content_size
from constant import DEFAULT_FONT_SIZE
from scrolled_window import ScrolledWindow

class TabBox(gtk.VBox):
    '''Tab box.'''
	
    def __init__(self):
        '''Init tab box.'''
        # Init.
        gtk.VBox.__init__(self)
        self.tab_height = 29
        self.tab_padding_x = 19
        self.tab_padding_y = 9
        self.tab_frame_color = "#D6D6D6"
        
        self.tab_title_box = EventBox()
        self.tab_title_box.set_size_request(-1, self.tab_height)
        self.tab_content_align = gtk.Alignment()
        self.tab_content_align.set(0.0, 0.0, 0.0, 0.0)
        self.tab_content_align.set_padding(0, 1, 1, 1)
        self.tab_content_scrolled_window = ScrolledWindow()
        self.tab_content_align.add(self.tab_content_scrolled_window)
        
        self.tab_items = []
        self.tab_title_widths = []
        self.tab_index = 0
        
        self.pack_start(self.tab_title_box, False, False)
        self.pack_start(self.tab_content_align, True, True)
        
        self.tab_title_box.connect("button-press-event", self.press_tab_title_box)
        self.tab_title_box.connect("expose-event", self.expose_tab_title_box)
        self.tab_content_box.connect("expose-event", self.expose_tab_content_box)
        
    def add_items(self, items, default_index=0):
        '''Add items.'''
        self.tab_items += items
        
        for item in items:
            self.tab_title_widths.append(get_content_size(item[0], DEFAULT_FONT_SIZE) + self.padding_x * 2)
        
        self.select_page(default_index)
        
    def select_page(self, index):
        '''Select page.'''
        if 0 <= index < len(self.items):
            self.tab_index = index
            self.switch_content(self.tab_items[index])
            self.queue_draw()    
    
    def switch_content(self, widget):
        '''Switch content.'''
        container_remove_all(self.tab_content_scrolled_window)            
        self.tab_content_scrolled_window.add_child(widget)
        
    def press_tab_title_box(self, widget, event):
        '''Press tab title box.'''
        pass

    def expose_tab_title_box(self, widget, event):
        '''Expose tab title box.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        for (index, item) in enumerate(self.items):
            title = item[0]
            if self.tab_index == index:
                with cairo_disable_antialias(cr):
                    cr.set_source_rgb(*color_hex_to_cairo(self.tab_frame_color))
                    cr.rectangle(rect.x + sum(self.tab_title_widths[0:self.tab_index]),
                                 rect.y, 
                                 self.tab_title_widths[0], 
                                 rect.y)
                    cr.stroke()
            else:
                # Draw title frame.
                with cairo_disable_antialias(cr):
                    cr.set_source_rgb(*color_hex_to_cairo(self.tab_frame_color))
                    cr.rectangle(rect.x + sum(self.tab_title_widths[0:self.tab_index]),
                                 rect.y, 
                                 self.tab_title_widths[0], 
                                 self.tab_height)
                    cr.stroke()
    
    def expose_tab_content_box(self, widget, event):
        '''Expose tab content box.'''
        pass

gobject.type_register(TabBox)               

class TabWindow(Window):
    '''Tab window.'''
	
    def __init__(self):
        '''Init tab window.'''
        
gobject.type_register(TabWindow)               
