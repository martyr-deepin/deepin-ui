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

from cache_pixbuf import CachePixbuf
from constant import DEFAULT_FONT_SIZE, ALIGN_END, ALIGN_START
from contextlib import contextmanager
from draw import draw_pixbuf, draw_vlinear, draw_text
from keymap import get_keyevent_name, has_ctrl_mask, has_shift_mask
from skin_config import skin_config
from theme import ui_theme
from deepin_utils.file import get_parent_dir
import math
import cairo
import copy
import gobject
import gtk
import os
import pango
import subprocess
import tempfile
import sys
import traceback
from deepin_utils.core import last_index, map_value, mix_list_max, unzip, get_disperse_index
from deepin_utils.file import remove_file
from utils import (get_content_size,
                   set_cursor, get_match_parent,
                   remove_timeout_id,
                   cairo_state, get_event_coords, is_left_button,
                   is_right_button, is_double_click, is_single_click,
                   get_window_shadow_size)

class ListView(gtk.DrawingArea):
    '''
    Powerful listview widget.

    @undocumented: update_select_rows
    @undocumented: auto_scroll_list_view
    @undocumented: auto_scroll_list_view_down
    @undocumented: auto_scroll_list_view_up
    @undocumented: update_redraw_request_list
    @undocumented: set_adjust_cursor
    @undocumented: realize_list_view
    @undocumented: size_allocate_list_view
    @undocumented: expose_list_view
    @undocumented: motion_list_view
    @undocumented: hover_item
    @undocumented: button_press_list_view
    @undocumented: click_item
    @undocumented: button_release_list_view
    @undocumented: release_item
    @undocumented: drag_select_items_at_cursor
    @undocumented: leave_list_view
    @undocumented: key_press_list_view
    @undocumented: key_release_list_view
    @undocumented: draw_items
    @undocumented: draw_items_row
    @undocumented: keep_select_status
    @undocumented: emit_item_event
    '''

    SORT_DESCENDING = False
    SORT_ASCENDING = True
    SORT_PADDING_X = 5
    TITLE_PADDING = 5

    __gsignals__ = {
        "delete-select-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "button-press-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "motion-notify-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "right-press-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int, int, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    def __init__(self,
                 sorts=[],
                 drag_data=None, # (targets, actions, button_masks)
                 enable_multiple_select=True,
                 enable_drag_drop=True,
                 drag_icon_pixbuf=ui_theme.get_pixbuf("listview/drag_preview.png"),
                 drag_out_offset=50,
                 mask_bound_height=12,
                 hide_columns=[],
                 hide_column_resize=False,
                 ):
        '''
        Initialize ListView widget.

        @param sorts: Sort function for column of listview.
        @param drag_data: Drag data for drag data from listview, format: (targets, actions, button_masks)
        @param enable_multiple_select: Whether allow user select multiple item, default is True.
        @param enable_drag_drop: Whether allow user drag drop on listview, default is True.
        @param drag_icon_pixbuf: Drag icon.
        @param drag_out_offset: Out offset value to trigger drag action on listview, default is 50 pixel, if cursor not drag more than 50 pixel, listview won't think it is B{drag out action}.
        @param mask_bound_height: The height of mask bound.
        @param hide_columns: The columns need to hide, default is empty list.
        @param hide_column_resize: Whether resize with hide column, default is False.
        '''
        # Init.
        gtk.DrawingArea.__init__(self)
        self.sorts = sorts
        self.drag_data = drag_data
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.items = []
        self.cell_widths = []
        self.cell_min_widths = []
        self.cell_min_heights = []
        self.left_button_press = False
        self.hover_row = None
        self.titles = None
        self.title_sorts = None
        self.single_click_row = None
        self.double_click_row = None
        self.start_select_item = None
        self.enable_drag_drop = enable_drag_drop
        self.start_drag = False
        self.drag_item = None
        self.highlight_item = None
        self.before_drag_items = []
        self.after_drag_items = []
        self.title_offset_y = 0
        self.item_height = 0
        self.press_ctrl = False
        self.press_shift = False
        self.select_rows = []
        self.start_select_row = None
        self.press_in_select_rows = None
        self.expand_column = None
        self.drag_reference_row = None
        self.drag_preview_pixbuf = None
        self.drag_line_pixbuf = CachePixbuf()
        self.enable_multiple_select = enable_multiple_select
        self.drag_icon_pixbuf = drag_icon_pixbuf
        self.drag_out_offset = drag_out_offset
        self.mask_bound_height = mask_bound_height
        self.auto_scroll_id = None
        self.auto_scroll_delay = 70 # milliseconds
        self.hide_columns = hide_columns
        self.hide_column_resize = hide_column_resize
        if len(self.hide_columns):
            self.hide_column_flag = True
        else:
            self.hide_column_flag = False

        # Signal.
        self.connect("realize", self.realize_list_view)
        self.connect("size-allocate", self.size_allocate_list_view)
        self.connect("expose-event", self.expose_list_view)
        self.connect("motion-notify-event", self.motion_list_view)
        self.connect("button-press-event", self.button_press_list_view)
        self.connect("button-release-event", self.button_release_list_view)
        self.connect("leave-notify-event", self.leave_list_view)
        self.connect("key-press-event", self.key_press_list_view)
        self.connect("key-release-event", self.key_release_list_view)

        # Unset drag source if drag data is not None.
        if self.drag_data:
            # We will manually start drags, details look function `hover-item`.
            self.drag_source_unset()

        # Redraw.
        self.redraw_request_list = []
        self.redraw_delay = 100 # 100 milliseconds should be enough for redraw
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)

        # Add key map.
        self.keymap = {
            "Home" : self.select_first_item,
            "End" : self.select_last_item,
            "Page_Up" : self.scroll_page_up,
            "Page_Down" : self.scroll_page_down,
            "Return" : self.double_click_item,
            "Up" : self.select_prev_item,
            "Down" : self.select_next_item,
            "Delete" : self.delete_select_items,
            "Shift + Up" : self.select_to_prev_item,
            "Shift + Down" : self.select_to_next_item,
            "Shift + Home" : self.select_to_first_item,
            "Shift + End" : self.select_to_last_item,
            "Ctrl + a" : self.select_all_items,
            }

    def hide_column(self, hide_columns=[]):
        '''
        Hide column.

        @param hide_columns: The columns need to hide, default is empty list.
        '''
        self.hide_columns = hide_columns
        if len(self.hide_columns):
            self.hide_column_flag = True
        else:
            self.hide_column_flag = False

    def set_hide_column_flag(self, hide_column_flag):
        '''
        Set hide column flag.

        @param hide_column_flag: The flag to control hide column.
        '''
        self.hide_column_flag = hide_column_flag

    def set_hide_column_resize(self, hide_column_resize):
        '''
        Set hide column resize.

        @param hide_column_resize: The flag to control hide column resize.
        '''
        self.hide_column_resize = hide_column_resize

    def set_expand_column(self, column):
        '''
        Set expand column.

        @param column: Column index to expand space.
        '''
        self.expand_column = column

    def update_redraw_request_list(self):
        '''
        Internal function to update redraw request list.
        '''
        # Redraw when request list is not empty.
        if len(self.redraw_request_list) > 0:
            # Get offset.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)

            # Get viewport index.
            start_y = offset_y - self.title_offset_y
            end_y = offset_y + viewport.allocation.height - self.title_offset_y
            start_index = max(start_y / self.item_height, 0)
            if (end_y - end_y / self.item_height * self.item_height) == 0:
                end_index = min(end_y / self.item_height + 1, len(self.items))
            else:
                end_index = min(end_y / self.item_height + 2, len(self.items))

            # Redraw whole viewport area once found any request item in viewport.
            viewport_range = range(start_index, end_index)
            for item in self.redraw_request_list:
                if item.get_index() in viewport_range:
                    self.queue_draw()
                    break

        # Clear redraw request list.
        self.redraw_request_list = []

        return True

    def add_titles(self, titles, title_height=24):
        '''
        Add titles.

        @param titles: A list of title.
        @param title_height: Height of title.
        '''
        self.titles = titles
        self.title_select_column = None
        self.title_adjust_column = None
        self.title_separator_width = 2
        self.title_clicks = map_value(self.titles, lambda _: False)
        self.title_sort_column = None
        self.title_sorts = map_value(self.titles, lambda _: self.SORT_DESCENDING)
        self.set_title_height(title_height)

        (title_widths, title_heights) = self.get_title_sizes()
        self.cell_widths = mix_list_max(self.cell_widths, title_widths)
        self.cell_min_widths = mix_list_max(self.cell_min_widths, title_widths)
        self.cell_min_heights = mix_list_max(self.cell_min_heights, title_heights)

        self.title_cache_pixbufs = []
        for title in self.titles:
            self.title_cache_pixbufs.append(CachePixbuf())

    def get_title_sizes(self):
        '''
        Get title sizes.

        @return: Return title size, as format (title_width, title_height).
        '''
        widths = []
        heights = []
        if self.titles != None:
            for title in self.titles:
                (title_width, title_height) = get_content_size(title, DEFAULT_FONT_SIZE)
                widths.append(title_width + self.TITLE_PADDING * 2)
                heights.append(title_height)

        return (widths, heights)

    def add_items(self, items, insert_pos=None, sort_list=False):
        '''
        Add items in listview.

        @param items: A list of item.
        @param insert_pos: The position to insert, default is None will insert new item at end of list.
        @param sort_list: Whether sort list after insert, default is False.
        '''
        # Add new items.
        with self.keep_select_status():
            if insert_pos == None:
                self.items += items
            else:
                self.items = self.items[0:insert_pos] + items + self.items[insert_pos::]

        # Re-calculate.
        (title_widths, title_heights) = self.get_title_sizes()
        sort_pixbuf = ui_theme.get_pixbuf("listview/sort_descending.png").get_pixbuf()
        sort_icon_width = sort_pixbuf.get_width() + self.SORT_PADDING_X * 2
        sort_icon_height = sort_pixbuf.get_height()

        cell_min_sizes = []
        for item in items:
            # Binding redraw request signal.
            item.connect("redraw_request", self.redraw_item)

            sizes = item.get_column_sizes()
            if cell_min_sizes == []:
                cell_min_sizes = sizes
            else:
                for (index, (width, height)) in enumerate(sizes):
                    if self.titles == None:
                        max_width = max([cell_min_sizes[index][0], width])
                        max_height = max([cell_min_sizes[index][1], sort_icon_height, height])
                    else:
                        max_width = max([cell_min_sizes[index][0], title_widths[index] + sort_icon_width * 2, width])
                        max_height = max([cell_min_sizes[index][1], title_heights[index], sort_icon_height, height])

                    cell_min_sizes[index] = (max_width, max_height)

        # Get value.
        (cell_min_widths, cell_min_heights) = unzip(cell_min_sizes)
        self.cell_min_widths = mix_list_max(self.cell_min_widths, cell_min_widths)
        self.cell_min_heights = mix_list_max(self.cell_min_heights, cell_min_heights)
        self.cell_widths = mix_list_max(self.cell_widths, copy.deepcopy(cell_min_widths))

        self.item_height = max(self.item_height, max(copy.deepcopy(cell_min_heights)))

        # Sort list if sort_list enable.
        if sort_list and self.sorts != [] and self.title_sort_column != None:
            if self.title_sorts == None:
                reverse_order = False
            else:
                reverse_order = self.title_sorts[0]

            with self.keep_select_status():
                self.items = sorted(self.items,
                                    key=self.sorts[self.title_sort_column][0],
                                    cmp=self.sorts[self.title_sort_column][1],
                                    reverse=reverse_order)

        # Update vertical adjustment.
        self.update_vadjustment()

        # Update item index.
        self.update_item_index()

    def sort_items(self, compare_method, sort_reverse=False):
        '''
        Sort items with given method.

        @param compare_method: Compare method to sort.
        @param sort_reverse: Whether sort reverse, default is False.
        '''
        # Sort items.
        with self.keep_select_status():
            self.items = sorted(self.items,
                                cmp=compare_method,
                                reverse=sort_reverse)

        # Update item index.
        self.update_item_index()

        # Redraw.
        self.queue_draw()

    def redraw_item(self, list_item):
        '''
        Redraw item.

        @param list_item: List item need to redraw.
        '''
        self.redraw_request_list.append(list_item)

    def update_item_index(self):
        '''
        Update index of items.
        '''
        for (index, item) in enumerate(self.items):
            item.set_index(index)

    def reorder_item(self, item, index):
        '''
        Reorder item with given index.

        @param item: Item need reorder.
        @param index: Reorder index.

        If index < 0, move to begin position of list view, if index > max_index, move to end position of list view.
        '''
        if index < 0:
            index = 0
        else:
            index = len(self.items) - 1

        with self.keep_select_status():
            self.items.remove(item)
            self.items.insert(index, item)

        self.update_item_index()

        self.queue_draw()

    def set_title_height(self, title_height):
        '''
        Set title height.

        @param title_height: Title height.
        '''
        self.title_height = title_height
        if self.titles:
            self.title_offset_y = self.title_height
        else:
            self.title_offset_y = 0

    def get_column_sort_type(self, column):
        '''
        Get sort type with given column index.

        @param column: Column index.
        @return: Return sort type with given column index, return None if haven't found match column index.
        '''
        if 0 <= column <= last_index(self.title_sorts):
            return self.title_sorts[column]
        else:
            return None

    def set_column_sort_type(self, column, sort_type):
        '''
        Set sort type with given value.

        @param column: Column index.
        @param sort_type: Sort type.
        '''
        if 0 <= column <= last_index(self.title_sorts):
            self.title_sorts[column] = sort_type

    def get_cell_widths(self):
        '''
        Get cell width of columns.

        @return: Return the width of cells.
        '''
        return self.cell_widths

    def set_cell_width(self, column, width):
        '''
        Set cell width with given value.

        @param column: Column index.
        @param width: Column width.
        '''
        if column <= last_index(self.cell_min_widths) and width >= self.cell_min_widths[column]:
            self.cell_widths[column] = width

    def set_adjust_cursor(self):
        '''
        Internal function to set cursor type when adjust size.
        '''
        set_cursor(self, gtk.gdk.SB_H_DOUBLE_ARROW)
        self.adjust_cursor = True

    def reset_cursor(self):
        '''
        Reset cursor type.
        '''
        set_cursor(self, None)
        self.adjust_cursor = False

    def get_offset_coordinate(self, widget):
        '''
        Get viewport offset coordinate and viewport.

        @param widget: ListView widget.
        @return: Return viewport offset and viewport: (offset_x, offset_y, viewport).
        '''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = get_match_parent(widget, ["Viewport"])
        if viewport:
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)

        else:
            return (0, 0, viewport)

    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linear_background").get_color_info()
                     )

    def draw_item_hover(self, cr, x, y, w, h):
        '''
        Draw item hover interface.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h, ui_theme.get_shadow_color("listview_hover").get_color_info())

    def draw_item_select(self, cr, x, y, w, h):
        '''
        Draw item select interface.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h, ui_theme.get_shadow_color("listview_select").get_color_info())

    def draw_item_highlight(self, cr, x, y, w, h):
        '''
        Draw item highlight interface.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h, ui_theme.get_shadow_color("listview_highlight").get_color_info())

    def __update_expand_cell_width(self, rect_width):
        expand_cell_width = rect_width - (sum(self.cell_widths) - self.cell_widths[self.expand_column])
        return expand_cell_width

    def realize_list_view(self, widget):
        '''
        Internal function for realize listview.

        @param widget: ListView widget.
        '''
        self.grab_focus()       # focus key after realize

        rect = widget.allocation
        '''
        TODO: expand_cell_width is rect.width - other no-expand columns width
        '''
        if 0 <= self.expand_column < len(self.cell_widths):
            self.set_cell_width(self.expand_column, self.__update_expand_cell_width(rect.width))

    def size_allocate_list_view(self, widget, allocation):
        '''
        Internal callback for `size_allocated` signal.

        @param widget: ListView widget.
        @param allocation: ListView allocation.
        '''
        rect = widget.allocation
        if 0 <= self.expand_column < len(self.cell_widths):
            self.set_cell_width(self.expand_column, self.__update_expand_cell_width(rect.width))

    def expose_list_view(self, widget, event):
        '''
        Internal callback for `expose-event` signal.

        @param widget: ListView widget.
        @param event: Expose event.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        '''
        TODO: when rect.width changed, cell_width need to consider about rect.width
        '''
        cell_widths = self.get_cell_widths()
        if self.hide_column_resize:
            self.set_size_request(rect.width, rect.height)

        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)

        # Draw background.
        with cairo_state(cr):
            scrolled_window = get_match_parent(self, ["ScrolledWindow"])
            cr.translate(-scrolled_window.allocation.x, -scrolled_window.allocation.y)
            cr.rectangle(offset_x, offset_y,
                         scrolled_window.allocation.x + scrolled_window.allocation.width,
                         scrolled_window.allocation.y + scrolled_window.allocation.height)
            cr.clip()

            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            skin_config.render_background(cr, self, offset_x + shadow_x, offset_y + shadow_y)

        # Draw mask.
        self.draw_mask(cr, offset_x, offset_y, viewport.allocation.width, viewport.allocation.height)

        # Draw items.
        self.draw_items(cr, rect, offset_x, offset_y, viewport, cell_widths)

        # Draw titles.
        if self.titles:
            i = 0
            if cell_widths[0] > rect.width:
                cell_widths[0] = rect.width - sum(cell_widths[1:len(cell_widths)])
            for (column, width) in enumerate(cell_widths):
                if self.hide_column_flag and column == self.expand_column:
                    for hide_column in self.hide_columns:
                        width += cell_widths[hide_column]

                if self.hide_column_flag and column in self.hide_columns:
                    continue
                # Get offset x coordinate.
                cell_offset_x = sum(cell_widths[0:column])
                if self.hide_column_flag and self.hide_column_resize:
                    for hide_column in self.hide_columns:
                        cell_offset_x -= cell_widths[hide_column]

                # Calculate current cell width.
                if column == last_index(cell_widths):
                    if sum(cell_widths) < rect.width:
                        cell_width = rect.width - cell_offset_x
                    else:
                        cell_width = width
                else:
                    cell_width = width

                # Draw title column background.
                if self.title_select_column == column:
                    if self.left_button_press:
                        header_pixbuf = ui_theme.get_pixbuf("listview/header_press.png").get_pixbuf()
                    else:
                        header_pixbuf = ui_theme.get_pixbuf("listview/header_hover.png").get_pixbuf()
                else:
                    header_pixbuf = ui_theme.get_pixbuf("listview/header_normal.png").get_pixbuf()
                self.title_cache_pixbufs[column].scale(
                    header_pixbuf, cell_width, self.title_height)
                draw_pixbuf(cr,
                            self.title_cache_pixbufs[column].get_cache(),
                            cell_offset_x, offset_y)

                # Draw title split line.
                if cell_offset_x != 0:
                    draw_pixbuf(cr,
                                ui_theme.get_pixbuf("listview/split.png").get_pixbuf(),
                                cell_offset_x - 1, offset_y)

                # Draw title.
                draw_text(cr, self.titles[column],
                          cell_offset_x, offset_y, cell_widths[column], self.title_height,
                          DEFAULT_FONT_SIZE,
                          ui_theme.get_color("list_view_title").get_color(),
                          alignment=pango.ALIGN_CENTER)

                # Draw sort icon.
                if self.title_sort_column == column:
                    sort_type = self.get_column_sort_type(column)
                    if sort_type == self.SORT_DESCENDING:
                        sort_pixbuf = ui_theme.get_pixbuf("listview/sort_descending.png").get_pixbuf()
                    elif sort_type == self.SORT_ASCENDING:
                        sort_pixbuf = ui_theme.get_pixbuf("listview/sort_ascending.png").get_pixbuf()

                    draw_pixbuf(cr, sort_pixbuf,
                                cell_offset_x + cell_width - sort_pixbuf.get_width() - self.SORT_PADDING_X,
                                offset_y + (self.title_height - sort_pixbuf.get_height()) / 2)

                i += 1

        # Draw drag reference row.
        if self.drag_reference_row != None:
            drag_pixbuf = ui_theme.get_pixbuf("listview/drag_line.png").get_pixbuf()
            self.drag_line_pixbuf.scale(drag_pixbuf, rect.width, drag_pixbuf.get_height())
            if self.drag_reference_row == 0:
                drag_line_y = rect.y + self.title_offset_y
            elif self.drag_reference_row == len(self.items):
                drag_line_y = rect.y + (self.drag_reference_row) * self.item_height + self.title_offset_y - drag_pixbuf.get_height()
            else:
                drag_line_y = rect.y + self.drag_reference_row * self.item_height + self.title_offset_y

            draw_pixbuf(cr, self.drag_line_pixbuf.get_cache(), rect.x, drag_line_y)

        return False

    def draw_items(self, cr, rect, offset_x, offset_y, viewport, cell_widths):
        if len(self.items) > 0:
            # Init.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()

            # Init top surface.
            if vadjust.get_value() != vadjust.get_lower():
                top_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, rect.width, self.mask_bound_height)
                top_surface_cr = gtk.gdk.CairoContext(cairo.Context(top_surface))

                clip_y = vadjust.get_value() + self.mask_bound_height
            else:
                top_surface = top_surface_cr = None

                clip_y = vadjust.get_value()

            # Init bottom surface.
            if vadjust.get_value() + vadjust.get_page_size() != vadjust.get_upper():
                bottom_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, rect.width, self.mask_bound_height)
                bottom_surface_cr = gtk.gdk.CairoContext(cairo.Context(bottom_surface))

                clip_height = vadjust.get_page_size() - self.mask_bound_height - (clip_y - vadjust.get_value())
            else:
                bottom_surface = bottom_surface_cr = None

                clip_height = vadjust.get_page_size() - (clip_y - vadjust.get_value())

            with cairo_state(cr):
                if top_surface_cr:
                    top_surface_cr.rectangle(rect.x, 0, rect.width, self.mask_bound_height)
                    top_surface_cr.clip()

                    self.draw_items_row(top_surface_cr, offset_x, viewport,
                                        int(vadjust.get_value()))

                if bottom_surface_cr:
                    bottom_surface_cr.rectangle(rect.x, 0, rect.width, self.mask_bound_height)
                    bottom_surface_cr.clip()

                    self.draw_items_row(bottom_surface_cr, offset_x, viewport,
                                        int(vadjust.get_value()) + int(vadjust.get_page_size()) + self.mask_bound_height)

                # Don't draw any item under title area.
                cr.rectangle(offset_x,
                             offset_y + self.title_offset_y + clip_y - vadjust.get_value(),
                             viewport.allocation.width,
                             clip_height + 1 - self.title_offset_y
                             )
                cr.clip()

                self.draw_items_row(cr, offset_x, viewport)

            with cairo_state(cr):
                # Don't draw any item under title area.
                cr.rectangle(offset_x,
                             offset_y + self.title_offset_y + clip_y - vadjust.get_value(),
                             viewport.allocation.width,
                             clip_height + 1 - self.title_offset_y
                             )
                cr.clip()

                # Get viewport index.
                start_y = offset_y - self.title_offset_y
                end_y = offset_y + viewport.allocation.height - self.title_offset_y
                start_index = max(start_y / self.item_height, 0)
                if (end_y - end_y / self.item_height * self.item_height) == 0:
                    end_index = min(end_y / self.item_height + 1, len(self.items))
                else:
                    end_index = min(end_y / self.item_height + 2, len(self.items))

                filter_renders = []
                for (row, item) in enumerate(self.items[start_index:end_index]):
                    if self.hide_column_flag:
                        renders = map(lambda (index, render): render, filter(lambda (index, render): not index in self.hide_columns, enumerate(item.get_renders())))
                        filter_renders = filter(lambda (index, render): not index in self.hide_columns, enumerate(item.get_renders()))
                    else:
                        renders = item.get_renders()
                    render_y = rect.y + (row + start_index) * self.item_height + self.title_offset_y
                    render_height = self.item_height

                    for (column, render) in enumerate(renders):
                        index = column
                        if self.hide_column_flag:
                            index = filter_renders[column][0]
                        cell_width = cell_widths[index]
                        cell_x = sum(cell_widths[0:index])
                        if column != 0 and self.hide_column_flag and self.hide_column_resize:
                            for hide_column in self.hide_columns:
                                cell_x -= cell_widths[hide_column]
                        render_x = rect.x + cell_x
                        render_width = cell_width

                        # Draw on top surface.
                        if top_surface_cr:
                            if (not float(render_y) > vadjust.get_value() + float(self.mask_bound_height)) and (not float(render_y + render_height) < vadjust.get_value()):
                                top_surface_cr.rectangle(rect.x, 0, rect.width, self.mask_bound_height)
                                top_surface_cr.clip()

                                render(
                                    top_surface_cr,
                                    gtk.gdk.Rectangle(render_x,
                                                      render_y - int(vadjust.get_value()),
                                                      render_width,
                                                      render_height),
                                    (start_index + row) in self.select_rows,
                                    item == self.highlight_item)

                        # Draw on bottom surface.
                        if bottom_surface_cr:
                            if (not float(render_y) > vadjust.get_value() + vadjust.get_page_size()) and (not float(render_y + render_height) < vadjust.get_value() + vadjust.get_page_size() - float(self.mask_bound_height)):
                                bottom_surface_cr.rectangle(rect.x, 0, rect.width, self.mask_bound_height)
                                bottom_surface_cr.clip()

                                render(
                                    bottom_surface_cr,
                                    gtk.gdk.Rectangle(render_x,
                                                      render_y - int(vadjust.get_value()) - int(vadjust.get_page_size() - self.mask_bound_height),
                                                      render_width,
                                                      render_height),
                                    (start_index + row) in self.select_rows,
                                    item == self.highlight_item)

                        with cairo_state(cr):
                            cr.rectangle(render_x,
                                         render_y,
                                         render_width,
                                         render_height)
                            cr.clip()

                            # Render cell.
                            render(cr,
                                   gtk.gdk.Rectangle(render_x,
                                                     render_y,
                                                     render_width,
                                                     render_height),
                                   (start_index + row) in self.select_rows,
                                   item == self.highlight_item)

            # Draw alpha mask on top surface.
            if top_surface:
                i = 0
                while (i <= self.mask_bound_height):
                    with cairo_state(cr):
                        cr.rectangle(rect.x, vadjust.get_value() + self.title_offset_y + i, rect.width, 1)
                        cr.clip()
                        cr.set_source_surface(
                            top_surface,
                            0,
                            vadjust.get_value() + self.title_offset_y
                            )
                        cr.paint_with_alpha(math.sin(i * math.pi / 2 / self.mask_bound_height))

                    i += 1

            # Draw alpha mask on bottom surface.
            if bottom_surface:
                i = 0
                while (i <= self.mask_bound_height):
                    with cairo_state(cr):
                        cr.rectangle(rect.x, vadjust.get_value() + vadjust.get_page_size() - self.mask_bound_height + i, rect.width, 1)
                        cr.clip()
                        cr.set_source_surface(
                            bottom_surface,
                            0,
                            vadjust.get_value() + vadjust.get_page_size() - self.mask_bound_height
                            )
                        cr.paint_with_alpha(1.0 - (math.sin(i * math.pi / 2 / self.mask_bound_height)))

                    i += 1

    def draw_items_row(self, cr, offset_x, viewport, render_offset_y=0):
        # Draw hover row.
        highlight_row = None
        if self.highlight_item:
            highlight_row = self.highlight_item.get_index()

        if self.hover_row != None and not self.hover_row in self.select_rows and self.hover_row != highlight_row:
            self.draw_item_hover(
                cr,
                offset_x,
                self.title_offset_y + self.hover_row * self.item_height - render_offset_y,
                viewport.allocation.width,
                self.item_height)

        # Draw select rows.
        for select_row in self.select_rows:
            if select_row != highlight_row:
                self.draw_item_select(
                    cr,
                    offset_x,
                    self.title_offset_y + select_row * self.item_height - render_offset_y,
                    viewport.allocation.width,
                    self.item_height)

        # Draw highlight row.
        if self.highlight_item:
            self.draw_item_highlight(
                cr,
                offset_x,
                self.title_offset_y + self.highlight_item.get_index() * self.item_height - render_offset_y,
                viewport.allocation.width,
                self.item_height)

    def motion_list_view(self, widget, event):
        '''
        Internal callback for `motion-notify-event` signal.

        @param widget: ListView widget.
        @param event: Motion event.
        '''
        if self.titles:
            # Get offset.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)

            if self.title_adjust_column != None:
                # Set column width.
                cell_min_end_x = sum(self.cell_widths[0:self.title_adjust_column]) + self.cell_min_widths[self.title_adjust_column]
                # Adjust column width.
                (ex, ey) = get_event_coords(event)
                adjust_cell_width = ex - sum(self.cell_widths[0:self.title_adjust_column])
                if ex >= cell_min_end_x:
                    self.set_cell_width(self.title_adjust_column, adjust_cell_width)
            else:
                if offset_y <= event.y <= offset_y + self.title_height:
                    cell_widths = self.get_cell_widths()
                    for (column, _) in enumerate(cell_widths):
                        if column == last_index(cell_widths):
                            cell_start_x = widget.allocation.width
                            cell_end_x = widget.allocation.width
                        else:
                            cell_start_x = sum(cell_widths[0:column + 1]) - self.title_separator_width
                            cell_end_x = sum(cell_widths[0:column + 1]) + self.title_separator_width

                        if event.x < cell_start_x:
                            self.title_select_column = column
                            self.reset_cursor()
                            break
                        elif cell_start_x <= event.x <= cell_end_x:
                            self.title_select_column = None
                            self.set_adjust_cursor()
                            break
                elif len(self.items) > 0:
                    self.hover_item(event)
        elif len(self.items) > 0:
            self.hover_item(event)

        # Disable press_in_select_rows once move mouse.
        self.press_in_select_rows = None

        # Redraw after motion.
        self.queue_draw()

    def hover_item(self, event):
        '''
        Internal function to handle hover item.

        @param event: Motion notify event.
        '''
        if self.left_button_press:
            if self.start_drag:
                if self.enable_drag_drop:
                    # Set drag cursor.
                    if self.drag_preview_pixbuf == None:
                        temp_filepath = tempfile.mktemp()
                        subprocess.Popen(
                            ["python",
                             os.path.join(get_parent_dir(__file__), "listview_preview_pixbuf.py"),
                             str(len(self.select_rows)),
                             str([(0, ("#40408c", 1)),
                                  (1, ("#0093F9", 1))]),
                             "#FFFFFF",
                             temp_filepath]).wait()
                        drag_num_pixbuf = gtk.gdk.pixbuf_new_from_file(temp_filepath)
                        drag_icon_pixbuf = self.drag_icon_pixbuf.get_pixbuf()
                        drag_num_pixbuf.copy_area(
                            0, 0, drag_num_pixbuf.get_width(), drag_num_pixbuf.get_height(),
                            drag_icon_pixbuf,
                            (drag_icon_pixbuf.get_width() - drag_num_pixbuf.get_width()) / 2,
                            drag_icon_pixbuf.get_height() - drag_num_pixbuf.get_height())
                        self.drag_preview_pixbuf = drag_icon_pixbuf
                        remove_file(temp_filepath)

                    self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.display_get_default(),
                                                          self.drag_preview_pixbuf,
                                                          0, 0))

                    # Get hover row.
                    if self.is_in_visible_area(event):
                        # Scroll viewport when cursor almost reach bound of viewport.
                        self.auto_scroll_list_view(event)

                        # Get drag reference row.
                        self.drag_reference_row = self.get_event_row(event, 1)

                        self.queue_draw()
                    else:
                        # Begin drag is drag_data is not None.
                        if self.drag_data:
                            (targets, actions, button) = self.drag_data
                            self.drag_begin(targets, actions, button, event)

                        self.drag_reference_row = None

                        self.queue_draw()
            else:
                if self.enable_multiple_select and (not self.press_ctrl and not self.press_shift):
                    # Get hover row.
                    hover_row = self.get_event_row(event)

                    # Highlight drag area.
                    if hover_row != None and self.start_select_row != None:
                        # Update select area.
                        if hover_row > self.start_select_row:
                            self.select_rows = range(self.start_select_row, hover_row + 1)
                        elif hover_row < self.start_select_row:
                            self.select_rows = range(hover_row, self.start_select_row + 1)
                        else:
                            self.select_rows = [hover_row]

                        # Scroll viewport when cursor almost reach bound of viewport.
                        self.auto_scroll_list_view(event)

                        self.queue_draw()
        else:
            # Rest cursor and title select column.
            self.title_select_column = None
            self.reset_cursor()

            # Set hover row.
            self.hover_row = self.get_event_row(event)

            # Emit motion notify event to item.
            self.emit_item_event("motion-notify-item", event)

    def auto_scroll_list_view(self, event):
        '''
        Internal function to scroll list view automatically.
        '''
        # Remove auto scroll handler.
        remove_timeout_id(self.auto_scroll_id)

        vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
        if event.y > vadjust.get_value() + vadjust.get_page_size() - 2 * self.item_height:
            self.auto_scroll_id = gobject.timeout_add(self.auto_scroll_delay, lambda : self.auto_scroll_list_view_down(vadjust))
        elif event.y < vadjust.get_value() + 2 * self.item_height + self.title_offset_y:
            self.auto_scroll_id = gobject.timeout_add(self.auto_scroll_delay, lambda : self.auto_scroll_list_view_up(vadjust))

    def auto_scroll_list_view_down(self, vadjust):
        '''
        Internal function to scroll list view down automatically.
        '''
        vadjust.set_value(min(vadjust.get_value() + self.item_height,
                              vadjust.get_upper() - vadjust.get_page_size()))

        if self.start_drag:
            self.drag_reference_row = self.get_row_with_coordinate(self.get_pointer()[1], 1)
        else:
            self.update_select_rows(self.get_row_with_coordinate(self.get_pointer()[1]))

        return True

    def auto_scroll_list_view_up(self, vadjust):
        '''
        Internal function to scroll list view up automatically.
        '''
        vadjust.set_value(max(vadjust.get_value() - self.item_height,
                              vadjust.get_lower()))

        if self.start_drag:
            self.drag_reference_row = self.get_row_with_coordinate(self.get_pointer()[1], 1)
        else:
            self.update_select_rows(self.get_row_with_coordinate(self.get_pointer()[1]))

        return True

    def button_press_list_view(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.

        @param widget: ListView widget.
        @param event: Button press event.
        '''
        # Grab focus when button press, otherwise key-press signal can't response.
        self.grab_focus()

        if is_left_button(event):
            self.left_button_press = True

            if self.titles:
                # Get offset.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
                if offset_y <= event.y <= offset_y + self.title_height:
                    cell_widths = self.get_cell_widths()
                    for (column, _) in enumerate(cell_widths):
                        if column == last_index(cell_widths):
                            cell_end_x = widget.allocation.width
                        else:
                            cell_end_x = sum(cell_widths[0:column + 1]) - self.title_separator_width

                        if column == 0:
                            cell_start_x = 0
                        else:
                            cell_start_x = sum(cell_widths[0:column]) + self.title_separator_width

                        if cell_start_x < event.x < cell_end_x:
                            self.title_clicks[column] = True
                            break
                        elif cell_end_x <= event.x <= cell_end_x + self.title_separator_width * 2:
                            self.title_adjust_column = column
                            break
                elif len(self.items) > 0:
                    self.click_item(event)
            elif len(self.items) > 0:
                self.click_item(event)
        elif is_right_button(event):
            if len(self.items) > 0:
                self.click_item(event)

        self.queue_draw()

    def click_item(self, event):
        '''
        Internal function to handle click item.

        @param event: Button press event.
        '''
        click_row = self.get_event_row(event)

        if self.left_button_press:
            if click_row == None:
                self.start_select_row = None
                self.select_rows = []
            else:
                if self.press_shift:
                    if self.select_rows == [] or self.start_select_row == None:
                        self.start_select_row = click_row
                        self.select_rows = [click_row]
                    else:
                        if len(self.select_rows) == 1:
                            self.start_select_row = self.select_rows[0]

                        if click_row < self.start_select_row:
                            self.select_rows = range(click_row, self.start_select_row + 1)
                        elif click_row > self.start_select_row:
                            self.select_rows = range(self.start_select_row, click_row + 1)
                        else:
                            self.select_rows = [click_row]
                elif self.press_ctrl:
                    if click_row in self.select_rows:
                        self.select_rows.remove(click_row)
                    else:
                        self.start_select_row = click_row
                        self.select_rows.append(click_row)
                    self.select_rows = sorted(self.select_rows)
                else:
                    if self.enable_drag_drop and click_row in self.select_rows:
                        self.start_drag = True

                        if self.start_select_row:
                            self.start_select_item = self.items[self.start_select_row]

                        self.before_drag_items = []
                        self.after_drag_items = []

                        for row in self.select_rows:
                            if row == click_row:
                                self.drag_item = self.items[click_row]
                            elif row < click_row:
                                self.before_drag_items.append(self.items[row])
                            elif row > click_row:
                                self.after_drag_items.append(self.items[row])

                        # Record press_in_select_rows, disable select rows if mouse not move after release button.
                        self.press_in_select_rows = click_row
                    else:
                        self.start_drag = False

                        self.start_select_row = click_row
                        self.select_rows = [click_row]
                        self.emit_item_event("button-press-item", event)

            if is_double_click(event):
                self.double_click_row = copy.deepcopy(click_row)
            elif is_single_click(event):
                self.single_click_row = copy.deepcopy(click_row)
        else:
            right_press_row = self.get_event_row(event)
            if right_press_row == None:
                self.start_select_row = None
                self.select_rows = []

                self.queue_draw()
            elif not right_press_row in self.select_rows:
                self.start_select_row = right_press_row
                self.select_rows = [right_press_row]

                self.queue_draw()

            # Emit right-press-items signal.
            if self.start_select_row == None:
                current_item = None
            else:
                current_item = self.items[self.start_select_row]

            select_items = []
            for row in self.select_rows:
                select_items.append(self.items[row])

            (wx, wy) = self.window.get_root_origin()
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
            self.emit("right-press-items",
                      event.x_root,
                      event.y_root,
                      current_item,
                      select_items)

    def button_release_list_view(self, widget, event):
        '''
        Internal callback for `button-release-event` signal.

        @param widget: ListView widget.
        @param event: Button release event.
        '''
        if is_left_button(event):
            self.left_button_press = False
            if self.titles:
                # Get offset.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
                if offset_y <= event.y <= offset_y + self.title_height:
                    cell_widths = self.get_cell_widths()
                    for (column, _) in enumerate(cell_widths):
                        if column == last_index(cell_widths):
                            cell_end_x = widget.allocation.width
                        else:
                            cell_end_x = sum(cell_widths[0:column + 1]) - self.title_separator_width

                        if column == 0:
                            cell_start_x = 0
                        else:
                            cell_start_x = sum(cell_widths[0:column]) + self.title_separator_width

                        if cell_start_x < event.x < cell_end_x:
                            if self.title_clicks[column]:
                                self.title_sort_column = column
                                self.title_sorts[column] = not self.title_sorts[column]
                                self.title_clicks[column] = False

                                if len(self.sorts) >= column + 1:
                                    with self.keep_select_status():
                                        # Re-sort.
                                        self.items = sorted(self.items,
                                                            key=self.sorts[column][0],
                                                            cmp=self.sorts[column][1],
                                                            reverse=self.title_sorts[column])

                                    # Update item index.
                                    self.update_item_index()
                                break
                elif len(self.items) > 0:
                    self.release_item(event)
            elif len(self.items) > 0:
                self.release_item(event)

            self.drag_reference_row = None
            self.drag_preview_pixbuf = None
            self.title_adjust_column = None
            self.queue_draw()

        # Remove auto scroll handler.
        remove_timeout_id(self.auto_scroll_id)

    @contextmanager
    def keep_select_status(self):
        '''
        Handy function that change listview and keep select status not change.
        '''
        # Save select items.
        start_select_item = None
        if self.start_select_row != None:
            start_select_item = self.items[self.start_select_row]

        select_items = []
        for row in self.select_rows:
            select_items.append(self.items[row])

        try:
            yield
        except Exception, e:
            print 'function keep_select_status got error %s' % e
            traceback.print_exc(file=sys.stdout)

        else:
            # Restore select status.
            if start_select_item != None or select_items != []:
                # Init start select row.
                if start_select_item != None:
                    self.start_select_row = None

                # Init select rows.
                if select_items != []:
                    self.select_rows = []

                for (index, item) in enumerate(self.items):
                    # Try restore select row.
                    if item in select_items:
                        self.select_rows.append(index)
                        select_items.remove(item)

                    # Try restore start select row.
                    if item == start_select_item:
                        self.start_select_row = index
                        start_select_item = None

                    # Stop loop when finish restore row status.
                    if select_items == [] and start_select_item == None:
                        break

    def release_item(self, event):
        '''
        Internal function to handle release item.

        @param event: Button release event.
        '''
        if is_left_button(event):
            release_row = self.get_event_row(event)

            if self.double_click_row == release_row:
                self.emit_item_event("double-click-item", event)
            elif self.single_click_row == release_row:
                self.emit_item_event("single-click-item", event)

            if self.start_drag and self.is_in_visible_area(event):
                self.drag_select_items_at_cursor(event)

            self.reset_cursor()
            self.double_click_row = None
            self.single_click_row = None
            self.start_drag = False

            # Disable select rows when press_in_select_rows valid after button release.
            if self.press_in_select_rows:
                self.start_select_row = self.press_in_select_rows
                self.select_rows = [self.press_in_select_rows]

                self.press_in_select_rows = None

                self.queue_draw()

    def is_in_visible_area(self, event):
        '''
        Is event coordinate in visible area.

        @param event: gtk.gdk.Event.
        @return: Return True if event coordinate in visible area.
        '''
        (event_x, event_y) = get_event_coords(event)
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        vadjust = scrolled_window.get_vadjustment()
        return (-self.drag_out_offset <= event_x <= scrolled_window.allocation.width + self.drag_out_offset
                and vadjust.get_value() - self.drag_out_offset <= event_y <= vadjust.get_value() + vadjust.get_page_size() + self.drag_out_offset)

    def drag_select_items_at_cursor(self, event):
        '''
        Internal function to drag select items at cursor position.
        '''
        (event_x, event_y) = get_event_coords(event)
        hover_row = min(max(int((event_y - self.title_offset_y) / self.item_height), 0),
                        len(self.items))

        # Filt items around drag item.
        filter_items = self.before_drag_items + [self.drag_item] + self.after_drag_items

        before_items = []
        for item in self.items[0:hover_row]:
            if not item in filter_items:
                before_items.append(item)

        after_items = []
        for item in self.items[hover_row::]:
            if not item in filter_items:
                after_items.append(item)

        # Update items order.
        self.items = before_items + self.before_drag_items + [self.drag_item] + self.after_drag_items + after_items

        # Update select rows.
        self.select_rows = range(len(before_items), len(self.items) - len(after_items))

        # Update select start row.
        for row in self.select_rows:
            if self.items[row] == self.start_select_item:
                self.start_select_row = row
                break


        # Update item index.
        self.update_item_index()

        # Redraw.
        self.queue_draw()

    def leave_list_view(self, widget, event):
        '''
        Internal callback for `leave-notify-event` signal.

        @param widget: ListView widget.
        @param event: Leave notify event.
        '''
        # Reset.
        self.title_select_column = None
        self.title_adjust_column = None
        if not self.left_button_press:
            self.reset_cursor()

        self.hover_row = None

        # Redraw.
        self.queue_draw()

    def key_press_list_view(self, widget, event):
        '''
        Internal callback for `key-press-event` signal.

        @param widget: ListView widget.
        @param event: Key press event.
        '''
        if has_ctrl_mask(event):
            self.press_ctrl = True

        if has_shift_mask(event):
            self.press_shift = True

        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

        # Hide hover row.
        if self.hover_row and not has_ctrl_mask(event) and not has_shift_mask(event):
            self.hover_row = None
            self.queue_draw()

        return True

    def key_release_list_view(self, widget, event):
        '''
        Internal callback for `key-release-event` signal.

        @param widget: ListView widget.
        @param event: Key release event.
        '''
        if has_ctrl_mask(event):
            self.press_ctrl = False

        if has_shift_mask(event):
            self.press_shift = False

    def emit_item_event(self, event_name, event):
        '''
        Wrap method for emit event signal.

        @param event_name: Event name.
        @param event: Event.
        '''
        (event_x, event_y) = get_event_coords(event)
        event_row = (event_y - self.title_offset_y) / self.item_height
        if 0 <= event_row <= last_index(self.items):
            offset_y = event_y - event_row * self.item_height - self.title_offset_y
            (event_column, offset_x) = get_disperse_index(self.cell_widths, event_x)

            self.emit(event_name, self.items[event_row], event_column, offset_x, offset_y)
        else:
            if event_name == "motion-notify-item":
                self.emit(event_name, None, 0, 0, 0)

    def get_coordinate_row(self, y):
        '''
        Get row with given y coordinate.

        @param y: Y coordinate.
        @return: Return row that match given y coordinate, return None if haven't any row match y coordinate.
        '''
        row = int((y - self.title_offset_y) / self.item_height)
        if 0 <= row <= last_index(self.items):
            return row
        else:
            return None

    def get_event_row(self, event, offset_index=0):
        '''
        Get row at event.

        @param event: gtk.gdk.Event instance.
        @param offset_index: Offset index base on event row.
        @return: Return row at event coordinate, return None if haven't any row match event coordinate.
        '''
        (event_x, event_y) = get_event_coords(event)
        return self.get_row_with_coordinate(event.y, offset_index)

    def get_row_with_coordinate(self, y, offset_index=0):
        '''
        Get row with y coordinate.

        @param y: Y coordinate.
        @param offset_index: Row offset index.
        @return: Return row at y coordinate, return None if haven't any row match y coordinate.
        '''
        row = int((y - self.title_offset_y) / self.item_height)
        if 0 <= row <= last_index(self.items) + offset_index:
            return row
        else:
            return None

    def update_select_rows(self, hover_row):
        '''
        Internal function to update select rows.
        '''
        hover_row = self.get_row_with_coordinate(self.get_pointer()[1])

        # Update select area.
        if hover_row != None and self.start_select_row != None:
            if hover_row > self.start_select_row:
                self.select_rows = range(self.start_select_row, hover_row + 1)
            elif hover_row < self.start_select_row:
                self.select_rows = range(hover_row, self.start_select_row + 1)
            else:
                self.select_rows = [hover_row]

    def select_first_item(self):
        '''
        Select first item.
        '''
        if len(self.items) > 0:
            # Update select rows.
            self.start_select_row = 0
            self.select_rows = [0]

            # Scroll to top.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            vadjust.set_value(vadjust.get_lower())

            # Redraw.
            self.queue_draw()

    def select_last_item(self):
        '''
        Select last item.
        '''
        if len(self.items) > 0:
            # Update select rows.
            last_row = last_index(self.items)
            self.start_select_row = last_row
            self.select_rows = [last_row]

            # Scroll to bottom.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

            # Redraw.
            self.queue_draw()

    def scroll_page_up(self):
        '''
        Scroll page up.
        '''
        if self.select_rows == []:
            # Select row.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            select_y = max(vadjust.get_value() - vadjust.get_page_size(), self.title_offset_y)
            select_row = int((select_y - self.title_offset_y) / self.item_height)

            # Update select row.
            self.start_select_row = select_row
            self.select_rows = [select_row]

            # Scroll viewport make sure preview row in visible area.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
            if select_row == 0:
                vadjust.set_value(vadjust.get_lower())
            elif offset_y > select_row * self.item_height + self.title_offset_y:
                vadjust.set_value(max((select_row - 1) * self.item_height + self.title_offset_y, vadjust.get_lower()))

            # Redraw.
            self.queue_draw()
        else:
            if self.start_select_row != None:
                # Record offset before scroll.
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                scroll_offset_y = self.start_select_row * self.item_height + self.title_offset_y - vadjust.get_value()

                # Get select row.
                select_y = max(self.start_select_row * self.item_height - vadjust.get_page_size(), self.title_offset_y)
                select_row = int((select_y - self.title_offset_y) / self.item_height)

                # Update select row.
                self.start_select_row = select_row
                self.select_rows = [select_row]

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                if select_row == 0:
                    vadjust.set_value(vadjust.get_lower())
                elif offset_y > select_row * self.item_height + self.title_offset_y:
                    vadjust.set_value(max(select_row * self.item_height + self.title_offset_y - scroll_offset_y,
                                          vadjust.get_lower()))

                # Redraw.
                self.queue_draw()
            else:
                print "scroll_page_up : impossible!"

    def scroll_page_down(self):
        '''
        Scroll page down.
        '''
        if self.select_rows == []:
            # Select row.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            select_y = min(vadjust.get_value() + vadjust.get_page_size(),
                           vadjust.get_upper() - self.item_height)
            select_row = int((select_y - self.title_offset_y) / self.item_height)

            # Update select row.
            self.start_select_row = select_row
            self.select_rows = [select_row]

            # Scroll viewport make sure preview row in visible area.
            max_y = vadjust.get_upper() - vadjust.get_page_size()
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
            if offset_y + vadjust.get_page_size() < (select_row + 1) * self.item_height + self.title_offset_y:
                vadjust.set_value(min(max_y, (select_row - 1) * self.item_height + self.title_offset_y))

            # Redraw.
            self.queue_draw()
        else:
            if self.start_select_row != None:
                # Record offset before scroll.
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                scroll_offset_y = self.start_select_row * self.item_height + self.title_offset_y - vadjust.get_value()

                # Get select row.
                select_y = min(self.start_select_row * self.item_height + vadjust.get_page_size(),
                               vadjust.get_upper() - self.item_height)
                select_row = int((select_y - self.title_offset_y) / self.item_height)

                # Update select row.
                self.start_select_row = select_row
                self.select_rows = [select_row]

                # Scroll viewport make sure preview row in visible area.
                max_y = vadjust.get_upper() - vadjust.get_page_size()
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                if offset_y + vadjust.get_page_size() < (select_row + 1) * self.item_height + self.title_offset_y:
                    vadjust.set_value(min(max_y, select_row * self.item_height + self.title_offset_y - scroll_offset_y))

                # Redraw.
                self.queue_draw()
            else:
                print "scroll_page_down : impossible!"

    def select_prev_item(self):
        '''
        Select preview item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        else:
            # Get preview row.
            prev_row = max(0, self.start_select_row - 1)

            # Redraw when preview row is not current row.
            if prev_row != self.start_select_row:
                # Select preview row.
                self.start_select_row = prev_row
                self.select_rows = [prev_row]

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y > prev_row * self.item_height:
                    vadjust.set_value(max(vadjust.get_lower(), (prev_row - 1) * self.item_height + self.title_offset_y))
                elif offset_y + vadjust.get_page_size() < prev_row * self.item_height + self.title_offset_y:
                    vadjust.set_value(min(vadjust.get_upper() - vadjust.get_page_size(),
                                          (prev_row - 1) * self.item_height + self.title_offset_y))

                # Redraw.
                self.queue_draw()
            elif len(self.select_rows) > 1:
                # Select preview row.
                self.start_select_row = prev_row
                self.select_rows = [prev_row]

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y > prev_row * self.item_height + self.title_offset_y:
                    vadjust.set_value(max(vadjust.get_lower(), (prev_row - 1) * self.item_height + self.title_offset_y))

                    # Redraw.
                    self.queue_draw()

    def select_next_item(self):
        '''
        Select next item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        else:
            # Get next row.
            next_row = min(last_index(self.items), self.start_select_row + 1)

            # Redraw when next row is not current row.
            if next_row != self.start_select_row:
                # Select next row.
                self.start_select_row = next_row
                self.select_rows = [next_row]

                # Scroll viewport make sure next row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y + vadjust.get_page_size() < (next_row + 1) * self.item_height + self.title_offset_y or offset_y > next_row * self.item_height + self.title_offset_y:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          (next_row + 1) * self.item_height + self.title_offset_y - vadjust.get_page_size()))

                # Redraw.
                self.queue_draw()
            elif len(self.select_rows) > 1:
                # Select next row.
                self.start_select_row = next_row
                self.select_rows = [next_row]

                # Scroll viewport make sure next row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y + vadjust.get_page_size() < (next_row + 1) * self.item_height + self.title_offset_y:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          (next_row + 1) * self.item_height + self.title_offset_y - vadjust.get_page_size()))

                    # Redraw.
                    self.queue_draw()

    def select_to_prev_item(self):
        '''
        Select to preview item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        elif self.start_select_row != None:
            if self.start_select_row == self.select_rows[-1]:
                first_row = self.select_rows[0]
                if first_row > 0:
                    prev_row = first_row - 1
                    self.select_rows = [prev_row] + self.select_rows

                    (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                    vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                    if offset_y > prev_row * self.item_height:
                        vadjust.set_value(max(vadjust.get_lower(), (prev_row - 1) * self.item_height + self.title_offset_y))

                    self.queue_draw()
            elif self.start_select_row == self.select_rows[0]:
                last_row = self.select_rows[-1]
                self.select_rows.remove(last_row)

                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y > self.select_rows[-1] * self.item_height:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          (self.select_rows[-1] - 1) * self.item_height + self.title_offset_y))

                self.queue_draw()
        else:
            print "select_to_prev_item : impossible!"

    def select_to_next_item(self):
        '''
        Select to next item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        elif self.start_select_row != None:
            if self.start_select_row == self.select_rows[0]:
                last_row = self.select_rows[-1]
                if last_row < last_index(self.items):
                    next_row = last_row + 1
                    self.select_rows.append(next_row)

                    (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                    vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                    if offset_y + vadjust.get_page_size() < next_row * self.item_height + self.title_offset_y:
                        vadjust.set_value(max(vadjust.get_lower(),
                                              (next_row + 1) * self.item_height + self.title_offset_y - vadjust.get_page_size()))

                    self.queue_draw()
            elif self.start_select_row == self.select_rows[-1]:
                first_row = self.select_rows[0]
                self.select_rows.remove(first_row)

                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                if offset_y + vadjust.get_page_size() < (self.select_rows[0] + 1) * self.item_height + self.title_offset_y:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          (self.select_rows[0] + 1) * self.item_height + self.title_offset_y - vadjust.get_page_size()))

                self.queue_draw()
        else:
            print "select_to_next_item : impossible!"

    def select_to_first_item(self):
        '''
        Select to first item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        elif self.start_select_row != None:
            if self.start_select_row == self.select_rows[-1]:
                self.select_rows = range(0, self.select_rows[-1] + 1)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                vadjust.set_value(vadjust.get_lower())
                self.queue_draw()
            elif self.start_select_row == self.select_rows[0]:
                self.select_rows = range(0, self.select_rows[0] + 1)
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                vadjust.set_value(vadjust.get_lower())
                self.queue_draw()
        else:
            print "select_to_first_item : impossible!"

    def select_to_last_item(self):
        '''
        Select to last item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        elif self.start_select_row != None:
            if self.start_select_row == self.select_rows[0]:
                self.select_rows = range(self.select_rows[0], len(self.items))
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
                self.queue_draw()
            elif self.start_select_row == self.select_rows[-1]:
                self.select_rows = range(self.select_rows[-1], len(self.items))
                vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
                vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
                self.queue_draw()
        else:
            print "select_to_end_item : impossible!"

    def select_all_items(self):
        '''
        Select all items.
        '''
        if self.select_rows == []:
            self.start_select_row = 0
            self.select_rows = range(0, len(self.items))

            self.queue_draw()
        else:
            self.select_rows = range(0, len(self.items))

            self.queue_draw()

    def delete_select_items(self):
        '''
        Delete select items.
        '''
        # Get select items.
        remove_items = []
        for row in self.select_rows:
            remove_items.append(self.items[row])

        self.delete_items(remove_items)

    def delete_items(self, remove_items):
        '''
        Delete given items.

        @param remove_items: Items need to remove.
        '''
        # Init select row.
        self.start_select_row = None
        self.select_rows = []
        cache_remove_items = []

        # Remove select items.
        for remove_item in remove_items:
            cache_remove_items.append(remove_item)
            self.items.remove(remove_item)

        # Emit remove items signal.
        self.emit("delete-select-items", cache_remove_items)

        # Update item index.
        self.update_item_index()

        # Update vertical adjustment.
        self.update_vadjustment()

        # Redraw.
        self.queue_draw()

    def update_vadjustment(self):
        '''
        Update vertical adjustment.
        '''
        list_height = self.title_offset_y + len(self.items) * self.item_height
        self.set_size_request(sum(self.cell_min_widths), list_height)
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        if scrolled_window != None:
            vadjust = scrolled_window.get_vadjustment()
            vadjust.set_upper(list_height)

    def double_click_item(self):
        '''
        Double click item.
        '''
        if len(self.select_rows) == 1:
            self.emit("double-click-item", self.items[self.select_rows[0]], -1, 0, 0)

    def clear(self):
        '''
        Clear all list.
        '''
        # Clear list.
        self.start_select_row = None
        self.select_rows = []
        self.items = []

        # Update vertical adjustment.
        self.update_vadjustment()

        # Redraw.
        self.queue_draw()

    def get_current_item(self):
        '''
        Get current item.

        @return: Return select row, or return None if not any item selected.
        '''
        if len(self.select_rows) != 1:
            return None
        else:
            return self.items[self.select_rows[0]]

    def set_highlight(self, item):
        '''
        Set highlight with given item.
        '''
        self.highlight_item = item

        self.visible_highlight()

        self.queue_draw()

    def clear_highlight(self):
        '''
        Clear highlight status.
        '''
        self.highlight_item = None
        self.queue_draw()

    def visible_highlight(self):
        '''
        Visible highlight item.
        '''
        if self.highlight_item == None:
            print "visible_highlight: highlight item is None."
        else:
            # Scroll viewport make sure highlight row in visible area.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
            scrolled_window = get_match_parent(self, ["ScrolledWindow"])
            if scrolled_window == None:
                raise Exception, "parent container is not ScrolledWindow"
            vadjust = scrolled_window.get_vadjustment()
            highlight_index = self.highlight_item.get_index()
            if offset_y > highlight_index * self.item_height:
                vadjust.set_value(highlight_index * self.item_height)
            elif offset_y + vadjust.get_page_size() < (highlight_index + 1) * self.item_height:
                vadjust.set_value((highlight_index + 1) * self.item_height - vadjust.get_page_size() + self.title_offset_y)

gobject.type_register(ListView)

class ListItem(gobject.GObject):
    '''
    ListItem template to build your own item for L{ I{ListView} <ListView>}.

    @note: This class just template to build list item, you should build new item with same interface.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, title, artist, length):
        '''
        Initialize ListItem class.

        @param title: Title.
        @param artist: Artist.
        @param length: Length.
        '''
        gobject.GObject.__init__(self)
        self.update(title, artist, length)
        self.index = None

    def set_index(self, index):
        '''
        Update index.

        This is ListView interface, you should implement it.

        @param index: Index.
        '''
        self.index = index

    def get_index(self):
        '''
        Get index.

        This is ListView interface, you should implement it.
        '''
        return self.index

    def emit_redraw_request(self):
        '''
        Emit redraw-request signal.

        This is ListView interface, you should implement it.
        '''
        self.emit("redraw-request")

    def update(self, title, artist, length):
        '''
        Update.

        This is ListView interface, you should implement it.

        @param title: Title.
        @param artist: Artist.
        @param length: Length.
        '''
        # Update.
        self.title = title
        self.artist = artist
        self.length = length

        # Calculate item size.
        self.title_padding_x = 10
        self.title_padding_y = 5
        (self.title_width, self.title_height) = get_content_size(self.title, DEFAULT_FONT_SIZE)

        self.artist_padding_x = 10
        self.artist_padding_y = 5
        (self.artist_width, self.artist_height) = get_content_size(self.artist, DEFAULT_FONT_SIZE)

        self.length_padding_x = 10
        self.length_padding_y = 5
        (self.length_width, self.length_height) = get_content_size(self.length, DEFAULT_FONT_SIZE)

    def render_title(self, cr, rect, in_select, in_highlight):
        '''
        Render title.

        @param cr: Cairo context.
        @param rect: Redraw rectangle.
        @param in_select: Whether current item is selected, this value pass from ListView.
        @param in_highlight: Whether current item is highlighted, this value pass from ListView.
        '''
        rect.x += self.title_padding_x
        rect.width -= self.title_padding_x * 2
        render_text(cr, rect, self.title, in_select, in_highlight)

    def render_artist(self, cr, rect, in_select, in_highlight):
        '''
        Render artist.

        @param cr: Cairo context.
        @param rect: Redraw rectangle.
        @param in_select: Whether current item is selected, this value pass from ListView.
        @param in_highlight: Whether current item is highlighted, this value pass from ListView.
        '''
        rect.x += self.artist_padding_x
        rect.width -= self.title_padding_x * 2
        render_text(cr, rect, self.artist, in_select, in_highlight)

    def render_length(self, cr, rect, in_select, in_highlight):
        '''
        Render length.

        @param cr: Cairo context.
        @param rect: Redraw rectangle.
        @param in_select: Whether current item is selected, this value pass from ListView.
        @param in_highlight: Whether current item is highlighted, this value pass from ListView.
        '''
        rect.width -= self.length_padding_x * 2
        render_text(cr, rect, self.length, in_select, in_highlight, align=ALIGN_END)

    def get_column_sizes(self):
        '''
        Get column sizes.

        This is ListView interface, you should implement it.

        @return: Return column size tuple.
        '''
        return [(self.title_width + self.title_padding_x * 2,
                 self.title_height + self.title_padding_y * 2),
                (self.artist_width + self.artist_padding_x * 2,
                 self.artist_height + self.artist_padding_y * 2),
                (self.length_width + self.length_padding_x * 2,
                 self.length_height + self.length_padding_y * 2),
                ]

    def get_renders(self):
        '''
        Get render callbacks.

        This is ListView interface, you should implement it.

        @return: Return render functions.
        '''
        return [self.render_title, self.render_artist, self.render_length]

def render_text(cr, rect, content, in_select, in_highlight, align=ALIGN_START, font_size=DEFAULT_FONT_SIZE):
    '''
    Helper render text function for ListItem, you should implement your own.

    @param cr: Cairo context.
    @param rect: Draw area.
    @param content: Content.
    @param in_select: Whether item is selected.
    @param in_highlight: Whether item is highlighted.
    @param align: Render alignment option, default is ALIGN_START.
    @param font_size: Render font size, default is DEFAULT_FONT_SIZE.
    '''
    if in_select or in_highlight:
        color = ui_theme.get_color("list_item_select_text").get_color()
    else:
        color = ui_theme.get_color("list_item_text").get_color()
    draw_text(cr, content,
              rect.x, rect.y, rect.width, rect.height,
              font_size,
              color,
              alignment=align)

def render_image(cr, rect, image_path, x, y):
    '''
    Helper render image function for ListItem, you should implement your own.

    @param cr: Cairo context.
    @param rect: Draw area.
    @param image_path: Image path.
    @param x: X coordinate of draw position.
    @param y: Y coordinate of draw position.
    '''
    draw_pixbuf(cr, ui_theme.get_pixbuf(image_path).get_pixbuf(), x, y)
