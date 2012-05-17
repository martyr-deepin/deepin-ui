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
from mask import draw_mask
from utils import is_in_rect, set_cursor, color_hex_to_cairo, enable_shadow, cairo_state, container_remove_all, cairo_disable_antialias, scroll_to_top
from keymap import has_shift_mask
from titlebar import Titlebar
from dominant_color import get_dominant_color
from iconview import IconView
from scrolled_window import ScrolledWindow
from button import Button
from theme import ui_theme
from config import Config
import math

def draw_skin_mask(cr, x, y, w, h):
    '''Draw skin mask.'''
    draw_vlinear(cr, x, y, w, h,
                 ui_theme.get_shadow_color("skinWindowBackground").get_color_info())
    
class SkinWindow(Window):
    '''SkinWindow.'''
	
    def __init__(self, preview_width=450, preview_height=500):
        '''Init skin.'''
        Window.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.draw_mask = lambda cr, x, y, w, h: draw_mask(self, x, y, w, h, draw_skin_mask)
        self.main_box = gtk.VBox()
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            "选择皮肤")
        
        self.window_frame.add(self.main_box)
        self.set_size_request(preview_width, preview_height)
        self.set_resizable(False)
        
        self.preview_page = SkinPreviewPage("/home/andy/deepin-ui-private/skin")
        
        self.main_box.pack_start(self.titlebar, False, False)
        self.body_box = gtk.VBox()
        self.main_box.pack_start(self.body_box, True, True)
        
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        
        self.add_move_event(self.titlebar)
        
        self.switch_preview_page()
        
        self.preview_page.preview_view.connect(
            "button-press-item", 
            lambda view, item, x, y: self.switch_edit_page(item.background_path))
        
    def switch_preview_page(self):
        '''Switch preview page.'''
        container_remove_all(self.body_box)
        self.body_box.add(self.preview_page)
        
    def switch_edit_page(self, background_path):
        '''Switch edit page.'''
        container_remove_all(self.body_box)
        edit_page = SkinEditPage(background_path)
        self.body_box.add(edit_page)
        
        edit_page.connect("click-save", lambda page: self.switch_preview_page())
        edit_page.connect("click-cancel", lambda page: self.switch_preview_page())
        
        self.show_all()
        
gobject.type_register(SkinWindow)

class SkinPreviewPage(gtk.VBox):
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
        self.preview_scrolled_window.draw_mask = lambda cr, x, y, w, h: draw_mask(self.preview_scrolled_window, x, y, w, h, draw_skin_mask)
        self.preview_view = IconView()
        self.preview_view.draw_mask = lambda cr, x, y, w, h: draw_mask(self.preview_view, x, y, w, h, draw_skin_mask)
                
        self.preview_align.add(self.preview_scrolled_window)
        self.preview_scrolled_window.add_child(self.preview_view)
        self.pack_start(self.preview_align, True, True)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 0, 20)
        self.close_button = Button("关闭")
        self.close_button.connect("clicked", lambda w: w.get_toplevel().destroy())
        self.button_align.add(self.close_button)
        self.pack_start(self.button_align, False, False)
        
        for root, dirs, files in os.walk(skin_dir):
            for filename in files:
                if filename == "background.jpg":
                    filepath = os.path.join(root, filename)
                    self.preview_view.add_items([SkinPreviewIcon(filepath)])
        
gobject.type_register(SkinPreviewPage)
        
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

class SkinEditPage(gtk.VBox):
    '''Init skin edit page.'''
	
    __gsignals__ = {
        "click-save" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "click-cancel" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, background_path):
        '''Init skin edit page.'''
        gtk.VBox.__init__(self)
        self.edit_area_align = gtk.Alignment()
        self.edit_area_align.set(0.5, 0.5, 1, 1)
        self.edit_area_align.set_padding(0, 0, 25, 25)
        self.edit_area = SkinEditArea(background_path)        
        self.edit_area_align.add(self.edit_area)
        
        self.color_select_align = gtk.Alignment()
        self.color_select_align.set(0.5, 0.5, 1, 1)
        self.color_select_align.set_padding(20, 20, 38, 38)
        self.color_select_view = IconView()
        self.color_select_view.draw_mask = lambda cr, x, y, w, h: draw_mask(self.color_select_view, x, y, w, h, draw_skin_mask)
        self.color_select_scrolled_window = ScrolledWindow()
        self.color_select_scrolled_window.set_scroll_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        self.color_select_scrolled_window.add_child(self.color_select_view)
        self.color_select_align.add(self.color_select_scrolled_window)
        
        for color in ["#C0FF00",
                      "#FFC600",
                      "#FCFF00",
                      "#8400FF",
                      "#00A8FF",
                      "#FF0000",
                      "#00FDFF",
                      "#0006FF",
                      "#BA00FF",
                      "#00FF60",
                      "#333333",
                      "#FF6C00",
                      "#FF00B4"]:
            self.color_select_view.add_items([ColorIconItem(color)])
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 0, 20)
        self.button_box = gtk.HBox()
        self.save_button = Button("保存")
        self.cancel_button = Button("取消")
        self.button_align.add(self.button_box)
        self.button_box.pack_start(self.save_button, False, False, 10)
        self.button_box.pack_start(self.cancel_button)
        
        self.pack_start(self.edit_area_align, False, False)
        self.pack_start(self.color_select_align, True, True)
        self.pack_start(self.button_align, False, False)
        
        self.save_button.connect("clicked", lambda w: self.emit("click-save"))
        self.cancel_button.connect("clicked", lambda w: self.emit("click-cancel"))
        
