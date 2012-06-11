#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Hou Shaohui
# 
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou Shaohui <houshao55@gmail.com>
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
from utils import (cairo_state , alpha_color_hex_to_cairo,
                   propagate_expose, get_widget_root_coordinate)

from constant import WIDGET_POS_TOP_LEFT

from button import ImageButton
from label import Label
from menu import Menu

class ComboBox(gtk.VBox):
    __gsignals__ = {
        "item-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "will-popup-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }
    
    def __init__(self, items=[], default_width=100):
        super(ComboBox, self).__init__()

        
        # Init.
        self.items = items
        self.current_item = None
        self.default_width = default_width
        self.background_color = ui_theme.get_alpha_color("textEntryBackground")
        self.acme_color = ui_theme.get_alpha_color("textEntryAcme")
        self.point_color = ui_theme.get_alpha_color("textEntryPoint")
        self.frame_point_color = ui_theme.get_alpha_color("textEntryFramePoint")
        self.frame_color = ui_theme.get_alpha_color("textEntryFrame")
        
        # Widget.
        arrow_button = self.__create_arrow_button()
        self.item_label = Label("", ui_theme.get_color("comboBoxText"))
        
        self.main_align = gtk.Alignment()
        self.main_align.set(0.5, 0.5, 0, 0)
        self.main_align.set_padding(1, 1, 1, 1)
        hbox = gtk.HBox()
        hbox.pack_start(self.item_label, False, False)        
        hbox.pack_start(arrow_button, False, False)
        hbox_align = gtk.Alignment()
        hbox_align.set(0.5, 0.5, 1.0, 1.0)
        hbox_align.set_padding(0, 0, 2, 0)
        hbox_align.add(hbox)
        self.main_align.add(hbox_align)
        self.pack_start(self.main_align, False, False)
        
        # Signals.
        self.connect("size-allocate", self.size_change_cb)
        arrow_button.connect("clicked", self.popup_items)
        arrow_button.connect("button-press-event", self.emit_popup_signal)
        self.item_label.connect("button-release-event", lambda w, e: self.popup_items(w))
        self.item_label.connect("button-press-event", self.emit_popup_signal)
        self.main_align.connect("expose-event", self.expose_combo_bg)
        
    def size_change_cb(self, widget, rect):    
        height = 18
        if rect.width > self.default_width:
            self.default_width = rect.width
            
        label_width = self.default_width - 16
        self.set_size_request(self.default_width, height)
        self.item_label.set_size_request(label_width, height)
        
    def popup_items(self, widget):    
        x, y = get_widget_root_coordinate(self, WIDGET_POS_TOP_LEFT)
        w = self.allocation.width + 8
        menu_items = []
        for combo_item in self.items:
            menu_items.append((combo_item.get_icon(), combo_item.get_label(), self.item_selected_cb, combo_item))
        
        popup_menu = Menu(menu_items, True, True, shadow_visible=False)
        popup_menu.set_keep_above(True)
        if menu_items:
            popup_menu.set_size_request(w, -1)
        else:    
            popup_menu.set_size_request(w, 60)
        popup_menu.show((x - 4, y + 16))    
        
    def item_selected_cb(self, combo_item):    
        self.current_item = combo_item
        self.item_label.set_text(combo_item.get_label())
        self.emit("item-selected", combo_item)
        
    def add_item(self, combo_item):    
        self.items.append(combo_item)
        
    def get_items(self):    
        return self.items
    
    def get_current_item(self):
        return self.current_item
    
    def set_items(self, items):
        self.items = items
        
    def set_select_label(self, item_label):    
        index = self.label_in_items(item_label)
        if index is not None:
            self.current_item = self.items[index]
            self.item_label.set_text(item_label)
        
    def set_select_item(self, combo_item):    
        if combo_item in self.items:
            self.current_item = combo_item
            self.item_label.set_text(combo_item.get_label())
        
    def set_select_index(self, item_index):    
        try:
            combo_item = self.items[item_index]
            self.current_item = combo_item
            self.item_label.set_text(combo_item.get_label())
        except:
            pass
        
    def label_in_items(self, label):    
        labels = [item.get_label() for item in self.items]
        if label in labels:
            return labels.index(label)
        else:
            return None
        
    def delete_item(self, index):    
        self.items.pop(index)
        
    def insert_item(self, index, combo_item):
        self.items.insert(index, combo_item)
        
    def get_count(self):    
        return len(self.items)
    
    def clear(self):    
        del self.items[:]
    
    def emit_popup_signal(self, widget, event):
        self.emit("will-popup-items")
        
    def expose_combo_bg(self, widget, event):    
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw background.
        with cairo_state(cr):
            cr.rectangle(x + 2, y, w - 4, 1)
            cr.rectangle(x + 1, y + 1, w - 2, 1)
            cr.rectangle(x, y + 2, w, h - 4)
            cr.rectangle(x + 2, y + h - 1, w - 4, 1)
            cr.rectangle(x + 1, y + h - 2, w - 2, 1)
            cr.clip()
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo(self.background_color.get_color_info()))
            cr.rectangle(x, y, w, h)
            cr.fill()

        # Draw background four acme points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(self.acme_color.get_color_info()))
        cr.rectangle(x, y, 1, 1)
        cr.rectangle(x + w - 1, y, 1, 1)
        cr.rectangle(x, y + h - 1, 1, 1)
        cr.rectangle(x + w - 1, y + h - 1, 1, 1)
        cr.fill()

        # Draw background eight points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(self.point_color.get_color_info()))
        
        cr.rectangle(x + 1, y, 1, 1)
        cr.rectangle(x, y + 1, 1, 1)
        
        cr.rectangle(x + w - 2, y, 1, 1)
        cr.rectangle(x + w - 1, y + 1, 1, 1)
        
        cr.rectangle(x, y + h - 2, 1, 1)
        cr.rectangle(x + 1, y + h - 1, 1, 1)

        cr.rectangle(x + w - 1, y + h - 2, 1, 1)
        cr.rectangle(x + w - 2, y + h - 1, 1, 1)
        
        cr.fill()
        
        # Draw frame point.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(self.frame_point_color.get_color_info()))
        
        cr.rectangle(x + 1, y, 1, 1)
        cr.rectangle(x, y + 1, 1, 1)
        
        cr.rectangle(x + w - 2, y, 1, 1)
        cr.rectangle(x + w - 1, y + 1, 1, 1)
        
        cr.rectangle(x, y + h - 2, 1, 1)
        cr.rectangle(x + 1, y + h - 1, 1, 1)

        cr.rectangle(x + w - 1, y + h - 2, 1, 1)
        cr.rectangle(x + w - 2, y + h - 1, 1, 1)
        
        cr.fill()
        
        # Draw frame.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(self.frame_color.get_color_info()))
        
        cr.rectangle(x + 2, y, w - 4, 1)
        cr.rectangle(x, y + 2, 1, h - 4)
        cr.rectangle(x + 2, y + h - 1, w - 4, 1)
        cr.rectangle(x + w - 1, y + 2, 1, h - 4)
        
        cr.fill()
        
        propagate_expose(widget, event)
        
        return False
        
        
    def __create_arrow_button(self):    
        button = ImageButton(
            ui_theme.get_pixbuf("combo/arrow_normal.png"),
            ui_theme.get_pixbuf("combo/arrow_hover.png"),
            ui_theme.get_pixbuf("combo/arrow_press.png")
            )
        return button
    
    
gobject.type_register(ComboBox)    


class ComboBoxItem(object):
    
    def __init__(self, item_label, item_icon=None):
        
        self.item_label = item_label
        self.item_icon = item_icon        
        
    def get_label(self):    
        return self.item_label
    
    def set_label(self, value):
        self.item_label = value

    def get_icon(self):    
        return self.item_icon 
    
    def set_icon(self, value):
        self.item_icon = value
        
