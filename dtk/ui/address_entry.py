#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Deepin, Inc.
#               2013 Zhai Xiang
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

from theme import ui_theme, DynamicColor
from utils import (color_hex_to_cairo, alpha_color_hex_to_cairo, 
                   cairo_disable_antialias, get_content_size,
                   container_remove_all)
from draw import draw_text
from new_entry import Entry
import gtk
import pango
import gobject

'''
only support ipv4
'''
class IpAddressEntry(gtk.HBox):

    __gsignals__ = {
        "focus-out" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,))
        }

    def __init__(self,
                 address = "",
                 width = 120,
                 height = 22,
                 alert_color="#e33939"):
        gtk.HBox.__init__(self)

        self.address = address
        self.ip_address = []
        self.entry_list = []
        self.width = width
        self.height = height
        self.alert_color = DynamicColor(alert_color)
        self.padding_x = 2
        self.token = "."
        self.ipv4_max = 255
        self.normal_frame = ui_theme.get_color("combo_entry_frame")
        self.frame_color = self.normal_frame

        self.connect("size-allocate", self.__on_size_allocate)
        self.connect("expose-event", self.__on_expose)
        self.connect("set-focus-child", self.__on_focus_child)

        self.__set_entry_list()

    def entry_changes(self, widget, content, index):
        if len(content) == 3:
            if index < 4:
                self.entry_list[index + 1].grab_focus()
    
    def __on_focus_child(self, widget, child):
        if child == None:
            self.emit("focus-out", widget.get_address())

    def __set_entry_list(self):
        if self.address != "":                                                  
            self.ip_address = [t for t in self.address.split(self.token)]
        else:
            self.ip_address = ""

        container_remove_all(self)
        self.entry_list = []

        ip_addr_len = len(self.ip_address)
        if ip_addr_len == 0:
            i = 0
            while i < 4:
                self.entry_list.append(Entry(padding_x = self.padding_x, is_ipv4 = True))
                self.pack_start(self.entry_list[i])
                i += 1
            map(lambda (i, e): e.connect("changed", self.entry_changes,i), enumerate(self.entry_list))
            return

        if ip_addr_len == 4:
            i = 0
            while i < 4:                                            
                self.entry_list.append(Entry(self.ip_address[i], padding_x = self.padding_x, is_ipv4 = True))
                self.pack_start(self.entry_list[i])                             
                i += 1                                                          
            map(lambda (i, e): e.connect("changed", self.entry_changes,i), enumerate(self.entry_list))
            return

    def set_frame_alert(self, state):
        if state:
            self.frame_color = self.alert_color
        else:
            self.frame_color = self.normal_frame
        # FIXME must let parent redraw, maybe let user do this?
        self.parent.queue_draw()

    def set_address(self, address):
        self.address = address
        self.__set_entry_list()
        self.queue_draw()

    def get_address(self):
        i = 0
        address = ""

        entry_list_len = len(self.entry_list)
        while i < entry_list_len:
            address += self.entry_list[i].get_text()
            
            if i < entry_list_len - 1:
                address += self.token
            i += 1

        return address

    def __on_size_allocate(self, widget, rect):
        if rect.width > self.width:                                             
            self.width = rect.width                                             
                                                                                
        self.set_size_request(self.width, self.height)                          

    def __on_expose(self, widget, event):
        cr = widget.window.cairo_create()                                       
        rect = widget.allocation 
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        token_spacing = 10
        
        ip_addr_len = len(self.ip_address) or 4
        i = 0
        
        '''
        check Ip Address format validate, it is better to use regex, 
        but regex is too heavy...
        '''
        if ip_addr_len != 0 and ip_addr_len != 4:
            print "IP address format is wrong!"
            return

        '''
        draw background
        '''
        with cairo_disable_antialias(cr):                                           
            cr.set_line_width(1)                                                    
            cr.set_source_rgb(*color_hex_to_cairo(
                self.frame_color.get_color()))
                #ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(x, y, w, h)                   
            cr.stroke()                                                             
                                                                                
            cr.set_source_rgba(*alpha_color_hex_to_cairo(
                (ui_theme.get_color("combo_entry_background").get_color(), 0.9)))            
            cr.rectangle(x, y, w - 1, h - 1)       
            cr.fill()        

        '''
        draw ip address and token
        '''
        ip_max_width, ip_max_height = get_content_size(str(self.ipv4_max))
        
        while i < ip_addr_len:
            if i != ip_addr_len - 1:
                draw_text(cr, 
                          self.token, 
                          x + (i + 1) * ip_max_width + i * token_spacing, 
                          y, 
                          token_spacing, 
                          h, 
                          alignment = pango.ALIGN_CENTER)
            
            i += 1

class MacAddressEntry(gtk.HBox):
    def __init__(self, address = "", width = 180, height = 22):
        gtk.HBox.__init__(self)

        self.address = address
        self.mac_address = []
        self.entry_list = []
        self.width = width
        self.height = height
        self.padding_x = 2
        self.token = ":"
        self.mac_max = "255"

        self.connect("size-allocate", self.__on_size_allocate)
        self.connect("expose-event", self.__on_expose)

        self.__set_entry_list()

    def __set_entry_list(self):
        if self.address != "":                                                  
            self.mac_address = [t for t in self.address.split(self.token)]

        mac_addr_len = len(self.mac_address)

        if mac_addr_len == 0:
            i = 0
            while i < 6:
                self.entry_list.append(Entry(padding_x = self.padding_x, is_mac = True))
                self.pack_start(self.entry_list[i])
                i += 1
            return

        if mac_addr_len == 6:
            i = 0
            while i < 6:                                                        
                self.entry_list.append(Entry(self.mac_address[i], padding_x = self.padding_x, is_mac = True))
                self.pack_start(self.entry_list[i])                             
                i += 1                                                          
            return

    def set_address(self, address):
        self.address = address
        self.__set_entry_list()
        self.queue_draw()

    def get_address(self):
        i = 0
        address = ""

        entry_list_len = len(self.entry_list)
        while i < entry_list_len:
            address += self.entry_list[i].get_text()
            
            if i < entry_list_len - 1:
                address += self.token

            i += 1

        return address

    def __on_size_allocate(self, widget, rect):
        if rect.width > self.width:                                             
            self.width = rect.width                                             
                                                                                
        self.set_size_request(self.width, self.height)                          

    def __on_expose(self, widget, event):
        cr = widget.window.cairo_create()                                       
        rect = widget.allocation 
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        token_spacing = 10
        
        mac_addr_len = len(self.mac_address)
        i = 0
        
        if mac_addr_len != 0 and mac_addr_len != 6:
            print "MAC address format is wrong!"
            return

        '''
        draw background
        '''
        with cairo_disable_antialias(cr):                                           
            cr.set_line_width(1)                                                    
            cr.set_source_rgb(*color_hex_to_cairo(
                ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(x, y, w, h)                   
            cr.stroke()                                                             
                                                                                
            cr.set_source_rgba(*alpha_color_hex_to_cairo(
                (ui_theme.get_color("combo_entry_background").get_color(), 0.9)))            
            cr.rectangle(x, y, w - 1, h - 1)       
            cr.fill()        

        '''
        draw ip address and token
        '''
        mac_max_width, mac_max_height = get_content_size(self.mac_max)
       
        while i < mac_addr_len:
            if i != mac_addr_len - 1:
                draw_text(cr, 
                          self.token, 
                          x + (i + 1) * mac_max_width + i * token_spacing, 
                          y, 
                          token_spacing, 
                          h, 
                          alignment = pango.ALIGN_CENTER)
            
            i += 1
