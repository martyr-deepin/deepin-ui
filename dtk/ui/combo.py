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

from button import DisableButton
from droplist import Droplist
from keymap import get_keyevent_name
from label import Label
from theme import ui_theme
import gobject
import gtk
from utils import (propagate_expose, cairo_disable_antialias, 
                   color_hex_to_cairo, get_widget_root_coordinate, 
                   WIDGET_POS_BOTTOM_LEFT, alpha_color_hex_to_cairo)

class ComboBox(gtk.VBox):
    '''Combo box.'''
	
    __gsignals__ = {
        "item-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
        "key-release" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
    }

    def __init__(self, items, droplist_height=None, select_index=0, max_width=None):
        '''Init combo box.'''
        # Init.
        gtk.VBox.__init__(self)
        self.set_can_focus(True)
        self.items = items
        self.droplist_height = droplist_height
        self.select_index = select_index
        self.focus_flag = False
        
        self.droplist = Droplist(self.items, max_width=max_width)
        if self.droplist_height:
            self.droplist.set_size_request(-1, self.droplist_height)
        self.width = self.droplist.get_droplist_width() 
        self.height = 22
        self.label_padding_left = 6
        self.box = gtk.HBox()
        self.dropbutton_width = ui_theme.get_pixbuf("combo/dropbutton_normal.png").get_pixbuf().get_width()
        self.label = Label(self.items[select_index][0], 
                           label_width=self.width - self.dropbutton_width - 1 - self.label_padding_left,
                           enable_select=False,
                           enable_double_click=False)
        self.label.text_color = ui_theme.get_color("menu_font")
        self.dropbutton = DisableButton(
            (ui_theme.get_pixbuf("combo/dropbutton_normal.png"),
             ui_theme.get_pixbuf("combo/dropbutton_hover.png"),
             ui_theme.get_pixbuf("combo/dropbutton_press.png"),
             ui_theme.get_pixbuf("combo/dropbutton_disable.png")),
            )
                
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 0.0, 0.0)
        self.align.set_padding(1, 1, 1 + self.label_padding_left, 1)
        
        self.pack_start(self.align, False, False)
        self.align.add(self.box)
        self.box.pack_start(self.label, False, False)
        self.box.pack_start(self.dropbutton, False, False)
        
        self.align.connect("expose-event", self.expose_combobox_frame)
        self.label.connect("button-press-event", self.click_drop_button)
        self.dropbutton.connect("button-press-event", self.click_drop_button)
        self.droplist.connect("item-selected", self.update_select_content)
        self.droplist.connect("key-release", lambda dl, s, o, i: self.emit("key-release", s, o, i))
        self.connect("key-press-event", self.key_press_combo)
        self.connect("key-release-event", self.key_release_combo)
        self.connect("focus-in-event", self.focus_in_combo)
        self.connect("focus-out-event", self.focus_out_combo)
        
        self.keymap = {
            "Home" : self.select_first_item,
            "End" : self.select_last_item,
            "Up" : self.select_prev_item,
            "Down" : self.select_next_item}
        
    def focus_in_combo(self, widget, event):
        '''Focus in combo.'''
        self.focus_flag = True
        self.label.text_color = ui_theme.get_color("menu_select_font")

        self.queue_draw()
        
    def focus_out_combo(self, widget, event):
        '''Focus out combo.'''
        self.focus_flag = False        
        self.label.text_color = ui_theme.get_color("menu_font")
            
        self.queue_draw()
        
    def click_drop_button(self, *args):
        '''Click drop button.'''
        if self.droplist.get_visible():
            self.droplist.hide()
        else:
            (align_x, align_y) = get_widget_root_coordinate(self.align, WIDGET_POS_BOTTOM_LEFT)
            self.droplist.show(
                (align_x - 1, align_y - 1),
                (0, -self.height + 1))
            
            self.droplist.item_select_index = self.select_index
            self.droplist.active_item()
            self.droplist.scroll_page_to_select_item()
            
        self.queue_draw()    
        
    def select_first_item(self):
        '''Select first item.'''
        if len(self.droplist.droplist_items) > 0:
            first_index = self.droplist.get_first_index()
            if first_index != None:
                self.droplist.item_select_index = first_index
                self.droplist.active_item()
                self.droplist.droplist_items[self.droplist.item_select_index].wrap_droplist_clicked_action()
    
    def select_last_item(self):
        '''Select last item.'''
        if len(self.droplist.droplist_items) > 0:
            last_index = self.droplist.get_last_index()
            if last_index != None:
                self.droplist.item_select_index = last_index
                self.droplist.active_item()
                self.droplist.droplist_items[self.droplist.item_select_index].wrap_droplist_clicked_action()
    
    def select_prev_item(self):
        '''Select preview item.'''
        if len(self.droplist.droplist_items) > 0:
            prev_index = self.droplist.get_prev_index()
            if prev_index != None:
                self.droplist.item_select_index = prev_index
                self.droplist.active_item()
                self.droplist.droplist_items[self.droplist.item_select_index].wrap_droplist_clicked_action()
    
    def select_next_item(self):
        '''Select next item.'''
        if len(self.droplist.droplist_items) > 0:
            next_index = self.droplist.get_next_index()
            if next_index != None:
                self.droplist.item_select_index = next_index
                self.droplist.active_item()
                self.droplist.droplist_items[self.droplist.item_select_index].wrap_droplist_clicked_action()
        
    def key_press_combo(self, widget, event):
        '''Key press combo.'''
        if not self.droplist.get_visible():
            key_name = get_keyevent_name(event)
            if self.keymap.has_key(key_name):
                self.keymap[key_name]()
            
            return True     
        
    def set_select_index(self, item_index):
        '''Set select index.'''
        if 0 <= item_index < len(self.items):
            item = self.items[item_index]
            if item:
                self.select_index = item_index
                self.label.set_text(item[0])
                
    def get_item_with_index(self, item_index):
        '''Get item with index.'''
        if 0 <= item_index < len(self.items):
            return self.items[item_index]                
        else:
            return None
        
    def get_current_item(self):
        '''Get current item.'''
        return self.get_item_with_index(self.select_index)
                
    def key_release_combo(self, widget, event):
        '''Handle key release.'''
        self.emit("key-release", 
                  self.items[self.select_index][0],
                  self.items[self.select_index][1],
                  self.select_index)    
    
    def update_select_content(self, droplist, item_content, item_value, item_index):
        '''Update select content.'''
        self.select_index = item_index
        self.label.set_text(item_content)
        
        self.emit("item-selected", item_content, item_value, item_index)
        
        self.grab_focus()
        
        self.queue_draw()
        
    def set_sensitive(self, sensitive):
        super(ComboBox, self).set_sensitive(sensitive)
        self.label.set_sensitive(sensitive)
        self.dropbutton.set_sensitive(sensitive)
            
    def expose_combobox_frame(self, widget, event):
        '''Expose combo box frame.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            if self.get_sensitive():
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            else:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("disable_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            if self.focus_flag:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_select_background").get_color(), 0.9)))
                cr.rectangle(rect.x, rect.y, rect.width - 1 - self.dropbutton_width, rect.height - 1)
                cr.fill()
                
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x + rect.width - 1 - self.dropbutton_width, rect.y, self.dropbutton_width, rect.height - 1)
                cr.fill()
            else:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
                cr.fill()
        
        # Propagate expose to children.
        propagate_expose(widget, event)
        
        return True
    
gobject.type_register(ComboBox)    
