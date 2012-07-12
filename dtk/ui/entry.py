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

from constant import DEFAULT_FONT_SIZE, DEFAULT_FONT
from contextlib import contextmanager 
from draw import draw_hlinear
from keymap import get_keyevent_name
from locales import _
from menu import Menu
from theme import ui_theme
import gobject
import gtk
import pango
import pangocairo
from utils import (propagate_expose, cairo_state, color_hex_to_cairo, 
                   get_content_size, is_double_click, is_right_button, 
                   is_left_button, alpha_color_hex_to_cairo, cairo_disable_antialias)

class Entry(gtk.EventBox):
    '''Entry.'''
    
    MOVE_LEFT = 1
    MOVE_RIGHT = 2
    MOVE_NONE = 3
    
    __gsignals__ = {
        "edit-alarm" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "press-return" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "invalid-value" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, content="", 
                 padding_x=5, 
                 padding_y=2,
                 text_color=ui_theme.get_color("entry_text"),
                 text_select_color=ui_theme.get_color("entry_select_text"),
                 background_select_color=ui_theme.get_shadow_color("entry_select_background"),
                 font_size=DEFAULT_FONT_SIZE, 
                 ):
        '''Init entry.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.im = gtk.IMMulticontext()
        self.font_size = font_size
        self.text_color = text_color
        self.text_select_color = text_select_color
        self.background_select_color = background_select_color
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.move_direction = self.MOVE_NONE
        self.double_click_flag = False
        self.left_click_flag = False
        self.left_click_coordindate = None
        self.drag_start_index = 0
        self.drag_end_index = 0
        self.grab_focus_flag = False
        self.editable_flag = True
        self.check_text = None
        self.cursor_visible_flag = True
        self.right_menu_visible_flag = True
        self.select_area_visible_flag = True
        
        self.content = content
        self.cursor_index = len(self.content)
        self.select_start_index = self.select_end_index = self.cursor_index
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
            [(None, "剪切", self.cut_to_clipboard),
             (None, "复制", self.copy_to_clipboard),
             (None, "粘贴", self.paste_from_clipboard),
             (None, "全选", self.select_all)],
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
        '''Set editable.'''
        self.editable_flag = editable
        
    def set_edit_mode(self, mode):
        '''Set edit mode.'''
        self.edit_mode = mode
        
    @contextmanager
    def monitor_entry_content(self):
        '''Monitor entry content.'''
        old_text = self.get_text()
        try:  
            yield  
        except Exception, e:  
            print 'monitor_entry_content error %s' % e  
        else:  
            new_text = self.get_text()
            if self.check_text == None or self.check_text(new_text):
                if old_text != new_text:
                    self.emit("changed", new_text)
            else:
                self.emit("invalid-value", new_text)
                self.set_text(old_text)
                
    def is_editable(self):
        '''Whether is editable.'''
        if not self.editable_flag:
            self.emit("edit-alarm")
            
        return self.editable_flag    
        
    def set_text(self, text):
        '''Set text.'''
        if self.is_editable():
            with self.monitor_entry_content():
                if text != None:
                    self.content = text
                    self.cursor_index = len(self.content)
                    self.select_start_index = self.select_end_index = self.cursor_index
                    
                    text_width = self.get_content_width(self.content)
                    rect = self.get_allocation()
                    
                    if text_width > rect.width - self.padding_x * 2 > 0:
                        self.offset_x = text_width - rect.width + self.padding_x * 2
                    else:
                        self.offset_x = 0
                    
                    self.queue_draw()
        
    def get_text(self):
        '''Get text.'''
        return self.content
    
    def realize_entry(self, widget):
        '''Realize entry.'''
        text_width = self.get_content_width(self.content)
        rect = self.get_allocation()

        if text_width > rect.width - self.padding_x * 2 > 0:
            self.offset_x = text_width - rect.width + self.padding_x * 2
        else:
            self.offset_x = 0
        
    def key_press_entry(self, widget, event):
        '''Callback for `key-press-event` signal.'''
        self.handle_key_press(widget, event)
        
    def handle_key_press(self, widget, event):
        '''Handle key press.'''
        # Pass key to IMContext.
        input_method_filt = self.im.filter_keypress(event)
        if not input_method_filt:
            self.handle_key_event(event)
        
        return False
    
    def handle_key_event(self, event):
        '''Handle key event.'''
        key_name = get_keyevent_name(event)
        
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
            
    def clear_select_status(self):
        '''Clear select status.'''
        self.select_start_index = self.select_end_index = self.cursor_index
        self.move_direction = self.MOVE_NONE            
            
    def move_to_start(self):
        '''Move to start.'''
        self.offset_x = 0
        self.cursor_index = 0
        
        self.clear_select_status()
        
        self.queue_draw()
        
    def move_to_end(self):
        '''Move to end.'''
        text_width = self.get_content_width(self.content)
        rect = self.get_allocation()
        if text_width > rect.width - self.padding_x * 2 > 0:
            self.offset_x = text_width - (rect.width - self.padding_x * 2)
        self.cursor_index = len(self.content)
        
        self.clear_select_status()
        
        self.queue_draw()
        
    def move_to_left(self):
        '''Move to left char.'''
        # Avoid change focus to other widget in parent.
        if self.keynav_failed(gtk.DIR_LEFT):
            self.get_toplevel().set_focus_child(self)
            
        if self.select_start_index != self.select_end_index:
            self.cursor_index = self.select_start_index
            select_start_width = self.get_content_width(self.content[0:self.select_start_index])

            self.clear_select_status()

            if select_start_width < self.offset_x:
                self.offset_x = select_start_width
            
            self.queue_draw()
        elif self.cursor_index > 0:
            self.cursor_index -= len(self.get_utf8_string(self.content[0:self.cursor_index], -1))
            
            text_width = self.get_content_width(self.content[0:self.cursor_index])
            if text_width - self.offset_x < 0:
                self.offset_x = text_width
                
            self.queue_draw()    
            
    def move_to_right(self):
        '''Move to right char.'''
        # Avoid change focus to other widget in parent.
        if self.keynav_failed(gtk.DIR_RIGHT):
            self.get_toplevel().set_focus_child(self)
                        
        if self.select_start_index != self.select_end_index:
            self.cursor_index = self.select_end_index
            select_end_width = self.get_content_width(self.content[0:self.select_end_index])

            self.clear_select_status()
            
            rect = self.get_allocation()
            if select_end_width > self.offset_x + rect.width - self.padding_x * 2:
                self.offset_x = select_end_width - rect.width + self.padding_x * 2
            
            self.queue_draw()
        elif self.cursor_index < len(self.content):
            self.cursor_index += len(self.content[self.cursor_index::].decode('utf-8')[0].encode('utf-8'))            
            
            text_width = self.get_content_width(self.content[0:self.cursor_index])
            rect = self.get_allocation()
            if text_width - self.offset_x > rect.width - self.padding_x * 2:
                self.offset_x = text_width - (rect.width - self.padding_x * 2)
            
            self.queue_draw()
            
    def backspace(self):
        '''Backspace.'''        
        if self.is_editable():
            with self.monitor_entry_content():
                if self.select_start_index != self.select_end_index:
                    self.delete()
                elif self.cursor_index > 0:
                    old_insert_width = self.get_content_width(self.content[0:self.cursor_index])
                    delete_char = self.get_utf8_string(self.content[0:self.cursor_index], -1)
                    self.cursor_index -= len(delete_char)
                    
                    self.content = self.content[0:self.cursor_index] + self.content[self.cursor_index + len(delete_char)::]
                    text_width = self.get_content_width(self.content)
                    insert_width = self.get_content_width(self.content[0:self.cursor_index])
                    rect = self.get_allocation()
                    if text_width < rect.width - self.padding_x * 2:
                        self.offset_x = 0
                    else:
                        self.offset_x += insert_width - old_insert_width
                        
                    self.queue_draw()    
            
    def select_all(self):
        '''Select all.'''
        self.select_start_index = 0
        self.select_end_index = len(self.content)
        
        self.queue_draw()
        
    def cut_to_clipboard(self):
        '''Cut select text to clipboard.'''
        if self.select_start_index != self.select_end_index:
            cut_text = self.content[self.select_start_index:self.select_end_index]
            
            if self.is_editable():
                with self.monitor_entry_content():
                    self.delete()
            
            clipboard = gtk.Clipboard()
            clipboard.set_text(cut_text)

    def copy_to_clipboard(self):
        '''Copy select text to clipboard.'''
        if self.select_start_index != self.select_end_index:
            cut_text = self.content[self.select_start_index:self.select_end_index]
            
            clipboard = gtk.Clipboard()
            clipboard.set_text(cut_text)
    
    def paste_from_clipboard(self):
        '''Paste text from clipboard.'''
        if self.is_editable():
            with self.monitor_entry_content():
                clipboard = gtk.Clipboard()    
                clipboard.request_text(lambda clipboard, text, data: self.commit_entry('\\n'.join(text.split('\n'))))
                
    def press_return(self):
        '''Press return.'''
        self.emit("press-return")
        
    def select_to_left(self):
        '''Select to preview.'''
        if self.select_start_index != self.select_end_index:
            if self.move_direction == self.MOVE_LEFT:
                if self.select_start_index > 0:
                    self.select_start_index -= len(self.get_utf8_string(self.content[0:self.select_start_index], -1))
                    select_start_width = self.get_content_width(self.content[0:self.select_start_index])    
                    if select_start_width < self.offset_x:
                        self.offset_x = select_start_width
            else:
                self.select_end_index -= len(self.get_utf8_string(self.content[0:self.select_end_index], -1))
                    
                select_end_width = self.get_content_width(self.content[0:self.select_end_index])
                if select_end_width < self.offset_x:
                    self.offset_x = select_end_width
        else:
            self.select_end_index = self.cursor_index
            self.select_start_index = self.cursor_index - len(self.get_utf8_string(self.content[0:self.cursor_index], -1))
            self.move_direction = self.MOVE_LEFT
            
        self.queue_draw()
        
    def select_to_right(self):
        '''Select to next.'''
        if self.select_start_index != self.select_end_index:
            rect = self.get_allocation()    
            
            if self.move_direction == self.MOVE_RIGHT:
                if self.select_end_index < len(self.content):
                    self.select_end_index += len(self.get_utf8_string(self.content[self.select_end_index::], 0))
                    
                    select_end_width = self.get_content_width(self.content[0:self.select_end_index])    
                    if select_end_width > self.offset_x + rect.width - self.padding_x * 2:
                        self.offset_x = select_end_width - rect.width + self.padding_x * 2
            else:
                self.select_start_index += len(self.get_utf8_string(self.content[self.select_start_index::], 0))
                select_start_width = self.get_content_width(self.content[0:self.select_start_index])
                if select_start_width > self.offset_x + rect.width - self.padding_x * 2:
                    self.offset_x = select_start_width - rect.width + self.padding_x * 2
        else:
            if self.select_end_index < len(self.content):
                self.select_start_index = self.cursor_index
                self.select_end_index = self.cursor_index + len(self.get_utf8_string(self.content[self.select_end_index::], 0))
                self.move_direction = self.MOVE_RIGHT
            
        self.queue_draw()        
        
    def select_to_start(self):
        '''Select to start.'''
        if self.select_start_index != self.select_end_index:
            if self.move_direction == self.MOVE_LEFT:
                self.select_start_index = 0
            else:
                self.select_end_index = self.select_start_index
                self.select_start_index = 0
                
                self.move_direction = self.MOVE_LEFT    
        else:
            self.select_start_index = 0
            self.select_end_index = self.cursor_index
            
            self.move_direction = self.MOVE_LEFT

        self.offset_x = 0    
        
        self.queue_draw()
        
    def select_to_end(self):
        '''Select to end.'''
        if self.select_start_index != self.select_end_index:
            if self.move_direction == self.MOVE_RIGHT:
                self.select_end_index = len(self.content)
            else:
                self.select_start_index = self.select_end_index
                self.select_end_index = len(self.content)
                
                self.move_direction = self.MOVE_RIGHT    
        else:
            self.select_start_index = self.cursor_index
            self.select_end_index = len(self.content)
            
            self.move_direction = self.MOVE_RIGHT
        
        rect = self.get_allocation()
        select_end_width = self.get_content_width(self.content)
        if select_end_width > self.offset_x + rect.width - self.padding_x * 2:
            self.offset_x = select_end_width - rect.width + self.padding_x * 2
        else:
            self.offset_x = 0
        
        self.queue_draw()
        
    def delete(self):
        '''Delete select text.'''
        if self.is_editable() and self.select_start_index != self.select_end_index:
            with self.monitor_entry_content():
                rect = self.get_allocation()
                
                self.cursor_index = self.select_start_index
                
                select_start_width = self.get_content_width(self.content[0:self.select_start_index])
                select_end_width = self.get_content_width(self.content[0:self.select_end_index])
                
                self.cursor_index = self.select_start_index
                if select_start_width < self.offset_x:
                    if select_end_width < self.offset_x + rect.width - self.padding_x * 2:
                        self.offset_x = max(select_start_width + self.offset_x - select_end_width, 0)
                    else:
                        self.offset_x = 0
                        
                self.content = self.content[0:self.select_start_index] + self.content[self.select_end_index::]
                            
                self.select_start_index = self.select_end_index = self.cursor_index
                
                self.queue_draw()
                            
    def expose_entry(self, widget, event):
        '''Callback for `expose-event` signal.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        if self.get_sensitive():
            self.draw_entry_background(cr, rect)
        
        # Draw text.
        self.draw_entry_text(cr, rect)
        
        # Draw cursor.
        if self.cursor_visible_flag and self.get_sensitive():
            self.draw_entry_cursor(cr, rect)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def draw_entry_background(self, cr, rect):
        '''Draw entry background.'''
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        if self.select_start_index != self.select_end_index and self.select_area_visible_flag:
            select_start_width = self.get_content_width(self.content[0:self.select_start_index])
            select_end_width = self.get_content_width(self.content[0:self.select_end_index])
            
            draw_hlinear(cr, 
                         x + self.padding_x + max(select_start_width - self.offset_x, 0),
                         y + self.padding_y,
                         min(select_end_width, self.offset_x + w - self.padding_x * 2) - max(select_start_width, self.offset_x),
                         h - self.padding_y * 2,
                         self.background_select_color.get_color_info())
            
    def draw_entry_text(self, cr, rect):
        '''Draw entry text.'''
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        with cairo_state(cr):
            # Clip text area first.
            draw_x = x + self.padding_x
            draw_y = y + self.padding_y
            draw_width = w - self.padding_x * 2
            draw_height = h - self.padding_y * 2
            cr.rectangle(draw_x, draw_y, draw_width, draw_height)
            cr.clip()
            
            # Create pangocairo context.
            context = pangocairo.CairoContext(cr)
            
            # Set layout.
            layout = context.create_layout()
            layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
            
            if not self.get_sensitive():
                # Set text.
                layout.set_text(self.content)
                
                # Get text size.
                (text_width, text_height) = layout.get_pixel_size()
                
                # Move text.
                cr.move_to(draw_x - self.offset_x, 
                           draw_y + (draw_height - text_height) / 2)
                
                # Draw text.
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("disable_text").get_color()))
                context.update_layout(layout)
                context.show_layout(layout)
            elif self.select_start_index != self.select_end_index and self.select_area_visible_flag:
                # Get string.
                before_select_str = self.content[0:self.select_start_index]
                select_str = self.content[self.select_start_index:self.select_end_index]
                after_select_str = self.content[self.select_end_index::]
                
                # Build render list.
                render_list = []
                
                layout.set_text(before_select_str)
                (before_select_width, before_select_height) = layout.get_pixel_size()
                render_list.append((before_select_str, 0, before_select_height, self.text_color))                
                
                layout.set_text(select_str)
                (select_width, select_height) = layout.get_pixel_size()
                render_list.append((select_str, before_select_width, select_height, self.text_select_color))
                
                layout.set_text(after_select_str)
                (after_select_width, after_select_height) = layout.get_pixel_size()
                render_list.append((after_select_str, before_select_width + select_width, after_select_height, self.text_color))
                
                # Render.
                for (string, offset, text_height, text_color) in render_list:
                    layout.set_text(string)
                    cr.move_to(draw_x - self.offset_x + offset,
                               draw_y + (draw_height - text_height) / 2)
                    cr.set_source_rgb(*color_hex_to_cairo(text_color.get_color()))
                    context.update_layout(layout)
                    context.show_layout(layout)
            else:
                # Set text.
                layout.set_text(self.content)
                
                # Get text size.
                (text_width, text_height) = layout.get_pixel_size()
                
                # Move text.
                cr.move_to(draw_x - self.offset_x, 
                           draw_y + (draw_height - text_height) / 2)
                
                # Draw text.
                cr.set_source_rgb(*color_hex_to_cairo(self.text_color.get_color()))
                context.update_layout(layout)
                context.show_layout(layout)
            
    def draw_entry_cursor(self, cr, rect):
        '''Draw entry cursor.'''
        if self.grab_focus_flag and self.select_start_index == self.select_end_index:
            # Init.
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            left_str = self.content[0:self.cursor_index]
            left_str_width = self.get_content_width(left_str)
            padding_y = (h - (get_content_size("Height", self.font_size)[-1])) / 2
            
            # Draw cursor.
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("entry_cursor").get_color()))
            cr.rectangle(x + self.padding_x + left_str_width - self.offset_x,
                         y + padding_y,
                         1, 
                         h - padding_y * 2
                         )
            cr.fill()
    
    def button_press_entry(self, widget, event):
        '''Button press entry.'''
        self.handle_button_press(widget, event)
        
    def handle_button_press(self, widget, event):
        '''Handle button press.'''
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
            
            self.drag_start_index = self.get_index_at_event(widget, event)
            
    def button_release_entry(self, widget, event):
        '''Callback for `button-release-event` signal.'''
        if not self.double_click_flag and self.left_click_coordindate == (event.x, event.y):
            self.cursor_index = self.get_index_at_event(widget, event)    
            self.select_start_index = self.select_end_index = self.cursor_index
            self.queue_draw()
            
        self.double_click_flag = False
        self.left_click_flag = False
            
    def motion_notify_entry(self, widget, event):
        '''Callback for `motion-notify-event` signal.'''
        if not self.double_click_flag and self.left_click_flag:
            self.cursor_index = self.drag_start_index
            self.drag_end_index = self.get_index_at_event(widget, event)
            
            self.select_start_index = min(self.drag_start_index, self.drag_end_index)
            self.select_end_index = max(self.drag_start_index, self.drag_end_index)
            
            if self.drag_start_index < self.drag_end_index:
                rect = self.get_allocation()
                if int(event.x) > rect.width:
                    self.move_offsetx_right(widget, event)
            else:
                if int(event.x) < 0:
                    self.move_offsetx_left(widget, event)
                
            self.queue_draw()    
            
    def focus_in_entry(self, widget, event):
        '''Callback for `focus-in-event` signal.'''
        self.grab_focus_flag = True
        
        # Focus in IMContext.
        self.im.set_client_window(widget.window)
        self.im.focus_in()
        
        self.queue_draw()
            
    def focus_out_entry(self, widget, event):
        '''Callback for `focus-out-event` signal.'''
        self.handle_focus_out(widget, event)
        
    def handle_focus_out(self, widget, event):
        '''Handle focus out.'''
        self.grab_focus_flag = False
        
        # Focus out IMContext.
        self.im.focus_out()

        self.queue_draw()
        
    def move_offsetx_right(self, widget, event):
        '''Move offset_x right.'''
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
            
    def move_offsetx_left(self, widget, event):
        '''Move offset_x left.'''
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
        '''Get index at event.'''
        cr = widget.window.cairo_create()
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
        layout.set_text(self.content)
        (text_width, text_height) = layout.get_pixel_size()
        if int(event.x) + self.offset_x - self.padding_x > text_width:
            return len(self.content)
        else:
            (x_index, y_index) = layout.xy_to_index((int(event.x) + self.offset_x - self.padding_x) * pango.SCALE, 0)
            return x_index
        
    def commit_entry(self, input_text):
        '''Entry commit.'''
        if self.is_editable():
            with self.monitor_entry_content():
                if self.select_start_index != self.select_end_index:
                    self.delete()
                    
                self.content = self.content[0:self.cursor_index] + input_text + self.content[self.cursor_index::]
                self.cursor_index += len(input_text)
                
                text_width = self.get_content_width(self.content)
                rect = self.get_allocation()
                if text_width <= rect.width - self.padding_x * 2:
                    self.offset_x = 0
                elif self.cursor_index == len(self.content):
                    self.offset_x = text_width - (rect.width - self.padding_x * 2)
                else:
                    old_text_width = self.get_content_width(self.content[0:self.cursor_index - len(input_text)])
                    input_text_width = self.get_content_width(input_text)
                    if old_text_width - self.offset_x + input_text_width > rect.width - self.padding_x * 2:
                        new_text_width = self.get_content_width(self.content[0:self.cursor_index])
                        self.offset_x = new_text_width - (rect.width - self.padding_x * 2)
                
                self.queue_draw()
        
    def get_content_width(self, content):
        '''Get content width.'''
        (content_width, content_height) = get_content_size(content, self.font_size)
        return content_width
        
    def get_utf8_string(self, content, index):
        '''Get utf8 string.'''
        try:
            return list(content.decode('utf-8'))[index].encode('utf-8')
        except Exception, e:
            print "get_utf8_string got error: %s" % (e)
            return ""
    
