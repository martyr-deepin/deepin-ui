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

from button import DisableButton
from entry import Entry
from theme import ui_theme
import gobject
import gtk
from utils import (alpha_color_hex_to_cairo, cairo_disable_antialias,
                   color_hex_to_cairo,
                   propagate_expose, is_float, remove_timeout_id)


class SpinBox(gtk.VBox):
    __gsignals__ = {
        "value-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        "key-release" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        }
    
    def __init__(self, value=0, lower=0, upper=100, step=10, default_width=55):
        gtk.VBox.__init__(self)
        self.current_value = value
        self.lower_value = lower
        self.upper_value = upper
        self.step_value  = step
        self.update_delay = 100 # milliseconds
        self.increase_value_id = None
        self.decrease_value_id = None
        
        # Init.
        self.default_width = default_width
        self.default_height = 22
        self.arrow_button_width = 19
        self.background_color = ui_theme.get_alpha_color("text_entry_background")
        self.acme_color = ui_theme.get_alpha_color("text_entry_acme")
        self.point_color = ui_theme.get_alpha_color("text_entry_point")
        self.frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point")
        self.frame_color = ui_theme.get_alpha_color("text_entry_frame")
        
        # Widget.
        arrow_up_button = self.create_simple_button("up", self.press_increase_button)
        arrow_down_button = self.create_simple_button("down", self.press_decrease_button)
        button_box = gtk.VBox()
        button_box.pack_start(arrow_up_button, False, False)
        button_box.pack_start(arrow_down_button, False, False)
        self.value_entry = Entry(str(value))
        self.value_entry.check_text = is_float
        
        self.main_align = gtk.Alignment()
        self.main_align.set(0.5, 0.5, 0, 0)
        hbox = gtk.HBox()
        hbox.pack_start(self.value_entry, False, False)        
        hbox.pack_start(button_box, False, False)
        hbox_align = gtk.Alignment()
        hbox_align.set(0.5, 0.5, 1.0, 1.0)
        hbox_align.set_padding(0, 1, 0, 0)
        hbox_align.add(hbox)
        self.main_align.add(hbox_align)
        self.pack_start(self.main_align, False, False)
        
        # Signals.
        self.connect("size-allocate", self.size_change_cb)
        self.main_align.connect("expose-event", self.expose_spin_bg)
        
    def set_sensitive(self, sensitive):
        super(SpinBox, self).set_sensitive(sensitive)
        self.value_entry.set_sensitive(sensitive)
            
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
        if rect.width > self.default_width:
            self.default_width = rect.width
            
        self.set_size_request(self.default_width, self.default_height)
        self.value_entry.set_size_request(self.default_width - self.arrow_button_width, self.default_height - 2)
        
    def press_increase_button(self, widget, event):
        '''Press increase arrow.'''
        self.stop_update_value()
        
        self.increase_value()
        
        self.increase_value_id = gtk.timeout_add(self.update_delay, self.increase_value)
                
    def press_decrease_button(self, widget, event):
        '''Press decrease arrow.'''
        self.stop_update_value()
        
        self.decrease_value()
        
        self.decrease_value_id = gtk.timeout_add(self.update_delay, self.decrease_value)
        
    def handle_key_release(self, widget, event):
        '''Handle key release.'''
        self.stop_update_value()
        
        self.emit("key-release", self.current_value)
        
    def stop_update_value(self):
        '''Stop update value.'''
        for timeout_id in [self.increase_value_id, self.decrease_value_id]:
            remove_timeout_id(timeout_id)
        
    def increase_value(self):    
        new_value = self.current_value + self.step_value
        if new_value > self.upper_value: 
            new_value = self.upper_value
        if new_value != self.current_value:
            self.update_and_emit(new_value)
            
        return True    
            
    def decrease_value(self):     
        new_value = self.current_value - self.step_value
        if new_value < self.lower_value: 
            new_value = self.lower_value
        if new_value != self.current_value:
            self.update_and_emit(new_value)
            
        return True                
        
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
        
        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            if widget.state == gtk.STATE_INSENSITIVE:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("disable_frame").get_color()))
            else:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            if widget.state == gtk.STATE_INSENSITIVE:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("disable_background").get_color(), 0.9)))
            else:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
            cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
            cr.fill()
        
        propagate_expose(widget, event)
        
        return False
        
    def create_simple_button(self, name, callback=None):    
        button = DisableButton(
            (ui_theme.get_pixbuf("spin/spin_arrow_%s_normal.png" % name),
             ui_theme.get_pixbuf("spin/spin_arrow_%s_hover.png" % name),
             ui_theme.get_pixbuf("spin/spin_arrow_%s_press.png" % name),
             ui_theme.get_pixbuf("spin/spin_arrow_%s_disable.png" % name)),
            )
        if callback:
            button.connect("button-press-event", callback)
            button.connect("button-release-event", self.handle_key_release)
        return button

gobject.type_register(SpinBox)    
