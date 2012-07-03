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

from draw import draw_hlinear, draw_vlinear
import gobject
import gtk

class HSeparator(gtk.Alignment):
    '''Horizontal separator.'''
	
    def __init__(self, color_infos, padding_x=0, padding_y=0):
        '''Init horizontal separator.'''
        # Init.
        gtk.Alignment.__init__(self)
        self.color_infos = color_infos
        self.set(0.0, 0.0, 1.0, 0.0)
        self.set_padding(padding_y, padding_y, padding_x, padding_x)
        
        # Init separator.
        self.separator = gtk.VBox()
        self.separator.set_size_request(-1, 1)
        self.separator.connect("expose-event", self.expose_hseparator)
        self.add(self.separator)

        # Show.
        self.show_all()

    def expose_hseparator(self, widget, event):
        '''Expose separator item.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw.
        start_x = rect.x
        y = rect.y + rect.height / 2
        draw_hlinear(cr, start_x, y, rect.width, 1, self.color_infos)
        
        return True

gobject.type_register(HSeparator)

class VSeparator(gtk.Alignment):
    
    def __init__(self, color_infos, padding_x=0, padding_y=0):
        gtk.Alignment.__init__(self)
        
        self.set(0.0, 0.0, 0.0, 1.0)
        self.set_padding(padding_y, padding_y, padding_x, padding_x)
        
        self.color_infos = color_infos
        self.separator = gtk.VBox()
        self.separator.set_size_request(1, -1)
        self.separator.connect("expose-event", self.expose_vseparator)
        self.add(self.separator)
        self.show_all()
        
    def expose_vseparator(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        start_x = rect.x + rect.width / 2
        draw_vlinear(cr, start_x, rect.y, 1, rect.height, self.color_infos)
        
        return True
    
gobject.type_register(VSeparator)    
