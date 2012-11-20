#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from constant import DEFAULT_FONT_SIZE, DEFAULT_FONT
from draw import draw_hlinear, draw_round_rectangle, draw_pixbuf
from keymap import get_keyevent_name
from locales import _
from menu import Menu
from theme import ui_theme
from contextlib import contextmanager 
import sys
import traceback
import gobject
import gtk
import pango
import cairo
import pangocairo
from dtk.ui.utils import (repeat, propagate_expose, cairo_state, color_hex_to_cairo, 
                   get_content_size, is_double_click, is_right_button, 
                   is_left_button, alpha_color_hex_to_cairo, cairo_disable_antialias)
import time
import threading as td

class CursorFlashThread(td.Thread):
    def __init__(self, argv):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = argv

    def run(self):
        try:
            self.draw_flash_cursor()
        except Exception, e:
            print "class LoadingThread got error: %s" % (e)
            traceback.print_exc(file=sys.stdout)

    def draw_flash_cursor(self):
        enable_flash = True
        while (True):
            if enable_flash:
                self.ThisPtr.m_draw_cursor()
            else:
                self.ThisPtr.m_clear_cursor()
            enable_flash = not enable_flash
            time.sleep(1)

class EntryBuffer(gobject.GObject):
    '''
    EntryBuffer
    stores text for display in a Entry
    '''
    __gproperties__ = {
        'cursor-visible': (gobject.TYPE_BOOLEAN, 'cursor_visible', 'cursor visible',
            True, gobject.PARAM_READWRITE),
        'visibility': (gobject.TYPE_BOOLEAN, 'visibility', 'visibility',
            True, gobject.PARAM_READWRITE),
        'select-area-visible': (gobject.TYPE_BOOLEAN, 'select_area_visible', 'select area visible',
            True, gobject.PARAM_READWRITE),
        'invisible-char': (gobject.TYPE_CHAR, 'invisible_char', 'invisible char', ' ', '~', '*', gobject.PARAM_READWRITE)}
    __gsignals__ = {
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "insert-pos-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "selection-pos-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}
    
    def __init__(self, text='',
                 font=DEFAULT_FONT,
                 font_size=DEFAULT_FONT_SIZE,
                 font_weight='normal',
                 text_color=ui_theme.get_color("entry_text").get_color(),
                 text_select_color=ui_theme.get_color("entry_select_text").get_color(),
                 background_select_color=ui_theme.get_shadow_color("entry_select_background"),
                 enable_clear_button=False,
                ):
        '''
        text: the buffer content
        @param text: Entry initialize content, default is \"\".
        @param font: font family, default is DEFAULT_FONT.
        @param font_size: font size, default is DEFAULT_FONT_SIZE.
        @param font_weight: font weight, default is 'normal'.
        @param text_color: Color of text in normal status, a hex string.
        @param text_select_color: Color of text in select status, a hex string.
        @param background_select_color: Color of background in select status, a hex string.
        '''
        self.__gobject_init__()
        self.buffer = gtk.TextBuffer()
        self.alignment = pango.ALIGN_LEFT
        self.font = font
        self.font_weight = font_weight
        self.font_size = font_size
        self.text_color = text_color
        self.text_select_color = text_select_color
        self.background_select_color = background_select_color
        self.cursor_cr = None
        self.cursor_x = -1
        self.cursor_y = -1
        self.cursor_pos1 = -1
        self.cursor_pos2 = -1
        '''
        TODO: Add clear button
        '''
        self.enable_clear_button = enable_clear_button
        '''
        property
        '''
        self.__prop_dict = {}
        self.__prop_dict['cursor-visible'] = True
        self.__prop_dict['select-area-visible'] = True
        self.__prop_dict['visibility'] = True
        self.__prop_dict['invisible-char'] = '*'

        # pango layout
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 0, 0) 
        cr = cairo.Context(surface)
        pango_cr = pangocairo.CairoContext(cr)
        self._layout = pango_cr.create_layout()
        self._layout.set_font_description(
            pango.FontDescription("%s %s %d" % (self.font, self.font_weight, self.font_size)))
        self._layout.set_alignment(self.alignment)
        self._layout.set_single_paragraph_mode(True)
        self.set_text(text)
        self.buffer.connect("changed", lambda bf: self.emit("changed"))

    def do_set_property(self, pspec, value):
        if pspec.name in self.__prop_dict:
            self.__prop_dict[pspec.name] = value
        else:
            raise AttributeError, 'unknown property %s' % pspec.name
    
    def do_get_property(self, pspec):
        if pspec.name in self.__prop_dict:
            return self.__prop_dict[pspec.name]
        else:
            raise AttributeError, 'unknown property %s' % pspec.name
    
    def set_font_family(self, font_family):
        '''
        set font family
        @param font_family: a string representing the family name.
        '''
        self.font = font_family
        self._layout.set_font_description(
            pango.FontDescription("%s %s %d" % (self.font, self.font_weight, self.font_size)))
    
    def get_font_family(self):
        '''
        get font family
        @return: a string representing the family name.
        '''
        return self.font
    
    def set_font_weight(self, font_weight):
        '''
        set font weight
        @param font_weight: the weight for the font description. The value must be one of pango weight. A string type
        '''
        self.font_weight = font_weight
        self._layout.set_font_description(
            pango.FontDescription("%s %s %d" % (self.font, self.font_weight, self.font_size)))
    
    def get_font_weight(self):
        '''
        get font weight
        @return: the weight for the font description. A string type
        '''
        return self.font_weight
    
    def set_font_size(self, font_size):
        '''
        set font size
        @param font_size: the size for the font description. An int type
        '''
        self.font_size = font_size
        self._layout.set_font_description(
            pango.FontDescription("%s %s %d" % (self.font, self.font_weight, self.font_size)))
    
    def get_font_size(self):
        '''
        get font size
        @return: the size for the font description. An int type
        '''
        return self.font_size
    
    def set_alignment(self, alignment):
        '''
        set alignment
        @param alignment: the alignment, the value must be one of pango alignment
        '''
        self.alignment = alignment
        self._layout.set_alignment(alignment)

    def get_alignment(self):
        '''
        get alignment
        @return: the alignment
        '''
        return self._layout.get_alignment()
    
    def set_invisible_char(self, char):
        '''
        set invisible-char property
        @param char: a Unicode character
        '''
        if not char:
            char = '*'
        #self.set_property("invisible-char", char[0])
        self.set_property('invisible-char', char[0])
    
    def get_invisible_char(self):
        '''
        get invisible-char property
        @return: a Unicode character
        '''
        #return self.get_property("invisible-char")
        return self.get_property('invisible-char')
    
    def set_visibility(self, visible):
        '''
        set visibility property
        @param visible: a bool type
        '''
        self.set_property("visibility", visible)
    
    def get_visibility(self):
        '''
        get visibility property
        @return: a bool type
        '''
        return self.get_property("visibility")
    
    def get_cursor_visible(self):
        '''
        get curosr-visible property
        @return: a bool type
        '''
        return self.get_property("cursor-visible")
    
    def set_cursor_visible(self, cursor_visible):
        '''
        set cursor-visible property
        @param cursor_visible: a bool type
        '''
        self.set_property("cursor-visible", cursor_visible)
    
    def set_text(self, text):
        '''
        set text to display
        @param text: the new text, a string.
        '''
        if text is None:
            text = ''
        self.buffer.set_text('\\n'.join(text.split('\n')))
        self._layout.set_text(self.get_text())
    
    def get_text(self):
        '''
        get text
        @return: the text showed, a string
        '''
        return self.buffer.get_text(*self.buffer.get_bounds())
    
    def place_cursor(self, offset):
        '''
        move insert-cursor and selection-cursor to the location specified by index.
        @param offset: a int num
        '''
        self.set_insert_pos(offset)
        self.set_selection_pos(offset)
    
    def set_insert_pos(self, pos):
        '''
        set insert-cursor location by pos
        @param pos: a int num
        '''
        if pos < 0:
            pos = 0
        max_offset = self.get_char_count()
        if pos > max_offset:
            pos = max_offset
        tmp_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        tmp_iter.set_line_offset(pos)
        self.buffer.move_mark_by_name("insert", tmp_iter)
        self.emit("insert-pos-changed")
    
    def get_insert_pos(self):
        '''
        get insert-curosr localtion offset
        @return: a int num
        '''
        insert_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        return insert_iter.get_line_offset()
    
    def get_insert_index(self):
        '''
        get insert-curosr localtion index
        @return: a int num
        '''
        insert_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        return insert_iter.get_line_index()
    
    def get_selection_pos(self):
        '''
        get selection-curosr localtion
        @return: a int num
        '''
        selection_iter = self.buffer.get_iter_at_mark(self.buffer.get_selection_bound())
        return selection_iter.get_line_offset()
    
    def get_selection_index(self):
        '''
        get selection-curosr localtion
        @return: a int num
        '''
        selection_iter = self.buffer.get_iter_at_mark(self.buffer.get_selection_bound())
        return selection_iter.get_line_index()
    
    def set_selection_pos(self, pos):
        '''
        set selection-cursor location by pos
        @param pos: a int num
        '''
        if pos < 0:
            pos = 0
        max_offset = self.get_char_count()
        if pos > max_offset:
            pos = max_offset
        tmp_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        tmp_iter.set_line_offset(pos)
        self.buffer.move_mark_by_name("selection_bound", tmp_iter)
        self.emit("selection-pos-changed")
    
    def get_selection_bounds(self):
        '''
        get selection bounds index
        @return: a 2-tuple containing the selction-range left pos and right pos
        '''
        bounds = self.buffer.get_selection_bounds()
        if not bounds:
            return bounds
        return (bounds[0].get_line_index(), bounds[1].get_line_index())
    
    def set_text_color(self, color):
        '''
        set text color
        @param color: the font color, a hex string
        '''
        self.text_color = color

    def get_text_color(self):
        '''
        get text color
        @return: the font color, a hex string
        '''
        return self.text_color
    
    def get_has_selection(self):
        '''
        get has-selection property
        @return: a bool type
        '''
        return self.buffer.get_has_selection()
    
    def get_length(self):
        '''
        get text length
        @return: the bytes num, an int num
        '''
        first_line = self.buffer.get_iter_at_line(0)
        return first_line.get_bytes_in_line()
    
    def get_char_count(self):
        '''
        get characters num
        @return: the chars num
        '''
        first_line = self.buffer.get_iter_at_line(0)
        return first_line.get_chars_in_line()
   
    def render(self, cr, rect, im=None, offset_x=0):
        '''render. Used by widget'''
        # Clip text area first.
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        cr.rectangle(x, y, w, h)
        cr.clip()
        # Draw text
        with cairo_state(cr):
            length = self.get_length()
            if self.get_visibility():
                self._layout.set_text(self.get_text())
            else:
                self._layout.set_text(self.get_invisible_char()*length)
            layout = self._layout.copy()
            # Create pangocairo context.
            context = pangocairo.CairoContext(cr)
            cr.move_to(x - offset_x, y)
            cr.set_source_rgb(*color_hex_to_cairo(self.text_color))
            context.update_layout(layout)
            context.show_layout(layout)
            # Draw selected text.
            if self.get_has_selection() and self.get_property("select-area-visible"):
                (left_pos, right_pos)= self.get_selection_bounds()
                if self.get_visibility():
                    layout.set_text(self.get_text()[left_pos:right_pos])
                else:
                    layout.set_text(self.get_invisible_char()*(right_pos-left_pos))
                # draw selection background
                mid_begin_pos = self.get_cursor_pos(left_pos)[0]
                mid_end_pos = self.get_cursor_pos(right_pos)[0]
                draw_hlinear(cr, 
                             x+mid_begin_pos[0]-offset_x,
                             y+mid_begin_pos[1],
                             mid_end_pos[0]-mid_begin_pos[0],
                             mid_begin_pos[3],
                             self.background_select_color.get_color_info())
                cr.move_to(x+mid_begin_pos[0]-offset_x, y)
                cr.set_source_rgb(*color_hex_to_cairo(self.text_select_color))
                context.update_layout(layout)
                context.show_layout(layout)
            # Draw cursor
            if self.get_cursor_visible():
                # Init.
                cursor_index = self.get_insert_index()
                cursor_pos = self.get_cursor_pos(cursor_index)[0]
                # Draw cursor.
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("entry_cursor").get_color()))
                cursor_pos_x = cursor_pos[0] + x - offset_x
                '''
                TODO: re-calc cursor pos when enabled clear button
                '''
                if self.enable_clear_button and x + w < cursor_pos_x:
                    cursor_pos_x = x + w - 1
                '''
                FIXME: switched im at first time, cursor pos was wrong
                '''
                if im:
                    im.set_cursor_location(gtk.gdk.Rectangle(cursor_pos[0]+x-offset_x, cursor_pos[1]+y, 1, cursor_pos[3]))
                
                self.cursor_cr = cr
                self.cursor_x = cursor_pos_x
                self.cursor_y = y
                self.cursor_pos1 = cursor_pos[1]
                self.cursor_pos2 = cursor_pos[3]
                self.m_draw_cursor()
                '''
                FIXME: HOWTO flash cursor
                CursorFlashThread(self).start()
                '''
    
    def m_draw_cursor(self):
        self.cursor_cr.set_source_rgb(0, 0, 0)
        self.cursor_cr.rectangle(self.cursor_x, 
                                 self.cursor_pos1 + self.cursor_y, 
                                 1, 
                                 self.cursor_pos2)
        self.cursor_cr.fill()

    def m_clear_cursor(self):
        self.cursor_cr.set_source_rgb(255, 255, 255)
        self.cursor_cr.rectangle(self.cursor_x, 
                                 self.cursor_pos1 + self.cursor_y, 
                                 1, 
                                 self.cursor_pos2)
        self.cursor_cr.fill()

    def get_cursor_pos(self, cursor):
        '''
        get cursor pos
        @return: a 2-lists containing two 4-lists representing the strong and weak cursor positions
        '''
        poses = list(self._layout.get_cursor_pos(cursor))
        new_poses = []
        for pos in poses:
            pos = list(pos)
            pos[0] /= pango.SCALE
            pos[1] /= pango.SCALE
            pos[2] /= pango.SCALE
            pos[3] /= pango.SCALE
            new_poses.append(pos)
        return new_poses
    
    def index_to_pos(self, index):
        '''
        index to pos
        @param index: the index of the text, an int num
        @return: a list containing the char's coordinate
        '''
        pos = self._layout.index_to_pos(index)
        pos = list(pos)
        pos[0] /= pango.SCALE
        pos[1] /= pango.SCALE
        pos[2] /= pango.SCALE
        pos[3] /= pango.SCALE
        return pos
    
    def xy_to_index(self, x, y):
        '''
        coord to index
        @param x: the x coord
        @param y: the y coord
        @return: the index
        '''
        return self._layout.xy_to_index(x, y)
    
    def index_to_offset(self, index):
        '''
        convert byte index to char offset
        @param index: the byte index from start of line
        '''
        if index < 0:
            index = 0
        elif index >= self.get_length():
            index = self.get_length()
        pos_iter = self.buffer.get_iter_at_line_index(0, index)
        return pos_iter.get_line_offset()
    
    def offset_to_index(self, offset):
        '''
        convert char offset to byte index
        @param offset: the char offset from start of line
        '''
        if offset < 0:
            offset = 0
        elif offset >= self.get_char_count():
            offset = self.get_char_count()
        pos_iter = self.buffer.get_iter_at_line_offset(0, offset)
        return pos_iter.get_line_index()
    
    def get_pixel_size(self):
        '''
        get the layout text size
        @return: a 2-tuple containing the logical width height of the pango.Layout
        '''
        return self._layout.get_pixel_size()
    
    def move_to_end(self):
        '''move insert cursor to end'''
        self.place_cursor(self.get_length())
    
    def move_to_start(self):
        '''move insert cursor to start'''
        self.place_cursor(0)
    
    def move_to_left(self):
        '''move insert cursor to left'''
        current = self.get_insert_pos()
        self.place_cursor(current-1)
    
    def move_to_right(self):
        '''move insert cursor to rigth'''
        current = self.get_insert_pos()
        self.place_cursor(current+1)

    def select_to_end(self):
        '''move selection cursor to end'''
        self.set_insert_pos(self.get_length())
    
    def select_to_start(self):
        '''move selection cursor to start'''
        self.set_insert_pos(0)
    
    def select_to_left(self):
        '''move selection cursor to left'''
        current = self.get_insert_pos()
        self.set_insert_pos(current-1)
     
    def select_to_right(self):
        '''move selection cursor to right'''
        current = self.get_insert_pos()
        self.set_insert_pos(current+1)
    
    def select_all(self):
        '''select all text'''
        self.set_selection_pos(0)
        self.set_insert_pos(self.get_char_count())
    
    def delete_selection(self):
        '''delete the selected text'''
        self.buffer.delete_selection(True, True)
    
    def insert_at_cursor(self, text):
        '''
        insert text at insert-cursor
        @param text: some text in UTF-8 format
        '''
        self.buffer.insert_at_cursor('\\n'.join(text.split('\n')))
        self._layout.set_text(self.get_text())
    
    def insert(self, pos, text):
        '''
        insert text
        @param pos: insert at the pos, an int type.
        @param text: the text to insert
        '''
        if pos < 0:
            pos = 0
        if pos > self.get_length():
            pos = self.get_length()
        tmp_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        tmp_iter.set_line_offset(pos)
        self.buffer.insert(tmp_iter, '\\n'.join(text.split('\n')))
        self._layout.set_text(self.get_text())
    
    def backspace(self):
        '''backspace'''
        self.buffer.backspace(
            self.buffer.get_iter_at_mark(self.buffer.get_insert()), True, True)
        self._layout.set_text(self.get_text())
    
    def delete(self):
        '''delete'''
        tmp_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        if tmp_iter.ends_line():
            return
        self.move_to_right()
        self.backspace()
    
    def cut_clipboard(self, clipboard, editable=True):
        '''
        copies the currently-selected text to the clipboard, then deletes said text if it's editable
        @param clipboard: a gtk.Clipboard type
        @param editable: whether the buffer is editable, a bool type
        '''
        self.buffer.cut_clipboard(clipboard, editable)
    
    def copy_clipboard(self, clipboard):
        '''
        copies the currently-selected text to the clipboard
        @param clipboard: a gtk.Clipboard type
        '''
        self.buffer.copy_clipboard(clipboard)
    
    def paste_clipboard(self, clipboard, editable=True):
        '''
        pastes the contents of the clipboard at the insertion point
        @param clipboard: a gtk.Clipboard type
        @param editable: whether the buffer is editable, a bool type
        '''
        self.buffer.paste_clipboard(clipboard, None, editable)
    
