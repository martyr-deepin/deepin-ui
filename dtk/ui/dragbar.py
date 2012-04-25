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

from box import EventBox
from draw import draw_pixbuf
from theme import ui_theme
from utils import set_hover_cursor, propagate_expose, resize_window
import cairo
import gobject
import gtk

class Dragbar(gtk.Window):
    '''Drag bar.'''
	
    def __init__(self, resize_window, monitor_wiget, offset_x=4, offset_y=4):
        '''Init drag bar.'''
        # Init.
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.resize_window = resize_window
        self.monitor_wiget = monitor_wiget
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.set_decorated(False)
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.set_resizable(False)
        self.set_transient_for(resize_window)
        
        # Follow monitor widget.
        resize_window.connect("configure-event", lambda w, e: self.adjust_position())
        resize_window.connect("size-allocate", lambda w, a: self.adjust_position())
        
        # Set size.
        drag_pixbuf = ui_theme.get_pixbuf("drag.png").get_pixbuf()
        self.set_size_request(drag_pixbuf.get_width(), drag_pixbuf.get_height())
        
        # Init drag bar.
        self.drag_box = EventBox()
        self.drag_box.connect("expose-event", self.expose_drag_box)
        self.drag_box.connect("button-press-event", self.drag)
        self.add(self.drag_box)
        set_hover_cursor(self.drag_box, gtk.gdk.BOTTOM_RIGHT_CORNER)
        
        # Show.
        self.show_all()
        
    def adjust_position(self):
        '''Adjust drag bar position.'''
        if self.resize_window.get_window() != None:
            # Init.
            (window_x, window_y) = self.resize_window.get_window().get_root_origin()
            monitor_wiget_rect = self.monitor_wiget.get_allocation()
            
            # Get monitor widget's coordinate.
            drag_pixbuf = ui_theme.get_pixbuf("drag.png").get_pixbuf()
            x = window_x + monitor_wiget_rect.x + monitor_wiget_rect.width - drag_pixbuf.get_width() - self.offset_x
            y = window_y + monitor_wiget_rect.y + monitor_wiget_rect.height - drag_pixbuf.get_height() - self.offset_y
            
            # Move drag bar position.
            self.move(x, y)
        
    def expose_drag_box(self, widget, event):
        '''Expose drag box.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        pixbuf = ui_theme.get_pixbuf("drag.png").get_pixbuf()
        
        # Clear color to transparent.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
    
        # Draw drag bar.
        draw_pixbuf(cr, pixbuf, rect.x, rect.y)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def drag(self, widget, event):
        '''Drag event.'''
        resize_window(widget, event, self.resize_window, gtk.gdk.WINDOW_EDGE_SOUTH_EAST)

gobject.type_register(Dragbar)
