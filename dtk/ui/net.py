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
import pango
from theme import ui_theme
from keymap import get_keyevent_name
from utils import (color_hex_to_cairo, alpha_color_hex_to_cairo, 
                   is_double_click,
                   cairo_disable_antialias, get_content_size)
from draw import draw_text, draw_hlinear

class IPV4Entry(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)
        self.width = 120
        self.height = 22
        self.set_size_request(self.width, self.height)
        self.normal_frame = ui_theme.get_color("combo_entry_frame")
        self.frame_color = self.normal_frame
        self.ip = "..."
        self.dot_size = 2
        self.grab_focus_flag = False
        self.ip_chars = map(str, range(0, 10)) + ["."]
        self.select_active_color=ui_theme.get_shadow_color("select_active_background")
        self.select_inactive_color=ui_theme.get_shadow_color("select_inactive_background")
        
        self.cursor_index = 0
        self.cursor_padding_y = 2
        self.cursor_positions = []
        self.cursor_segment_index = 0
        self.highlight_segment_index = None
        
        self.draw_area = gtk.EventBox()
        self.draw_area.set_visible_window(False)
        self.draw_area.add_events(gtk.gdk.ALL_EVENTS_MASK)        
        self.draw_area.set_can_focus(True) # can focus to response key-press signal
        self.pack_start(self.draw_area, True, True, 1)

        self.draw_area.connect("button-press-event", self.button_press_ipv4_entry)
        self.draw_area.connect("key-press-event", self.key_press_ipv4_entry)
        self.draw_area.connect("expose-event", self.expose_ipv4_entry)
        self.draw_area.connect("focus-in-event", self.focus_in_ipv4_entry)
        self.draw_area.connect("focus-out-event", self.focus_out_ipv4_entry)
        
        self.keymap = {
            "Left" : self.move_to_left,
            "Right" : self.move_to_right,
            "Home" : self.move_to_start,
            "End" : self.move_to_end,
            "Ctrl + a" : self.select_current_segment,
            "BackSpace" : self.backspace,
            }
        
        self.calculate_cursor_positions()
        
    def move_to_left(self):
        if self.cursor_index > 0:
            self.set_cursor_index(self.cursor_index - 1)
            self.clear_highlight_segment()
            self.queue_draw()
    
    def move_to_right(self):
        if self.cursor_index < len(self.ip):
            self.set_cursor_index(self.cursor_index + 1)
            self.clear_highlight_segment()
            self.queue_draw()
            
    def move_to_start(self):
        if self.cursor_index != 0:
            self.set_cursor_index(0)
            self.clear_highlight_segment()
            self.queue_draw()
            
    def move_to_end(self):
        if self.cursor_index != len(self.ip):
            self.set_cursor_index(len(self.ip))
            self.clear_highlight_segment()
            self.queue_draw()
        
    def set_ip(self, ip_string):
        ip = ip_string.replace(" ", "")
        if self.is_ip_address(ip):
            self.ip = ip 
            self.calculate_cursor_positions()
            self.queue_draw()
        else:
            print "%s is not valid IPv4 address" % ip_string
            
    def is_ip_address(self, ip_string):
        for ip_char in ip_string:
            if ip_char not in self.ip_chars:
                return False
            
        for ip_segment in ip_string.split("."):
            if ip_segment != "" and not self.in_valid_range(ip_segment):
                return False
            
        return True    
        
    def get_ip(self):
        return self.ip
    
    def calculate_cursor_positions(self):
        self.cursor_positions = []
        
        ip_segment_distance = self.width / 4
        ip_segments = self.ip.split(".")
        for (ip_segment_index, ip_segment) in enumerate(ip_segments):
            if len(ip_segment) == 0:
                self.cursor_positions.append(ip_segment_distance * ip_segment_index + ip_segment_distance / 2)
            else:
                (ip_segment_width, ip_segment_height) = get_content_size(ip_segment)
                ip_segment_x = ip_segment_distance * ip_segment_index
                ip_segment_offset_x = (ip_segment_distance - ip_segment_width) / 2
                ip_char_width = ip_segment_width / len(ip_segment)
                
                # Append ip char position.
                for (ip_char_index, ip_char) in enumerate(ip_segment):
                    self.cursor_positions.append(ip_segment_x + ip_segment_offset_x + ip_char_width * ip_char_index)
                    
                # Append the position of last char in ip segment.
                self.cursor_positions.append(ip_segment_x + ip_segment_offset_x + ip_char_width * (ip_char_index + 1))
            
    def button_press_ipv4_entry(self, widget, event):
        self.draw_area.grab_focus()
        
        if event.x <= self.cursor_positions[0]:
            self.set_cursor_index(0)
        elif event.x >= self.cursor_positions[-1]:
            self.set_cursor_index(len(self.ip))
        else:
            for (cursor_index, cursor_position) in enumerate(self.cursor_positions):
                if cursor_position < event.x <= self.cursor_positions[cursor_index + 1]:
                    self.set_cursor_index(cursor_index)
                    break
                
        if is_double_click(event):
            self.highlight_current_segment()
        else:
            self.clear_highlight_segment()
                
        self.queue_draw()    
        
    def select_current_segment(self):
        self.highlight_current_segment()
        self.queue_draw()
        
    def backspace(self):
        ip_segments = self.ip.split(".")
        if self.highlight_segment_index != None:
            # Get new ip string.
            ip_segments[self.highlight_segment_index] = ""
            
            # Get new cursor index.
            string_before_select = ""
            for ip_segment in ip_segments[0:self.highlight_segment_index]:
                string_before_select += "%s." % ip_segment 
            new_cursor_index = len(string_before_select)
            
            # Set new ip.
            self.clear_highlight_segment()
            self.set_ip('.'.join(ip_segments))  # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index
        else:
            if ip_segments[self.cursor_segment_index] == "":
                if self.cursor_segment_index > 0:
                    self.move_to_left()
            else:
                # Get new cursor index.
                string_before_select = ""
                for ip_segment in ip_segments[0:self.cursor_segment_index]:
                    string_before_select += "%s." % ip_segment 
                segment_first_index = len(string_before_select)
                
                if self.cursor_index == segment_first_index:
                    if self.cursor_segment_index > 0:
                        self.move_to_left()
                else:
                    current_segment = ip_segments[self.cursor_segment_index]
                    before_insert_string = current_segment[0:self.cursor_index - segment_first_index - 1]
                    after_insert_string = current_segment[self.cursor_index - segment_first_index:len(current_segment)]
                    new_current_segment = before_insert_string + after_insert_string
                    new_cursor_index = self.cursor_index - 1
                    ip_segments[self.cursor_segment_index] = new_current_segment
                    
                    self.set_ip(".".join(ip_segments))
                    self.set_cursor_index(new_cursor_index)
        
    def highlight_current_segment(self):
        self.set_highlight_segment(self.cursor_segment_index)
        
    def set_highlight_segment(self, segment_index, move_cursor_right=False):
        # Get ip segments.
        ip_segments = self.ip.split(".")
        
        # Just highlight segment when segment content is not empty.
        if len(ip_segments[segment_index]) > 0:
            self.highlight_segment_index = segment_index
        
        # Set new cursor after at end of next segment.
        current_segment = ip_segments[segment_index]
        string_before_select = ""
        for ip_segment in ip_segments[0:segment_index]:
            string_before_select += "%s." % ip_segment 
            
        new_cursor_index = len(string_before_select) + len(current_segment)
        
        self.set_cursor_index(new_cursor_index)
        self.queue_draw()
    
    def clear_highlight_segment(self):
        self.highlight_segment_index = None
        
    def key_press_ipv4_entry(self, widget, event):
        self.handle_key_event(event)
        
    def handle_key_event(self, event):
        key_name = get_keyevent_name(event, False)
        
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
        elif key_name in map(str, range(0, 10)):
            self.insert_ip_number(key_name)
        elif key_name == ".":
            self.insert_ip_dot()
            
    def set_cursor_index(self, cursor_index):
        self.cursor_index = cursor_index
        
        dot_indexes = []
        for (ip_char_index, ip_char) in enumerate(self.ip):
            if ip_char == ".":
                dot_indexes.append(ip_char_index)
                
        self.cursor_segment_index = 0
        for (segment_index, dot_index) in enumerate(dot_indexes):
            if cursor_index > dot_index:
                self.cursor_segment_index = segment_index + 1
            else:    
                break
            
    def insert_ip_number(self, ip_number):
        if self.highlight_segment_index != None:
            # Get new ip string.
            ip_segments = self.ip.split(".")
            ip_segments[self.highlight_segment_index] = ip_number
            
            # Get new cursor index.
            string_before_select = ""
            for ip_segment in ip_segments[0:self.highlight_segment_index]:
                string_before_select += "%s." % ip_segment 
            new_cursor_index = len(string_before_select) + 1
            
            # Set new ip.
            self.clear_highlight_segment()
            self.set_ip('.'.join(ip_segments))  # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index
        else:
            # Get last index of current segment.
            ip_segments = self.ip.split(".")
            current_segment = ip_segments[self.cursor_segment_index]
            current_segment_len = len(current_segment)
            
            string_before_select = ""
            for ip_segment in ip_segments[0:self.cursor_segment_index]:
                string_before_select += "%s." % ip_segment 
                
            last_index = len(string_before_select) + len(current_segment)
            
            # Insert ip character at end of current segment.
            if last_index == self.cursor_index:
                if current_segment_len < 3:
                    new_current_segment = current_segment + ip_number
                    self.set_current_segment(ip_segments, new_current_segment, True)
            # Insert at middle if current cursor not at end position.
            else:
                if current_segment_len < 3:
                    split_offset = last_index - self.cursor_index
                    before_insert_string = current_segment[0:current_segment_len - split_offset]
                    after_insert_string = current_segment[-split_offset:current_segment_len]
                    new_current_segment = before_insert_string + ip_number + after_insert_string
                    self.set_current_segment(ip_segments, new_current_segment)
                        
    def set_current_segment(self, ip_segments, new_current_segment, highlight_next_segment=False):
        if self.in_valid_range(new_current_segment):
            new_cursor_index = self.cursor_index + 1
            ip_segments[self.cursor_segment_index] = new_current_segment
            self.set_ip('.'.join(ip_segments)) # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index
            
            if highlight_next_segment:
                # Highlight next segment if have 3 characters in current segment.
                if len(new_current_segment) >= 3 and self.cursor_segment_index != 3:
                    self.set_highlight_segment(self.cursor_segment_index + 1, True)
                    self.queue_draw()
                    
    def in_valid_range(self, ip_segment):
        try:
            return 0 <= int(ip_segment) <= 255
        except:
            return False
    
    def insert_ip_dot(self):
        # Just move cursort to next segment when cursor haven't at last segment.
        if self.cursor_segment_index < 3:
            self.set_highlight_segment(self.cursor_segment_index + 1, True)
            self.queue_draw()
            
    def focus_in_ipv4_entry(self, widget, event):
        self.grab_focus_flag = True
        self.queue_draw()
        
    def focus_out_ipv4_entry(self, widget, event):
        self.grab_focus_flag = False
        self.queue_draw()

    def expose_ipv4_entry(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation        
        
        self.draw_background(cr, rect)
        
        self.draw_ip(cr, rect)
        
        self.draw_cursor(cr, rect)
        
        return True
        
    def draw_background(self, cr, rect):    
        with cairo_disable_antialias(cr):                                           
            # Draw frame.
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            cr.set_line_width(1)                                                    
            cr.set_source_rgb(*color_hex_to_cairo(
                self.frame_color.get_color()))
            cr.rectangle(x, y, w, h)                   
            cr.stroke()                                                             
            
            # Draw background.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(
                (ui_theme.get_color("combo_entry_background").get_color(), 0.9)))            
            cr.rectangle(x, y, w - 1, h - 1)       
            cr.fill()        
            
            # Draw ipv4 dot.
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
            dot_distance = self.width / 4
            dot_bottom_padding = 9
            for index in range(0, 3):
                cr.rectangle(x + dot_distance * (index + 1) - self.dot_size / 2, y + h - dot_bottom_padding, self.dot_size, self.dot_size)
                cr.fill()
                
    def draw_ip(self, cr, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        ip_segment_distance = self.width / 4
        for (ip_segment_index, ip_segment) in enumerate(self.ip.split(".")):
            text_color = "#000000"
            if ip_segment_index == self.highlight_segment_index:
                (ip_segment_width, ip_segment_height) = get_content_size(ip_segment)
                
                if self.grab_focus_flag:
                    background_color = self.select_active_color.get_color_info()
                else:
                    background_color = self.select_inactive_color.get_color_info()
                draw_hlinear(
                    cr,
                    x + ip_segment_index * ip_segment_distance + (ip_segment_distance - ip_segment_width) / 2,
                    y + self.cursor_padding_y,
                    ip_segment_width + 1,
                    h - self.cursor_padding_y * 2,
                    background_color,
                    )
                
                text_color = "#FFFFFF"
                
            draw_text(cr, ip_segment,
                      x + ip_segment_index * ip_segment_distance,
                      y,
                      ip_segment_distance,
                      h,
                      alignment=pango.ALIGN_CENTER,
                      text_color=text_color,
                      )
            
    def draw_cursor(self, cr, rect):
        if self.grab_focus_flag and self.highlight_segment_index == None:
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            cr.set_source_rgba(0, 0, 0, 1.0)
            cr.rectangle(x + self.cursor_positions[self.cursor_index], y + self.cursor_padding_y, 1, h - self.cursor_padding_y * 2)
            cr.fill()
        
gobject.type_register(IPV4Entry)
