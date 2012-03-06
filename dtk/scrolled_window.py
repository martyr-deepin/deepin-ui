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
	
    def __init__(self, hscrollbar_policy=gtk.POLICY_AUTOMATIC, vscrollbar_policy=gtk.POLICY_AUTOMATIC, 
                 draw_mask=True):
        '''Init scrolled window.'''
        # Init.
        gtk.ScrolledWindow.__init__(self)
        self.draw_mask = draw_mask
        self.set_policy(hscrollbar_policy, vscrollbar_policy)
        
        # Draw vertical scrollbar.
        vscrollbar = self.get_vscrollbar()
        vscrollbar.set_size_request(
            ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_bg.png").get_pixbuf().get_width(), 
            -1)
        vscrollbar.connect("expose-event", self.expose_vscrollbar)
        vscrollbar.connect("value-changed", lambda rang: self.queue_draw())
        
        # Draw horizontal scrollbar.
        hscrollbar = self.get_hscrollbar()
        hscrollbar.set_size_request(
            -1,
            ui_theme.get_dynamic_pixbuf("scrollbar/hscrollbar_bg.png").get_pixbuf().get_height(), 
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
            bg_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/hscrollbar_bg.png").get_pixbuf()
            fg_left_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/hscrollbar_fg_left.png").get_pixbuf()
            fg_middle_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/hscrollbar_fg_middle.png").get_pixbuf()
            fg_right_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/hscrollbar_fg_right.png").get_pixbuf()
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            min_width = fg_left_pixbuf.get_width() + fg_middle_pixbuf.get_width() + fg_right_pixbuf.get_width()
            progress_width = max(int(rect.width / (upper - lower) * rect.width), min_width)    
            
            # Draw foreground.
            ft_width = fg_left_pixbuf.get_width()
            
            if (upper - lower - page_size) == 0:
                offset_x = rect.x
            else:
                offset_x = rect.x + value * (rect.width - progress_width) / (upper - lower - page_size)
            draw_pixbuf(cr, fg_left_pixbuf, offset_x, rect.y)
            
            fm_pixbuf = fg_middle_pixbuf.scale_simple(progress_width - ft_width * 2 + 2, rect.height, gtk.gdk.INTERP_BILINEAR)
            draw_pixbuf(cr, fm_pixbuf, offset_x + ft_width - 1, rect.y)
            
            draw_pixbuf(cr, fg_right_pixbuf, offset_x + progress_width - ft_width, rect.y)
            
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
            bg_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_bg.png").get_pixbuf()
            fg_top_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_fg_top.png").get_pixbuf()
            fg_middle_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_fg_middle.png").get_pixbuf()
            fg_bottom_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_fg_bottom.png").get_pixbuf()
            value = adjust.get_value()
            page_size = adjust.get_page_size()
            min_height = fg_top_pixbuf.get_height() + fg_middle_pixbuf.get_height() + fg_bottom_pixbuf.get_height()
            progress_height = max(int(rect.height / (upper - lower) * rect.height), min_height)    
        
            # Draw background.
            if self.draw_mask:
                vbg_pixbuf = ui_theme.get_dynamic_pixbuf("scrollbar/vscrollbar_bg.png").get_pixbuf()
                draw_vlinear(cr, rect.x, rect.y, vbg_pixbuf.get_width(), rect.height,
                             ui_theme.get_dynamic_shadow_color("linearBackground").get_color_info())
            
            # Draw foreground.
            ft_height = fg_top_pixbuf.get_height()
            
            if (upper - lower - page_size) == 0:
                offset_y = rect.y
            else:
                offset_y = rect.y + value * (rect.height - progress_height) / (upper - lower - page_size)
            draw_pixbuf(cr, fg_top_pixbuf, rect.x, offset_y)
            
            fm_pixbuf = fg_middle_pixbuf.scale_simple(rect.width, progress_height - ft_height * 2 + 2, gtk.gdk.INTERP_BILINEAR)
            draw_pixbuf(cr, fm_pixbuf, rect.x, offset_y + ft_height - 1)
            
            draw_pixbuf(cr, fg_bottom_pixbuf, rect.x, offset_y + progress_height - ft_height)
            
            cr.fill()
        
        return True

gobject.type_register(ScrolledWindow)
