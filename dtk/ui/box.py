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

from draw import draw_pixbuf, propagate_expose, draw_vlinear, cairo_state
from skin_config import skin_config
from utils import get_window_shadow_size
import gobject
import gtk

class EventBox(gtk.EventBox):
    '''Event box.'''
	
    def __init__(self):
        '''Init event box.'''
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        
class ImageBox(gtk.EventBox):
    '''Box just contain image.'''
	
    def __init__(self, image_dpixbuf):
        '''Init image box.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.image_dpixbuf = image_dpixbuf
        
        # Set size.
        pixbuf = self.image_dpixbuf.get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        
        # Connect expose signal.
        self.connect("expose-event", self.expose_image_box)
        
    def expose_image_box(self, widget, event):
        '''Expose image box.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        pixbuf = self.image_dpixbuf.get_pixbuf()
        
        # Draw.
        draw_pixbuf(cr, pixbuf, rect.x, rect.y)
        
        # Propagate expose.
        propagate_expose(widget, event)
    
        return True
    
gobject.type_register(ImageBox)

class BackgroundBox(gtk.VBox):
    '''Box to expande background.'''
	
    def __init__(self):
        '''Init background box.'''
        # Init.
        gtk.VBox.__init__(self)
        self.set_can_focus(True)
        
        self.connect("expose-event", self.expose_background_box)
        
    def draw_mask(self, cr, x, y, w, h):
        '''Draw mask.'''
        draw_vlinear(cr, x, y, w, h,
                     [(0, ("#FF0000", 1)),
                      (1, ("#FF0000", 1))]
                     )
        
    def expose_background_box(self, widget, event):
        '''Expose background box.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        toplevel = widget.get_toplevel()
        coordinate = widget.translate_coordinates(toplevel, rect.x, rect.y)
        (offset_x, offset_y) = coordinate
        
        with cairo_state(cr):
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.clip()
            
            (shadow_x, shadow_y) = get_window_shadow_size(toplevel)
            skin_config.render_background(cr, widget, shadow_x, shadow_y)
            
        self.draw_mask(cr, rect.x, rect.y, rect.width, rect.height)    

        return False
        
gobject.type_register(BackgroundBox)

