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
                 
from constant import DEFAULT_FONT_SIZE, ALIGN_START, DEFAULT_FONT
from draw import draw_text, draw_hlinear
from keymap import get_keyevent_name
from theme import ui_theme
from utils import propagate_expose, get_content_size, is_double_click, is_left_button
import gtk
import pango 
import pangocairo

class Label(gtk.EventBox):
    '''Label.'''
	
    def __init__(self, 
                 text, 
                 text_color=None,
                 text_size=DEFAULT_FONT_SIZE,
                 text_x_align=ALIGN_START,
                 label_width=None,
                 enable_gaussian=False,
                 enable_select=True,
                 enable_double_click=True,
                 gaussian_radious=2,
                 border_radious=1,
                 wrap_width=None,
                 ):
        '''Init label.'''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.label_width = label_width
        self.enable_gaussian = enable_gaussian
        self.enable_select = enable_select
        self.enable_double_click = enable_double_click
        self.select_start_index = self.select_end_index = 0
        self.double_click_flag = False
        self.left_click_flag = False
        self.left_click_coordindate = None
        self.drag_start_index = 0
        self.drag_end_index = 0
        self.wrap_width = wrap_width
        
        self.text = text
        self.text_size = text_size
        if text_color == None:
            self.text_color = ui_theme.get_color("label_text")
        else:
            self.text_color = text_color
        self.text_select_color = ui_theme.get_color("label_select_text")    
        self.text_select_background = ui_theme.get_color("label_select_background")    
            
        if self.enable_gaussian:
            self.gaussian_radious = gaussian_radious
            self.border_radious = border_radious
            self.gaussian_color="#000000"
            self.border_color="#000000"
        else:
            self.gaussian_radious=None
            self.border_radious=None
            self.gaussian_color=None
            self.border_color=None
            
        self.text_x_align = text_x_align
        
        self.update_size()
            
        self.connect("expose-event", self.expose_label)    
        self.connect("button-press-event", self.button_press_label)
        self.connect("button-release-event", self.button_release_label)
        self.connect("motion-notify-event", self.motion_notify_label)
        self.connect("key-press-event", self.key_press_label)
        self.connect("focus-out-event", self.focus_out_label)
        
        # Add keymap.
        self.keymap = {
            "Ctrl + c" : self.copy_to_clipboard,
            }
        
    def copy_to_clipboard(self):
        '''Copy select text to clipboard.'''
        if self.select_start_index != self.select_end_index:
            cut_text = self.text[self.select_start_index:self.select_end_index]
            
            clipboard = gtk.Clipboard()
            clipboard.set_text(cut_text)
            
    def button_press_label(self, widget, event):
        '''Button press label.'''
        if not self.enable_gaussian:
            # Get input focus.
            self.grab_focus()
        
            # Select all when double click left button.
            if is_double_click(event) and self.enable_double_click:
                self.double_click_flag = True
                self.select_all()
            # Change cursor when click left button.
            elif is_left_button(event):
                self.left_click_flag = True
                self.left_click_coordindate = (event.x, event.y)
                
                self.drag_start_index = self.get_index_at_event(widget, event)
            
    def button_release_label(self, widget, event):
        '''Button release label.'''
        if not self.double_click_flag and self.left_click_coordindate == (event.x, event.y):
            self.select_start_index = self.select_end_index = 0
            self.queue_draw()
            
        self.double_click_flag = False
        self.left_click_flag = False
        
    def motion_notify_label(self, widget, event):
        '''Callback for `motion-notify-event` signal.'''
        if not self.double_click_flag and self.left_click_flag and self.enable_select:
            self.drag_end_index = self.get_index_at_event(widget, event)
            
            self.select_start_index = min(self.drag_start_index, self.drag_end_index)
            self.select_end_index = max(self.drag_start_index, self.drag_end_index)
            
            self.queue_draw()    
            
    def key_press_label(self, widget, event):
        '''Callback for `key-press-event` signal.'''
        key_name = get_keyevent_name(event)
        
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
            
        return False
    
    def focus_out_label(self, widget, event):
        '''Focus out label.'''
        if self.select_start_index != self.select_end_index:
            self.select_start_index = self.select_end_index = 0
            
            self.queue_draw()
    
    def get_index_at_event(self, widget, event):
        '''Get index at event.'''
        cr = widget.window.cairo_create()
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.text_size)))
        layout.set_text(self.text)
        (text_width, text_height) = layout.get_pixel_size()
        if int(event.x) > text_width:
            return len(self.text)
        else:
            (x_index, y_index) = layout.xy_to_index(int(event.x) * pango.SCALE, 0)
            return x_index
        
    def get_content_width(self, content):
        '''Get content width.'''
        (content_width, content_height) = get_content_size(content, self.text_size, wrap_width=self.wrap_width)
        return content_width
    
    def select_all(self):
        '''Select all.'''
        self.select_start_index = 0
        self.select_end_index = len(self.text)
        
        self.queue_draw()
    
    def expose_label(self, widget, event):
        '''Expose label.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        self.draw_label_background(cr, rect)
        
        self.draw_label_text(cr, rect)
        
        propagate_expose(widget, event)
        
        return True
    
    def draw_label_background(self, cr, rect):
        '''Draw label background.'''
        if self.select_start_index != self.select_end_index:
            select_start_width = self.get_content_width(self.text[0:self.select_start_index])
            select_end_width = self.get_content_width(self.text[0:self.select_end_index])
            
            draw_hlinear(cr, 
                         rect.x + select_start_width,
                         rect.y,
                         select_end_width - select_start_width,
                         rect.height,
                         [(0, (self.text_select_background.get_color(), 0)),
                          (0, (self.text_select_background.get_color(), 1))]
                         )
    
    def draw_label_text(self, cr, rect):
        '''Draw label text.'''
        if self.enable_gaussian:
            label_color = "#FFFFFF"
        else:
            label_color = self.text_color.get_color()

        if not self.get_sensitive():    
            draw_text(cr, self.text, 
                      rect.x, rect.y, rect.width, rect.height,
                      self.text_size,
                      ui_theme.get_color("disable_text").get_color(),
                      alignment=self.text_x_align, 
                      gaussian_radious=self.gaussian_radious,
                      gaussian_color=self.gaussian_color,
                      border_radious=self.border_radious,
                      border_color=self.border_color,
                      wrap_width=self.wrap_width
                      )
        elif self.select_start_index == self.select_end_index:    
            draw_text(cr, self.text, 
                      rect.x, rect.y, rect.width, rect.height,
                      self.text_size,
                      label_color,
                      alignment=self.text_x_align, 
                      gaussian_radious=self.gaussian_radious,
                      gaussian_color=self.gaussian_color,
                      border_radious=self.border_radious,
                      border_color=self.border_color,
                      wrap_width=self.wrap_width
                      )
        else:
            select_start_width = self.get_content_width(self.text[0:self.select_start_index])
            select_end_width = self.get_content_width(self.text[0:self.select_end_index])

            # Draw left text.
            if self.text[0:self.select_start_index] != "":
                draw_text(cr, self.text[0:self.select_start_index], 
                          rect.x, rect.y, rect.width, rect.height,
                          self.text_size,
                          label_color,
                          alignment=self.text_x_align, 
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width
                          )

            # Draw middle text.
            if self.text[self.select_start_index:self.select_end_index] != "":
                draw_text(cr, self.text[self.select_start_index:self.select_end_index], 
                          rect.x + select_start_width, rect.y, rect.width, rect.height,
                          self.text_size,
                          self.text_select_color.get_color(),
                          alignment=self.text_x_align, 
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width
                          )

            # Draw right text.
            if self.text[self.select_end_index::] != "":
                draw_text(cr, self.text[self.select_end_index::], 
                          rect.x + select_end_width, rect.y, rect.width, rect.height,
                          self.text_size,
                          label_color,
                          alignment=self.text_x_align, 
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width
                          )
        
    def get_text(self):
        '''Get text of label.'''
        return self.text
    
    def set_text(self, text):
        '''Set text.'''
        self.text = text
        
        self.update_size()

        self.queue_draw()
    
    def update_size(self):
        '''Update size.'''
        if self.label_width == None:
            (label_width, label_height) = get_content_size(self.text, self.text_size, wrap_width=self.wrap_width)
        else:
            (label_width, label_height) = get_content_size(self.text, self.text_size, wrap_width=self.wrap_width)
            label_width = self.label_width
            
        if self.enable_gaussian:
            label_width += self.gaussian_radious * 2
            label_height += self.gaussian_radious * 2
            
        self.set_size_request(label_width, label_height)
