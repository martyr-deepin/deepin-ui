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
import cairo
from utils import *
from draw import *

class Entry(gtk.EventBox):
    '''Entry.'''
	
    def __init__(self, content="", font_size=DEFAULT_FONT_SIZE, padding_x=10, padding_y=5):
        '''Init entry.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.im = gtk.IMMulticontext()
        self.font_size = font_size
        self.content = content
        self.cursor_index = 0
        self.padding_x = padding_x
        self.padding_y = padding_y
        
        # Set entry height.
        (self.text_width, self.text_height) = get_content_size("E", font_size)        
        self.set_size_request(self.text_width + padding_x * 2 + 300, self.text_height + padding_y * 2)
        
        # Connect signal.
        self.connect("realize", self.realize_entry)
        self.connect("key-press-event", self.key_press_entry)
        self.connect("expose-event", self.expose_entry)
        self.connect("button-press-event", self.button_press_entry)
        
        self.im.connect("commit", self.commit_entry)
        
    def realize_entry(self, widget):
        '''Realize entry.'''
        # Init IMContext.
        self.im.set_client_window(widget.window)
        self.im.focus_in()
        
    def key_press_entry(self, widget, event):
        '''Callback for `key-press-event` signal.'''
        # Pass key to IMContext.
        self.im.filter_keypress(event)
        
        return False
    
    def expose_entry(self, widget, event):
        '''Callback for `expose-event` signal.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw background.
        draw_hlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                     ui_theme.get_shadow_color("entryBackground").get_color_info())
        
        # Draw font.
        draw_text(cr, rect.x, rect.y, rect.width, rect.height,
                  self.content,
                  ui_theme.get_text_style("entry").get_style())
        
        # Draw foreground.
        draw_hlinear(cr, rect.x, rect.y, self.text_width * 2, rect.height,
                     ui_theme.get_shadow_color("entryLeft").get_color_info())
        draw_hlinear(cr, rect.x + rect.width - self.text_width * 2, rect.y, self.text_width * 2, rect.height,
                     ui_theme.get_shadow_color("entryRight").get_color_info())
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def button_press_entry(self, widget, event):
        '''Button press entry.'''
        self.grab_focus()
        
    def commit_entry(self, im, im_str):
        '''Entry commit.'''
        self.content += im_str
        
        self.queue_draw()
        
gobject.type_register(Entry)

if __name__ == "__main__":
    window = gtk.Window()
    window.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
    window.set_decorated(False)
    window.add_events(gtk.gdk.ALL_EVENTS_MASK)        
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(300, -1)
    window.move(100, 100)
    
    entry = Entry("Enter to search")
    window.add(entry)

    window.show_all()
    
    gtk.main()
