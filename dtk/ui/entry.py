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
        self.content = content
        self.cursor_index = 0
        self.select_start_index = 0
        self.select_end_index = 0
        self.offset_x = 0
        self.text_color = text_color
        self.text_select_color = text_select_color
        self.background_color = background_color
        self.background_select_color = background_select_color
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.move_direction = self.MOVE_NONE
        
        # Add keymap.
        self.keymap = {
            "Left" : self.move_to_left,
            "Right" : self.move_to_right,
            "Home" : self.move_to_start,
            "End" : self.move_to_end,
            "BackSpace" : self.backspace,
            "Delete" : self.delete,
            "S-Left" : self.select_to_prev,
            "S-Right" : self.select_to_next,
            "S-Home" : self.select_to_start,
            "S-End" : self.select_to_end,
            "C-a" : self.select_all}
        
        # Connect signal.
        self.connect("realize", self.realize_entry)
        self.connect("key-press-event", self.key_press_entry)
        self.connect("expose-event", self.expose_entry)
        self.connect("button-press-event", self.button_press_entry)
        
        self.im.connect("commit", self.commit_entry)
        
    def set_text(self, text):
        '''Set text.'''
        self.content = text

        self.queue_draw()
        
    def get_text(self):
        '''Get text.'''
        return self.content
        
    def realize_entry(self, widget):
        '''Realize entry.'''
        # Init IMContext.
        self.im.set_client_window(widget.window)
        self.im.focus_in()
        
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
            
    def move_to_start(self):
        '''Move to start.'''
        self.offset_x = 0
        self.cursor_index = 0
        
        self.queue_draw()
        
    def move_to_end(self):
        '''Move to end.'''
        (text_width, text_height) = get_content_size(self.content, self.font_size)
        rect = self.get_allocation()
        if text_width > rect.width - self.padding_x * 2:
            self.offset_x = text_width - (rect.width - self.padding_x * 2)
        self.cursor_index = len(self.content)
        
        self.queue_draw()
        
    def move_to_left(self):
        '''Move to left char.'''
        if self.select_start_index != self.select_end_index:
            self.cursor_index = self.select_start_index
            (select_start_width, select_start_height) = get_content_size(self.content[0:self.select_start_index], self.font_size)

            self.select_start_index = self.select_end_index = 0
            self.move_direction = self.MOVE_NONE

            if select_start_width < self.offset_x:
                self.offset_x = select_start_width
            
            self.queue_draw()
        elif self.cursor_index > 0:
            self.cursor_index -= len(list(self.content[0:self.cursor_index].decode('utf-8'))[-1].encode('utf-8'))
            
            (text_width, text_height) = get_content_size(self.content[0:self.cursor_index], self.font_size)
            if text_width - self.offset_x < 0:
                self.offset_x = text_width
                
            self.queue_draw()    
            
    def move_to_right(self):
        '''Move to right char.'''
        if self.select_start_index != self.select_end_index:
            self.cursor_index = self.select_end_index
            (select_end_width, select_end_height) = get_content_size(self.content[0:self.select_end_index], self.font_size)

            self.select_start_index = self.select_end_index = 0
            self.move_direction = self.MOVE_NONE
            
            rect = self.get_allocation()
            if select_end_width > self.offset_x + rect.width - self.padding_x * 2:
                self.offset_x = select_end_width - rect.width + self.padding_x * 2
            
            self.queue_draw()
        elif self.cursor_index < len(self.content):
            self.cursor_index += len(self.content[self.cursor_index::].decode('utf-8')[0].encode('utf-8'))            
            
            (text_width, text_height) = get_content_size(self.content[0:self.cursor_index], self.font_size)
            rect = self.get_allocation()
            if text_width - self.offset_x > rect.width - self.padding_x * 2:
                self.offset_x = text_width - (rect.width - self.padding_x * 2)
            
            self.queue_draw()
            
    def backspace(self):
        '''Backspace.'''
        if self.cursor_index > 0:
            (old_insert_width, old_insert_height) = get_content_size(self.content[0:self.cursor_index], self.font_size)
            delete_char = list(self.content[0:self.cursor_index].decode('utf-8'))[-1].encode('utf-8')
            self.cursor_index -= len(delete_char)
            
            self.content = self.content[0:self.cursor_index] + self.content[self.cursor_index + len(delete_char)::]
            (text_width, text_height) = get_content_size(self.content, self.font_size)
            (insert_width, insert_height) = get_content_size(self.content[0:self.cursor_index], self.font_size)
            rect = self.get_allocation()
            if text_width < rect.width - self.padding_x * 2:
                self.offset_x = 0
            else:
                adjust_x = self.offset_x + (rect.width - self.padding_x * 2) - old_insert_width
                                
                self.offset_x = insert_width - (rect.width - self.padding_x * 2) + adjust_x
                
            self.queue_draw()    
            
    def select_all(self):
        '''Select all.'''
        self.select_start_index = 0
        self.select_end_index = len(self.content)
        
        self.queue_draw()
        
    def select_to_prev(self):
        '''Select to preview.'''
        if self.select_start_index != self.select_end_index:
            if self.select_start_index > 0:
                if self.move_direction == self.MOVE_LEFT:
                    self.select_start_index -= len(list(self.content[0:self.select_start_index].decode('utf-8'))[-1].encode('utf-8'))
                else:
                    self.select_end_index -= len(list(self.content[0:self.select_end_index].decode('utf-8'))[-1].encode('utf-8'))
        else:
            self.select_end_index = self.cursor_index
            self.select_start_index = self.cursor_index - len(list(self.content[0:self.cursor_index].decode('utf-8'))[-1].encode('utf-8'))
            self.move_direction = self.MOVE_LEFT
            
        (select_start_width, select_start_height) = get_content_size(self.content[0:self.select_start_index], self.font_size)    
        if select_start_width < self.offset_x:
            self.offset_x = select_start_width
            
        self.queue_draw()
        
    def select_to_next(self):
        '''Select to next.'''
        if self.select_start_index != self.select_end_index:
            if self.select_end_index < len(self.content):
                if self.move_direction == self.MOVE_RIGHT:
                    self.select_end_index += len(list(self.content[self.select_end_index::].decode('utf-8')[0].encode('utf-8')))
                else:
                    self.select_start_index += len(list(self.content[self.select_start_index::].decode('utf-8')[0].encode('utf-8')))
        else:
            self.select_start_index = self.cursor_index
            self.select_end_index = self.cursor_index + len(list(self.content[self.select_end_index::].decode('utf-8')[0].encode('utf-8')))
            self.move_direction = self.MOVE_RIGHT
            
        rect = self.get_allocation()    
        (select_end_width, select_end_height) = get_content_size(self.content[0:self.select_end_index], self.font_size)    
        if select_end_width > self.offset_x + rect.width - self.padding_x * 2:
            self.offset_x = select_end_width - rect.width + self.padding_x * 2
        
        self.queue_draw()        
        
    def select_to_start(self):
        '''Select to start.'''
        if self.select_start_index != self.select_end_index:
            if self.move_direction == self.MOVE_LEFT:
                self.select_start_index = 0
            else:
                self.select_start_index = 0
                self.select_end_index = self.select_start_index
        else:
            self.select_start_index = 0
            self.select_end_index = self.cursor_index

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
        else:
            self.select_start_index = self.cursor_index
            self.select_end_index = len(self.content)
        
        rect = self.get_allocation()
        (select_end_width, select_end_height) = get_content_size(self.content, self.font_size)
        self.offset_x = select_end_width - rect.width + self.padding_x * 2
        
        self.queue_draw()
        
    def delete(self):
        '''Delete select text.'''
        if self.select_start_index != self.select_end_index:
            rect = self.get_allocation()
            
            self.cursor_index = self.select_start_index
            
            (select_start_width, select_start_height) = get_content_size(self.content[0:self.select_start_index], self.font_size)
            (select_end_width, select_end_height) = get_content_size(self.content[0:self.select_end_index], self.font_size)
            
            self.cursor_index = self.select_start_index
            if select_start_width < self.offset_x:
                if select_end_width < self.offset_x + rect.width - self.padding_x * 2:
                    self.offset_x = max(select_start_width + self.offset_x - select_end_width, 0)
                else:
                    self.offset_x = 0
                    
            self.content = self.content[0:self.select_start_index] + self.content[self.select_end_index::]
                        
            self.select_start_index = self.select_end_index = 0
            
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
            (select_start_width, select_start_height) = get_content_size(self.content[0:self.select_start_index], self.font_size)
            (select_end_width, select_end_height) = get_content_size(self.content[0:self.select_end_index], self.font_size)
            
            draw_hlinear(cr, 
                         x + self.padding_x + max(select_start_width - self.offset_x, 0),
                         y + self.padding_y,
                         min(select_end_width - select_start_width, 
                             w - self.padding_x * 2 - max(select_start_width - self.offset_x, 0)),
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
            (left_str_width, left_str_height) = get_content_size(left_str, self.font_size)
            
            # Draw cursor.
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("entryCursor").get_color()))
            cr.rectangle(x + self.padding_x + left_str_width - self.offset_x,
                         y + self.padding_y,
                         1, 
                         h - self.padding_y * 2)
            cr.fill()
    
    def button_press_entry(self, widget, event):
        '''Button press entry.'''
        self.grab_focus()
        
    def commit_entry(self, im, input_text):
        '''Entry commit.'''
        self.content = self.content[0:self.cursor_index] + input_text + self.content[self.cursor_index::]
        self.cursor_index += len(input_text)
        
        (text_width, text_height) = get_content_size(self.content, self.font_size)
        rect = self.get_allocation()
        if text_width <= rect.width - self.padding_x * 2:
            self.offset_x = 0
        elif self.cursor_index == len(self.content):
            self.offset_x = text_width - (rect.width - self.padding_x * 2)
        else:
            (old_text_width, old_text_height) = get_content_size(self.content[0:self.cursor_index - len(input_text)], self.font_size)
            (input_text_width, input_text_height) = get_content_size(input_text, self.font_size)
            if old_text_width - self.offset_x + input_text_width > rect.width - self.padding_x * 2:
                (new_text_width, new_text_height) = get_content_size(self.content[0:self.cursor_index], self.font_size)
                self.offset_x = new_text_width - (rect.width - self.padding_x * 2)
        
        self.queue_draw()
        
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
