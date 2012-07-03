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

from cache_pixbuf import CachePixbuf
from draw import draw_pixbuf
from utils import is_left_button
import gobject
import gtk

class HScalebar(gtk.HScale):
    '''Scalebar.'''
	
    def __init__(self,
                 left_fg_dpixbuf,
                 left_bg_dpixbuf,
                 middle_fg_dpixbuf,
                 middle_bg_dpixbuf,
                 right_fg_dpixbuf,
                 right_bg_dpixbuf,
                 point_dpixbuf
                 ):
        '''Init scalebar.'''
        # Init.
        gtk.HScale.__init__(self)
        self.set_draw_value(False)
        self.set_range(0, 100)
        self.left_fg_dpixbuf = left_fg_dpixbuf
        self.left_bg_dpixbuf = left_bg_dpixbuf
        self.middle_fg_dpixbuf = middle_fg_dpixbuf
        self.middle_bg_dpixbuf = middle_bg_dpixbuf
        self.right_fg_dpixbuf = right_fg_dpixbuf
        self.right_bg_dpixbuf = right_bg_dpixbuf
        self.point_dpixbuf = point_dpixbuf
        self.cache_bg_pixbuf = CachePixbuf()
        self.cache_fg_pixbuf = CachePixbuf()
        
        # Set size request.
        self.set_size_request(-1, self.point_dpixbuf.get_pixbuf().get_height())
        
        # Redraw.
        self.connect("expose-event", self.expose_h_scalebar)
        self.connect("button-press-event", self.press_volume_progressbar)
        
    def expose_h_scalebar(self, widget, event):
        '''Callback for `expose-event` event.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Init pixbuf.
        left_fg_pixbuf = self.left_fg_dpixbuf.get_pixbuf()
        left_bg_pixbuf = self.left_bg_dpixbuf.get_pixbuf()
        middle_fg_pixbuf = self.middle_fg_dpixbuf.get_pixbuf()
        middle_bg_pixbuf = self.middle_bg_dpixbuf.get_pixbuf()
        right_fg_pixbuf = self.right_fg_dpixbuf.get_pixbuf()
        right_bg_pixbuf = self.right_bg_dpixbuf.get_pixbuf()
        point_pixbuf = self.point_dpixbuf.get_pixbuf()
        
        # Init value.
        upper = self.get_adjustment().get_upper() 
        lower = self.get_adjustment().get_lower() 
        total_length = max(upper - lower, 1)
        side_width = left_bg_pixbuf.get_width()
        point_width = point_pixbuf.get_width()
        point_height = point_pixbuf.get_height()
        x, y, w, h = rect.x + point_width / 2, rect.y, rect.width - point_width, rect.height
        line_height = left_bg_pixbuf.get_height()
        line_y = y + (point_height - line_height) / 2
        value = int((self.get_value() - lower) / total_length * w)

        # Draw background.
        self.cache_bg_pixbuf.scale(middle_bg_pixbuf, w - side_width * 2, line_height)
        draw_pixbuf(cr, left_bg_pixbuf, x, line_y)
        draw_pixbuf(cr, self.cache_bg_pixbuf.get_cache(), x + side_width, line_y)
        draw_pixbuf(cr, right_bg_pixbuf, x + w - side_width, line_y)
        
        # Draw foreground.
        if value > 0:
            self.cache_fg_pixbuf.scale(middle_fg_pixbuf, value, line_height)
            draw_pixbuf(cr, left_fg_pixbuf, x, line_y)
            draw_pixbuf(cr, self.cache_fg_pixbuf.get_cache(), x + side_width, line_y)
            draw_pixbuf(cr, right_fg_pixbuf, x + value, line_y)
            
        # Draw drag point.
        draw_pixbuf(cr, point_pixbuf, x + value - point_pixbuf.get_width() / 2, y)    
                
        return True        

    def press_volume_progressbar(self, widget, event):
        '''Press volume progressbar.'''
        # Init.
        if is_left_button(event):
            rect = widget.allocation
            lower = self.get_adjustment().get_lower()
            upper = self.get_adjustment().get_upper()
            point_width = self.point_dpixbuf.get_pixbuf().get_width()
            
            # Set value.
            self.set_value(lower + ((event.x - point_width / 2)  / (rect.width - point_width)) * (upper - lower))
            self.queue_draw()
        
        return False
    
gobject.type_register(HScalebar)

class VScalebar(gtk.VScale):
    '''Vscalebar.'''
    
    def __init__(self,
                 upper_fg_dpixbuf,
                 upper_bg_dpixbuf,
                 middle_fg_dpixbuf,
                 middle_bg_dpixbuf,
                 bottom_fg_dpixbuf,
                 bottom_bg_dpixbuf,
                 point_dpixbuf,
                 ):
        
        gtk.VScale.__init__(self)

        self.set_draw_value(False)
        self.set_range(0, 100)
        self.__has_point = True
        self.set_inverted(True)
        self.upper_fg_dpixbuf = upper_fg_dpixbuf
        self.upper_bg_dpixbuf = upper_bg_dpixbuf
        self.middle_fg_dpixbuf = middle_fg_dpixbuf
        self.middle_bg_dpixbuf = middle_bg_dpixbuf
        self.bottom_fg_dpixbuf = bottom_fg_dpixbuf
        self.bottom_bg_dpixbuf = bottom_bg_dpixbuf
        self.point_dpixbuf = point_dpixbuf
        self.cache_bg_pixbuf = CachePixbuf()
        self.cache_fg_pixbuf = CachePixbuf()
        
        self.set_size_request(self.point_dpixbuf.get_pixbuf().get_height(), -1)
        
        self.connect("expose-event", self.expose_v_scalebar)
        self.connect("button-press-event", self.press_progressbar)
        
    def expose_v_scalebar(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Init pixbuf.
        upper_fg_pixbuf = self.upper_fg_dpixbuf.get_pixbuf()
        upper_bg_pixbuf = self.upper_bg_dpixbuf.get_pixbuf()
        middle_fg_pixbuf = self.middle_fg_dpixbuf.get_pixbuf()
        middle_bg_pixbuf = self.middle_bg_dpixbuf.get_pixbuf()
        bottom_fg_pixbuf = self.bottom_fg_dpixbuf.get_pixbuf()
        bottom_bg_pixbuf = self.bottom_bg_dpixbuf.get_pixbuf()
        point_pixbuf = self.point_dpixbuf.get_pixbuf()
        
        upper_value = self.get_adjustment().get_upper()
        lower_value = self.get_adjustment().get_lower()
        total_length = max(upper_value - lower_value, 1)
        point_width = point_pixbuf.get_width()
        point_height = point_pixbuf.get_height()
        
        line_width = upper_bg_pixbuf.get_width()
        side_height = upper_bg_pixbuf.get_height()

        x, y, w, h  = rect.x, rect.y + point_height, rect.width, rect.height - point_height - point_height / 2
        line_x = x + (point_width - line_width / 1.5) / 2
        point_y = h - int((self.get_value() - lower_value ) / total_length * h)
        value = int((self.get_value() - lower_value ) / total_length * h)

        self.cache_bg_pixbuf.scale(middle_bg_pixbuf, line_width, h - side_height * 2 + point_height / 2)
        draw_pixbuf(cr, upper_bg_pixbuf, line_x, y - point_height / 2)
        draw_pixbuf(cr, self.cache_bg_pixbuf.get_cache(), line_x, y + side_height - point_height / 2)
        draw_pixbuf(cr, bottom_bg_pixbuf, line_x, y + h - side_height)
                
        if value > 0:
            self.cache_fg_pixbuf.scale(middle_fg_pixbuf, line_width, value)
            draw_pixbuf(cr, self.cache_fg_pixbuf.get_cache(), line_x, y + point_y - side_height)
        draw_pixbuf(cr, bottom_fg_pixbuf, line_x, y + h - side_height)
        
        if self.get_value() == upper_value:
            draw_pixbuf(cr, upper_fg_pixbuf, line_x, y - point_height / 2)
            
        if self.__has_point:    
            draw_pixbuf(cr, point_pixbuf, x, y + point_y - side_height / 2 - point_height / 2)
            
        return True
        
    def press_progressbar(self, widget, event):
        if is_left_button(event):
            rect = widget.allocation
            lower_value = self.get_adjustment().get_lower()
            upper_value = self.get_adjustment().get_upper()
            point_height = self.point_dpixbuf.get_pixbuf().get_height()
            self.set_value(upper_value - ((event.y - point_height / 2) / (rect.height - point_height)) * (upper_value - lower_value) )
            self.queue_draw()
            
        return False    
    
    def set_has_point(self, value):
        self.__has_point = value
        
    def get_has_point(self):    
        return self.__has_point
    
gobject.type_register(VScalebar)        
