#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Zhai Xiang
# 
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from draw import draw_pixbuf, cairo_state
from theme import ui_theme
from skin_config import skin_config
import gobject
import gtk
from button import Button
from label import Label
from constant import ALIGN_START, ALIGN_MIDDLE

class DateTime(gtk.VBox):
    def __init__(self, 
                 hour_value, 
                 minute_value, 
                 second_value = None, 
                 width=200, 
                 height=100, 
                 box_spacing=100):
        gtk.VBox.__init__(self)
        
        self.hour_value = hour_value
        self.minute_value = minute_value
        self.second_value = second_value
        
        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)
        self.text_size = self.height - 60

        '''
        + button
        '''
        self.top_align = self.__setup_align()
        self.top_box = gtk.HBox(spacing = box_spacing)
        self.hour_up_button = Button("+")
        self.hour_up_button.connect("button-press-event", self.__hour_up_button_press)
        self.minute_up_button = Button("+")
        self.minute_up_button.connect("button-press-event", self.__minute_up_button_press)
        self.__widget_pack_start(self.top_box, [self.hour_up_button, self.minute_up_button])
        self.top_align.add(self.top_box)
        '''
        datetime label
        '''
        self.datetime_align = self.__setup_align()
        self.datetime_box = gtk.HBox(spacing=10)
        self.hour_label = self.__setup_label(("%d" % self.hour_value).zfill(2), self.text_size, self.height)
        self.comma_label = self.__setup_label(":", self.text_size, 30)
        self.minute_label = self.__setup_label(("%d" % self.minute_value).zfill(2), self.text_size, self.height)
        self.__widget_pack_start(self.datetime_box, 
                                 [self.hour_label, self.comma_label, self.minute_label])
        self.datetime_align.add(self.datetime_box)
        '''
        - button
        '''
        self.buttom_align = self.__setup_align()
        self.buttom_box = gtk.HBox(spacing = box_spacing)
        self.hour_down_button = Button("-")
        self.hour_down_button.connect("button-press-event", self.__hour_down_button_press)
        self.minute_down_button = Button("-")
        self.minute_down_button.connect("button-press-event", self.__minute_down_button_press)
        self.__widget_pack_start(self.buttom_box, [self.hour_down_button, self.minute_down_button])
        self.buttom_align.add(self.buttom_box)
        '''
        this->VBox pack_start
        '''
        self.__widget_pack_start(self, [self.top_align, self.datetime_align, self.buttom_align])

    def __setup_align(self, 
                      xalign=0.5, 
                      yalign=0.5, 
                      xscale=1.0, 
                      yscale=1.0, 
                      padding_top=10, 
                      padding_bottom=10, 
                      padding_left=10, 
                      padding_right=10):
        align = gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        align.set_padding(padding_top, padding_bottom, padding_left, padding_right)
        return align

    def __setup_label(self, text, text_size=40, width=60, align=ALIGN_MIDDLE):
        label = Label(text, None, text_size, align, width)
        return label
    
    def __widget_pack_start(self, parent_widget, widgets=[], expand=False, fill=False):
        if parent_widget == None:                                                
            return                                                               
            
        for item in widgets:                                                     
            parent_widget.pack_start(item, expand, fill)

    def __hour_up_button_press(self, widget, event):
        self.hour_value += 1

        if self.hour_value >= 24:
            self.hour_value = 0

        self.hour_label.set_text(("%d" % self.hour_value).zfill(2))

    def __hour_down_button_press(self, widget, event):
        self.hour_value -= 1

        if self.hour_value <= 0:
            self.hour_value = 23

        self.hour_label.set_text(("%d" % self.hour_value).zfill(2))

    def __minute_up_button_press(self, widget, event):
        self.minute_value += 1

        if self.minute_value >= 60:
            self.minute_value = 0

        self.minute_label.set_text(("%d" % self.minute_value).zfill(2))

    def __minute_down_button_press(self, widget, event):
        self.minute_value -= 1

        if self.minute_value <= 0:
            self.minute_value = 59

        self.minute_label.set_text(("%d" % self.minute_value).zfill(2))

gobject.type_register(DateTime)
