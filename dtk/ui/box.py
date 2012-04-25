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

from constant import BACKGROUND_IMAGE, DEFAULT_FONT_SIZE
from draw import draw_pixbuf, propagate_expose, draw_vlinear, cairo_state, draw_text
from theme import ui_theme
from utils import get_content_size
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

class TextBox(gtk.EventBox):
    '''Box just contain text.'''
	
    def __init__(self, text, text_style=ui_theme.get_text_style("titlebar")):
        '''Init text box.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.text = text
        self.text_style = text_style
        
        # Request size.
        (font_width, font_height) = get_content_size(text, DEFAULT_FONT_SIZE)
        self.set_size_request(font_width, font_height)
        
        # Connect expose signal.
        self.connect("expose-event", self.expose_text_box)
        
    def change_text(self, text):
        '''Change text.'''
        self.text = text
        self.queue_draw()
        
    def expose_text_box(self, widget, event):
        '''Expose text box.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw text.
        draw_text(cr, 
                  rect.x, rect.y, rect.width, rect.height,
                  self.text, 
                  self.text_style.get_style())
        
        # Propagate expose.
        propagate_expose(widget, event)
    
        return True
    
gobject.type_register(TextBox)

class BackgroundBox(gtk.VBox):
    '''Box to expande background.'''
	
    def __init__(self, 
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE)):
        '''Init background box.'''
        # Init.
        gtk.VBox.__init__(self)
        self.set_can_focus(True)
        self.background_pixbuf = background_pixbuf        
        
        self.connect("expose-event", self.expose_background_box)
        
    def expose_background_box(self, widget, event):
        '''Expose background box.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        toplevel = widget.get_toplevel()
        coordinate = widget.translate_coordinates(toplevel, rect.x, rect.y)
        (offset_x, offset_y) = coordinate
        
        with cairo_state(cr):
            cr.translate(-offset_x, -offset_y)
            cr.rectangle(offset_x, offset_y, rect.width, rect.height)
            cr.clip()
            
            draw_pixbuf(cr, self.background_pixbuf.get_pixbuf(), rect.x, rect.y)
            
        draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height,
                     ui_theme.get_shadow_color("linearBackground").get_color_info())

        propagate_expose(widget, event)
        
        return False
        
gobject.type_register(BackgroundBox)

