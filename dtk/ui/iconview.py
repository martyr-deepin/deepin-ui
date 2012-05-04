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
from constant import BACKGROUND_IMAGE
from theme import ui_theme
from utils import get_match_parent, cairo_state, get_event_coords, is_in_rect, is_left_button, is_double_click, is_single_click
from draw import draw_pixbuf
from keymap import get_keyevent_name

class IconView(gtk.DrawingArea):
    '''Icon view.'''
	
    __gsignals__ = {
        "lost-focus-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "motion-notify-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
    }

    def __init__(self, 
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE)):
        '''Init icon view.'''
        # Init.
        gtk.DrawingArea.__init__(self)
        self.background_pixbuf = background_pixbuf
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.items = []
        self.focus_item = None
        self.double_click_item = None
        self.single_click_item = None
        
        # Signal.
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        self.connect("expose-event", self.expose_icon_view)    
        self.connect("motion-notify-event", self.motion_icon_view)
        self.connect("button-press-event", self.button_press_icon_view)
        self.connect("button-release-event", self.button_release_icon_view)
        self.connect("leave-notify-event", self.leave_icon_view)
        self.connect("key-press-event", self.key_press_icon_view)
        
        # Redraw.
        self.redraw_request_list = []
        self.redraw_delay = 100 # 100 milliseconds should be enough for redraw
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)
        
        self.keymap = {
            "Home" : self.select_first_item,
            "End" : self.select_last_item,
            # "Page_Up" : self.scroll_page_up,
            # "Page_Down" : self.scroll_page_down,
            "Return" : self.double_click_item,
            # "Up" : self.select_up_item,
            # "Down" : self.select_down_item,
            # "Left" : self.select_left_item,
            # "Right" : self.select_right_item,
            }
        
    def select_first_item(self):
        '''Select first item.'''
        if len(self.items) > 0:
            self.clear_focus_item()        
            self.focus_item = self.items[0]
            
            self.emit("motion-notify-item", self.focus_item, 0, 0)
            
            # Scroll to top.
            vadjust = get_match_parent(self, "ScrolledWindow").get_vadjustment()
            vadjust.set_value(vadjust.get_lower())
            
    def select_last_item(self):
        '''Select last item.'''
        if len(self.items) > 0:
            self.clear_focus_item()        
            self.focus_item = self.items[-1]
            
            self.emit("motion-notify-item", self.focus_item, 0, 0)
        
            # Scroll to bottom.
            vadjust = get_match_parent(self, "ScrolledWindow").get_vadjustment()
            vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
            
    def double_click_item(self):
        '''Double click item.'''
        if self.focus_item:
            self.emit("double-click-item", self.focus_item, 0, 0)
            
    def add_items(self, items, insert_pos=None):
        '''Add items.'''
        if insert_pos == None:
            self.items += items
        else:
            self.items = self.items[0:insert_pos] + items + self.items[insert_pos::]
            
        for item in items:
            item.connect("redraw_request", self.redraw_item)
            
        self.queue_draw()    
        
    def delete_items(self, items):
        '''Delete item.'''
        match_item = False
        for item in items:
            if item in self.items:
                self.items.remove(item)
                match_item = True
                
        if match_item:        
            self.queue_draw()
            
    def clear(self):
        '''Clear items'''
        self.items = []            
        self.queue_draw()
            
    def expose_icon_view(self, widget, event):
        '''Expose list view.'''
        # Update vadjustment.
        self.update_vadjustment()    
        
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
            
        # Draw background.
        with cairo_state(cr):
            cr.translate(-viewport.allocation.x, -viewport.allocation.y)
            cr.rectangle(offset_x, offset_y, 
                         viewport.allocation.x + viewport.allocation.width, 
                         viewport.allocation.y + viewport.allocation.height)
            cr.clip()
            
            draw_pixbuf(cr, self.background_pixbuf.get_pixbuf(), offset_x, offset_y)
            
        # Draw item.
        if len(self.items) > 0:
            with cairo_state(cr):
                # Don't draw any item out of viewport area.
                cr.rectangle(offset_x, offset_y,
                             viewport.allocation.width, 
                             viewport.allocation.height)        
                cr.clip()
                
                # Draw item.
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, "ScrolledWindow")
                columns = int(scrolled_window.allocation.width / item_width)
                    
                # Get viewport index.
                start_y = offset_y
                start_row = max(int(start_y / item_height), 0)
                start_index = start_row * columns
                
                end_y = offset_y + viewport.allocation.height
                if end_y % item_height == 0:
                    end_row = end_y / item_height - 1
                else:
                    end_row = end_y / item_height
                end_index = min((end_row + 1) * columns, len(self.items))
                
                for (index, item) in enumerate(self.items[start_index:end_index]):
                    row = int((start_index + index) / columns)
                    column = (start_index + index) % columns
                    render_x = rect.x + column * item_width
                    render_y = rect.y + row * item_height
                    
                    with cairo_state(cr):
                        # Don't allow draw out of item area.
                        cr.rectangle(render_x, render_y, item_width, item_height)
                        cr.clip()
                        
                        item.render(cr, gtk.gdk.Rectangle(render_x, render_y, item_width, item_height))
                        
    def clear_focus_item(self):
        '''Clear focus item status.'''
        if self.focus_item:
            self.emit("lost-focus-item", self.focus_item)
            self.focus_item = None
                        
    def motion_icon_view(self, widget, event):
        '''Motion list view.'''
        if len(self.items) > 0:
            index_info = self.icon_view_get_event_index(event)
            if index_info == None:
                self.clear_focus_item()
            else:
                (row_index, column_index, item_index, offset_x, offset_y) = index_info
                self.clear_focus_item()
                self.focus_item = self.items[item_index]
                
                self.emit("motion-notify-item", self.focus_item, offset_x, offset_y)
                    
    def icon_view_get_event_index(self, event):
        '''Get index at event.'''
        if len(self.items) > 0:
            (event_x, event_y) = get_event_coords(event)
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            scrolled_window = get_match_parent(self, "ScrolledWindow")
            columns = int(scrolled_window.allocation.width / item_width)
            if len(self.items) % columns == 0:
                rows = int(len(self.items) / columns)
            else:
                rows = int(len(self.items) / columns) + 1
                
            if event_x > columns * item_width:
                return None
            elif event_y > rows * item_height:
                return None
            else:
            
                if event_x % item_width == 0:
                    column_index = max(event_x / item_width - 1, 0)
                else:
                    column_index = min(event_x / item_width, columns - 1)
                
                if event_y % item_height == 0:
                    row_index = max(event_y / item_height - 1, 0)
                else:
                    row_index = min(event_y / item_height, rows - 1)
                    
                item_index = row_index * columns + column_index
                if item_index > len(self.items) - 1:
                    return None
                else:
                    return (row_index, column_index, item_index,
                            event_x - column_index * item_width,
                            event_y - row_index * item_height)

    def button_press_icon_view(self, widget, event):
        '''Button press event handler.'''
        # Grab focus when button press, otherwise key-press signal can't response.
        self.grab_focus()
        
        if len(self.items) > 0 and is_left_button(event):
            index_info = self.icon_view_get_event_index(event)
            if is_double_click(event):
                if index_info:
                    self.double_click_item = index_info[2]
                else:
                    self.double_click_item = None
            elif is_single_click(event):
                if index_info:
                    self.single_click_item = index_info[2]
                else:
                    self.single_click_item = None

    def button_release_icon_view(self, widget, event):
        '''Button release event handler.'''
        if len(self.items) > 0 and is_left_button(event):
            index_info = self.icon_view_get_event_index(event)
            if index_info:
                (row_index, column_index, item_index, offset_x, offset_y) = index_info
                
                if self.double_click_item == item_index:
                    self.emit("double-click-item", self.items[self.double_click_item], offset_x, offset_y)
                elif self.single_click_item == item_index:
                    self.emit("single-click-item", self.items[self.single_click_item], offset_x, offset_y)
            
            self.double_click_item = None
            self.single_click_item = None
        
    def leave_icon_view(self, widget, event):
        '''leave-notify-event signal handler.'''
        # Hide hover row when cursor out of viewport area.
        vadjust = get_match_parent(self, "ScrolledWindow").get_vadjustment()
        hadjust = get_match_parent(self, "ScrolledWindow").get_hadjustment()
        if not is_in_rect((event.x, event.y), 
                          (hadjust.get_value(), vadjust.get_value(), hadjust.get_page_size(), vadjust.get_page_size())):
            self.clear_focus_item()
        
    def key_press_icon_view(self, widget, event):
        '''Callback to handle key-press signal.'''
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
        
        return True
            
    def key_release_icon_view(self, widget, event):
        '''Callback to handle key-release signal.'''
        pass
        
    def update_redraw_request_list(self):
        '''Update redraw request list.'''
        # Redraw when request list is not empty.
        if len(self.redraw_request_list) > 0:
            # Get offset.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
            
            # Get viewport index.
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            scrolled_window = get_match_parent(self, "ScrolledWindow")
            columns = int(scrolled_window.allocation.width / item_width)
                
            start_y = offset_y
            start_row = max(int(start_y / item_height), 0)
            start_index = start_row * columns
            
            end_y = offset_y + viewport.allocation.height
            if end_y % item_height == 0:
                end_row = end_y / item_height - 1
            else:
                end_row = end_y / item_height
            end_index = min((end_row + 1) * columns, len(self.items))
            
            # Redraw whole viewport area once found any request item in viewport.
            for item in self.redraw_request_list:
                if item in self.items[start_index:end_index]:
                    self.queue_draw()
                    break
        
        # Clear redraw request list.
        self.redraw_request_list = []

        return True
    
    def redraw_item(self, list_item):
        '''Redraw item.'''
        self.redraw_request_list.append(list_item)
        
    def get_offset_coordinate(self, widget):
        '''Get offset coordinate.'''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = get_match_parent(widget, "Viewport")
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)
        else:
            return (0, 0, viewport)
            
    def update_vadjustment(self):
        '''Update vertical adjustment.'''
        scrolled_window = get_match_parent(self, "ScrolledWindow")
        
        if len(self.items) > 0:
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            columns = int(scrolled_window.allocation.width / item_width)
            if len(self.items) % columns == 0:
                view_height = int(len(self.items) / columns) * item_height
            else:
                view_height = (int(len(self.items) / columns) + 1) * item_height
                
            self.set_size_request(columns * item_width, view_height)
            if scrolled_window != None:
                vadjust = scrolled_window.get_vadjustment()
                vadjust.set_upper(view_height)
        else:
            self.set_size_request(scrolled_window.allocation.width, 
                                  scrolled_window.allocation.height)
            vadjust = scrolled_window.get_vadjustment()
            vadjust.set_upper(scrolled_window.allocation.height)
            
gobject.type_register(IconView)

class IconItem(gobject.GObject):
    '''Icon item.'''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, pixbuf):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.pixbuf = pixbuf
        self.padding_x = 24
        self.padding_y = 24
        self.hover_flag = False
        
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.pixbuf.get_width() + self.padding_x * 2
        
    def get_height(self):
        '''Get height.'''
        return self.pixbuf.get_height() + self.padding_y * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Draw cover border.
        border_size = 4
        
        if self.hover_flag:
            cr.set_source_rgb(1, 0, 0)
        else:
            cr.set_source_rgb(1, 1, 1)
        cr.rectangle(
            rect.x + (rect.width - self.pixbuf.get_width()) / 2 - border_size,
            rect.y + (rect.height - self.pixbuf.get_height()) / 2 - border_size,
            self.pixbuf.get_width() + border_size * 2,
            self.pixbuf.get_height() + border_size * 2)
        cr.fill()
        
        # Draw cover.
        draw_pixbuf(
            cr, 
            self.pixbuf, 
            rect.x + self.padding_x,
            rect.y + self.padding_y)
        
    def icon_item_motion_notify(self, x, y):
        '''Handle `motion-notify-event` signal.'''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''Lost focus.'''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
gobject.type_register(IconItem)
