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

import os
import gtk
import gobject
from window import Window
from draw import draw_window_shadow, draw_window_frame, draw_pixbuf, draw_vlinear, draw_hlinear
from utils import propagate_expose, is_in_rect, set_cursor, color_hex_to_cairo, enable_shadow, cairo_state, container_remove_all
from keymap import has_shift_mask
from titlebar import Titlebar
from dominant_color import get_dominant_color
from iconview import IconView
from scrolled_window import ScrolledWindow
from button import Button

class SkinWindow(Window):
    '''SkinWindow.'''
	
    def __init__(self, preview_width, preview_height, background_path):
        '''Init skin.'''
        Window.__init__(self)
        self.main_box = gtk.VBox()
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            "选择皮肤")
        
        self.window_frame.add(self.main_box)
        self.set_size_request(preview_width, preview_height)
        self.set_resizable(False)
        
        self.edit_area_align = gtk.Alignment()
        self.edit_area_align.set(0, 0, 1, 1)
        self.edit_area_align.set_padding(0, 1, 1, 1)
        # self.edit_area = SkinEditArea(preview_width, preview_height, background_path)
        # self.edit_area_align.add(self.edit_area)
        
        self.preview = SkinPreview("/home/andy/deepin-ui-private/skin")
        
        self.main_box.pack_start(self.titlebar, False, False)
        self.body_box = gtk.VBox()
        self.main_box.pack_start(self.body_box, True, True)
        
        self.titlebar.close_button.connect("clicked", lambda w: gtk.main_quit())
        self.connect("destroy", lambda w: gtk.main_quit())
        
        self.add_move_event(self.titlebar)
        
        self.switch_preview_page()
        
        self.preview.preview_view.connect("button-press-item", lambda view, item, x, y: self.switch_edit_page(item.background_path))
        
    def switch_preview_page(self):
        '''Switch preview page.'''
        container_remove_all(self.body_box)
        self.body_box.add(self.preview)
        
    def switch_edit_page(self, background_path):
        '''Switch edit page.'''
        container_remove_all(self.body_box)
        container_remove_all(self.edit_area_align)
        self.body_box.add(self.edit_area_align)
        self.edit_area_align.add(SkinEditArea(background_path))
        
        self.show_all()
        
gobject.type_register(SkinWindow)

class SkinPreview(gtk.VBox):
    '''Skin preview.'''
	
    def __init__(self, skin_dir):
        '''Init skin preview.'''
        gtk.VBox.__init__(self)
        self.skin_dir = skin_dir
        
        self.preview_align = gtk.Alignment()
        self.preview_align.set(0.5, 0.5, 1, 1)
        self.preview_align.set_padding(0, 0, 10, 5)
        self.preview_scrolled_window = ScrolledWindow()
        self.preview_scrolled_window.set_scroll_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.preview_view = IconView()
                
        self.preview_align.add(self.preview_scrolled_window)
        self.preview_scrolled_window.add_child(self.preview_view)
        self.pack_start(self.preview_align, True, True)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 0, 20)
        self.close_button = Button("Close")
        self.button_align.add(self.close_button)
        self.pack_start(self.button_align, False, False)
        
        for root, dirs, files in os.walk(skin_dir):
            for filename in files:
                if filename == "background.jpg":
                    filepath = os.path.join(root, filename)
                    self.preview_view.add_items([SkinPreviewIcon(filepath)])
        
gobject.type_register(SkinPreview)
        
