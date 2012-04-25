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

from constant import BACKGROUND_IMAGE
from draw import draw_pixbuf, draw_vlinear
from theme import ui_theme
from utils import cairo_state, alpha_color_hex_to_cairo
import gobject
import gtk

class ScrolledWindow(gtk.ScrolledWindow):
    '''Scrolled window.'''
	
    def __init__(self, 
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE)):
        '''Init scrolled window.'''
        # Init.
        gtk.ScrolledWindow.__init__(self)
        self.background_pixbuf = background_pixbuf
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrollebar_size = 16
        self.min_progress_size = 15
        
        # Draw vertical scrollbar.
        vscrollbar = self.get_vscrollbar()
        vscrollbar.set_size_request(
            self.scrollebar_size,
            -1)
        vscrollbar.connect("value-changed", lambda rang: self.queue_draw())
        
        # Draw horizontal scrollbar.
        hscrollbar = self.get_hscrollbar()
        hscrollbar.set_size_request(
            -1,
            self.scrollebar_size
            )
        hscrollbar.connect("value-changed", lambda rang: self.queue_draw())
        
        self.connect("expose-event", self.expose_scrolled_window)
        
    def expose_scrolled_window(self, widget, event):
        '''Expose scrolled window.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        with cairo_state(cr):
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.clip()
            draw_pixbuf(cr, self.background_pixbuf.get_pixbuf(), 0, 0)
            
        # Draw mask.
        draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height,
                     ui_theme.get_shadow_color("linearBackground").get_color_info())
        
        # Draw vertical scrollbar.
        self.draw_v_scrollbar(cr, rect)

        # Draw horizontal scrollbar.
        self.draw_h_scrollbar(cr, rect)
        
        return True
        
    def add_child(self, child):
        '''Add child in scrolled window, don't use useViewport option if child has native scrolling.'''
        self.add_with_viewport(child)
        self.get_child().set_shadow_type(gtk.SHADOW_NONE)
        
    def draw_v_scrollbar(self, cr, window_rect):
        '''Draw vertical scrollbar.'''
        adjust = self.get_vadjustment()
        lower = adjust.get_lower()
        upper = adjust.get_upper()
        
        if upper > lower:
            # Init.
            rect = gtk.gdk.Rectangle(
                window_rect.x + window_rect.width - self.scrollebar_size, window_rect.y,
                self.scrollebar_size, window_rect.height)
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            
            if upper - lower <= page_size:
                progress_height = page_size - 2
            else:
                progress_height = max(int(rect.height / (upper - lower) * rect.height), self.min_progress_size)    
        
            # Draw foreground.
            if value == 0:
                offset_y = rect.y + 1
            elif upper - value - page_size == 0:
                offset_y = rect.y + value * (rect.height - progress_height) / (upper - lower - page_size) - 1
            else:
                offset_y = rect.y + value * (rect.height - progress_height) / (upper - lower - page_size)
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("scrollebarForeground").get_color_info()))
            cr.rectangle(rect.x + 2, offset_y, rect.width - 4, progress_height)
            cr.fill()
        
        return True
    
    def draw_h_scrollbar(self, cr, window_rect):
        '''Draw horizontal scrollbar.'''
        adjust = self.get_hadjustment()
        lower = adjust.get_lower()
        upper = adjust.get_upper()
        
        if upper > lower:
            # Init.
            rect = gtk.gdk.Rectangle(
                window_rect.x, window_rect.y + window_rect.height - self.scrollebar_size,
                window_rect.width, self.scrollebar_size)
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            
            if upper - lower <= page_size:
                progress_width = page_size - 2
            else:
                progress_width = max(int(rect.width / (upper - lower) * rect.width), self.min_progress_size)    
            
            # Draw foreground.
            if value == 0:
                offset_x = rect.x + 1
            elif upper - value - page_size == 0:
                offset_x = rect.x + value * (rect.width - progress_width) / (upper - lower - page_size) - 1
            else:
                offset_x = rect.x + value * (rect.width - progress_width) / (upper - lower - page_size)
                
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("scrollebarForeground").get_color_info()))
            cr.rectangle(offset_x, rect.y + 2, progress_width, rect.height - 4)
            cr.fill()
        
        return True

gobject.type_register(ScrolledWindow)