gobject.type_register(SkinEditPage)

class ColorIconItem(gobject.GObject):
    '''Icon item.'''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, color):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.color = color
        self.width = 40
        self.height = 25
        self.padding_x = 6
        self.padding_y = 6
        self.select_frame_size = 2
        self.hover_flag = False
        self.highlight_flag = False
        
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.width + self.padding_x * 2
        
    def get_height(self):
        '''Get height.'''
        return self.height + self.padding_y * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Draw select effect.
        if self.hover_flag:
            cr.set_source_rgb(1, 0, 0)
        elif self.highlight_flag:
            cr.set_source_rgb(0, 1, 0)
        else:
            cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.rectangle(
            rect.x + self.padding_x - self.select_frame_size,
            rect.y + self.padding_y - self.select_frame_size,
            self.width + self.select_frame_size * 2,
            self.height + self.select_frame_size * 2,
            )
        cr.fill()
        
        # Draw color area.
        cr.set_source_rgb(*color_hex_to_cairo(self.color))
        cr.rectangle(
            rect.x + self.padding_x,
            rect.y + self.padding_y,
            self.width,
            self.height)
        cr.fill()
        
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
    
gobject.type_register(ColorIconItem)

class SkinEditArea(gtk.EventBox):
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
    
    def __init__(self, background_path):
        '''Init skin edit area.'''
        gtk.EventBox.__init__(self)
        self.set_has_window(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        
        self.app_window_width = 900
        self.app_window_height = 600
        self.preview_window_width = 300
        self.preview_window_height = 200
        self.preview_frame_width = 400
        self.preview_frame_height = 300
        self.padding_x = (self.preview_frame_width - self.preview_window_width) / 2
        self.padding_y = (self.preview_frame_height - self.preview_window_height) / 2
        
        self.background_pixbuf = gtk.gdk.pixbuf_new_from_file(background_path)
        self.set_size_request(self.preview_frame_width, self.preview_frame_height)
        self.dominant_color = get_dominant_color(background_path)
        
        self.resize_pointer_size = 8
        self.resize_frame_size = 2
        self.resize_x = 0
        self.resize_y = 0
        self.resize_width = int(self.background_pixbuf.get_width() * self.preview_window_width / self.app_window_width)
        self.resize_height = int(self.background_pixbuf.get_height() * self.preview_window_width / self.app_window_width)
        self.min_resize_width = self.min_resize_height = 32
        
        self.shadow_radius = 6
        self.frame_radius = 2
        self.shadow_padding = self.shadow_radius - self.frame_radius
        self.shadow_size = int(200 * self.preview_window_width / self.app_window_width)
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_background_x = 0
        self.drag_background_y = 0
        
        self.action_type = None
        self.button_press_flag = False
        self.button_release_flag = True
        self.resize_frame_flag = False
        self.in_resize_area_flag = False
        self.press_shift_flag = False
        
        self.connect("expose-event", self.expose_skin_edit_area)
        self.connect("button-press-event", self.button_press_skin_edit_area)
        self.connect("button-release-event", self.button_release_skin_edit_area)
        self.connect("motion-notify-event", self.motion_skin_edit_area)
        self.connect("leave-notify-event", self.leave_notify_skin_edit_area)
        self.connect("key-press-event", self.key_press_skin_edit_area)
        self.connect("key-release-event", self.key_release_skin_edit_area)
        
    def expose_skin_edit_area(self, widget, event):
        '''Expose edit area.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        if self.button_release_flag:
            offset_x = x + self.padding_x
            offset_y = y + self.padding_y
            
            # Draw dominant color.
            cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))        
            cr.rectangle(
                offset_x + self.resize_x,
                offset_y + self.resize_y,
                w - self.padding_x - self.resize_x,
                h - self.padding_y - self.resize_y)
            cr.fill()
            
        # Draw background.
        draw_pixbuf(
            cr, 
            self.background_pixbuf.scale_simple(
                self.resize_width,
                self.resize_height,
                gtk.gdk.INTERP_BILINEAR),
            x + self.padding_x + self.resize_x,
            y + self.padding_y + self.resize_y)
        
        # Draw dominant shadow color.
        if self.button_release_flag:
            offset_x = x + self.padding_x
            offset_y = y + self.padding_y
            background_area_width = self.resize_width + self.resize_x
            background_area_height = self.resize_height + self.resize_y
            draw_hlinear(
                cr, 
                offset_x + background_area_width - self.shadow_size,
                offset_y + self.resize_y,
                self.shadow_size,
                background_area_height - self.resize_y,
                [(0, (self.dominant_color, 0)),
                 (1, (self.dominant_color, 1))])
            
            draw_vlinear(
                cr, 
                offset_x + self.resize_x,
                offset_y + background_area_height - self.shadow_size,
                background_area_width - self.resize_x,
                self.shadow_size,
                [(0, (self.dominant_color, 0)),
                 (1, (self.dominant_color, 1))]
                )
            
        # Draw window shadow.
        if enable_shadow(self):
            draw_window_shadow(
                cr, 
                x + self.padding_x - self.shadow_padding,
                y + self.padding_y - self.shadow_padding,
                self.preview_window_width + self.shadow_padding * 2,
                self.preview_window_height + self.shadow_padding * 2,
                self.shadow_radius, 
                self.shadow_padding)
        
        # Draw window frame.
        draw_window_frame(
            cr, 
            x + self.padding_x,
            y + self.padding_y,
            self.preview_window_width,
            self.preview_window_height)    

        if self.in_resize_area_flag:
            resize_x = x + self.padding_x + self.resize_x
            resize_y = y + self.padding_y + self.resize_y
            
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
            cr.arc(           # top-left
                resize_x,
                resize_y,
                self.resize_pointer_size / 2,
                0,
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # top-center
                resize_x + self.resize_width / 2,
                resize_y,
                self.resize_pointer_size / 2,
                0,
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # top-right
                resize_x + self.resize_width,
                resize_y,
                self.resize_pointer_size / 2,
                0,
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # bottom-left
                resize_x,
                resize_y + self.resize_height,
                self.resize_pointer_size / 2,
                0, 
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # bottom-center
                resize_x + self.resize_width / 2,
                resize_y + self.resize_height,
                self.resize_pointer_size / 2,
                0,
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # bottom-right
                resize_x + self.resize_width,
                resize_y + self.resize_height,
                self.resize_pointer_size / 2,
                0, 
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # left-center
                resize_x,
                resize_y + self.resize_height / 2,
                self.resize_pointer_size / 2,
                0,
                2 * math.pi)
            cr.fill()
            
            cr.arc(           # right-center
                resize_x + self.resize_width,
                resize_y + self.resize_height / 2,
                self.resize_pointer_size / 2,
                0, 
                2 * math.pi)
            cr.fill()
        
        # Draw preview frame.
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.rectangle(x, y + 1, w, h)
            cr.stroke()
            
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
    
    def leave_notify_skin_edit_area(self, widget, event):
        '''Callback for `leave-notify-event` signal.'''
        self.in_resize_area_flag = False        
        
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
    
    def skin_edit_area_drag_background(self, event):
        '''Drag background.'''
        new_resize_x = int(event.x) - self.drag_start_x + self.drag_background_x
        new_resize_y = int(event.y) - self.drag_start_y + self.drag_background_y
        self.resize_x = min(max(new_resize_x, self.min_resize_width - self.resize_width), 0)
        self.resize_y = min(max(new_resize_y, self.min_resize_height - self.resize_height), 0)
        
        self.queue_draw()
        
gobject.type_register(SkinEditArea)

class Skin(gobject.GObject):
    '''Skin.'''
	
    def __init__(self):
        '''Init skin.'''
        # Init.
        gobject.GObject.__init__(self)
        
    def load_skin(self, skin_dir):
        '''Load skin, return True if load finish, otherwise return False.'''
        try:
            # Load config file.
            self.config = Config(os.path.join(skin_dir, "config.ini"))
            self.config.load()
            
            # Get name config.
            self.ui_theme_name = self.config.get("name", "ui_theme_name")
            self.app_theme_name = self.config.get("name", "app_theme_name")
            
            # Get application config.
            self.app_id = self.config.get("application", "app_id")
            self.app_version = self.config.getfloat("application", "app_version")
            
            # Get background config.
            self.image = self.config.get("background", "image")
            self.x = self.config.getint("background", "x")
            self.y = self.config.getint("background", "y")
            self.scale = self.config.getfloat("background", "scale")
            self.dominant_color = self.config.get("background", "dominant_color")
            
            # Get editable config.
            self.editable = self.config.getboolean("editable", "editable")
            
            return True
        except Exception, e:
            print "load_skin: %s" % (e)
            return False
    
    def save_skin(self):
        '''Save skin.'''
        pass
    
    def apply_skin(self):
        '''Apply skin.'''
        pass
    
    def import_skin(self):
        '''Import skin.'''
        pass
        
    def export_skin(self):
        '''Export skin.'''
        pass
    
    def build_skin_package(self):
        '''Build skin package.'''
        pass
    
    def extract_skin_package(self):
        '''Extract skin package.'''
        pass
    
gobject.type_register(Skin)

if __name__ == '__main__':
    skin_window = SkinWindow()
    
    skin_window.show_all()
    
    gtk.main()
    
