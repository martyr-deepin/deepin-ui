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
from label import *
from entry import *
from scrolled_window import *

class PlaylistItemBox(gtk.Alignment):
    '''Box for item of playlist.'''
	
    def __init__(self, 
                 item, 
                 set_focus_item_box, 
                 get_focus_item_box,
                 ):
        '''Init playlist item box.'''
        gtk.Alignment.__init__(self)
        self.padding_x = 10
        self.set(0.5, 0.5, 1.0, 1.0)
        self.set_padding(0, 0, self.padding_x, self.padding_x)
        self.item = item
        self.item_label = None
        self.item_entry = None
        self.set_focus_item_box = set_focus_item_box
        self.get_focus_item_box = get_focus_item_box
        self.button_press_id = None
        self.focus_out_id = None
        
        self.init_text()
        
        self.connect("expose-event", self.expose_item_box)
        
    def expose_item_box(self, widget, event):
        '''Expose item box.'''
        cr = widget.window.cairo_create()        
        rect = widget.allocation

        if self.get_focus_item_box() == self:
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listviewSelect").get_color_info())
        
        propagate_expose(widget, event)
        
        return True
    
    def remove_children(self):
        '''Clear child.'''
        if self.focus_out_id:
            gobject.source_remove(self.focus_out_id)
            self.focus_out_id = None
            
        if self.button_press_id:
            gobject.source_remove(self.button_press_id)
            self.button_press_id = None
        
        container_remove_all(self)
        
        self.item_label = None
        self.item_entry = None
     
    def init_text(self):
        '''Init text.'''
        self.remove_children()
        self.item_label = Label(self.item.get_text(), ui_theme.get_color("playlistviewFont"))
        self.item_label.set_size_request(-1, 24)
        self.item_label.grab_focus()
        self.add(self.item_label)
        
        self.button_press_id = self.item_label.connect("button-press-event", self.button_press_item_box)
        
        self.show_all()
        
    def button_press_item_box(self, widget, event):
        '''Callback for `button-press-event` signal.'''
        if is_double_click(event):
            self.switch_on_editable()
        elif is_left_button(event):
            self.active_item()
        
    def switch_on_editable(self):
        '''Switch on editable status.'''
        self.set_focus_item_box(None)
        
        self.remove_children()
        self.item_entry = Entry(self.item.get_text(), 1)
        self.item_entry.set_size_request(-1, 24)
        self.item_entry.select_all()
        
        self.add(self.item_entry)
        
        self.focus_out_id = self.item_entry.connect("focus-out-event", lambda w, e: self.switch_off_editable())
        self.item_entry.grab_focus()
        
        self.show_all()
        
    def switch_off_editable(self):
        '''Switch off editable status.'''
        self.item.set_text(self.item_entry.get_text())
        self.init_text()
        
    def active_item(self):
        '''Active item.'''
        # Get old focus item box.
        old_focus_item_box = self.get_focus_item_box()
        
        # Redraw.
        self.set_focus_item_box(self)
        self.queue_draw()
        
        if old_focus_item_box:
            old_focus_item_box.queue_draw()
            
        # Active item.
        self.item.active()
        
        self.item_label.grab_focus()

class PlaylistView(ScrolledWindow):
    '''Scroll window.'''
	
    def __init__(self, 
                 items=[],
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE),
                 ):
        '''Init playlist view.'''
        # Init.
        ScrolledWindow.__init__(self, background_pixbuf)
        self.items = items
        self.focus_item_box = None
        self.edit_item_box = None
        self.background_pixbuf = background_pixbuf
        
        # Background box.
        self.background_box = BackgroundBox(background_pixbuf)
        self.add_child(self.background_box)

        for item in self.items:
            item_box = PlaylistItemBox(
                item, 
                self.set_focus_item_box, 
                self.get_focus_item_box,
                )
            item_box.set_size_request(-1, 24)
            self.background_box.pack_start(item_box)
            
    def set_focus_item_box(self, item_box):
        '''Set focus item box.'''
        self.focus_item_box = item_box
        
    def get_focus_item_box(self):
        '''Get focus item box.'''
        return self.focus_item_box
    
class PlaylistItem(object):
    '''Play list item.'''
	
    def __init__(self, text):
        '''Init playlist item.'''
        self.text = text

    def set_text(self, text):
        '''Set text.'''
        self.text = text
        
    def get_text(self):
        '''Get text.'''
        return self.text
        
    def active(self):
        '''Active.'''
        print self.text
    