gobject.type_register(Entry)

class TextEntry(gtk.VBox):
    '''Input entry.'''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 ):
        '''Init input entry.'''
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
        super(TextEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
            
    def emit_action_active_signal(self):
        '''Emit action-active signal.'''
        self.emit("action-active", self.get_text())                
        
    def expose_text_entry(self, widget, event):
        '''Callback for `expose-event` signal.'''
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
        '''Set size.'''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''Set editable.'''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''Set text.'''
        self.entry.set_text(text)
        
    def get_text(self):
        '''Get text.'''
        return self.entry.get_text()
    
    def focus_input(self):
        '''Focus input.'''
        self.entry.grab_focus()
        
gobject.type_register(TextEntry)

class InputEntry(gtk.VBox):
    '''Input entry.'''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 ):
        '''Init input entry.'''
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
        super(InputEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
            
    def emit_action_active_signal(self):
        '''Emit action-active signal.'''
        self.emit("action-active", self.get_text())                
        
    def expose_text_entry(self, widget, event):
        '''Callback for `expose-event` signal.'''
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
        '''Set size.'''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''Set editable.'''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''Set text.'''
        self.entry.set_text(text)
        
    def get_text(self):
        '''Get text.'''
        return self.entry.get_text()
    
    def focus_input(self):
        '''Focus input.'''
        self.entry.grab_focus()
        
gobject.type_register(InputEntry)

class ShortcutKeyEntry(gtk.VBox):
    '''Input entry.'''
	
    __gsignals__ = {
        "action-active" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "wait-key-input" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
        "shortcut-key-change" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
    }
    
    def __init__(self, content="",
                 action_button=None,
                 background_color = ui_theme.get_alpha_color("text_entry_background"),
                 acme_color = ui_theme.get_alpha_color("text_entry_acme"),
                 point_color = ui_theme.get_alpha_color("text_entry_point"),
                 frame_point_color = ui_theme.get_alpha_color("text_entry_frame_point"),
                 frame_color = ui_theme.get_alpha_color("text_entry_frame"),
                 ):
        '''Init input entry.'''
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
        self.align.connect("expose-event", self.expose_text_entry)
        
        # Setup flags.
        self.entry.cursor_visible_flag = False
        self.entry.right_menu_visible_flag = False
        self.entry.select_area_visible_flag = False
        self.entry.editable_flag = False
    
        # Overwrite entry's function.
        self.entry.handle_button_press = self.handle_button_press
        self.entry.handle_focus_out = self.handle_focus_out
        self.entry.handle_key_press = self.handle_key_press
        
        self.shortcut_key = content
        self.shortcut_key_record = None
        
    def set_sensitive(self, sensitive):
        super(ShortcutKeyEntry, self).set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
        
    def handle_button_press(self, widget, event):
        '''Button press entry.'''
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
        '''Handle focus out.'''
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
        '''Handle key press.'''
        keyname = get_keyevent_name(event)
        if keyname != "":
            if keyname == "BackSpace":
                self.set_shortcut_key(None)
            elif keyname != "":
                self.set_shortcut_key(keyname)
            
    def set_shortcut_key(self, shortcut_key):
        '''Set shortcut key.'''
        self.shortcut_key = shortcut_key
        
        self.entry.editable_flag = True
        if self.shortcut_key == None:
            self.set_text(_("Disabled"))
        else:
            self.set_text(self.shortcut_key)
        self.entry.editable_flag = False
                
    def get_shortcut_key(self):
        '''Get shortcut key.'''
        return self.shortcut_key
            
    def emit_action_active_signal(self):
        '''Emit action-active signal.'''
        self.emit("action-active", self.get_text())                
        
    def expose_text_entry(self, widget, event):
        '''Callback for `expose-event` signal.'''
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
        '''Set size.'''
        self.set_size_request(width, height)    
        
        action_button_width = 0
        if self.action_button:
            action_button_width = self.action_button.get_size_request()[-1] + self.entry.padding_x
            
        self.entry.set_size_request(width - 2 - action_button_width, height - 2)
        
    def set_editable(self, editable):
        '''Set editable.'''
        self.entry.set_editable(editable)
        
    def set_text(self, text):
        '''Set text.'''
        self.entry.set_text(text)
        
    def get_text(self):
        '''Get text.'''
        return self.entry.get_text()
    
    def focus_input(self):
        '''Focus input.'''
        self.entry.grab_focus()
        
gobject.type_register(ShortcutKeyEntry)

if __name__ == "__main__":
    window = gtk.Window()
    window.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
    window.set_decorated(False)
    window.add_events(gtk.gdk.ALL_EVENTS_MASK)        
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(300, -1)
    window.move(100, 100)
    
    entry = Entry("Enter to search")
    window.add(entry)

    window.show_all()
    
    gtk.main()
