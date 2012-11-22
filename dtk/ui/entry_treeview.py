#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Long Changjin
# 
# Author:     Long Changjin <admin@longchangjin.cn>
# Maintainer: Long Changjin <admin@longchangjin.cn>
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

from dtk.ui.new_treeview import TreeView, TreeItem
from dtk.ui.draw import draw_text
from dtk.ui.utils import color_hex_to_cairo, is_left_button, is_right_button
from dtk.ui.new_entry import EntryBuffer, Entry
import gtk
import gobject

class EntryTreeView(TreeView):
    __gsignals__ = {
        "select"  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int)),
        "unselect": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "double-click" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int))}
    
    def __init__(self, 
            items=[],
            drag_data=None,
            enable_hover=False,
            enable_highlight=True,
            enable_multiple_select=False,
            enable_drag_drop=False,
            drag_icon_pixbuf=None,
            start_drag_offset=50,
            mask_bound_height=24,
            right_space=0,
            top_bottom_space=3):
        super(EntryTreeView, self).__init__(
            items, drag_data, enable_hover,
            enable_highlight, enable_multiple_select,
            enable_drag_drop, drag_icon_pixbuf,
            start_drag_offset, mask_bound_height,
            right_space, top_bottom_space)
    
    def release_item(self, event):
        if is_left_button(event):
            cell = self.get_cell_with_event(event)
            if cell is not None:
                (release_row, release_column, offset_x, offset_y) = cell
                
                if release_row is not None:
                    if self.double_click_row == release_row:
                        self.visible_items[release_row].double_click(release_column, offset_x, offset_y)
                        self.emit("double-click", self.visible_items[release_row], release_column)
                    elif self.single_click_row == release_row:
                        self.visible_items[release_row].single_click(release_column, offset_x, offset_y)
                
                if self.start_drag and self.is_in_visible_area(event):
                    self.drag_select_items_at_cursor()
                    
                self.double_click_row = None    
                self.single_click_row = None    
                self.start_drag = False
                
                # Disable select rows when press_in_select_rows valid after button release.
                if self.press_in_select_rows:
                    self.set_select_rows([self.press_in_select_rows])
                    self.start_select_row = self.press_in_select_rows
                    self.press_in_select_rows = None
                
                self.set_drag_row(None)
        
class EntryTreeItem(TreeItem):
    
    def __init__(self, title, content):
        TreeItem.__init__(self)
        self.title = title
        self.entry = None
        self.entry_buffer = EntryBuffer(content)
        self.entry_buffer.set_property('cursor-visible', False)
        self.entry_buffer.connect("changed", self.entry_buffer_changed)
        self.entry_buffer.connect("insert-pos-changed", self.entry_buffer_changed)
        self.entry_buffer.connect("selection-pos-changed", self.entry_buffer_changed)
        self.child_items = []
        self.height = 24
        self.ENTRY_COLUMN = 1
        self.is_double_click = False
    
    def entry_buffer_changed(self, bf):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def get_height(self):
        return self.height
    
    def get_column_widths(self):
        return [-1, 200]
    
    def get_column_renders(self):
        return [self.render_title, self.render_content]
    
    def render_title(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            cr.set_source_rgb(*color_hex_to_cairo(bg_color))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.paint()
        else:
            text_color = "#000000"
        draw_text(cr, self.title, rect.x, rect.y, rect.width, rect.height, text_color=text_color)
    
    def render_content(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            if not self.is_double_click:
                cr.set_source_rgb(*color_hex_to_cairo(bg_color))
                cr.rectangle(rect.x, rect.y, rect.width, rect.height)
                cr.paint()
        else:
            text_color = "#000000"
            self.entry_buffer.move_to_start()
        self.entry_buffer.set_text_color(text_color)
        height = self.entry_buffer.get_pixel_size()[1]
        offset = (self.height - height)/2
        if offset < 0 :
            offset = 0
        rect.y += offset
        if self.entry and self.entry.allocation.width == self.get_column_widths()[1]-4:
            self.entry.calculate()
            rect.x += 2
            rect.width -= 4
            self.entry_buffer.set_text_color("#000000")
            self.entry_buffer.render(cr, rect, self.entry.im, self.entry.offset_x)
        else:
            self.entry_buffer.render(cr, rect)
    
    def unselect(self):
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self, column, offset_x, offset_y):
        pass

    def unhover(self, column, offset_x, offset_y):
        pass

    def single_click(self, column, offset_x, offset_y):
        self.is_double_click = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def double_click(self, column, offset_x, offset_y):
        self.is_double_click = True

    def expand(self):
        if self.is_expand:
            return
        self.is_expand = True
        self.add_items_callback(self.child_items, self.row_index+1)
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def unexpand(self):
        self.is_expand = False
        self.delete_items_callback(self.child_items)

gobject.type_register(EntryTreeItem)

'''
Please play with the demo entry_treeview_demo.py
'''
