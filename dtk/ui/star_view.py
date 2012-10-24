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
from theme import ui_theme
from draw import draw_pixbuf
from utils import propagate_expose, get_event_coords

STAR_SIZE = 16

class StarBuffer(gobject.GObject):
    '''
    class docs
    '''
	
    def __init__(self, star_level=5):
        '''
        init docs
        '''
        gobject.GObject.__init__(self)
        self.star_level = star_level
        
    def render(self, cr, rect):
        for i in range(0, 5):
            pixbuf = self.get_star_path(i + 1)
            draw_pixbuf(cr,
                        pixbuf,
                        rect.x + i * STAR_SIZE,
                        rect.y + (rect.height - pixbuf.get_height()) / 2,
                        )
    
    def get_star_path(self, star_index):
        '''Get star path.'''
        if star_index == 1:
            if self.star_level > 8:
                pixbuf_path = "star_green.png"
            elif self.star_level > 2:
                pixbuf_path = "star_yellow.png"
            elif self.star_level == 2:
                pixbuf_path = "star_red.png"
            else:
                pixbuf_path = "halfstar_red.png"
        elif star_index in [2, 3, 4]:
            if self.star_level > 8:
                pixbuf_path = "star_green.png"
            elif self.star_level >= star_index * 2:
                pixbuf_path = "star_yellow.png"
            elif self.star_level == star_index * 2 - 1:
                pixbuf_path = "halfstar_yellow.png"
            else:
                pixbuf_path = "star_gray.png"
        elif star_index == 5:
            if self.star_level >= star_index * 2:
                pixbuf_path = "star_green.png"
            elif self.star_level == star_index * 2 - 1:
                pixbuf_path = "halfstar_green.png"
            else:
                pixbuf_path = "star_gray.png"
                
        return ui_theme.get_pixbuf("star/%s" % pixbuf_path).get_pixbuf()        
        
gobject.type_register(StarBuffer)        

class StarView(gtk.Button):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.Button.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.star_buffer = StarBuffer()
        
        self.set_size_request(STAR_SIZE * 5, STAR_SIZE)
        
        self.connect("motion-notify-event", self.motion_notify_star_view)
        self.connect("expose-event", self.expose_star_view)        
        
    def expose_star_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        self.star_buffer.render(cr, rect)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True        
    
    def motion_notify_star_view(self, widget, event):
        (event_x, event_y) = get_event_coords(event)
        self.star_buffer.star_level = int(min(event_x / (STAR_SIZE / 2) + 1, 10))
        
        self.queue_draw()
        
gobject.type_register(StarView)        
