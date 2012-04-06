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
import cairo
from utils import *
from draw import *
from keymap import *
from menu import *

class Entry(gtk.EventBox):
    '''Entry.'''
    
    MOVE_LEFT = 1
    MOVE_RIGHT = 2
    MOVE_NONE = 3
	
    def __init__(self, content="", 
                 text_color=ui_theme.get_color("entryText"),
                 text_select_color=ui_theme.get_color("entrySelectText"),
                 background_color=ui_theme.get_shadow_color("entryBackground"),
                 background_select_color=ui_theme.get_shadow_color("entrySelectBackground"),
                 font_size=DEFAULT_FONT_SIZE, 
                 padding_x=10, padding_y=5):
        '''Init entry.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.im = gtk.IMMulticontext()
        self.font_size = font_size
        self.text_color = text_color
        self.text_select_color = text_select_color
        self.background_color = background_color
        self.background_select_color = background_select_color
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.move_direction = self.MOVE_NONE
        self.double_click_flag = False
        self.left_click_flag = False
        self.left_click_coordindate = None
        
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
            "S-Left" : self.select_to_left,
            "S-Right" : self.select_to_right,
            "S-Home" : self.select_to_start,
            "S-End" : self.select_to_end,
            "C-a" : self.select_all,
            "C-x" : self.cut_to_clipboard,
            "C-c" : self.copy_to_clipboard,
            "C-v" : self.paste_from_clipboard}
        
        # Add menu.
        self.right_menu = Menu(
            [(None, "剪切", self.cut_to_clipboard),
             (None, "复制", self.copy_to_clipboard),
             (None, "粘贴", self.paste_from_clipboard),
             (None, "全选", self.select_all)],
            MENU_POS_TOP_LEFT)
        
        # Connect signal.
        self.connect("realize", self.realize_entry)
        self.connect("key-press-event", self.key_press_entry)
        self.connect("expose-event", self.expose_entry)
        self.connect("button-press-event", self.button_press_entry)
        self.connect("button-release-event", self.button_release_entry)
        self.connect("motion-notify-event", self.motion_notify_entry)
        
        self.im.connect("commit", lambda im, input_text: self.commit_entry(input_text))
        
    def set_text(self, text):
        '''Set text.'''
        self.content = text
        self.cursor_index = len(self.content)
        self.select_start_index = self.select_end_index = self.cursor_index
        
        text_width = self.get_content_width(self.content)
        rect = self.get_allocation()
        if text_width > rect.width - self.padding_x * 2:
            self.offset_x = text_width - rect.width + self.padding_x * 2
        else:
            self.offset_x = 0

        self.queue_draw()
        
    def get_text(self):
        '''Get text.'''
        return self.content
    
    def realize_entry(self, widget):
        '''Realize entry.'''
        # Init IMContext.
        self.im.set_client_window(widget.window)
        self.im.focus_in()
        
        text_width = self.get_content_width(self.content)
        rect = self.get_allocation()
        self.offset_x = max(0, text_width - rect.width + self.padding_x * 2)
        
    def key_press_entry(self, widget, event):
        '''Callback for `key-press-event` signal.'''
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
        if text_width > rect.width - self.padding_x * 2:
            self.offset_x = text_width - (rect.width - self.padding_x * 2)
        self.cursor_index = len(self.content)
        
        self.clear_select_status()
        
        self.queue_draw()
        
    def move_to_left(self):
        '''Move to left char.'''
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
        clipboard = gtk.Clipboard()    
        clipboard.request_text(lambda clipboard, text, data: self.commit_entry('\\n'.join(text.split('\n'))))
        
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
        if self.select_start_index != self.select_end_index:
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
        self.draw_entry_background(cr, rect)
        
        # Draw text.
        self.draw_entry_text(cr, rect)
        
        # Draw cursor.
        self.draw_entry_cursor(cr, rect)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def draw_entry_background(self, cr, rect):
        '''Draw entry background.'''
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        draw_hlinear(cr, x, y, w, h,
                     self.background_color.get_color_info())
        
        if self.select_start_index != self.select_end_index:
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
            
            if self.select_start_index != self.select_end_index:
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
        if self.select_start_index == self.select_end_index:
            # Init.
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            left_str = self.content[0:self.cursor_index]
            right_str = self.content[self.cursor_index::]
            left_str_width = self.get_content_width(left_str)
            
            # Draw cursor.
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("entryCursor").get_color()))
            cr.rectangle(x + self.padding_x + left_str_width - self.offset_x,
                         y + self.padding_y,
                         1, 
                         h - self.padding_y * 2)
            cr.fill()
    
    def button_press_entry(self, widget, event):
        '''Button press entry.'''
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
            (wx, wy) = self.window.get_root_origin()
            (cx, cy, modifier) = self.window.get_pointer()
            self.right_menu.show((wx + int(event.x), cy + wy))
        # Change cursor when click left button.
        elif is_left_button(event):
            self.left_click_flag = True
            self.left_click_coordindate = (event.x, event.y)
            
    def button_release_entry(self, widget, event):
        '''Callback for `button-release-event` signal.'''
        if not self.double_click_flag and self.left_click_coordindate == (event.x, event.y):
            cr = widget.window.cairo_create()
            context = pangocairo.CairoContext(cr)
            layout = context.create_layout()
            layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
            layout.set_text(self.content)
            (text_width, text_height) = layout.get_pixel_size()
            if int(event.x) > text_width:
                self.cursor_index = len(self.content)
            else:
                (render_text_offset_x, render_text_offset_y) = layout.xy_to_index((int(event.x) + self.offset_x) * pango.SCALE, 0)
                self.cursor_index = max(render_text_offset_x - 1, 0)
                
            self.select_start_index = self.select_end_index = self.cursor_index
            
            self.queue_draw()
            
        self.double_click_flag = False
        self.left_click_flag = False
            
    def motion_notify_entry(self, widget, event):
        '''Callback for `motion-notify-event` signal.'''
        print event
        
    def commit_entry(self, input_text):
        '''Entry commit.'''
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
            return ""
    
gobject.type_register(Entry)

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