class SkinPreviewIcon(gobject.GObject):
    '''Icon item.'''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, background_path):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.background_path = background_path
        self.width = 86
        self.height = 56
        self.icon_padding = 2
        self.padding_x = 7
        self.padding_y = 10
        self.hover_flag = False
        self.highlight_flag = False
        
        self.create_preview_pixbuf(background_path)
        
    def create_preview_pixbuf(self, background_path):
        '''Create preview pixbuf.'''
        background_pixbuf = gtk.gdk.pixbuf_new_from_file(background_path)        
        background_width, background_height = background_pixbuf.get_width(), background_pixbuf.get_height()
        if background_width >= self.width and background_height >= self.height:
            if background_width / background_height == self.width / self.height:
                scale_width, scale_height = self.width, self.height
            elif background_width / background_height > self.width / self.height:
                scale_height = self.height
                scale_width = int(background_width * self.height / background_height)
            else:
                scale_width = self.width
                scale_height = int(background_height * self.width / background_width)
                
            self.pixbuf = background_pixbuf.scale_simple(
                scale_width, 
                scale_height, 
                gtk.gdk.INTERP_BILINEAR).subpixbuf(0, 0, self.width, self.height)
        else:
            self.pixbuf = background_pixbuf
                
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.width + (self.icon_padding + self.padding_x) * 2
        
    def get_height(self):
        '''Get height.'''
        return self.height + (self.icon_padding + self.padding_y) * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Draw frame.
        if self.hover_flag:
            cr.set_source_rgb(1, 0, 0)
        elif self.highlight_flag:
            cr.set_source_rgb(0, 1, 0)
        else:
            cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.rectangle(
            rect.x + self.padding_x,
            rect.y + self.padding_y,
            rect.width - self.padding_x * 2,
            rect.height - self.padding_y * 2
            )
        cr.fill()
        
        # Draw background.
        with cairo_state(cr):
            # Draw cover.
            draw_pixbuf(
                cr, 
                self.pixbuf, 
                rect.x + (rect.width - self.pixbuf.get_width()) / 2,
                rect.y + (rect.height - self.pixbuf.get_height()) / 2
                )
        
    def icon_item_motion_notify(self, x, y):
        '''Handle `motion-notify-event` signal.'''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''Lost focus.'''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''Highlight item.'''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''Set item with normal status.'''
        self.highlight_flag = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''Handle button-press event.'''
        pass        
    
    def icon_item_button_release(self, x, y):
        '''Handle button-release event.'''
        pass
    
    def icon_item_single_click(self, x, y):
        '''Handle single click event.'''
        pass

    def icon_item_double_click(self, x, y):
        '''Handle double click event.'''
        pass
        
gobject.type_register(SkinPreviewIcon)
        
