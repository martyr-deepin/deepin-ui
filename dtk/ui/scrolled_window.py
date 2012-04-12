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
from box import *
from draw import *
from constant import *

class ScrolledWindow(gtk.ScrolledWindow):
    '''Scrolled window.'''
	
    # def __init__(self, hscrollbar_policy=gtk.POLICY_AUTOMATIC, vscrollbar_policy=gtk.POLICY_AUTOMATIC, 
    def __init__(self, hscrollbar_policy=gtk.POLICY_ALWAYS, vscrollbar_policy=gtk.POLICY_AUTOMATIC, 
                 draw_mask=True):
        '''Init scrolled window.'''
        # Init.
        gtk.ScrolledWindow.__init__(self)
        self.draw_mask = draw_mask
        self.set_policy(hscrollbar_policy, vscrollbar_policy)
        self.scrollebar_size = 16
        self.min_progress_size = 15
        
        # Draw vertical scrollbar.
        vscrollbar = self.get_vscrollbar()
        vscrollbar.set_size_request(
            self.scrollebar_size,
            -1)
        vscrollbar.connect("expose-event", self.expose_vscrollbar)
        vscrollbar.connect("value-changed", lambda rang: self.queue_draw())
        
        # Draw horizontal scrollbar.
        hscrollbar = self.get_hscrollbar()
        hscrollbar.set_size_request(
            -1,
            self.scrollebar_size
            )
        hscrollbar.connect("expose-event", self.expose_hscrollbar)
        hscrollbar.connect("value-changed", lambda rang: self.queue_draw())
        
    def add_child(self, child):
        '''Add child in scrolled window, don't use useViewport option if child has native scrolling.'''
        self.add_with_viewport(child)
        self.get_child().set_shadow_type(gtk.SHADOW_NONE)
        
    def expose_hscrollbar(self, widget, event):
        '''Draw horizontal scrollbar.'''
        adjust = self.get_hadjustment()
        lower = adjust.get_lower()
        upper = adjust.get_upper()
        
        if upper > lower:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            
            if upper - lower <= page_size:
                progress_width = page_size - 2
            else:
                progress_width = max(int(rect.width / (upper - lower) * rect.width), self.min_progress_size)    
            
            # Draw background.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("scrollebarBackground").get_color_info()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
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

    def expose_vscrollbar(self, widget, event):
        '''Draw vertical scrollbar.'''
        adjust = self.get_vadjustment()
        lower = adjust.get_lower()
        upper = adjust.get_upper()
        
        if upper > lower:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            
            if upper - lower <= page_size:
                progress_height = page_size - 2
            else:
                progress_height = max(int(rect.height / (upper - lower) * rect.height), self.min_progress_size)    
        
            # Draw background.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("scrollebarBackground").get_color_info()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
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

gobject.type_register(ScrolledWindow)