gobject.type_register(EntryBuffer)

class Entry(gtk.EventBox):
    '''
    Entry.
    
    @undocumented: monitor_entry_content
    @undocumented: realize_entry
    @undocumented: key_press_entry
    @undocumented: handle_key_press
    @undocumented: handle_key_event
    @undocumented: expose_entry
    @undocumented: draw_entry_background
    @undocumented: draw_entry_text
    @undocumented: draw_entry_cursor
    @undocumented: button_press_entry
    @undocumented: handle_button_press
    @undocumented: button_release_entry
    @undocumented: motion_notify_entry
    @undocumented: focus_in_entry
    @undocumented: focus_out_entry
    @undocumented: handle_focus_out
    @undocumented: move_offsetx_right
    @undocumented: move_offsetx_left
    @undocumented: get_index_at_event
    @undocumented: commit_entry
    @undocumented: get_content_width
    @undocumented: get_utf8_string
    '''
    
    MOVE_LEFT = 1
    MOVE_RIGHT = 2
    MOVE_NONE = 3
    
    __gsignals__ = {
        "edit-alarm" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "press-return" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "invalid-value" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, 
                 content="", 
                 padding_x=5, 
                 padding_y=2,
                 text_color=ui_theme.get_color("entry_text"),
                 text_select_color=ui_theme.get_color("entry_select_text"),
                 background_select_color=ui_theme.get_shadow_color("entry_select_background"),
                 font_size=DEFAULT_FONT_SIZE, 
                 enable_clear_button=False,
                 ):
        '''
        Initialize Entry class.
        
        @param content: Entry initialize content, default is \"\".
        @param padding_x: Horizontal padding value, default is 5 pixel.
        @param padding_y: Vertical padding value, default is 2 pixel.
        @param text_color: Color of text in normal status.
        @param text_select_color: Color of text in select status.
        @param background_select_color: Color of background in select status.
        @param font_size: Entry font size, default is DEFAULT_FONT_SIZE.
        '''
        # Init.
        gtk.EventBox.__init__(self)
        # in order to compatible before code
        if not isinstance(text_color, str):
            text_color = text_color.get_color()
        if not isinstance(text_select_color, str):
            text_select_color = text_select_color.get_color()
        self.entry_buffer = EntryBuffer(
            content, DEFAULT_FONT, font_size,
            'noraml', text_color, text_select_color, 
            background_select_color, enable_clear_button)
        '''
        TODO: Add clear button
        '''
        self.clear_button = ClearButton(False)
        self.enable_clear_button = enable_clear_button
        self.clear_button_x = -1
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.im = gtk.IMMulticontext()
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.move_direction = self.MOVE_NONE
        self.double_click_flag = False
        self.left_click_flag = False
        self.left_click_coordindate = None
        self.grab_focus_flag = False
        self.editable_flag = True
        self.check_text = None
        self.cursor_visible_flag = True
        self.right_menu_visible_flag = True
        self.select_area_visible_flag = True
        self.entry_buffer.set_property("select-area-visible", self.select_area_visible_flag)
        
        self.offset_x = 0
        
        # Add keymap.
        self.keymap = {
            "Left" : self.move_to_left,
            "Right" : self.move_to_right,
            "Home" : self.move_to_start,
            "End" : self.move_to_end,
            "BackSpace" : self.backspace,
            "Delete" : self.delete,
            "Shift + Left" : self.select_to_left,
            "Shift + Right" : self.select_to_right,
            "Shift + Home" : self.select_to_start,
            "Shift + End" : self.select_to_end,
            "Ctrl + a" : self.select_all,
            "Ctrl + x" : self.cut_to_clipboard,
            "Ctrl + c" : self.copy_to_clipboard,
            "Ctrl + v" : self.paste_from_clipboard,
            "Return" : self.press_return}
        
        # Add menu.
        self.right_menu = Menu(
            [(None, _("Cut"), self.cut_to_clipboard),
             (None, _("Copy"), self.copy_to_clipboard),
             (None, _("Paste"), self.paste_from_clipboard),
             (None, _("Select all"), self.select_all)],
            True)
        
        # Connect signal.
        self.connect_after("realize", self.realize_entry)
        self.connect("key-press-event", self.key_press_entry)
        self.connect("expose-event", self.expose_entry)
        self.connect("button-press-event", self.button_press_entry)
        self.connect("button-release-event", self.button_release_entry)
        self.connect("motion-notify-event", self.motion_notify_entry)
        self.connect("focus-in-event", self.focus_in_entry)
        self.connect("focus-out-event", self.focus_out_entry)
        
        self.im.connect("commit", lambda im, input_text: self.commit_entry(input_text))
    
    def set_editable(self, editable):
        '''
        Set entry editable status.
        
        @param editable: If it is True, entry can edit, else entry not allow edit.
        '''
        self.editable_flag = editable
        
    @contextmanager
    def monitor_entry_content(self):
        '''
        Internal function to monitor entry content.
        '''
        old_text = self.get_text()
        try:  
            yield  
        except Exception, e:  
            print 'function monitor_entry_content got error %s' % e  
            traceback.print_exc(file=sys.stdout)
        else:  
            new_text = self.get_text()
            if self.check_text is None or self.check_text(new_text):
                if old_text != new_text:
                    self.emit("changed", new_text)
            else:
                self.emit("invalid-value", new_text)
                self.set_text(old_text)
                
    def is_editable(self):
        '''
        Whether entry is editable.
        
        @return: Return True if entry editable, else return False. 
        '''
        if not self.editable_flag:
            self.emit("edit-alarm")
            
        return self.editable_flag    
        
    def set_text(self, text):
        '''
        Set entry text.
        
        @param text: Entry text string.
        '''
        if self.is_editable():
            with self.monitor_entry_content():
                if text is not None:
                    self.entry_buffer.set_text(text)
                    '''
                    FIXME: if call set_text then cursor offset is wrong
                    '''
                    #self.__calculate_cursor_offset()
            self.queue_draw()
        
    def get_text(self):
        '''
        Get entry text.
        
        @return: Return entry text string.
        '''
        return self.entry_buffer.get_text()
    
    def get_buffer(self):
        '''
        get EntryBuffer
        @return: the EntryBuffer
        '''
        return self.entry_buffer
    
    def set_buffer(self, entry_buffer):
        '''
        set EntryBuffer
        @param entry_buffer: the EntryBuffer'''
        self.entry_buffer = entry_buffer
    
    def realize_entry(self, widget):
        '''
        Internal callback for `realize` signal.
        '''
        self.__calculate_cursor_offset()
            
        self.im.set_client_window(widget.window)
        
    def key_press_entry(self, widget, event):
        '''
        Internal callback for `key-press-event` signal.
        '''
        self.handle_key_press(widget, event)
        
    def handle_key_press(self, widget, event):
        '''
        Internal function to handle key press.
        '''
        # Pass key to IMContext.
        input_method_filt = self.im.filter_keypress(event)
        if not input_method_filt:
            self.handle_key_event(event)
        
        return False
    
    def handle_key_event(self, event):
        '''
        Internal function to handle key event.
        '''
        key_name = get_keyevent_name(event)
        
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
            
    def clear_select_status(self):
        '''
        Clear entry select status.
        '''
        self.entry_buffer.set_selection_pos(self.entry_buffer.get_insert_pos())
        self.move_direction = self.MOVE_NONE            
            
    def move_to_start(self):
        '''
        Move cursor to start position of entry.
        '''
        self.entry_buffer.move_to_start()
        self.offset_x = 0
        self.queue_draw()
        
    def move_to_end(self):
        '''
        Move cursor to end position of entry.
        '''
        self.entry_buffer.move_to_end()
        self.__calculate_cursor_offset()
        self.queue_draw()
        
    def move_to_left(self):
        '''
        Backward cursor one char.
        '''
        # Avoid change focus to other widget in parent.
        if self.keynav_failed(gtk.DIR_LEFT):
            self.get_toplevel().set_focus_child(self)
            
        self.entry_buffer.move_to_left()
        # comput coord offset
        self.__calculate_cursor_offset()
        self.queue_draw()
            
    def move_to_right(self):
        '''
        Forward cursor one char.
        '''
        # Avoid change focus to other widget in parent.
        if self.keynav_failed(gtk.DIR_RIGHT):
            self.get_toplevel().set_focus_child(self)
                        
        self.entry_buffer.move_to_right()
        self.__calculate_cursor_offset()
        self.queue_draw()
            
    def backspace(self):
        '''
        Do backspace action.
        '''        
        if self.is_editable():
            with self.monitor_entry_content():
                if self.entry_buffer.get_has_selection():
                    self.entry_buffer.delete_selection()
                else:
                    self.entry_buffer.backspace()

                # comput coord offset
                self.__calculate_cursor_offset()
            self.queue_draw()    
            
    def select_all(self):
        '''
        Select all text of entry.
        '''
        self.entry_buffer.select_all()
        self.__calculate_cursor_offset()
        self.queue_draw()
        
    def cut_to_clipboard(self):
        '''
        Cut selected text to clipboard.
        '''
        with self.monitor_entry_content():
            self.entry_buffer.cut_clipboard(gtk.Clipboard(), self.is_editable())
        self.queue_draw()

    def copy_to_clipboard(self):
        '''
        Copy selected text to clipboard.
        '''
        self.entry_buffer.copy_clipboard(gtk.Clipboard())
    
    def paste_from_clipboard(self):
        '''
        Paste text to entry from clipboard.
        '''
        if self.is_editable():
            with self.monitor_entry_content():
                clipboard = gtk.Clipboard()    
                clipboard.request_text(lambda clipboard, text, data: self.commit_entry('\\n'.join(text.split('\n'))))
                
    def press_return(self):
        '''
        Do return action.
        '''
        self.emit("press-return")
        
    def select_to_left(self):
        '''
        Select text to left char.
        '''
        self.entry_buffer.select_to_left()
        self.__calculate_cursor_offset()
        self.queue_draw()
        
    def select_to_right(self):
        '''
        Select text to right char.
        '''
        self.entry_buffer.select_to_right()
        self.__calculate_cursor_offset()
        self.queue_draw()        
        
    def select_to_start(self):
        '''
        Select text to start position.
        '''
        self.entry_buffer.select_to_start()
        self.offset_x = 0    
        self.queue_draw()
        
    def select_to_end(self):
        '''
        Select text to end position.
        '''
        self.entry_buffer.select_to_end()
        self.__calculate_cursor_offset()
        self.queue_draw()
        
    def delete(self):
        '''
        Delete selected text.
        '''
        if self.is_editable():
            with self.monitor_entry_content():
                if self.entry_buffer.get_has_selection():
                    self.entry_buffer.delete_selection()
                else:
                    self.entry_buffer.delete()

                self.__calculate_cursor_offset()
            self.queue_draw()
                            
    def expose_entry(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        rect.x += self.padding_x
        rect.y += self.padding_y
        '''
        TODO: keep some space for clear button
        '''
        if self.enable_clear_button:
            rect.width -= (2 * self.padding_x + ClearButton.button_padding_x)
            self.clear_button_x = rect.width
        else:
            rect.width -= 2 * self.padding_x
        rect.height -= 2 * self.padding_y
        
        # Draw background.
        if not self.get_sensitive():
            self.entry_buffer.set_property("select-area-visible", False)

        '''
        TODO: Draw clear button
        ''' 
        if self.enable_clear_button and len(self.get_text()):
            self.clear_button.render(cr, rect)
        
        '''
        Draw entry
        '''
        self.entry_buffer.render(cr, rect, self.im, self.offset_x)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def button_press_entry(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.
        '''
        if self.enable_clear_button and not event.x < self.clear_button_x:
            self.set_text("")
        self.handle_button_press(widget, event)
        
    def handle_button_press(self, widget, event):
        '''
        Internal function to handle button press.
        '''
        # Get input focus.
        self.grab_focus()
        
        # Hide right menu immediately.
        self.right_menu.hide()
        
        # Select all when double click left button.
        if is_double_click(event):
            self.double_click_flag = True
            self.select_all()
        # Show right menu when click right button.
        elif is_right_button(event):
            if self.right_menu_visible_flag:
                (wx, wy) = self.window.get_root_origin()
                (cx, cy, modifier) = self.window.get_pointer()
                self.right_menu.show((cx + wx, cy + wy))
        # Change cursor when click left button.
        elif is_left_button(event):
            self.left_click_flag = True
            self.left_click_coordindate = (event.x, event.y)
            self.entry_buffer.place_cursor(
                self.entry_buffer.index_to_offset(self.get_index_at_event(widget, event)))
        self.queue_draw()    
            
    def button_release_entry(self, widget, event):
        '''
        Internal callback for `button-release-event` signal.
        '''
        self.double_click_flag = False
        self.left_click_flag = False
            
    def motion_notify_entry(self, widget, event):
        '''
        Internal callback for `motion-notify-event` signal.
        '''
        if not self.double_click_flag and self.left_click_flag:
            self.entry_buffer.set_insert_pos(
                self.entry_buffer.index_to_offset(self.get_index_at_event(widget, event)))
            self.__calculate_cursor_offset()
            self.queue_draw()    
            
    def focus_in_entry(self, widget, event):
        '''
        Internal callback for `focus-in-event` signal.
        '''
        self.grab_focus_flag = True
        self.im.focus_in()
        self.queue_draw()
            
    def focus_out_entry(self, widget, event):
        '''
        Internal callback for `focus-out-event` signal.
        '''
        self.handle_focus_out(widget, event)
        
    def handle_focus_out(self, widget, event):
        '''
        Internal function to handle focus out.
        '''
        self.grab_focus_flag = False
        
        # Focus out IMContext.
        self.im.focus_out()

        self.queue_draw()
        
    # this function maybe can be deleted
    def move_offsetx_right(self, widget, event):
        '''
        Internal function to move offset_x to right.
        '''
        text_width = self.get_content_width(self.content)
        rect = self.get_allocation()
        if self.offset_x + rect.width - self.padding_x * 2 < text_width:
            cr = widget.window.cairo_create()
            context = pangocairo.CairoContext(cr)
            layout = context.create_layout()
            layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
            layout.set_text(self.content)
            (text_width, text_height) = layout.get_pixel_size()
            (x_index, y_index) = layout.xy_to_index((self.offset_x + rect.width - self.padding_x * 2) * pango.SCALE, 0)
            
            self.offset_x += len(self.get_utf8_string(self.content[x_index::], 0))
            
    # this function maybe can be deleted
    def move_offsetx_left(self, widget, event):
        '''
        Internal function to move offset_x to left.
        '''
        if self.offset_x > 0:
            cr = widget.window.cairo_create()
            context = pangocairo.CairoContext(cr)
            layout = context.create_layout()
            layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
            layout.set_text(self.content)
            (text_width, text_height) = layout.get_pixel_size()
            (x_index, y_index) = layout.xy_to_index((self.offset_x + self.padding_x) * pango.SCALE, 0)
            
            self.offset_x -= len(self.get_utf8_string(self.content[0:x_index], -1))
        
    def get_index_at_event(self, widget, event):
        '''
        Internal function to get index at event.
        '''
        (text_width, text_height) = self.entry_buffer.get_pixel_size()
        if int(event.x) + self.offset_x - self.padding_x > text_width:
            return self.entry_buffer.get_length()
        else:
            (x_index, y_index) = self.entry_buffer.xy_to_index((int(event.x) + self.offset_x - self.padding_x) * pango.SCALE, 0)
            return x_index
        
    def commit_entry(self, input_text):
        '''
        Internal callback for `commit` signal.
        '''
        if self.is_editable():
            with self.monitor_entry_content():
                if self.entry_buffer.get_has_selection():
                    self.entry_buffer.delete_selection()
                    
                self.entry_buffer.insert_at_cursor(input_text)
                
                self.__calculate_cursor_offset()
            self.queue_draw()
        
    # this function maybe can be deleted
    def get_content_width(self, content):
        '''
        Internal function to get content width.
        '''
        (content_width, content_height) = get_content_size(content, self.entry_buffer.font_size)
        return content_width
        
    # this function maybe can be deleted
    def get_utf8_string(self, content, index):
        '''
        Internal to get utf8 string.
        '''
        try:
            return list(content.decode('utf-8'))[index].encode('utf-8')
        except Exception, e:
            print "function get_utf8_string got error: %s" % (e)
            traceback.print_exc(file=sys.stdout)
            return ""
    
    def __calculate_cursor_offset(self):
        '''calculate the cursor offset'''
        # comput coord offset
        rect = self.allocation
        cursor_index = self.entry_buffer.get_insert_index()
        cursor_pos = self.entry_buffer.get_cursor_pos(cursor_index)[0]
        if cursor_pos[0] - self.offset_x > rect.width - self.padding_x * 2 :
            self.offset_x = cursor_pos[0] - (rect.width - self.padding_x * 2) + 2
        elif cursor_pos[0] - self.offset_x < 0:
            self.offset_x = cursor_pos[0]
        if self.offset_x < 0:
            self.offset_x = 0

    def calculate(self):
        '''docstring for calculate'''
        self.__calculate_cursor_offset()
    
gobject.type_register(Entry)

'''
TODO: Add x button (Clear Button)
'''
class ClearButton(gtk.EventBox):
    button_padding_x = 20
    
    def __init__(self,
                 visible=False, 
                ):
        gtk.EventBox.__init__(self)
        self.button_margin_x = 4
        self.button_padding_y = 1
        self.clear_pixbuf = ui_theme.get_pixbuf("entry/gtk-cancel.png")

    def render(self, cr, rect):
        draw_pixbuf(cr, 
                    self.clear_pixbuf.get_pixbuf(), 
                    rect.x + rect.width + self.button_margin_x, 
                    rect.y + self.button_padding_y)

gobject.type_register(ClearButton)

class TextEntry(gtk.VBox):
    '''
    Text entry.
    
    @undocumented: set_sensitive
    @undocumented: emit_action_active_signal
    @undocumented: expose_text_entry
    '''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, 
                 content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 ):
        '''
        Initialize TextEntry class.
        
        @param content: Initialize entry text, default is \"\".
        @param action_button: Extra button add at right side of text entry, default is None.
        @param background_color: Color of text entry background.
        @param acme_color: Acme point color of text entry.
        @param point_color: Pointer color of text entry.
        @param frame_point_color: Frame pointer color of text entry.
        @param frame_color: Frame color of text entry.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 1.0, 1.0)
        self.action_button = action_button
        self.h_box = gtk.HBox()
        self.entry = Entry(content)
        self.background_color = background_color
        self.acme_color = acme_color
        self.point_color = point_color
        self.frame_point_color = frame_point_color
        self.frame_color = frame_color
        
        self.pack_start(self.align, False, False)
        self.align.add(self.h_box)
        self.h_box.pack_start(self.entry)
        if action_button:
            self.action_align = gtk.Alignment()
            self.action_align.set(0.0, 0.5, 0, 0)
            self.action_align.set_padding(0, 0, 0, self.entry.padding_x)
            self.action_align.add(self.action_button)
            
            self.h_box.pack_start(self.action_align, False, False)
            
            self.action_button.connect("clicked", lambda w: self.emit_action_active_signal())

        # Handle signal.
        self.align.connect("expose-event", self.expose_text_entry)
        
    def set_sensitive(self, sensitive):
        '''
        Internal function to wrap function `set_sensitive`.
        '''
        super(TextEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
            
    def emit_action_active_signal(self):
        '''
        Internal callback for `action-active` signal.
        '''
        self.emit("action-active", self.get_text())                
        
    def expose_text_entry(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
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
        
        return True
    
    def set_size(self, width, height):
        '''
        Set text entry size with given value.
        
        @param width: New width of text entry.
        @param height: New height of text entry.
        '''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''
        Set editable status of text entry.
        
        @param editable: Text entry can editable if option is True, else can't edit.
        '''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''
        Set text of text entry.
        
        @param text: Text entry string.
        '''
        self.entry.set_text(text)
        
    def get_text(self):
        '''
        Get text of text entry.
        
        @return: Return text of text entry.
        '''
        return self.entry.get_text()
    
    def focus_input(self):
        '''
        Focus input cursor.
        '''
        self.entry.grab_focus()
        
gobject.type_register(TextEntry)

class InputEntry(gtk.VBox):
    '''
    Text entry.
    
    Generically speaking, InputEntry is similar L{ I{TextEntry} <TextEntry>},
    
    only difference between two class is ui style, internal logic is same.
    
    @undocumented: set_sensitive
    @undocumented: emit_action_active_signal
    @undocumented: expose_input_entry
    '''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, 
                 content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 enable_clear_button=False,
                 ):
        '''

        Initialize InputEntry class.
        
        @param content: Initialize entry text, default is \"\".
        @param action_button: Extra button add at right side of input entry, default is None.
        @param background_color: Color of input entry background.
        @param acme_color: Acme point color of input entry.
        @param point_color: Pointer color of input entry.
        @param frame_point_color: Frame pointer color of input entry.
        @param frame_color: Frame color of input entry.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 1.0, 1.0)
        self.action_button = action_button
        self.h_box = gtk.HBox()
        self.entry = Entry(content, enable_clear_button=enable_clear_button)
        self.background_color = background_color
        self.acme_color = acme_color
        self.point_color = point_color
        self.frame_point_color = frame_point_color
        self.frame_color = frame_color
        
        self.pack_start(self.align, False, False)
        self.align.add(self.h_box)
        self.h_box.pack_start(self.entry)
        if action_button:
            self.action_align = gtk.Alignment()
            self.action_align.set(0.0, 0.5, 0, 0)
            self.action_align.set_padding(0, 0, 0, self.entry.padding_x)
            self.action_align.add(self.action_button)
            
            self.h_box.pack_start(self.action_align, False, False)
            
            self.action_button.connect("clicked", lambda w: self.emit_action_active_signal())

        # Handle signal.
        self.align.connect("expose-event", self.expose_input_entry)
            
    def set_sensitive(self, sensitive):
        '''
        Internal function to wrap function `set_sensitive`.
        '''
        super(InputEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
            
    def emit_action_active_signal(self):
        '''
        Internal callback for `action-active` signal.
        '''
        self.emit("action-active", self.get_text())                
        
    def expose_input_entry(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
            cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
            cr.fill()
        
        propagate_expose(widget, event)
        
        return True
    
    def set_size(self, width, height):
        '''
        Set input entry size with given value.
        
        @param width: New width of input entry.
        @param height: New height of input entry.
        '''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''
        Set editable status of input entry.
        
        @param editable: input entry can editable if option is True, else can't edit.
        '''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''
        Set text of input entry.
        
        @param text: input entry string.
        '''
        self.entry.set_text(text)
        
    def get_text(self):
        '''
        Get text of input entry.
        
        @return: Return text of input entry.
        '''
        return self.entry.get_text()
    
    def focus_input(self):
        '''
        Focus input cursor.
        '''
        self.entry.grab_focus()
        
gobject.type_register(InputEntry)

class ShortcutKeyEntry(gtk.VBox):
    '''
    Shortcut key entry.
    
    @undocumented: set_sensitive
    @undocumented: emit_action_active_signal
    @undocumented: expose_shortcutkey_entry
    @undocumented: handle_focus_out
    @undocumented: handle_key_press
    '''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "wait-key-input" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "shortcut-key-change" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, 
                 content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 ):
        '''
        Initialize ShortcutKeyEntry class.
        
        @param content: Initialize entry text, default is \"\".
        @param action_button: Extra button add at right side of shortcutkey entry, default is None.
        @param background_color: Color of shortcutkey entry background.
        @param acme_color: Acme point color of shortcutkey entry.
        @param point_color: Pointer color of shortcutkey entry.
        @param frame_point_color: Frame pointer color of shortcutkey entry.
        @param frame_color: Frame color of shortcutkey entry.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 1.0, 1.0)
        self.action_button = action_button
        self.h_box = gtk.HBox()
        self.entry = Entry(content)
        self.background_color = background_color
        self.acme_color = acme_color
        self.point_color = point_color
        self.frame_point_color = frame_point_color
        self.frame_color = frame_color
        
        self.pack_start(self.align, False, False)
        self.align.add(self.h_box)
        self.h_box.pack_start(self.entry)
        if action_button:
            self.action_align = gtk.Alignment()
            self.action_align.set(0.0, 0.5, 0, 0)
            self.action_align.set_padding(0, 0, 0, self.entry.padding_x)
            self.action_align.add(self.action_button)
            
            self.h_box.pack_start(self.action_align)
            
            self.action_button.connect("clicked", lambda w: self.emit_action_active_signal())

        # Handle signal.
        self.align.connect("expose-event", self.expose_shortcutkey_entry)
        
        # Setup flags.
        self.entry.cursor_visible_flag = False
        self.entry.entry_buffer.set_property("cursor-visible", self.entry.cursor_visible_flag)
        self.entry.right_menu_visible_flag = False
        self.entry.select_area_visible_flag = False
        self.entry.entry_buffer.set_property("select-area-visible", self.entry.select_area_visible_flag)
        self.entry.editable_flag = False
    
        # Overwrite entry's function.
        self.entry.handle_button_press = self.handle_button_press
        self.entry.handle_focus_out = self.handle_focus_out
        self.entry.handle_key_press = self.handle_key_press
        
        self.shortcut_key = content
        self.shortcut_key_record = None
        
    def set_sensitive(self, sensitive):
        '''
        Internal function to wrap function `set_sensitive`.
        '''
        super(ShortcutKeyEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
        
    def handle_button_press(self, widget, event):
        '''
        Internal callback for `action-active` signal.
        '''
        # Get input focus.
        self.entry.grab_focus()
        self.shortcut_key_record = self.shortcut_key
        
        if is_left_button(event):
            self.entry.editable_flag = True
            self.emit("wait-key-input", self.shortcut_key)
            self.set_text(_("Please input new shortcuts"))
            self.entry.editable_flag = False
            
            self.entry.queue_draw()
            
    def handle_focus_out(self, widget, event):
        '''
        Internal function to handle focus out.
        '''
        if self.shortcut_key != None:
            self.entry.editable_flag = True
            self.set_text(self.shortcut_key)
            self.entry.editable_flag = False
        
        self.entry.grab_focus_flag = False
        self.entry.im.focus_out()
        self.entry.queue_draw()
        
        if self.shortcut_key != self.shortcut_key_record:
            self.emit("shortcut-key-change", self.shortcut_key)
            self.shortcut_key_record = None
            
    def handle_key_press(self, widget, event):
        '''
        Internal function to handle key press.
        '''
        keyname = get_keyevent_name(event)
        if keyname != "":
            if keyname == "BackSpace":
                self.set_shortcut_key(None)
            elif keyname != "":
                self.set_shortcut_key(keyname)
            
    def set_shortcut_key(self, shortcut_key):
        '''
        Set shortcut key.
        
        @param shortcut_key: Key string that return by function `dtk.ui.keymap.get_keyevent_name`.
        '''
        self.shortcut_key = shortcut_key
        
        self.entry.editable_flag = True
        if self.shortcut_key == None:
            self.set_text(_("Disabled"))
        else:
            self.set_text(self.shortcut_key)
        self.entry.editable_flag = False
                
    def get_shortcut_key(self):
        '''
        Get shortcut key.
        
        @return: Return shortcut key string, string format look function `dtk.ui.keymap.get_keyevent_name`.
        '''
        return self.shortcut_key
            
    def emit_action_active_signal(self):
        '''
        Internal callback for `action-active` signal.
        '''
        self.emit("action-active", self.get_text())                
        
    def expose_shortcutkey_entry(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
            cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
            cr.fill()
        
        propagate_expose(widget, event)
        
        return True
    
    def set_size(self, width, height):
        '''
        Set shortcutkey entry size with given value.
        
        @param width: New width of shortcutkey entry.
        @param height: New height of shortcutkey entry.
        '''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''
        Set editable status of shortcutkey entry.
        
        @param editable: shortcutkey entry can editable if option is True, else can't edit.
        '''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''
        Set text of shortcutkey entry.
        
        @param text: shortcutkey entry string.
        '''
        self.entry.set_text(text)
        
    def get_text(self):
        '''
        Get text of shortcutkey entry.
        
        @return: Return text of shortcutkey entry.
        '''
        return self.entry.get_text()
    
    def focus_input(self):
        '''
        Focus input cursor.
        '''
        self.entry.grab_focus()
        
gobject.type_register(ShortcutKeyEntry)

'''
TODO: Act like Mac style
      The last character when inputting is visible then disappeared for a while
'''
class PasswordEntry(gtk.VBox):
    
    '''
    Perhaps it need more signals
    '''
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),    
    }
    
    def __init__(self, 
                 content="", 
                 action_button=None, 
                 background_color=ui_theme.get_alpha_color("text_entry_background"), 
                 acme_color=ui_theme.get_alpha_color("text_entry_acme"), 
                 point_color=ui_theme.get_alpha_color("text_entry_point"), 
                 frame_point_color=ui_theme.get_alpha_color("text_entry_frame_point"), 
                 frame_color=ui_theme.get_alpha_color("text_entry_frame"), 
                 shown_password=False):
        gtk.VBox.__init__(self)
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 1.0, 1.0)
        self.action_button = action_button
        self.h_box = gtk.HBox()
        self.entry = Entry(content, True)
        self.entry.connect("key-press-event", self.key_press_entry)
        self.entry.connect("key-release-event", self.key_released_entry)
        self.background_color = background_color
        self.acme_color = acme_color
        self.point_color = point_color
        self.frame_point_color = frame_point_color
        self.frame_color = frame_color
        self.shown_password = shown_password

        self.pack_start(self.align, False, False)
        self.align.add(self.h_box)
        self.h_box.pack_start(self.entry)
        if action_button:
            self.action_align = gtk.Alignment()
            self.action_align.set(0.0, 0.5, 0, 0)
            self.action_align.set_padding(0, 0, 0, self.entry.padding_x)
            self.action_align.add(self.action_button)

            self.h_box.pack_start(self.action_align, False, False)

            self.action_button.connect("clicked", lambda w: self.emit_action_active_signal())

        '''
        signal callback
        '''
        self.align.connect("expose-event", self.expose_password_entry)

    def show_password(self, shown_password=False):
        self.shown_password = shown_password

    def key_press_entry(self, widget, argv):
        if self.shown_password:
            return
        old_str = self.entry.get_text()
        str_len = len(old_str)
        new_str = ""
        if str_len < 2:
            return
        new_str = old_str[0:str_len - 2] + "*" + old_str[str_len - 1]
        self.entry.set_text(new_str)

    def key_released_entry(self, widget, argv):
        if self.shown_password:
            return
        old_str = self.entry.get_text()
        str_len = len(old_str)
        new_str = ""
        if str_len == 1:
            new_str = "*"
        else:
            new_str = old_str[0:str_len - 1] + "*"
        timer = gobject.timeout_add(200, self.reset_password_entry, new_str)

    def reset_password_entry(self, argv):
        self.entry.set_text(argv)

    def emit_action_active_signal(self):
        pass

    def expose_password_entry(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
            cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
            cr.fill()

        propagate_expose(widget, event)

        return True

    def set_size(self, width, height):
        self.set_size_request(width, height)

        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x

        self.entry.set_size_request(width - 2 - action_button_width, height - 2)

gobject.type_register(PasswordEntry)

if __name__ == "__main__":
    def entry_changed(entry, text):
        '''entry text changed '''
        print "entry changed:", entry.get_text()

    def entry_check_text(text):
        '''check text'''
        if text and text[0] in "0123456789":
            return False
        return True
    window = gtk.Window()
    window.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
    window.set_decorated(False)
    window.add_events(gtk.gdk.ALL_EVENTS_MASK)        
    window.connect("destroy", lambda w: gtk.main_quit())
    #window.set_size_request(300, 100)
    window.move(150, 50)
    
    hbox = gtk.HBox(False, 10)
    entry = Entry("")
    entry.check_text = entry_check_text
    #entry.entry_buffer.set_property("visibility", False)
    #entry.connect("changed", entry_changed)
    entry.set_size_request(100, 25)
    hbox.pack_start(entry, False, False)
    window.add(hbox)
    #window.connect("expose-event", show_entry_buf, entry_buf)

    window.show_all()
    
    gtk.main()
