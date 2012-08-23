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
from draw import draw_vlinear
from theme import ui_theme
from utils import (cairo_state, get_window_shadow_size, get_event_coords, 
                   is_left_button, is_double_click, is_single_click)
from skin_config import skin_config
from scrolled_window import ScrolledWindow
import copy

class TreeView(gtk.VBox):
    '''
    TreeView widget.
    '''
	
    def __init__(self,
                 items=[],
                 sort_methods=[],
                 drag_data=None,
                 enable_hover=True,
                 enable_highlight=True,
                 enable_multiple_select=True,
                 enable_drag_drop=True,
                 drag_icon_pixbuf=None,
                 start_drag_offset=50,
                 right_space=0,
                 top_bottom_space=3
                 ):
        '''
        Initialize TreeView class.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.visible_items = []
        self.sort_methods = sort_methods
        self.drag_data = drag_data
        self.enable_hover = enable_hover
        self.enable_highlight = enable_highlight
        self.enable_multiple_select = enable_multiple_select
        self.enable_drag_drop = enable_drag_drop
        self.drag_icon_pixbuf = drag_icon_pixbuf
        self.start_drag_offset = start_drag_offset
        self.start_drag = False
        self.start_select_row = None
        self.select_rows = []
        self.press_item = None
        self.title_offset_y = 0
        self.left_button_press = False
        self.press_ctrl = False
        self.press_shift = False
        self.single_click_row = None
        self.double_click_row = None
        
        # Init redraw.
        self.redraw_request_list = []
        self.redraw_delay = 100 # update redraw item delay, milliseconds
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)
        
        # Init widgets.
        self.draw_area = gtk.DrawingArea()
        self.draw_area.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.draw_area.set_can_focus(True)
        self.draw_align = gtk.Alignment()
        self.draw_align.set(0.5, 0.5, 1, 1)
        
        self.scrolled_window = ScrolledWindow(right_space, top_bottom_space)
        
        # Connect widgets.
        self.draw_align.add(self.draw_area)
        self.scrolled_window.add_child(self.draw_align)
        
        self.pack_start(self.scrolled_window, True, True)
        
        
        # Handle signals.
        self.draw_area.connect("expose-event", lambda w, e: self.expose_tree_view(w))
        self.draw_area.connect("button-press-event", self.button_press_tree_view)
        self.draw_area.connect("button-release-event", self.button_release_tree_view)
        
        # Add items.
        self.add_items(items)
        
    def update_item_index(self):
        '''
        Update index of items.
        '''
        for (index, item) in enumerate(self.visible_items):
            item.row_index = index
            
    def redraw_request(self, item):
        if not item in self.redraw_request_list:
            self.redraw_request_list.append(item)
    
    def update_redraw_request_list(self):
        if len(self.redraw_request_list) > 0:
            self.scrolled_window.queue_draw()
        
        # Clear redraw request list.
        self.redraw_request_list = []
        
        return True
        
    def add_items(self, items, insert_pos=None):
        '''
        Add items.
        '''
        if insert_pos == None:
            self.visible_items += items
        else:
            self.visible_items = self.visible_items[0:insert_pos] + items + self.visible_items[insert_pos::]
        
        # Update redraw callback.
        # Callback is better way to avoid perfermance problem than gobject signal.
        for item in items:
            item.redraw_request_callback = self.redraw_request
            item.add_items_callback = self.add_items
            item.delete_items_callback = self.delete_items
        
        self.update_item_index()    
            
        self.update_vadjustment()
        
    def delete_items(self, items):
        for item in items:
            if item in self.visible_items:
                self.visible_items.remove(item)
                
            if item.row_index in self.select_rows:
                item.is_select = False
                self.select_rows.remove(item.row_index)
            
        self.update_item_index()    
        
        self.update_vadjustment()
        
    def update_vadjustment(self):
        vadjust_height = sum(map(lambda i: i.get_height(), self.visible_items))
        self.draw_area.set_size_request(-1, vadjust_height)
        vadjust = self.scrolled_window.get_vadjustment()
        vadjust.set_upper(vadjust_height)
        
    def expose_tree_view(self, widget):
        '''
        Internal callback to handle `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw background.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
        with cairo_state(cr):
            cr.translate(-self.scrolled_window.allocation.x, -self.scrolled_window.allocation.y)
            cr.rectangle(offset_x, offset_y, 
                         self.scrolled_window.allocation.x + self.scrolled_window.allocation.width, 
                         self.scrolled_window.allocation.y + self.scrolled_window.allocation.height)
            cr.clip()
            
            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            skin_config.render_background(cr, widget, offset_x + shadow_x, offset_y + shadow_y)
            
        # Draw mask.
        self.draw_mask(cr, offset_x, offset_y, viewport.allocation.width, viewport.allocation.height)
        
        # Draw items.
        (start_row, end_row, item_height_count) = self.get_expose_bound()
        for item in self.visible_items[start_row:end_row]:
            render_x = rect.x
            render_y = rect.y + item_height_count
            render_width = rect.width
            render_height = item.get_height()
            
            with cairo_state(cr):
                cr.rectangle(render_x, render_y, render_width, render_height)
                cr.clip()

                item.get_column_renders()[0](cr, gtk.gdk.Rectangle(render_x, render_y, render_width, render_height))
                
            item_height_count += item.get_height()    
        
        return False
    
    def get_expose_bound(self):
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
        page_size = self.scrolled_window.get_vadjustment().get_page_size()
        
        start_row = None
        end_row = None
        start_y = None
        item_height_count = 0
        item_index_count = 0
        for item in self.visible_items:
            if start_row == None and start_y == None:
                if item_height_count <= offset_y <= item_height_count + item.get_height():
                    start_row = item_index_count
                    start_y = item_height_count
            elif end_row == None:
                if item_height_count <= offset_y + page_size <= item_height_count + item.get_height():
                    end_row = item_index_count + 1 # add 1 for python list split operation
            else:
                break
            
            item_index_count += 1
            item_height_count += item.get_height()
            
        assert(start_row != None and start_y != None)    
        
        # Items' height must smaller than page size if end_row is None after scan all items.
        # Then we need adjust end_row with last index of visible list.
        if end_row == None:
            end_row = len(self.visible_items)
        
        return (start_row, end_row, start_y)    
    
    def button_press_tree_view(self, widget, event):
        # if event.window != self.scrolled_window.vwindow and event.window != self.scrolled_window.hwindow:
        self.scrolled_window.grab_focus()
        
        if is_left_button(event):
            self.left_button_press = True
            
            self.click_item(event)
            
    def click_item(self, event):
        click_row = self.get_event_row(event)
        
        if self.left_button_press:
            if click_row == None:
                for row in self.select_rows:
                    self.visible_items[row].unselect()
                
                self.start_select_row = None
                self.select_rows = []
            else:
                if self.press_shift:
                    pass
                elif self.press_ctrl:
                    pass
                else:
                    if self.enable_drag_drop and click_row in self.select_rows:
                        pass
                    else:
                        for row in self.select_rows:
                            self.visible_items[row].unselect()
                    
                        self.start_drag = False
                        
                        self.start_select_row = click_row
                        self.select_rows = [click_row]
                        self.visible_items[click_row].select()
                        
            if is_double_click(event):
                self.double_click_row = copy.deepcopy(click_row)
            elif is_single_click(event):
                self.single_click_row = copy.deepcopy(click_row)                
                
    def button_release_tree_view(self, widget, event):
        if is_left_button(event):
            self.left_button_press = False
            self.release_item(event)
            
    def release_item(self, event):
        if is_left_button(event):
            release_row = self.get_event_row(event)
            
            if self.double_click_row == release_row:
                self.visible_items[release_row].double_click()
            elif self.single_click_row == release_row:
                self.visible_items[release_row].single_click()

            self.double_click_row = None    
            self.single_click_row = None    
            self.start_drag = False
                        
    def get_event_row(self, event, offset_index=0):
        '''
        Get row at event.

        @param event: gtk.gdk.Event instance.
        @param offset_index: Offset index base on event row.
        @return: Return row at event coordinate, return None if haven't any row match event coordiante.
        '''
        (event_x, event_y) = get_event_coords(event)
        
        item_height_count = 0
        item_index_count = 0
        for item in self.visible_items:
            if item_height_count <= event_y <= item_height_count + item.get_height():
                return item_index_count
            
            item_height_count += item.get_height()
            item_index_count += 1
            
        return None    

    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linear_background").get_color_info()
                     )
        
    def get_offset_coordinate(self, widget):
        '''
        Get viewport offset coordinate and viewport.

        @param widget: ListView widget.
        @return: Return viewport offset and viewport: (offset_x, offset_y, viewport).
        '''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = self.scrolled_window.get_child()
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)    

        else:
            return (0, 0, viewport)
        
gobject.type_register(TreeView)

class TreeItem(gobject.GObject):
    '''
    Tree item template use for L{ I{TreeView} <TreeView>}.
    '''
	
    def __init__(self):
        '''
        Initialize TreeItem class.
        '''
        gobject.GObject.__init__(self)
        self.parent_item = None
        self.chlid_items = None
        self.row_index = None
        self.column_index = None
        self.redraw_request_callback = None
        self.add_items_callback = None
        self.delete_items_callback = None
        self.is_select = False
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        pass
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        pass
        
    def unselect(self):
        pass
    
    def select(self):
        pass
    
    def single_click(self):
        pass        

    def double_click(self):
        pass        
    
gobject.type_register(TreeItem)
