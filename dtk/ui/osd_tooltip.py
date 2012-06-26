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

from utils import (get_widget_root_coordinate, WIDGET_POS_TOP_LEFT, remove_signal_id, unique_print)
import cairo
import gtk
import gobject

class OSDTooltip(gtk.Window):
    '''OSD tooltip.'''
	
    def __init__(self, monitor_widget, text, offset_x=0, offset_y=0,
                 text_size=None, border_color=None, border_radious=None):
        '''Init osd tooltip.'''
        # Init.
        gtk.Window.__init__(self)
        self.monitor_widget = monitor_widget
        self.text = text
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.text_size = text_size
        self.border_color = border_color
        self.border_radious = border_radious
        self.monitor_window = None
        
        # Init callback id.
        self.configure_event_callback_id = None
        
        # Init window.
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        
        # Connect signal.
        self.connect("expose-event", self.expose_osd_tooltip)
        
    def expose_osd_tooltip(self, widget, event):
        '''Expose osd tooltip.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Clear color to transparent window.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        
        cr.set_source_rgba(1, 0, 0, 0.5)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
    def show(self):
        '''Show.'''
        (monitor_x, monitor_y) = get_widget_root_coordinate(self.monitor_widget, WIDGET_POS_TOP_LEFT)
        self.move(monitor_x + self.offset_x, monitor_y + self.offset_y)
        
        self.monitor_window = self.monitor_widget.get_toplevel()
        handler_id = self.monitor_window.connect("configure-event", lambda w, e: self.hide_immediately())
        self.configure_event_callback_id = (self.monitor_window, handler_id)
        
        self.show_all()
        
    def hide(self):
        '''Hide.'''
        pass
    
    def hide_immediately(self):
        '''Hide immediately.'''
        unique_print("Hide immediately")
        
        remove_signal_id(self.configure_event_callback_id)
        
        self.hide_all()
        
gobject.type_register(OSDTooltip)
