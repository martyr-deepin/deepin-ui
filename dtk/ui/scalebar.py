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
import cairo
from utils import *
from draw import *

class HScalebar(gtk.HScale):
    '''Scalebar.'''
	
    def __init__(self,
                 left_fg_dpixbuf=ui_theme.get_pixbuf("hscalebar/left_fg.png"),
                 left_bg_dpixbuf=ui_theme.get_pixbuf("hscalebar/left_bg.png"),
                 middle_fg_dpixbuf=ui_theme.get_pixbuf("hscalebar/middle_fg.png"),
                 middle_bg_dpixbuf=ui_theme.get_pixbuf("hscalebar/middle_bg.png"),
                 right_fg_dpixbuf=ui_theme.get_pixbuf("hscalebar/right_fg.png"),
                 right_bg_dpixbuf=ui_theme.get_pixbuf("hscalebar/right_bg.png"),
                 point_dpixbuf=ui_theme.get_pixbuf("hscalebar/point.png"),
                 ):
        '''Init scalebar.'''
        # Init.
        gtk.HScale.__init__(self)
        self.set_draw_value(False)
        self.left_fg_dpixbuf = left_fg_dpixbuf
        self.left_bg_dpixbuf = left_bg_dpixbuf
        self.middle_fg_dpixbuf = middle_fg_dpixbuf
        self.middle_bg_dpixbuf = middle_bg_dpixbuf
        self.right_fg_dpixbuf = right_fg_dpixbuf
        self.right_bg_dpixbuf = right_bg_dpixbuf
        self.point_dpixbuf = point_dpixbuf
        
        # Set size request.
        self.set_size_request(-1, self.point_dpixbuf.get_pixbuf().get_height())
        
        # Redraw.
        self.connect("expose-event", self.expose_h_scalebar)
        
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
        side_width = left_bg_pixbuf.get_width()
        point_width = point_pixbuf.get_width()
        point_height = point_pixbuf.get_height()
        x, y, w, h = rect.x + point_width / 2, rect.y, rect.width - point_width, rect.height
        line_height = left_bg_pixbuf.get_height()
        line_y = y + (point_height - line_height) / 2
        value = int(self.get_value() / 100 * w)

        # Draw background.
        draw_pixbuf(cr, left_bg_pixbuf, x, line_y)
        draw_pixbuf(cr, middle_bg_pixbuf.scale_simple(w - side_width * 2, line_height, gtk.gdk.INTERP_BILINEAR), x + side_width, line_y)
        draw_pixbuf(cr, right_bg_pixbuf, x + w - side_width, line_y)
        
        # Draw foreground.
        if value > 0:
            draw_pixbuf(cr, left_fg_pixbuf, x, line_y)
            draw_pixbuf(cr, middle_fg_pixbuf.scale_simple(value, line_height, gtk.gdk.INTERP_BILINEAR), x + side_width, line_y)
            draw_pixbuf(cr, right_fg_pixbuf, x + value, line_y)
            
        # Draw drag point.
        draw_pixbuf(cr, point_pixbuf, x + value - point_pixbuf.get_width() / 2, y)    
                
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True        

gobject.type_register(HScalebar)
