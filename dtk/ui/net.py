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
from locales import _
from menu import Menu
from theme import ui_theme
from keymap import get_keyevent_name
from utils import (color_hex_to_cairo, alpha_color_hex_to_cairo,
                   is_double_click, is_right_button, is_left_button,
                   cairo_disable_antialias, get_content_size)
from draw import draw_text, draw_hlinear
from gsettings import DESKTOP_SETTINGS, DEFAULT_CURSOR_BLINK_TIME

class IPV4Entry(gtk.VBox):
    '''
    IPV4Entry class.

    @undocumented: is_ip_address
    @undocumented: calculate_cursor_positions
    @undocumented: button_press_ipv4_entry
    @undocumented: paste_ip
    @undocumented: highlight_current_segment
    @undocumented: set_highlight_segment
    @undocumented: clear_highlight_segment
    @undocumented: key_press_ipv4_entry
    @undocumented: handle_key_event
    @undocumented: insert_ip_number
    @undocumented: set_current_segment
    @undocumented: in_valid_range
    @undocumented: insert_ip_dot
    @undocumented: focus_in_ipv4_entry
    @undocumented: cursor_flash_tick
    @undocumented: focus_out_ipv4_entry
    @undocumented: expose_ipv4_entry
    @undocumented: draw_background
    @undocumented: draw_ip
    @undocumented: draw_cursor
    '''

    __gsignals__ = {
        "editing" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "invalid-value" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }

    def __init__(self):
        '''
        Initialize IPV4Entry class.
        '''
        gtk.VBox.__init__(self)
        self.width = 120
        self.height = 22
        self.set_size_request(self.width, self.height)
        self.normal_frame = ui_theme.get_color("entry_normal_frame")
        self.alert_frame = ui_theme.get_color("entry_alert_frame")
        self.frame_color = self.normal_frame
        self.default_address = "..."
        self.ip = self.default_address
        self.dot_size = 2
        self.grab_focus_flag = False
        self.segment_split_char = "."
        self.ip_chars = map(str, range(0, 10)) + [self.segment_split_char]
        self.select_active_color=ui_theme.get_shadow_color("select_active_background")
        self.select_inactive_color=ui_theme.get_shadow_color("select_inactive_background")
        self.segment_number = 4
        self.last_segment_index = self.segment_number - 1
        self.segment_max_chars = 3

        self.cursor_index = 0
        self.cursor_padding_y = 2
        self.cursor_positions = []
        self.cursor_segment_index = 0
        self.highlight_segment_index = None

        self.cursor_alpha = 1
        self.cursor_blank_id = None
        self.edit_complete_flag = True
        self.edit_timeout_id = None

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
        self.connect("editing", self.__edit_going)

        self.keymap = {
            "Left" : self.move_to_left,
            "Right" : self.move_to_right,
            "Home" : self.move_to_start,
            "End" : self.move_to_end,
            "Ctrl + a" : self.select_current_segment,
            "Ctrl + c" : self.copy_to_clipboard,
            "Ctrl + x" : self.cut_to_clipboard,
            "Ctrl + v" : self.paste_from_clipboard,
            "BackSpace" : self.backspace,
            "Space" : self.insert_ip_dot,
            "." : self.insert_ip_dot,
            }

        self.right_menu = Menu(
            [(None, _("Cut"), self.cut_to_clipboard),
             (None, _("Copy"), self.copy_to_clipboard),
             (None, _("Paste"), self.paste_from_clipboard),
             ],
            True)

        self.calculate_cursor_positions()

    def set_frame_alert(self, state):
        '''
        Make frame show alert color.

        @param state: Show alert color if state is True, otherwise show normal color.
        '''
        if state:
            self.frame_color = self.alert_frame
        else:
            self.frame_color = self.normal_frame

        # FIXME must let parent redraw, maybe let user do this?
        self.parent.queue_draw()

    def move_to_left(self):
        '''
        Move cursor backward.
        '''
        if self.cursor_index > 0:
            self.set_cursor_index(self.cursor_index - 1)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_right(self):
        '''
        Move cursor forward.
        '''
        if self.cursor_index < len(self.ip):
            self.set_cursor_index(self.cursor_index + 1)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_start(self):
        '''
        Move cursor to start position.
        '''
        if self.cursor_index != 0:
            self.set_cursor_index(0)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_end(self):
        '''
        Move cursor to end position.
        '''
        if self.cursor_index != len(self.ip):
            self.set_cursor_index(len(self.ip))
            self.clear_highlight_segment()
            self.queue_draw()

    def set_address(self, address):
        self.set_ip(address)

    def set_ip(self, ip_string):
        '''
        Set ipv4 address.

        @param ip_string: The string of ipv4 address.
        @return: Return True if ip_string set successful, emit `invalid-value` signal and return False is ip address is not valid format.
        '''
        ip = ip_string.replace(" ", "")
        if self.is_ip_address(ip):
            if self.ip != ip:
                if ip == self.default_address:
                    self.emit("changed", "")
                else:
                    self.emit("changed", ip)

            self.ip = ip
            self.calculate_cursor_positions()
            self.queue_draw()

            return True
        else:
            self.emit("invalid-value", ip_string)

            return False

    def is_ip_address(self, ip_string):
        for ip_char in ip_string:
            if ip_char not in self.ip_chars:
                return False

        for ip_segment in ip_string.split(self.segment_split_char):
            if ip_segment != "" and not self.in_valid_range(ip_segment):
                return False

        return True

    def get_address(self):
        return self.get_ip()

    def get_ip(self):
        '''
        Get ip address.

        @return: Return string of ip address.
        '''
        return self.ip

    def calculate_cursor_positions(self):
        self.cursor_positions = []

        ip_segment_distance = self.width / self.segment_number
        ip_segments = self.ip.split(self.segment_split_char)
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
            ip_segment_distance = self.width / self.segment_number
            segment_index = int(event.x / ip_segment_distance)

            for (cursor_index, cursor_position) in enumerate(self.cursor_positions):
                if len(self.ip.split(self.segment_split_char)[segment_index]) == 0:
                    self.set_cursor_index(segment_index)
                    break
                elif cursor_position < event.x <= self.cursor_positions[cursor_index + 1]:
                    self.set_cursor_index(cursor_index)
                    break

        # Hide right menu immediately.
        self.right_menu.hide()

        if is_double_click(event):
            self.highlight_current_segment()
        elif is_left_button(event):
            self.clear_highlight_segment()
        elif is_right_button(event):
            x, y = self.window.get_root_origin()
            wx, wy = int(event.x), int(event.y)
            (offset_x, offset_y) = widget.translate_coordinates(self, 0, 0)
            (_, px, py, modifier) = widget.get_display().get_pointer()
            self.right_menu.show((px - offset_x, py - wy - offset_y + widget.allocation.height))

        self.queue_draw()

    def select_current_segment(self):
        '''
        Select current ip segment.
        '''
        self.highlight_current_segment()
        self.queue_draw()

    def cut_to_clipboard(self):
        '''
        Cut ip address to clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.set_text(self.get_ip())
        self.set_ip(self.default_address)
        self.move_to_start()

    def copy_to_clipboard(self):
        '''
        Copy ip address to clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.set_text(self.get_ip())

    def paste_from_clipboard(self):
        '''
        Paste ip address from clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.request_text(lambda clipboard, text, data: self.paste_ip(text))

    def paste_ip(self, text):
        if self.set_ip(text):
            self.move_to_end()

    def backspace(self):
        '''
        Delete backward.
        '''
        ip_segments = self.ip.split(self.segment_split_char)
        if self.highlight_segment_index != None:
            # Get new ip string.
            ip_segments[self.highlight_segment_index] = ""

            # Get new cursor index.
            string_before_select = ""
            for ip_segment in ip_segments[0:self.highlight_segment_index]:
                string_before_select += "%s%s" % (ip_segment, self.segment_split_char)
            new_cursor_index = len(string_before_select)

            # Set new ip.
            self.clear_highlight_segment()
            self.set_ip(self.segment_split_char.join(ip_segments))  # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index
        else:
            if ip_segments[self.cursor_segment_index] == "":
                if self.cursor_segment_index > 0:
                    self.move_to_left()
            else:
                # Get new cursor index.
                string_before_select = ""
                for ip_segment in ip_segments[0:self.cursor_segment_index]:
                    string_before_select += "%s%s" % (ip_segment, self.segment_split_char)
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

                    self.set_ip(self.segment_split_char.join(ip_segments))
                    self.set_cursor_index(new_cursor_index)

    def highlight_current_segment(self):
        self.set_highlight_segment(self.cursor_segment_index)

    def set_highlight_segment(self, segment_index, move_cursor_right=False):
        # Get ip segments.
        ip_segments = self.ip.split(self.segment_split_char)

        # Just highlight segment when segment content is not empty.
        if len(ip_segments[segment_index]) > 0:
            self.highlight_segment_index = segment_index

        # Set new cursor after at end of next segment.
        current_segment = ip_segments[segment_index]
        string_before_select = ""
        for ip_segment in ip_segments[0:segment_index]:
            string_before_select += "%s%s" % (ip_segment, self.segment_split_char)

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
            self.emit("editing")
        elif key_name in map(str, range(0, 10)):
            self.insert_ip_number(key_name)
            self.emit("editing")

    def set_cursor_index(self, cursor_index):
        '''
        Set cursor index.

        @param cursor_index: The cursor index to set.
        '''
        self.cursor_index = cursor_index

        dot_indexes = []
        for (ip_char_index, ip_char) in enumerate(self.ip):
            if ip_char == self.segment_split_char:
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
            ip_segments = self.ip.split(self.segment_split_char)
            ip_segments[self.highlight_segment_index] = ip_number

            # Get new cursor index.
            string_before_select = ""
            for ip_segment in ip_segments[0:self.highlight_segment_index]:
                string_before_select += "%s%s" % (ip_segment, self.segment_split_char)
            new_cursor_index = len(string_before_select) + 1

            # Set new ip.
            self.clear_highlight_segment()
            self.set_ip(self.segment_split_char.join(ip_segments))  # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index
        else:
            # Get last index of current segment.
            ip_segments = self.ip.split(self.segment_split_char)
            current_segment = ip_segments[self.cursor_segment_index]
            current_segment_len = len(current_segment)

            string_before_select = ""
            for ip_segment in ip_segments[0:self.cursor_segment_index]:
                string_before_select += "%s%s" % (ip_segment, self.segment_split_char)

            last_index = len(string_before_select) + len(current_segment)

            # Insert ip character at end of current segment.
            if last_index == self.cursor_index:
                # if current_segment_len < self.last_segment_index:
                if current_segment_len < self.segment_max_chars:
                    new_current_segment = current_segment + ip_number
                    self.set_current_segment(ip_segments, new_current_segment, True)
            # Insert at middle if current cursor not at end position.
            else:
                # if current_segment_len < self.last_segment_index:
                if current_segment_len < self.segment_max_chars:
                    split_offset = last_index - self.cursor_index
                    before_insert_string = current_segment[0:current_segment_len - split_offset]
                    after_insert_string = current_segment[-split_offset:current_segment_len]
                    new_current_segment = before_insert_string + ip_number + after_insert_string
                    self.set_current_segment(ip_segments, new_current_segment)

    def set_current_segment(self, ip_segments, new_current_segment, highlight_next_segment=False):
        if self.in_valid_range(new_current_segment):
            new_cursor_index = self.cursor_index + 1
            ip_segments[self.cursor_segment_index] = new_current_segment
            self.set_ip(self.segment_split_char.join(ip_segments)) # set ip first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set ip, otherwise will got wrong cursor_segment_index

            if highlight_next_segment:
                # Highlight next segment if have 3 characters in current segment.
                # if len(new_current_segment) >= self.last_segment_index and self.cursor_segment_index != self.last_segment_index:
                if len(new_current_segment) >= self.segment_max_chars and self.cursor_segment_index != self.last_segment_index:
                    self.set_highlight_segment(self.cursor_segment_index + 1, True)
                    self.queue_draw()

    def in_valid_range(self, ip_segment):
        try:
            #print ip_segment, " ", int(ip_segment)
            return 0 <= int(ip_segment) <= 255
        except:
            return False

    def insert_ip_dot(self):
        # Just move cursor to next segment when cursor haven't at last segment.
        if self.cursor_segment_index < self.last_segment_index:
            ip_segments = self.ip.split(self.segment_split_char)
            current_segment = ip_segments[self.cursor_segment_index]
            if len(current_segment) > 0:
                self.set_highlight_segment(self.cursor_segment_index + 1, True)
                self.queue_draw()

    def focus_in_ipv4_entry(self, widget, event):
        self.grab_focus_flag = True
        self.queue_draw()

        if self.cursor_blank_id != None:
            gobject.source_remove(self.cursor_blank_id)

        try:
            cursor_blink_time = int(DESKTOP_SETTINGS.get_int("cursor-blink-time") / 2)
        except Exception:
            cursor_blink_time = DEFAULT_CURSOR_BLINK_TIME
        self.cursor_blank_id = gobject.timeout_add(cursor_blink_time, self.cursor_flash_tick)

    def cursor_flash_tick(self):
        # redraw entry text and cursor
        self.queue_draw()

        # according edit status change cursor alpha color every 500 microsecond
        if self.cursor_alpha == 1 and self.edit_complete_flag:
            self.cursor_alpha = 0
        else:
            self.cursor_alpha = 1
        return self.grab_focus_flag

    def __edit_going(self, widget):
        self.cursor_alpha = 1
        self.edit_complete_flag = False
        if self.edit_timeout_id != None:
            gobject.source_remove(self.edit_timeout_id)
        self.edit_timeout_id = gobject.timeout_add(500, self.__wait_edit_complete)

    def __wait_edit_complete(self):
        self.edit_complete_flag = True
        return False

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
            dot_distance = self.width / self.segment_number
            dot_bottom_padding = 9
            for index in range(0, self.last_segment_index):
                cr.rectangle(x + dot_distance * (index + 1) - self.dot_size / 2, y + h - dot_bottom_padding, self.dot_size, self.dot_size)
                cr.fill()

    def draw_ip(self, cr, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        ip_segment_distance = self.width / self.segment_number
        for (ip_segment_index, ip_segment) in enumerate(self.ip.split(self.segment_split_char)):
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
            cr.set_source_rgba(0, 0, 0, self.cursor_alpha)
            cr.rectangle(x + self.cursor_positions[self.cursor_index], y + self.cursor_padding_y, 1, h - self.cursor_padding_y * 2)
            cr.fill()

gobject.type_register(IPV4Entry)

class MACEntry(gtk.VBox):
    '''
    MACEntry class.

    @undocumented: is_mac_address
    @undocumented: calculate_cursor_positions
    @undocumented: button_press_mac_entry
    @undocumented: paste_mac
    @undocumented: highlight_current_segment
    @undocumented: set_highlight_segment
    @undocumented: clear_highlight_segment
    @undocumented: key_press_mac_entry
    @undocumented: handle_key_event
    @undocumented: insert_mac_number
    @undocumented: set_current_segment
    @undocumented: in_valid_range
    @undocumented: insert_mac_dot
    @undocumented: focus_in_mac_entry
    @undocumented: cursor_flash_tick
    @undocumented: focus_out_mac_entry
    @undocumented: expose_mac_entry
    @undocumented: draw_background
    @undocumented: draw_mac
    @undocumented: draw_cursor
    '''

    __gsignals__ = {
        "editing" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "invalid-value" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }

    def __init__(self):
        '''
        Initialize MACEntry class.
        '''
        gtk.VBox.__init__(self)
        self.width = 130
        self.height = 22
        self.set_size_request(self.width, self.height)
        self.normal_frame = ui_theme.get_color("entry_normal_frame")
        self.alert_frame = ui_theme.get_color("entry_alert_frame")
        self.frame_color = self.normal_frame
        self.default_address = ":::::"
        self.mac = self.default_address
        self.grab_focus_flag = False
        self.segment_split_char = ":"
        self.dot_size = get_content_size(self.segment_split_char)[0]
        self.chars_a_z = map(lambda a: str(chr(a)), range(97, 103))
        self.chars_A_Z = map(lambda a: str(chr(a)), range(65, 71))
        self.mac_chars = self.chars_a_z + self.chars_A_Z + map(str, range(0, 10)) + [self.segment_split_char]
        self.select_active_color=ui_theme.get_shadow_color("select_active_background")
        self.select_inactive_color=ui_theme.get_shadow_color("select_inactive_background")
        self.segment_number = 6
        self.last_segment_index = self.segment_number - 1
        self.segment_max_chars = 2

        self.cursor_index = 0
        self.cursor_padding_y = 2
        self.cursor_positions = []
        self.cursor_segment_index = 0
        self.highlight_segment_index = None

        self.cursor_alpha = 1
        self.cursor_blank_id = None
        self.edit_complete_flag = True
        self.edit_timeout_id = None

        self.draw_area = gtk.EventBox()
        self.draw_area.set_visible_window(False)
        self.draw_area.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.draw_area.set_can_focus(True) # can focus to response key-press signal
        self.pack_start(self.draw_area, True, True, 1)

        self.draw_area.connect("button-press-event", self.button_press_mac_entry)
        self.draw_area.connect("key-press-event", self.key_press_mac_entry)
        self.draw_area.connect("expose-event", self.expose_mac_entry)
        self.draw_area.connect("focus-in-event", self.focus_in_mac_entry)
        self.draw_area.connect("focus-out-event", self.focus_out_mac_entry)
        self.connect("editing", self.__edit_going)

        self.keymap = {
            "Left" : self.move_to_left,
            "Right" : self.move_to_right,
            "Home" : self.move_to_start,
            "End" : self.move_to_end,
            "Ctrl + a" : self.select_current_segment,
            "Ctrl + c" : self.copy_to_clipboard,
            "Ctrl + x" : self.cut_to_clipboard,
            "Ctrl + v" : self.paste_from_clipboard,
            "BackSpace" : self.backspace,
            "Space" : self.insert_mac_dot,
            ":" : self.insert_mac_dot,
            }

        self.right_menu = Menu(
            [(None, _("Cut"), self.cut_to_clipboard),
             (None, _("Copy"), self.copy_to_clipboard),
             (None, _("Paste"), self.paste_from_clipboard),
             ],
            True)

        self.calculate_cursor_positions()

    def set_frame_alert(self, state):
        '''
        Make frame show alert color.

        @param state: Show alert color if state is True, otherwise show normal color.
        '''
        if state:
            self.frame_color = self.alert_frame
        else:
            self.frame_color = self.normal_frame

        self.queue_draw()

    def move_to_left(self):
        '''
        Move cursor backward.
        '''
        if self.cursor_index > 0:
            self.set_cursor_index(self.cursor_index - 1)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_right(self):
        '''
        Move cursor forward.
        '''
        if self.cursor_index < len(self.mac):
            self.set_cursor_index(self.cursor_index + 1)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_start(self):
        '''
        Move cursor to start position.
        '''
        if self.cursor_index != 0:
            self.set_cursor_index(0)
            self.clear_highlight_segment()
            self.queue_draw()

    def move_to_end(self):
        '''
        Move cursor to end position.
        '''
        if self.cursor_index != len(self.mac):
            self.set_cursor_index(len(self.mac))
            self.clear_highlight_segment()
            self.queue_draw()

    def set_address(self, address):
        self.set_mac(address)

    def set_mac(self, mac_string):
        '''
        Set mac address.

        @param mac_string: The string of mac address.
        @return: Return True if mac_string set successful, emit `invalid-value` signal and return False is mac address is not valid format.
        '''
        mac = mac_string.replace(" ", "")
        if self.is_mac_address(mac):
            if self.mac != mac:
                if mac == self.default_address:
                    self.emit("changed", "")
                else:
                    self.emit("changed", mac)

            self.mac = mac
            self.calculate_cursor_positions()
            self.queue_draw()

            return True
        else:
            self.emit("invalid-value", mac_string)

            return False

    def is_mac_address(self, mac_string):
        for mac_char in mac_string:
            if mac_char not in self.mac_chars:
                return False

        for mac_segment in mac_string.split(self.segment_split_char):
            if mac_segment != "" and not self.in_valid_range(mac_segment):
                return False

        return True

    def get_address(self):
        return self.get_mac()

    def get_mac(self):
        '''
        Get mac address.

        @return: Return string of mac address.
        '''
        return self.mac

    def calculate_cursor_positions(self):
        self.cursor_positions = []

        mac_segment_distance = self.width / self.segment_number
        mac_segments = self.mac.split(self.segment_split_char)
        for (mac_segment_index, mac_segment) in enumerate(mac_segments):
            if len(mac_segment) == 0:
                self.cursor_positions.append(mac_segment_distance * mac_segment_index + mac_segment_distance / 2)
            else:
                (mac_segment_width, mac_segment_height) = get_content_size(mac_segment)
                mac_segment_x = mac_segment_distance * mac_segment_index
                mac_segment_offset_x = (mac_segment_distance - mac_segment_width) / 2
                mac_char_width = mac_segment_width / len(mac_segment)

                # Append mac char position.
                for (mac_char_index, mac_char) in enumerate(mac_segment):
                    self.cursor_positions.append(mac_segment_x + mac_segment_offset_x + mac_char_width * mac_char_index)

                # Append the position of last char in mac segment.
                self.cursor_positions.append(mac_segment_x + mac_segment_offset_x + mac_char_width * (mac_char_index + 1))

    def button_press_mac_entry(self, widget, event):
        self.draw_area.grab_focus()

        if event.x <= self.cursor_positions[0]:
            self.set_cursor_index(0)
        elif event.x >= self.cursor_positions[-1]:
            self.set_cursor_index(len(self.mac))
        else:
            ip_segment_distance = self.width / self.segment_number
            segment_index = int(event.x / ip_segment_distance)

            for (cursor_index, cursor_position) in enumerate(self.cursor_positions):
                if len(self.mac.split(self.segment_split_char)[segment_index]) == 0:
                    self.set_cursor_index(segment_index)
                    break
                elif cursor_position < event.x <= self.cursor_positions[cursor_index + 1]:
                    self.set_cursor_index(cursor_index)
                    break

        # Hide right menu immediately.
        self.right_menu.hide()

        if is_double_click(event):
            self.highlight_current_segment()
        elif is_left_button(event):
            self.clear_highlight_segment()
        elif is_right_button(event):
            x, y = self.window.get_root_origin()
            wx, wy = int(event.x), int(event.y)
            (offset_x, offset_y) = widget.translate_coordinates(self, 0, 0)
            (_, px, py, modifier) = widget.get_display().get_pointer()
            self.right_menu.show((px - offset_x, py - wy - offset_y + widget.allocation.height))

        self.queue_draw()

    def select_current_segment(self):
        '''
        Select current mac segment.
        '''
        self.highlight_current_segment()
        self.queue_draw()

    def cut_to_clipboard(self):
        '''
        Cut mac address to clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.set_text(self.get_mac())
        self.set_mac(self.default_address)
        self.move_to_start()

    def copy_to_clipboard(self):
        '''
        Copy mac address to clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.set_text(self.get_mac())

    def paste_from_clipboard(self):
        '''
        Paste mac address from clipboard.
        '''
        clipboard = gtk.Clipboard()
        clipboard.request_text(lambda clipboard, text, data: self.paste_mac(text))

    def paste_mac(self, text):
        if self.set_mac(text):
            self.move_to_end()

    def backspace(self):
        '''
        Delete backward.
        '''
        mac_segments = self.mac.split(self.segment_split_char)
        if self.highlight_segment_index != None:
            # Get new mac string.
            mac_segments[self.highlight_segment_index] = ""

            # Get new cursor index.
            string_before_select = ""
            for mac_segment in mac_segments[0:self.highlight_segment_index]:
                string_before_select += "%s%s" % (mac_segment, self.segment_split_char)
            new_cursor_index = len(string_before_select)

            # Set new mac.
            self.clear_highlight_segment()
            self.set_mac(self.segment_split_char.join(mac_segments))  # set mac first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set mac, otherwise will got wrong cursor_segment_index
        else:
            if mac_segments[self.cursor_segment_index] == "":
                if self.cursor_segment_index > 0:
                    self.move_to_left()
            else:
                # Get new cursor index.
                string_before_select = ""
                for mac_segment in mac_segments[0:self.cursor_segment_index]:
                    string_before_select += "%s%s" % (mac_segment, self.segment_split_char)
                segment_first_index = len(string_before_select)

                if self.cursor_index == segment_first_index:
                    if self.cursor_segment_index > 0:
                        self.move_to_left()
                else:
                    current_segment = mac_segments[self.cursor_segment_index]
                    before_insert_string = current_segment[0:self.cursor_index - segment_first_index - 1]
                    after_insert_string = current_segment[self.cursor_index - segment_first_index:len(current_segment)]
                    new_current_segment = before_insert_string + after_insert_string
                    new_cursor_index = self.cursor_index - 1
                    mac_segments[self.cursor_segment_index] = new_current_segment

                    self.set_mac(self.segment_split_char.join(mac_segments))
                    self.set_cursor_index(new_cursor_index)

    def highlight_current_segment(self):
        self.set_highlight_segment(self.cursor_segment_index)

    def set_highlight_segment(self, segment_index, move_cursor_right=False):
        # Get mac segments.
        mac_segments = self.mac.split(self.segment_split_char)

        # Just highlight segment when segment content is not empty.
        if len(mac_segments[segment_index]) > 0:
            self.highlight_segment_index = segment_index

        # Set new cursor after at end of next segment.
        current_segment = mac_segments[segment_index]
        string_before_select = ""
        for mac_segment in mac_segments[0:segment_index]:
            string_before_select += "%s%s" % (mac_segment, self.segment_split_char)

        new_cursor_index = len(string_before_select) + len(current_segment)

        self.set_cursor_index(new_cursor_index)
        self.queue_draw()

    def clear_highlight_segment(self):
        self.highlight_segment_index = None

    def key_press_mac_entry(self, widget, event):
        self.handle_key_event(event)

    def handle_key_event(self, event):
        key_name = get_keyevent_name(event, False)

        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
            self.emit("editing")
        elif key_name in self.chars_a_z + self.chars_A_Z + map(str, range(0, 10)):
            self.insert_mac_number(key_name)
            self.emit("editing")

    def set_cursor_index(self, cursor_index):
        '''
        Set cursor index.

        @param cursor_index: The cursor index to set.
        '''
        self.cursor_index = cursor_index

        dot_indexes = []
        for (mac_char_index, mac_char) in enumerate(self.mac):
            if mac_char == self.segment_split_char:
                dot_indexes.append(mac_char_index)

        self.cursor_segment_index = 0
        for (segment_index, dot_index) in enumerate(dot_indexes):
            if cursor_index > dot_index:
                self.cursor_segment_index = segment_index + 1
            else:
                break

    def insert_mac_number(self, mac_number):
        # Convert to upper character first.
        if mac_number in self.chars_a_z:
            mac_number = mac_number.upper()

        if self.highlight_segment_index != None:
            # Get new mac string.
            mac_segments = self.mac.split(self.segment_split_char)
            mac_segments[self.highlight_segment_index] = mac_number

            # Get new cursor index.
            string_before_select = ""
            for mac_segment in mac_segments[0:self.highlight_segment_index]:
                string_before_select += "%s%s" % (mac_segment, self.segment_split_char)
            new_cursor_index = len(string_before_select) + 1

            # Set new mac.
            self.clear_highlight_segment()
            self.set_mac(self.segment_split_char.join(mac_segments))  # set mac first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set mac, otherwise will got wrong cursor_segment_index
        else:
            # Get last index of current segment.
            mac_segments = self.mac.split(self.segment_split_char)
            current_segment = mac_segments[self.cursor_segment_index]
            current_segment_len = len(current_segment)

            string_before_select = ""
            for mac_segment in mac_segments[0:self.cursor_segment_index]:
                string_before_select += "%s%s" % (mac_segment, self.segment_split_char)

            last_index = len(string_before_select) + len(current_segment)

            # Insert mac character at end of current segment.
            if last_index == self.cursor_index:
                # if current_segment_len < self.last_segment_index:
                if current_segment_len < self.segment_max_chars:
                    new_current_segment = current_segment + mac_number
                    self.set_current_segment(mac_segments, new_current_segment, True)
            # Insert at middle if current cursor not at end position.
            else:
                # if current_segment_len < self.last_segment_index:
                if current_segment_len < self.segment_max_chars:
                    split_offset = last_index - self.cursor_index
                    before_insert_string = current_segment[0:current_segment_len - split_offset]
                    after_insert_string = current_segment[-split_offset:current_segment_len]
                    new_current_segment = before_insert_string + mac_number + after_insert_string
                    self.set_current_segment(mac_segments, new_current_segment)

    def set_current_segment(self, mac_segments, new_current_segment, highlight_next_segment=False):
        if self.in_valid_range(new_current_segment):
            new_cursor_index = self.cursor_index + 1
            mac_segments[self.cursor_segment_index] = new_current_segment
            self.set_mac(self.segment_split_char.join(mac_segments)) # set mac first.
            self.set_cursor_index(new_cursor_index) # NOTE: set new cursor index of set mac, otherwise will got wrong cursor_segment_index

            if highlight_next_segment:
                # Highlight next segment if have 3 characters in current segment.
                # if len(new_current_segment) >= self.last_segment_index and self.cursor_segment_index != self.last_segment_index:
                if len(new_current_segment) >= self.segment_max_chars and self.cursor_segment_index != self.last_segment_index:
                    self.set_highlight_segment(self.cursor_segment_index + 1, True)
                    self.queue_draw()

    def in_valid_range(self, mac_segment):
        try:
            return 0 <= int(mac_segment, 16) <= 255
        except:
            return False

    def insert_mac_dot(self):
        # Just move cursor to next segment when cursor haven't at last segment.
        if self.cursor_segment_index < self.last_segment_index:
            self.set_highlight_segment(self.cursor_segment_index + 1, True)
            self.queue_draw()

    def focus_in_mac_entry(self, widget, event):
        self.grab_focus_flag = True
        self.queue_draw()

        if self.cursor_blank_id != None:
            gobject.source_remove(self.cursor_blank_id)

        try:
            cursor_blink_time = int(DESKTOP_SETTINGS.get_int("cursor-blink-time") / 2)
        except Exception:
            cursor_blink_time = DEFAULT_CURSOR_BLINK_TIME
        self.cursor_blank_id = gobject.timeout_add(cursor_blink_time, self.cursor_flash_tick)

    def cursor_flash_tick(self):
        # redraw entry text and cursor
        self.queue_draw()

        # according edit status change cursor alpha color every 500 microsecond
        if self.cursor_alpha == 1 and self.edit_complete_flag:
            self.cursor_alpha = 0
        else:
            self.cursor_alpha = 1
        return self.grab_focus_flag

    def __edit_going(self, widget):
        self.cursor_alpha = 1
        self.edit_complete_flag = False
        if self.edit_timeout_id != None:
            gobject.source_remove(self.edit_timeout_id)
        self.edit_timeout_id = gobject.timeout_add(500, self.__wait_edit_complete)

    def __wait_edit_complete(self):
        self.edit_complete_flag = True
        return False

    def focus_out_mac_entry(self, widget, event):
        self.grab_focus_flag = False
        self.queue_draw()

    def expose_mac_entry(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        self.draw_background(cr, rect)

        self.draw_mac(cr, rect)

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

            # Draw mac dot.
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
            dot_distance = self.width / self.segment_number
            dot_bottom_padding = 18
            for index in range(0, self.last_segment_index):
                draw_text(cr,
                          self.segment_split_char,
                          x + dot_distance * (index + 1) - self.dot_size / 2,
                          y + h - dot_bottom_padding,
                          self.dot_size,
                          self.dot_size,
                          )

    def draw_mac(self, cr, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        mac_segment_distance = self.width / self.segment_number
        for (mac_segment_index, mac_segment) in enumerate(self.mac.split(self.segment_split_char)):
            text_color = "#000000"
            if mac_segment_index == self.highlight_segment_index:
                (mac_segment_width, mac_segment_height) = get_content_size(mac_segment)

                if self.grab_focus_flag:
                    background_color = self.select_active_color.get_color_info()
                else:
                    background_color = self.select_inactive_color.get_color_info()
                draw_hlinear(
                    cr,
                    x + mac_segment_index * mac_segment_distance + (mac_segment_distance - mac_segment_width) / 2,
                    y + self.cursor_padding_y,
                    mac_segment_width + 1,
                    h - self.cursor_padding_y * 2,
                    background_color,
                    )

                text_color = "#FFFFFF"

            draw_text(cr, mac_segment,
                      x + mac_segment_index * mac_segment_distance,
                      y,
                      mac_segment_distance,
                      h,
                      alignment=pango.ALIGN_CENTER,
                      text_color=text_color,
                      )

    def draw_cursor(self, cr, rect):
        if self.grab_focus_flag and self.highlight_segment_index == None:
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            cr.set_source_rgba(0, 0, 0, self.cursor_alpha)
            cr.rectangle(x + self.cursor_positions[self.cursor_index], y + self.cursor_padding_y, 1, h - self.cursor_padding_y * 2)
            cr.fill()

gobject.type_register(MACEntry)