class SkinEditArea(gtk.DrawingArea):
    '''Skin edit area.'''
    
    POSITION_LEFT_SIDE = 0
    POSITION_RIGHT_SIDE = 1
    POSITION_TOP_SIDE = 2
    POSITION_BOTTOM_SIDE = 3
    POSITION_TOP_LEFT_CORNER = 4
    POSITION_TOP_RIGHT_CORNER = 5
    POSITION_BOTTOM_LEFT_CORNER = 6
    POSITION_BOTTOM_RIGHT_CORNER = 7
    POSITION_INSIDE = 8
    POSITION_OUTSIDE = 9
	
    # def __init__(self, preview_width, preview_height, background_path):
    def __init__(self, background_path):
        '''Init skin edit area.'''
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        # self.preview_width = preview_width
        # self.preview_height = preview_height
        self.background_pixbuf = gtk.gdk.pixbuf_new_from_file(background_path)
        self.padding_x = 20
        self.padding_y = 20
        self.resize_pointer_size = 8
        self.resize_frame_size = 2
        self.resize_x = 0
        self.resize_y = 0
        self.resize_width = self.background_pixbuf.get_width()
        self.resize_height = self.background_pixbuf.get_height()
        self.min_resize_width = self.min_resize_height = 32
        self.shadow_radius = 6
        self.frame_radius = 2
        self.shadow_padding = self.shadow_radius - self.frame_radius
        self.action_type = None
        self.button_press_flag = False
        self.button_release_flag = True
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_background_x = 0
        self.drag_background_y = 0
        self.resize_frame_flag = False
        self.in_resize_area_flag = False
        self.dominant_color = get_dominant_color(background_path)
        self.shadow_size = 200  # pixel
        self.press_shift_flag = False
        
        # self.set_size_request(
        #     self.preview_width + self.padding_x * 2,
        #     self.preview_height + self.padding_y * 2
        #     )
        
        self.connect("expose-event", self.expose_skin_edit_area)
        self.connect("button-press-event", self.button_press_skin_edit_area)
        self.connect("button-release-event", self.button_release_skin_edit_area)
        self.connect("motion-notify-event", self.motion_skin_edit_area)
        self.connect("key-press-event", self.key_press_skin_edit_area)
        self.connect("key-release-event", self.key_release_skin_edit_area)
        
    def is_in_resize_area(self, event):
        '''Is at resize area.'''
        offset_x = self.padding_x + self.shadow_padding
        offset_y = self.padding_y + self.shadow_padding
        return is_in_rect(
            (event.x, event.y),
            (self.resize_x + offset_x - self.resize_pointer_size / 2,
             self.resize_y + offset_y - self.resize_pointer_size / 2, 
             self.resize_width + self.resize_pointer_size, 
             self.resize_height + self.resize_pointer_size))        
        
    def expose_skin_edit_area(self, widget, event):
        '''Expose edit area.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        offset_x = self.padding_x + self.shadow_padding
        offset_y = self.padding_y + self.shadow_padding
        resize_x = offset_x + self.resize_x
        resize_y = offset_y + self.resize_y

        # Draw background.
        draw_pixbuf(
            cr,
            self.background_pixbuf.scale_simple(
                self.resize_width,
                self.resize_height,
                gtk.gdk.INTERP_BILINEAR),
            resize_x,
            resize_y)
        
        # Draw dominant shadow color.
        if self.button_release_flag:
            background_area_width = self.resize_width + self.resize_x
            background_area_height = self.resize_height + self.resize_y
            if background_area_width < w - offset_x * 2:
                draw_hlinear(
                    cr, 
                    offset_x + background_area_width - self.shadow_size,
                    offset_y + self.resize_y,
                    self.shadow_size,
                    background_area_height - self.resize_y,
                    [(0, (self.dominant_color, 0)),
                     (1, (self.dominant_color, 1))])
                
                cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))        
                cr.rectangle(
                    offset_x + background_area_width,
                    offset_y + self.resize_y,
                    w - offset_x * 2 - background_area_width,
                    background_area_height - self.resize_y)
                cr.fill()
            if background_area_height < h - offset_y * 2:
                draw_vlinear(
                    cr, 
                    offset_x + self.resize_x,
                    offset_y + background_area_height - self.shadow_size,
                    background_area_width - self.resize_x,
                    self.shadow_size,
                    [(0, (self.dominant_color, 0)),
                     (1, (self.dominant_color, 1))]
                    )

                cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))        
                cr.rectangle(
                    offset_x + self.resize_x,
                    offset_y + background_area_height,
                    w - offset_x * 2 - self.resize_x,
                    h - offset_y * 2 - background_area_height)
                cr.fill()
        
        # Draw window shadow.
        if enable_shadow(self):
            draw_window_shadow(
                cr, 
                self.padding_x, 
                self.padding_y, 
                w - self.padding_x * 2,
                h - self.padding_y * 2,
                self.shadow_radius, 
                self.shadow_padding)

        # Draw window frame.
        draw_window_frame(
            cr,
            offset_x,
            offset_y,
            w - offset_x * 2,
            h - offset_y * 2)    
        
        if self.in_resize_area_flag:
            # Draw resize frame.
            cr.set_source_rgb(0, 1, 1)
            
            # Resize frame.
            cr.rectangle(           # top
                resize_x, 
                resize_y - self.resize_frame_size / 2,
                self.resize_width,
                self.resize_frame_size)
            cr.rectangle(           # bottom
                resize_x,
                resize_y + self.resize_height - self.resize_frame_size / 2,
                self.resize_width,
                self.resize_frame_size)
            cr.rectangle(           # left
                resize_x - self.resize_frame_size / 2,
                resize_y,
                self.resize_frame_size,
                self.resize_height)
            cr.rectangle(           # right
                resize_x + self.resize_width - self.resize_frame_size / 2,
                resize_y,
                self.resize_frame_size,
                self.resize_height)
            
            # Resize pointer.
            cr.rectangle(           # top-left
                resize_x - self.resize_pointer_size / 2,
                resize_y - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # top-center
                resize_x + self.resize_width / 2 - self.resize_pointer_size / 2,
                resize_y - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # top-right
                resize_x + self.resize_width - self.resize_pointer_size / 2,
                resize_y - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # bottom-left
                resize_x - self.resize_pointer_size / 2,
                resize_y + self.resize_height - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # bottom-center
                resize_x + self.resize_width / 2 - self.resize_pointer_size / 2,
                resize_y + self.resize_height - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # bottom-right
                resize_x + self.resize_width - self.resize_pointer_size / 2,
                resize_y + self.resize_height - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # left-center
                resize_x - self.resize_pointer_size / 2,
                resize_y + self.resize_height / 2 - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            cr.rectangle(           # right-center
                resize_x + self.resize_width - self.resize_pointer_size / 2,
                resize_y + self.resize_height / 2 - self.resize_pointer_size / 2,
                self.resize_pointer_size,
                self.resize_pointer_size)
            
            cr.fill()
        
        propagate_expose(widget, event)
        
        return True
    
    def button_press_skin_edit_area(self, widget, event):
        '''Callback for `button-press-event`'''
        self.button_press_flag = True
        self.button_release_flag = False
        self.action_type = self.skin_edit_area_get_action_type(event)
        self.skin_edit_area_set_cursor(self.action_type)
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.drag_background_x = self.resize_x
        self.drag_background_y = self.resize_y

    def button_release_skin_edit_area(self, widget, event):
        '''Callback for `button-release-event`.'''
        self.button_press_flag = False
        self.button_release_flag = True
        self.action_type = None
        self.skin_edit_area_set_cursor(self.skin_edit_area_get_action_type(event))
    
        self.queue_draw()
        
    def motion_skin_edit_area(self, widget, event):
        '''Callback for `motion-notify-event`.'''
        if self.button_press_flag:
            if self.action_type != None:
                if self.action_type == self.POSITION_INSIDE:
                    self.skin_edit_area_drag_background(event)
                elif self.action_type == self.POSITION_TOP_LEFT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_TOP_RIGHT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_LEFT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_TOP_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_LEFT_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_RIGHT_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
        else:
            self.skin_edit_area_set_cursor(self.skin_edit_area_get_action_type(event))

            old_flag = self.in_resize_area_flag
            self.in_resize_area_flag = self.is_in_resize_area(event)
            if old_flag != self.in_resize_area_flag:
                self.queue_draw()
                
    def key_press_skin_edit_area(self, widget, event):
        '''Callback for `key-press-event` signal.'''
        if has_shift_mask(event):
            self.press_shift_flag = True
        
    def key_release_skin_edit_area(self, widget, event):
        '''Callback for `key-release-event` signal.'''
        if has_shift_mask(event):
            self.press_shift_flag = False
                
    def skin_edit_area_drag_background(self, event):
        '''Drag background.'''
        new_resize_x = int(event.x) - self.drag_start_x + self.drag_background_x
        new_resize_y = int(event.y) - self.drag_start_y + self.drag_background_y
        self.resize_x = min(max(new_resize_x, self.min_resize_width - self.resize_width), 0)
        self.resize_y = min(max(new_resize_y, self.min_resize_height - self.resize_height), 0)
        
        self.queue_draw()
            
    def skin_edit_area_resize(self, action_type, event):
        '''Resize.'''
        if action_type == self.POSITION_LEFT_SIDE:
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_SIDE:
            self.skin_edit_area_adjust_top(event)
            self.queue_draw()
        elif action_type == self.POSITION_RIGHT_SIDE:
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_SIDE:
            self.skin_edit_area_adjust_bottom(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_LEFT_CORNER:
            self.skin_edit_area_adjust_top(event)
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_RIGHT_CORNER:
            self.skin_edit_area_adjust_top(event)
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_LEFT_CORNER:
            self.skin_edit_area_adjust_bottom(event)
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
            self.skin_edit_area_adjust_bottom(event)
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
            
    def skin_edit_area_adjust_left(self, event):
        '''Adjust left.'''
        offset_x = self.padding_x + self.shadow_padding
        new_resize_x = min(int(event.x) - offset_x, 0)
        self.resize_width = self.resize_width + self.resize_x - new_resize_x
        self.resize_x = int(new_resize_x)
        
    def skin_edit_area_adjust_top(self, event):
        '''Adjust top.'''
        offset_y = self.padding_y + self.shadow_padding
        new_resize_y = min(int(event.y) - offset_y, 0)
        self.resize_height = self.resize_height + self.resize_y - new_resize_y
        self.resize_y = int(new_resize_y)
        
    def skin_edit_area_adjust_right(self, event):
        '''Adjust right.'''
        offset_x = self.padding_x + self.shadow_padding
        new_resize_x = max(offset_x + self.min_resize_width, int(event.x))
        self.resize_width = int(new_resize_x - self.resize_x - offset_x)
        
    def skin_edit_area_adjust_bottom(self, event):
        '''Adjust bottom.'''
        offset_y = self.padding_y + self.shadow_padding
        new_resize_y = max(offset_y + self.min_resize_height, int(event.y))
        self.resize_height = int(new_resize_y - self.resize_y - offset_y)

    def skin_edit_area_set_cursor(self, action_type):
        '''Set cursor.'''
        if action_type == self.POSITION_INSIDE:
            set_cursor(self, gtk.gdk.FLEUR)
        elif action_type == self.POSITION_TOP_LEFT_CORNER:
            set_cursor(self, gtk.gdk.TOP_LEFT_CORNER)
        elif action_type == self.POSITION_TOP_RIGHT_CORNER:
            set_cursor(self, gtk.gdk.TOP_RIGHT_CORNER)
        elif action_type == self.POSITION_BOTTOM_LEFT_CORNER:
            set_cursor(self, gtk.gdk.BOTTOM_LEFT_CORNER)
        elif action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
            set_cursor(self, gtk.gdk.BOTTOM_RIGHT_CORNER)
        elif action_type == self.POSITION_TOP_SIDE:
            set_cursor(self, gtk.gdk.TOP_SIDE)
        elif action_type == self.POSITION_BOTTOM_SIDE:
            set_cursor(self, gtk.gdk.BOTTOM_SIDE)
        elif action_type == self.POSITION_LEFT_SIDE:
            set_cursor(self, gtk.gdk.LEFT_SIDE)
        elif action_type == self.POSITION_RIGHT_SIDE:
            set_cursor(self, gtk.gdk.RIGHT_SIDE)
        else:
            set_cursor(self, None)
        
    def skin_edit_area_get_action_type(self, event):
        '''Get action type.'''
        ex, ey = event.x, event.y
        resize_x = self.padding_x + self.shadow_padding + self.resize_x
        resize_y = self.padding_y + self.shadow_padding + self.resize_y
        
        if is_in_rect((ex, ey), 
                      (resize_x - self.resize_pointer_size / 2,
                       resize_y - self.resize_pointer_size / 2,
                       self.resize_pointer_size,
                       self.resize_pointer_size)):
            return self.POSITION_TOP_LEFT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y - self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_TOP_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_TOP_RIGHT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x - self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_LEFT_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_RIGHT_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x - self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_LEFT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_RIGHT_CORNER
        elif is_in_rect((ex, ey),
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_INSIDE
        else:
            return self.POSITION_OUTSIDE
        
gobject.type_register(SkinEditArea)
        
if __name__ == '__main__':
    skin_window = SkinWindow(450, 500, "/data/Picture/Misc/23424.jpg")
    skin_window.move(400, 100)
    
    skin_window.show_all()
    
    gtk.main()
    
