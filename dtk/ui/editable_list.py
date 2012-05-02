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

from box import BackgroundBox, EventBox
from constant import BACKGROUND_IMAGE
from draw import draw_vlinear
from entry import Entry
from label import Label
from scrolled_window import ScrolledWindow
from theme import ui_theme
from utils import propagate_expose, container_remove_all, is_double_click, is_left_button, is_right_button, remove_callback_id
import gobject
import gtk

class EditableItemBox(gtk.Alignment):
    '''Box for item of editable.'''
	
    def __init__(self, 
                 editable_list,
                 item, 
                 set_focus_item_box, 
                 get_focus_item_box,
                 editable=False
                 ):
        '''Init editable item box.'''
        gtk.Alignment.__init__(self)
        self.editable_list = editable_list
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
        self.press_entry_id = None
        
        if editable:
            self.switch_on_editable()
        else:
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
        remove_callback_id(self.focus_out_id)
        remove_callback_id(self.focus_entry_id)
        remove_callback_id(self.focus_press_id)
        
        container_remove_all(self)
        
        self.item_label = None
        self.item_entry = None
     
    def init_text(self):
        '''Init text.'''
        self.remove_children()
        self.item_label = Label(self.item.get_text(), ui_theme.get_color("editablelistFont"))
        self.item_label.set_size_request(-1, 24)
        self.item_label.grab_focus()
        self.add(self.item_label)
        
        self.button_press_id = self.item_label.connect("button-press-event", self.button_press_item_box)
        
        self.show_all()
        
    def button_press_item_box(self, widget, event):
        '''Callback for `button-press-event` signal.'''
        if is_double_click(event):
            if self.item.get_editable():
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
        # self.press_entry_id = self.item_entry.connect("press-return", lambda e: self.editable_list.highlight_item(self.item))
        self.item_entry.grab_focus()
        
        self.show_all()
        
    def switch_off_editable(self):
        '''Switch off editable status.'''
        if self.item_entry:
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
        self.editable_list.emit("active", self.item)
        
        self.item_label.grab_focus()

class EditableList(ScrolledWindow):
    '''Scroll window.'''
	
    __gsignals__ = {
        "active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "right-press" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int,)),
    }
    
    def __init__(self, 
                 items=[],
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE),
                 ):
        '''Init editable list.'''
        # Init.
        ScrolledWindow.__init__(self, background_pixbuf)
        self.items = items
        self.focus_item_box = None
        self.edit_item_box = None
        self.background_pixbuf = background_pixbuf
        
        # Background box.
        self.background_box = BackgroundBox(background_pixbuf)
        self.background_eventbox = EventBox()
        self.add_child(self.background_eventbox)
        self.background_eventbox.add(self.background_box)

        for item in self.items:
            item_box = EditableItemBox(
                self,
                item, 
                self.set_focus_item_box, 
                self.get_focus_item_box,
                )
            item_box.set_size_request(-1, 24)
            self.background_box.pack_start(item_box, False, False)
            
        self.background_eventbox.connect("button-press-event", self.button_press_background)    
        
    def button_press_background(self, widget, event):
        '''Button press background box.'''
        if is_left_button(event):
            # Find edit item.
            edit_item = None
            for child in self.background_box.get_children():
                if child.item_entry:
                    edit_item = child
                    break
                
            # Change focus.
            self.background_box.grab_focus()
            
            # Change edit item to focus item if find.
            if edit_item:
                # Turn off editable.
                edit_item.switch_off_editable()
                
                # Set focus item if cursor at last item or out of list area.
                click_row = self.get_item_at_cursor(event)
                if click_row >= len(self.items) - 1:
                    self.set_focus_item_box(edit_item)
                
                # Redraw.
                self.queue_draw()
        elif is_right_button(event):
            cursor_index = self.get_item_at_cursor(event)
            cursor_item = None
            if cursor_index < len(self.items):
                cursor_item = self.items[cursor_index]
            self.emit("right-press", 
                      cursor_item,
                      event.x_root,
                      event.y_root)
            
    def get_item_at_cursor(self, event):
        '''Get item at cursor.'''
        vadjust = self.get_vadjustment()
        (sw_x, sw_y) = self.background_box.translate_coordinates(self.get_toplevel(), 0, int(vadjust.get_value()))
        (tw_x, tw_y) = self.get_toplevel().get_position()
        return int((event.y_root - sw_y - tw_y + vadjust.get_value()) / 24)
            
    def set_focus_item_box(self, item_box):
        '''Set focus item box.'''
        self.focus_item_box = item_box
        
    def get_focus_item_box(self):
        '''Get focus item box.'''
        return self.focus_item_box
    
    def get_items(self):
        '''Get items.'''
        return self.items
    
    def delete_item(self, item):
        '''Delete item.'''
        for item_box in self.background_box.get_children():
            if item == item_box.item:
                self.background_box.remove(item_box)
                self.items.remove(item)
                break
            
    def add_items(self, items):
        '''Add items.'''
        for item in items:
            self.items.append(item)
            item_box = EditableItemBox(
                self,
                item,
                self.set_focus_item_box,
                self.get_focus_item_box,
                )
            item_box.set_size_request(-1, 24)
            self.background_box.pack_start(item_box, False, False)
            
    def new_item(self, item):
        '''New item.'''
        # Find and remove edit item.
        edit_item = None
        for child in self.background_box.get_children():
            if child.item_entry:
                edit_item = child
                break

        if edit_item:
            edit_item.switch_off_editable()
            
        # Add item.
        self.items.append(item)
        
        # Create new item box.
        item_box = EditableItemBox(
            self,
            item,
            self.set_focus_item_box,
            self.get_focus_item_box,
            True
            )
        item_box.set_size_request(-1, 24)
        self.background_box.pack_start(item_box, False, False)
        
        # Scroll window to bottom.
        vadjust = self.get_vadjustment()
        vadjust.set_value(vadjust.get_upper())
        
        self.queue_draw()
        
    def highlight_item(self, item):
        '''Highlight item.'''
        for item_box in self.background_box.get_children():
            if item_box.item == item:
                if item_box.item_entry:
                    item_box.switch_off_editable()
                
                self.set_focus_item_box(item_box)
                self.queue_draw()
                break
    
class EditableItem(gobject.GObject):
    '''Play list item.'''
    
    def __init__(self, text):
        '''Init editable item.'''
        gobject.GObject.__init__(self)
        self.text = text
        self.editable = True

    def set_text(self, text):
        '''Set text.'''
        self.text = text
        
    def get_text(self):
        '''Get text.'''
        return self.text
        
    def get_editable(self):
        '''Get editable.'''
        return self.editable
    
    def set_editable(self, editable):
        '''Set editable.'''
        self.editable = editable
        
gobject.type_register(EditableItem)
