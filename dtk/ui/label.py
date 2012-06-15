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
                 
from constant import DEFAULT_FONT_SIZE, ALIGN_START, ALIGN_MIDDLE
from draw import draw_font
from theme import ui_theme
from utils import propagate_expose, get_content_size
import gtk

class Label(gtk.EventBox):
    '''Label.'''
	
    def __init__(self, 
                 text, 
                 text_color=ui_theme.get_color("labelText"),
                 text_size=DEFAULT_FONT_SIZE,
                 text_x_align=ALIGN_START,
                 text_y_align=ALIGN_MIDDLE,
                 label_size=None):
        '''Init label.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.label_size = label_size
        
        self.text = text
        self.text_size = text_size
        self.text_color = text_color
        self.text_x_align = text_x_align
        self.text_y_align = text_y_align
        
        if self.label_size == None:
            self.set_size_request(*get_content_size(self.text, self.text_size))
        else:
            self.set_size_request(*self.label_size)        
            
        self.connect("expose-event", self.expose_label)    
        
    def expose_label(self, widget, event):
        '''Expose label.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        draw_font(cr, self.text, self.text_size,
                  self.text_color.get_color(),
                  rect.x, rect.y, rect.width, rect.height,
                  self.text_x_align, 
                  self.text_y_align)
        
        propagate_expose(widget, event)
        
        return True
        
    def get_text(self):
        '''Get text of label.'''
        return self.text
    
    def set_text(self, text):
        '''Set text.'''
        self.text = text
        
        if self.label_size == None:
            self.set_size_request(*get_content_size(self.text, self.text_size))
        else:
            self.set_size_request(*self.label_size)        

        self.queue_draw()
    
        
