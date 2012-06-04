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
                   propagate_expose)

from button import ImageButton
from entry import Entry


class SpinBox(gtk.VBox):
    __gsignals__ = {
        "value-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        }
    
    def __init__(self, value=0, lower=0, upper=100, step=10, default_width=55):
        gtk.VBox.__init__(self)
        self.current_value = value
        self.lower_value = lower
        self.upper_value = upper
        self.step_value  = step
        
        # Init.
        self.default_width = default_width
        self.background_color = ui_theme.get_alpha_color("textEntryBackground")
        self.acme_color = ui_theme.get_alpha_color("textEntryAcme")
        self.point_color = ui_theme.get_alpha_color("textEntryPoint")
        self.frame_point_color = ui_theme.get_alpha_color("textEntryFramePoint")
        self.frame_color = ui_theme.get_alpha_color("textEntryFrame")
        
        # Widget.
        arrow_up_button = self.create_simple_button("up", self.increase_value)
        arrow_down_button = self.create_simple_button("down", self.decrease_value)
        button_box = gtk.VBox()
        button_box.pack_start(arrow_up_button, False, False)
        button_box.pack_start(arrow_down_button, False, False)
        self.value_entry = Entry(str(value))
        
        self.main_align = gtk.Alignment()
        self.main_align.set(0.5, 0.5, 0, 0)
        self.main_align.set_padding(1, 1, 1, 1)
        hbox = gtk.HBox()
        hbox.pack_start(self.value_entry, False, False)        
        hbox.pack_start(button_box, False, False)
        hbox_align = gtk.Alignment()
        hbox_align.set(0.5, 0.5, 1.0, 1.0)
        hbox_align.set_padding(0, 0, 2, 0)
        hbox_align.add(hbox)
        self.main_align.add(hbox_align)
        self.pack_start(self.main_align, False, False)
        
        # Signals.
        self.connect("size-allocate", self.size_change_cb)
        self.main_align.connect("expose-event", self.expose_spin_bg)
        
    def get_value(self):    
        return self.current_value
    
    def set_value(self, value):
        new_value = self.adjust_value(value)
        if new_value != self.current_value:
            self.update_and_emit(new_value)
            
    def value_changed(self):        
        self.emit("value-changed", self.current_value)
        
    def get_lower(self):    
        return self.lower_value
    
    def set_lower(self, value):
        self.lower_value = value
        
    def get_upper(self):    
        return self.upper_value
    
    def set_upper(self, value):
        self.upper_value = value
        
    def get_step(self):
        return self.step_value
    
    def set_step(self, value):
        self.set_step = value
        
    def size_change_cb(self, widget, rect):    
        height = 18
        if rect.width > self.default_width:
            self.default_width = rect.width
            
        label_width = self.default_width - 16
        self.set_size_request(self.default_width, height)
        self.value_entry.set_size_request(label_width, height)
        
    def increase_value(self, widget):    
        new_value = self.current_value + self.step_value
        if new_value > self.upper_value: 
            new_value = self.upper_value
        if new_value != self.current_value:
            self.update_and_emit(new_value)
            
    def adjust_value(self, value):        
        if not isinstance(value, int):
            return self.current_value
        else:
            if value < self.lower_value:
                return self.lower_value
            elif value > self.upper_value:
                return self.upper_value
            else:
                return value
        
    def decrease_value(self, widget):     
        new_value = self.current_value - self.step_value
        if new_value < self.lower_value: 
            new_value = self.lower_value
        if new_value != self.current_value:
            self.update_and_emit(new_value)
        
    def update(self, new_value):
        '''Update value, just use when need avoid emit signal recursively.'''
        self.current_value = new_value
        self.value_entry.set_text(str(self.current_value))
            
    def update_and_emit(self, new_value):    
        self.current_value = new_value
        self.value_entry.set_text(str(self.current_value))
        self.emit("value-changed", self.current_value)
        
    def expose_spin_bg(self, widget, event):    
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
        
    def create_simple_button(self, name, callback=None):    
        button = ImageButton(
            ui_theme.get_pixbuf("spin/%s_normal.png" % name),
            ui_theme.get_pixbuf("spin/%s_hover.png" % name),
            ui_theme.get_pixbuf("spin/%s_press.png" % name)
            )
        if callback:
            button.connect("clicked", callback)
        return button

gobject.type_register(SpinBox)    