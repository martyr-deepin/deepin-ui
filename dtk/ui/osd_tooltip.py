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

from draw import draw_text
from utils import (get_widget_root_coordinate, WIDGET_POS_TOP_LEFT, 
                   remove_signal_id, remove_timeout_id, get_content_size)
import cairo
import gtk
import gobject
from theme import ui_theme
from animation import Animation

class OSDTooltip(gtk.Window):
    '''OSD tooltip.'''
	
    def __init__(self, monitor_widget, text_size=18, window_type=gtk.WINDOW_TOPLEVEL, offset_x=0, offset_y=0,
                 text_color=ui_theme.get_color("osdTooltipText"), 
                 border_color=ui_theme.get_color("osdTooltipBorder"), 
                 border_radious=1):
        '''Init osd tooltip.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        self.monitor_widget = monitor_widget
        self.text = ""
        self.text_size = text_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.text_color = text_color
        self.border_color = border_color
        self.border_radious = border_radious
        self.monitor_window = None
        self.monitor_window_x = None
        self.monitor_window_y = None
        self.monitor_window_width = None
        self.monitor_window_height = None
        self.start_hide_delay = 5000 # milliseconds
        self.hide_time = 500         # milliseconds
        
        # Init callback id.
        self.configure_event_callback_id = None
        self.start_hide_callback_id = None
        
        # Init window.
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_accept_focus(False) # make Alt+Space menu can't response
        
        # Connect signal.
        self.connect("expose-event", self.expose_osd_tooltip)
        self.connect("realize", self.realize_osd_tooltip)
        self.connect("show", self.show_osd_tooltip)
        
    def realize_osd_tooltip(self, widget):
        '''Realize osd tooltip.'''
        # Make all event passthrough osd tooltip.
        self.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0) 
        
        # Never draw background.
        self.window.set_back_pixmap(None, False)
        
    def show_osd_tooltip(self, widget):
        '''Show osd tooltip.'''
        self.move(self.tooltip_x, self.tooltip_y)
        self.resize(self.tooltip_width, self.tooltip_height)
        
    def expose_osd_tooltip(self, widget, event):
        '''Expose osd tooltip.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Clear color to transparent window.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        
        # Draw font.
        draw_text(cr, self.text, 
                  rect.x, rect.y, rect.width, rect.height,
                  self.text_size,
                  self.text_color.get_color(),
                  border_radious=self.border_radious,
                  border_color=self.border_color.get_color())
        
        return True
        
    def show(self, text):
        '''Show.'''
        # Remove callback.
        remove_signal_id(self.configure_event_callback_id)
        remove_timeout_id(self.start_hide_callback_id)
        
        # Update text.
        self.text = text
        
        # Get tooltip size.
        (self.tooltip_width, self.tooltip_height) = get_content_size(self.text, self.text_size + self.border_radious * 2)
        
        # Move tooltip to given position.
        (monitor_x, monitor_y) = get_widget_root_coordinate(self.monitor_widget, WIDGET_POS_TOP_LEFT)
        self.tooltip_x = monitor_x + self.offset_x
        self.tooltip_y = monitor_y + self.offset_y
        
        # Monitor configure-event signal.
        self.monitor_window = self.monitor_widget.get_toplevel()
        handler_id = self.monitor_window.connect("configure-event", self.handle_configure_event)
        self.configure_event_callback_id = (self.monitor_window, handler_id)
        
        # Save monitor window position.
        rect = self.monitor_window.allocation
        (monitor_window_x, monitor_window_y) = self.monitor_window.window.get_origin()
        monitor_window_width, monitor_window_height = rect.width, rect.height
        self.monitor_window_x = monitor_window_x
        self.monitor_window_y = monitor_window_y
        self.monitor_window_width = monitor_window_width
        self.monitor_window_height = monitor_window_height
        
        # Show.
        self.set_opacity(1)
        self.show_all()
        
        self.start_hide_callback_id = gobject.timeout_add(
            self.start_hide_delay, 
            lambda : Animation(self, "opacity", self.hide_time, [1, 0],
                           stop_callback=self.hide_immediately).start())
        
        self.queue_draw()
    
    def hide_immediately(self):
        '''Hide immediately.'''
        # Remove callback.
        remove_signal_id(self.configure_event_callback_id)
        remove_timeout_id(self.start_hide_callback_id)
        
        self.hide_all()
        
    def handle_configure_event(self, widget, event):
        '''Handle configure event.'''
        # Init.
        rect = widget.allocation
        (monitor_window_x, monitor_window_y) = widget.window.get_origin()
        monitor_window_width, monitor_window_height = rect.width, rect.height
        
        if (self.monitor_window_x != monitor_window_x 
            or self.monitor_window_y != monitor_window_y
            or self.monitor_window_width != monitor_window_width
            or self.monitor_window_height != monitor_window_height):
            
            self.monitor_window_x = monitor_window_x
            self.monitor_window_y = monitor_window_y
            self.monitor_window_width = monitor_window_width
            self.monitor_window_height = monitor_window_height
            
            self.hide_immediately()
        
gobject.type_register(OSDTooltip)
