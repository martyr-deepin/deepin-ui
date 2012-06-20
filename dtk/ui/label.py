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
                 
from constant import DEFAULT_FONT_SIZE, ALIGN_START
from draw import draw_text
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
                 label_width=None,
                 enable_gaussian=False,
                 ):
        '''Init label.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.label_width = label_width
        self.enable_gaussian = enable_gaussian
        
        self.text = text
        self.text_size = text_size
        self.text_color = text_color
        if self.enable_gaussian:
            self.gaussian_radious=2
            self.gaussian_color="#000000"
            self.border_radious=1
            self.border_color="#000000"
        else:
            self.gaussian_radious=None
            self.gaussian_color=None
            self.border_radious=None
            self.border_color=None
            
        self.text_x_align = text_x_align
        
        self.update_size()
            
        self.connect("expose-event", self.expose_label)    
        
    def expose_label(self, widget, event):
        '''Expose label.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.enable_gaussian:
            label_color = "#FFFFFF"
        else:
            label_color = self.text_color.get_color()
            
        draw_text(cr, self.text, 
                  rect.x, rect.y, rect.width, rect.height,
                  self.text_size,
                  label_color,
                  alignment=self.text_x_align, 
                  gaussian_radious=self.gaussian_radious,
                  gaussian_color=self.gaussian_color,
                  border_radious=self.border_radious,
                  border_color=self.border_color
                  )
        
        propagate_expose(widget, event)
        
        return True
        
    def get_text(self):
        '''Get text of label.'''
        return self.text
    
    def set_text(self, text):
        '''Set text.'''
        self.text = text
        
        self.update_size()

        self.queue_draw()
    
    def update_size(self):
        '''Update size.'''
        if self.label_width == None:
            (label_width, label_height) = get_content_size(self.text, self.text_size)
        else:
            (label_width, label_height) = get_content_size(self.text, self.text_size)
            label_width = self.label_width
            
        if self.enable_gaussian:
            label_width += self.gaussian_radious * 2
            label_height += self.gaussian_radious * 2
            
        self.set_size_request(label_width, label_height)
        
        print (label_width, label_height)
        
