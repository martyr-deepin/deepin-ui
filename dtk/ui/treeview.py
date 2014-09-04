#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
#             Hou Shaohui <houshao55@gmail.com>
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

import sys
import traceback
from contextlib import contextmanager
from constant import DEFAULT_FONT_SIZE
import gtk
import gobject
import cairo
import gc
from threads import post_gui
from draw import draw_vlinear, draw_pixbuf, draw_text
from theme import ui_theme
from keymap import has_ctrl_mask, has_shift_mask, get_keyevent_name
from cache_pixbuf import CachePixbuf
from deepin_utils.core import get_disperse_index
from utils import (cairo_state, get_window_shadow_size, get_event_coords, color_hex_to_cairo,
                   is_in_rect,is_left_button, is_double_click, is_single_click,
                   remove_timeout_id, is_right_button)
from skin_config import skin_config
from scrolled_window import ScrolledWindow
import copy
import pango
import math
import threading as td

__all__ = ["TreeView"]

class SortThread(td.Thread):

    def __init__(self, sort_action, render_action):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.sort_action = sort_action
        self.render_action = render_action

    def run(self):
        self.render_action(*self.sort_action())

class Titlebar(gtk.Button):

    __gsignals__ = {"clicked-title" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                       (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))}

    def __init__(self):
        gtk.Button.__init__(self)
        self.bg_cache_pixbuf = CachePixbuf()
        self.hover_cache_pixbuf = CachePixbuf()
        self.press_cache_pixbuf = CachePixbuf()

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK)

        self.connect("expose-event", self.on_titlebar_expose_event)
        self.connect("button-press-event", self.on_titlebar_press_event)
        self.connect("button-release-event", self.on_titlebar_release_event)
        self.connect("motion-notify-event", self.on_titlebar_motion_notify)
        self.connect("leave-notify-event", self.on_titlebar_leave_notify)

        bg_pixbuf = ui_theme.get_pixbuf("listview/header_normal.png").get_pixbuf()
        self.default_height = bg_pixbuf.get_height()

        self.titles = None
        self.hover_index = None
        self.press_index = None
        self.title_widths = None
        self.expand_index = None

        self.set_no_show_all(True)
        self.hide_all()

    def enable(self):
        self.set_no_show_all(False)
        self.show_all()

    def set_titles(self, titles, expand_index=0):
        self.titles = titles
        self.expand_index = expand_index
        self.sort_ascendings = [False] * len(titles)
        self.set_size_request(-1, self.default_height)

        self.enable()

    def set_widths(self, widths):
        self.title_widths = dict(widths)
        self.queue_draw()

    def get_before_width(self, index):
        filter_items = filter(lambda item: item[0] < index, self.title_widths.items())
        if filter_items:
            return sum(zip(*filter_items)[-1])
        else:
            return 0

    def on_titlebar_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        title_rect = gtk.gdk.Rectangle(x, y, w, h)

        if self.titles == None:
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(*rect)
            cr.fill()
            return True

        if not self.title_widths and len(self.titles) > 0:
            average_width = rect.width / len(self.titles)
            self.title_widths = {key: average_width for key in range(len(self.titles))}

        # Draw background.
        bg_pixbuf = ui_theme.get_pixbuf("listview/header_normal.png").get_pixbuf()
        self.bg_cache_pixbuf.scale(bg_pixbuf, w, h)
        draw_pixbuf(cr, self.bg_cache_pixbuf.get_cache(), x, y)

        # Draw press status.
        if self.press_index != None:
            press_pixbuf = ui_theme.get_pixbuf("listview/header_press.png").get_pixbuf()
            self.press_cache_pixbuf.scale(press_pixbuf, self.title_widths[self.press_index], h)
            draw_pixbuf(cr, self.press_cache_pixbuf.get_cache(),
                         x + self.get_before_width(self.press_index), y)

        # Draw hover status.
        elif self.hover_index != None:
            hover_pixbuf = ui_theme.get_pixbuf("listview/header_hover.png").get_pixbuf()
            self.hover_cache_pixbuf.scale(hover_pixbuf, self.title_widths[self.hover_index], h)
            draw_pixbuf(cr, self.hover_cache_pixbuf.get_cache(),
                        x + self.get_before_width(self.hover_index), y)

        # Draw split.
        split_pixbuf = ui_theme.get_pixbuf("listview/split.png").get_pixbuf()
        split_start_x = x
        for index, each_width in self.title_widths.items():
            split_start_x += each_width
            if index != max(self.title_widths.keys()):
                draw_pixbuf(cr, split_pixbuf, split_start_x - 1, y)

            # Draw title.
            # FIXME: IndexError: tuple index out of range
            if index < len(self.titles):
                draw_text(cr, self.titles[index], title_rect.x, y, each_width, h,
                          alignment=pango.ALIGN_CENTER)
            title_rect.x += each_width

            # Draw sort icon.
            if self.hover_index != None and self.hover_index == index:
                if self.sort_ascendings[self.hover_index]:
                    sort_pixbuf = ui_theme.get_pixbuf("listview/sort_ascending.png").get_pixbuf()
                else:
                    sort_pixbuf = ui_theme.get_pixbuf("listview/sort_descending.png").get_pixbuf()

                draw_pixbuf(cr, sort_pixbuf,
                            title_rect.x - sort_pixbuf.get_width(),
                            y + (h - sort_pixbuf.get_height()) / 2
                            )
        return True

    def on_titlebar_press_event(self, widget, event):
        if self.hover_index !=None:
            self.press_index = self.hover_index

            self.queue_draw()

    def on_titlebar_release_event(self, widget, event):
        if self.press_index != None:
            self.sort_ascendings[self.press_index] = not self.sort_ascendings[self.press_index]
            self.emit("clicked-title", self.press_index, self.sort_ascendings[self.press_index])
            self.press_index = None

    def on_titlebar_motion_notify(self, widget, event):
        if not self.title_widths:
            return

        rect = widget.allocation
        rect.x = rect.y = 0
        for index, width in self.title_widths.items():
            title_rect = gtk.gdk.Rectangle(rect.x, rect.y, width, self.default_height)
            if is_in_rect((event.x, event.y), title_rect):
                self.hover_index = index
                break
            rect.x += width
        else:
            self.hover_index = None
        self.queue_draw()

    def on_titlebar_leave_notify(self, widget, event):
        self.hover_index = None
        self.queue_draw()


class TreeView(gtk.VBox):
    '''
    TreeView widget.

    @undocumented: realize_tree_view
    @undocumented: button_release_scrolled_window
    @undocumented: on_titlebar_clicked_title
    @undocumented: render_sort_column
    @undocumented: update_item_widths
    @undocumented: redraw_request
    @undocumented: update_redraw_request_list
    @undocumented: update_vadjustment
    @undocumented: expose_tree_view
    @undocumented: draw_background
    @undocumented: draw_mask
    @undocumented: draw_items
    @undocumented: get_expose_bound
    @undocumented: button_press_tree_view
    @undocumented: click_item
    @undocumented: shift_click
    @undocumented: ctrl_click
    @undocumented: button_release_tree_view
    @undocumented: release_item
    @undocumented: is_in_visible_area
    @undocumented: set_drag_row
    @undocumented: drag_select_items_at_cursor
    @undocumented: motion_tree_view
    @undocumented: hover_item
    @undocumented: auto_scroll_tree_view
    @undocumented: get_drag_row
    @undocumented: auto_scroll_tree_view_down
    @undocumented: auto_scroll_tree_view_up
    @undocumented: update_select_rows
    @undocumented: key_press_tree_view
    @undocumented: key_release_tree_view
    @undocumented: size_allocated_tree_view
    @undocumented: leave_tree_view
    @undocumented: focus_out_tree_view
    @undocumented: unhover_row
    @undocumented: set_hover_row
    @undocumented: get_cell_with_event
    @undocumented: get_row_with_coordinate
    @undocumented: get_offset_coordinate
    @undocumented: keep_select_status
    '''

    AUTO_SCROLL_HEIGHT = 24

    __gsignals__ = {
        "items-change" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "delete-select-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "press-return" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "button-press-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "motion-notify-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int, int)),
        "right-press-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                               (int, int, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    def __init__(self,
                 items=[],
                 drag_data=None,
                 enable_hover=True,
                 enable_highlight=True,
                 enable_multiple_select=True,
                 enable_drag_drop=True,
                 drag_icon_pixbuf=None,
                 start_drag_offset=50,
                 mask_bound_height=12,
                 right_space=0,
                 top_bottom_space=3,
                 padding_x=0,
                 padding_y=0,
                 expand_column=0,
                 ):
        '''
        Initialize TreeView class.

        @param items: The init items.
        @param drag_data: Data for drag action.
        @param enable_hover: Whether enable mouse hover effect, default is True.
        @param enable_highlight: Whether enable highlight effect, default is True.
        @param enable_multiple_select: Whether enable multiple select operation, default is True.
        @param enable_drag_drop: Whether enable drag drop operation, default is True.
        @param drag_icon_pixbuf: The pixbuf display when drag drop operation start.
        @param start_drag_offset: The offset to trigger drag drop operation, default is 50 pixels.
        @param mask_bound_height: The height of mask bound, default is 12 pixels.
        @param right_space: Right space, default is 0.
        @param top_bottom_space: Top bottom space, default is 3 pixels.
        @param padding_x: The padding x value.
        @param padding_y: The padding y value.
        @param expand_column: The expand column, default is 0.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.visible_items = []
        self.titles = None
        self.sort_methods = None
        self.drag_data = drag_data
        self.enable_hover = enable_hover
        self.enable_highlight = enable_highlight
        self.enable_multiple_select = enable_multiple_select
        self.enable_drag_drop = enable_drag_drop
        self.drag_icon_pixbuf = drag_icon_pixbuf
        self.start_drag_offset = start_drag_offset
        self.mask_bound_height = mask_bound_height
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.start_drag = False
        self.start_select_row = None
        self.select_rows = []
        self.hover_row = None
        self.press_item = None
        self.press_in_select_rows = None
        self.left_button_press = False
        self.press_ctrl = False
        self.press_shift = False
        self.single_click_row = None
        self.double_click_row = None
        self.auto_scroll_id = None
        self.auto_scroll_delay = 70 # milliseconds
        self.drag_item = None
        self.drag_reference_row = None
        self.column_widths = []
        self.sort_action_id = 0
        self.title_offset_y = -1

        self.highlight_item = None

        # hide columns.
        self.hide_columns = None

        # expand column.
        self.expand_column = expand_column

        # Init redraw.
        self.redraw_request_list = []
        self.redraw_delay = 100 # update redraw item delay, milliseconds
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)

        # Init widgets.
        self.title_box = Titlebar()
        self.title_box.connect("clicked-title", self.on_titlebar_clicked_title)
        self.draw_area = gtk.DrawingArea()
        self.draw_area.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.draw_area.set_can_focus(True)
        self.draw_align = gtk.Alignment()
        self.draw_align.set(0.5, 0.5, 1, 1)
        # FIXME
        # Add padding will make all coordinate calculation failed,
        # we need review all code after uncomment below line.
        # self.draw_align.set_padding(self.padding_y, self.padding_y, self.padding_x, self.padding_x)

        self.scrolled_window = ScrolledWindow(right_space, top_bottom_space)

        # Connect widgets.
        self.draw_align.add(self.draw_area)
        self.scrolled_window.add_child(self.draw_align)
        self.pack_start(self.title_box, False, True)
        self.pack_start(self.scrolled_window, True, True)

        # Handle signals.
        self.draw_area.connect("realize", self.realize_tree_view)
        self.draw_area.connect("realize", lambda w: self.grab_focus())
        self.draw_area.connect("expose-event", lambda w, e: self.expose_tree_view(w))
        self.draw_area.connect("button-press-event", self.button_press_tree_view)
        self.draw_area.connect("button-release-event", self.button_release_tree_view)
        self.draw_area.connect("motion-notify-event", self.motion_tree_view)
        self.draw_area.connect("key-press-event", self.key_press_tree_view)
        self.draw_area.connect("key-release-event", self.key_release_tree_view)
        self.draw_area.connect("size-allocate", self.size_allocated_tree_view)
        self.draw_area.connect("leave-notify-event", self.leave_tree_view)
        self.draw_area.connect("focus-out-event", self.focus_out_tree_view)

        # Add items.
        self.add_items(items)

        # Init keymap.
        self.keymap = {
            "Home" : self.select_first_item,
            "End" : self.select_last_item,
            "Page_Up" : self.scroll_page_up,
            "Page_Down" : self.scroll_page_down,
            "Up" : self.select_prev_item,
            "Down" : self.select_next_item,
            "Left" : self.unexpand_item,
            "Right" : self.expand_item,
            "Shift + Up" : self.select_to_prev_item,
            "Shift + Down" : self.select_to_next_item,
            "Shift + Home" : self.select_to_first_item,
            "Shift + End" : self.select_to_last_item,
            "Ctrl + a" : self.select_all_items,
            "Delete" : self.delete_select_items,
            "Return" : self.press_return,
            }

    def get_items(self):
        '''
        Get items.

        @return: Return all visible items.
        '''
        return self.visible_items

    def realize_tree_view(self, widget):
        self.scrolled_window.connect("button-release-event", self.button_release_scrolled_window)

    def button_release_scrolled_window(self, widget, event):
        if len(self.visible_items) > 0:
            (start_index, end_index, item_height_count) = self.get_expose_bound()

            need_gc_collect = False
            for item in self.visible_items[0:start_index] + self.visible_items[end_index:-1]:
                if hasattr(item, "release_resource") and item.release_resource():
                    need_gc_collect = True

            if need_gc_collect:
                gc.collect()

    def expand_item(self):
        '''
        Expand item.
        '''
        if len(self.select_rows) == 1:
            self.visible_items[self.select_rows[0]].expand()

    def unexpand_item(self):
        '''
        Unexpand item.
        '''
        if len(self.select_rows) == 1:
            select_item = self.visible_items[self.select_rows[0]]
            if select_item.is_expand:
                select_item.unexpand()
            else:
                if select_item.parent_item != None:
                    new_row = select_item.parent_item.row_index
                    self.start_select_row = new_row
                    self.set_select_rows([new_row])

                    # Scroll viewport make sure preview row in visible area.
                    (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                    vadjust = self.scrolled_window.get_vadjustment()
                    new_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:new_row]))
                    if offset_y > new_row_height_count:
                        vadjust.set_value(max(vadjust.get_lower(),
                                              new_row_height_count - self.visible_items[new_row].get_height()))


    def on_titlebar_clicked_title(self, widget, index, sort_ascending):
        if self.sort_methods:
            SortThread(lambda : self.sort_column(index, sort_ascending), self.render_sort_column).start()

    def sort_column(self, sort_column_index, sort_ascending):
        '''
        Sort column.

        @param sort_column_index: The index of sort column.
        @param sort_ascending: Sort ascending.
        '''
        # Update sort action id.
        self.sort_action_id += 1

        # Save current action id to return.
        sort_action_id = self.sort_action_id

        # Split items with different column index.
        level_items = []
        column_index = None
        for item in self.visible_items:
            if item.column_index != column_index:
                level_items.append((item.column_index, item.parent_item, [item]))
                column_index = item.column_index
            else:
                if len(level_items) == 0:
                    level_items.append((item.column_index, item.parent_item, [item]))
                else:
                    level_items[-1][2].append(item)

        # Connect all toplevel items to sort.
        toplevel_items = []
        child_items = []
        for item in level_items:
            (column_index, parent_item, items) = item
            if column_index == 0:
                toplevel_items += items
            else:
                child_items.append(item)
        level_items = [(0, None, toplevel_items)] + child_items

        # Sort items with different column index to make sure parent item sort before child item.
        level_items = sorted(level_items, key=lambda (column_index, parent_item, items): column_index)

        # Sort all items.
        result_items = []
        for (column_index, parent_item, items) in level_items:
            # Do sort action.
            sort_items = self.sort_methods[sort_column_index](
                items,
                sort_ascending
                )

            # If column index is 0, insert at last position.
            if column_index == 0:
                result_items += sort_items
            # Insert after parent item if column index is not 0 (child items).
            else:
                split_index = result_items.index(parent_item) + 1
                result_items = result_items[0:split_index] + sort_items + result_items[split_index::]

        return (result_items, sort_action_id)

    @post_gui
    def render_sort_column(self, items, sort_action_id):
        if sort_action_id == self.sort_action_id:
            self.add_items(items, None, True)
        else:
            print "render_sort_column: drop old sort result!"

    def set_column_titles(self,
                          titles,
                          sort_methods=None,
                          ):
        '''
        Set column titles.

        @param titles: The title list to column.
        @param sort_methods: The sort method for column.
        '''
        if titles:
            self.titles = titles
            self.title_box.set_titles(titles)
            self.sort_methods = sort_methods
            self.title_offset_y = self.title_box.default_height
        else:
            self.titles = None
            self.sort_methods = None

    def select_items(self,
                     items,
                     ):
        '''
        Select items.

        @param items: The items need to select.
        '''
        for select_row in self.select_rows:
            self.visible_items[select_row].unselect()

        select_rows = []
        for item in items:
            try:
                select_rows.append(self.visible_items.index(item))
            except Exception, e:
                print "function select_items got error: %s" % e
                traceback.print_exc(file=sys.stdout)

        self.select_rows = select_rows

        if select_rows == []:
            self.start_select_row = None
        else:
            for select_row in self.select_rows:
                self.visible_items[select_row].select()

    def set_select_rows(self, rows):
        '''
        Set select rows.

        @param rows: The row to select.
        '''
        for select_row in self.select_rows:
            self.visible_items[select_row].unselect()

        self.select_rows = rows

        if rows == []:
            self.start_select_row = None
        else:
            for select_row in self.select_rows:
                self.visible_items[select_row].select()

    def select_first_item(self):
        '''
        Select first item.
        '''
        if len(self.visible_items) > 0:
            # Update select rows.
            self.start_select_row = 0
            self.set_select_rows([0])

            # Scroll to top.
            vadjust = self.scrolled_window.get_vadjustment()
            vadjust.set_value(vadjust.get_lower())

    def select_last_item(self):
        '''
        Select last item.
        '''
        if len(self.visible_items) > 0:
            # Update select rows.
            last_row = len(self.visible_items) - 1
            self.start_select_row = last_row
            self.set_select_rows([last_row])

            # Scroll to bottom.
            vadjust = self.scrolled_window.get_vadjustment()
            vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

    def scroll_page_up(self):
        '''
        Scroll page up.
        '''
        if self.select_rows == []:
            # Select row.
            vadjust = self.scrolled_window.get_vadjustment()
            select_y = max(vadjust.get_value() - vadjust.get_page_size(), 0)
            select_row = self.get_row_with_coordinate(select_y)

            # Update select row.
            self.start_select_row = select_row
            self.set_select_rows([select_row])

            # Scroll viewport make sure preview row in visible area.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
            if select_row == 0:
                vadjust.set_value(vadjust.get_lower())
            else:
                item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:select_row]))
                if offset_y > item_height_count:
                    vadjust.set_value(max(item_height_count - self.visible_items[select_row].get_height(), vadjust.get_lower()))
        else:
            if self.start_select_row != None:
                # Record offset before scroll.
                vadjust = self.scrolled_window.get_vadjustment()

                item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:self.start_select_row]))
                scroll_offset_y = item_height_count - vadjust.get_value()

                # Get select row.
                select_y = max(item_height_count - vadjust.get_page_size(), 0)
                select_row = self.get_row_with_coordinate(select_y)

                # Update select row.
                self.start_select_row = select_row
                self.set_select_rows([select_row])

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                if select_row == 0:
                    vadjust.set_value(vadjust.get_lower())
                else:
                    item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:select_row]))
                    if offset_y > item_height_count:
                        vadjust.set_value(max(item_height_count - scroll_offset_y,
                                              vadjust.get_lower()))
            else:
                print "scroll_page_up : impossible!"


    def scroll_page_down(self):
        '''
        Scroll page down.
        '''
        if self.select_rows == []:
            # Select row.
            vadjust = self.scrolled_window.get_vadjustment()
            select_y = min(vadjust.get_value() + vadjust.get_page_size(), vadjust.get_upper())
            select_row = self.get_row_with_coordinate(select_y)

            # Update select row.
            self.start_select_row = select_row
            self.set_select_rows([select_row])

            # Scroll viewport make sure preview row in visible area.
            max_y = vadjust.get_upper() - vadjust.get_page_size()
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
            item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(self.start_select_row + 1)]))
            if offset_y + vadjust.get_page_size() < item_height_count:
                vadjust.set_value(min(max_y, item_height_count))
        else:
            if self.start_select_row != None:
                # Record offset before scroll.
                vadjust = self.scrolled_window.get_vadjustment()
                item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(self.start_select_row + 1)]))
                scroll_offset_y = item_height_count - vadjust.get_value()

                # Get select row.
                select_y = min(item_height_count + vadjust.get_page_size(), vadjust.get_upper())
                select_row = self.get_row_with_coordinate(select_y)

                # Update select row.
                self.start_select_row = select_row
                self.set_select_rows([select_row])

                # Scroll viewport make sure preview row in visible area.
                max_y = vadjust.get_upper() - vadjust.get_page_size()
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                item_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(self.start_select_row + 1)]))
                if offset_y + vadjust.get_page_size() < item_height_count:
                    vadjust.set_value(min(max_y, item_height_count - scroll_offset_y))
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
                self.set_select_rows([prev_row])

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                vadjust = self.scrolled_window.get_vadjustment()
                prev_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:prev_row]))
                if offset_y > prev_row_height_count:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          prev_row_height_count - self.visible_items[prev_row].get_height()))
                elif offset_y + vadjust.get_page_size() < prev_row_height_count:
                    vadjust.set_value(min(vadjust.get_upper() - vadjust.get_page_size(),
                                          prev_row_height_count - self.visible_items[prev_row].get_height()))
            elif len(self.select_rows) > 1:
                # Select preview row.
                self.start_select_row = prev_row
                self.set_select_rows([prev_row])

                # Scroll viewport make sure preview row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                vadjust = self.scrolled_window.get_vadjustment()
                prev_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:prev_row]))
                if offset_y > prev_row_height_count:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          prev_row_height_count - self.visible_items[prev_row].get_height()))

    def select_next_item(self):
        '''
        Select next item.
        '''
        if self.select_rows == []:
            self.select_first_item()
        else:
            # Get next row.
            next_row = min(len(self.visible_items) - 1, self.start_select_row + 1)

            # Redraw when next row is not current row.
            if next_row != self.start_select_row:
                # Select next row.
                self.start_select_row = next_row
                self.set_select_rows([next_row])

                # Scroll viewport make sure next row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                vadjust = self.scrolled_window.get_vadjustment()
                next_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:next_row]))
                if offset_y + vadjust.get_page_size() < next_row_height_count + self.visible_items[next_row].get_height() or offset_y > next_row_height_count:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          next_row_height_count + self.visible_items[next_row].get_height() - vadjust.get_page_size()))
            elif len(self.select_rows) > 1:
                # Select next row.
                self.start_select_row = next_row
                self.set_select_rows([next_row])

                # Scroll viewport make sure next row in visible area.
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                vadjust = self.scrolled_window.get_vadjustment()
                next_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(next_row + 1)]))
                if offset_y + vadjust.get_page_size() < next_row_height_count:
                    vadjust.set_value(max(vadjust.get_lower(),
                                          next_row_height_count - vadjust.get_page_size()))

    def select_to_prev_item(self):
        '''
        Select to preview item.
        '''
        if self.enable_multiple_select:
            if self.select_rows == []:
                self.select_first_item()
            elif self.start_select_row != None:
                if self.start_select_row == self.select_rows[-1]:
                    first_row = self.select_rows[0]
                    if first_row > 0:
                        prev_row = first_row - 1
                        self.set_select_rows([prev_row] + self.select_rows)

                        (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                        vadjust = self.scrolled_window.get_vadjustment()
                        prev_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:prev_row]))
                        if offset_y > prev_row_height_count:
                            vadjust.set_value(max(vadjust.get_lower(),
                                                  prev_row_height_count - self.visible_items[prev_row].get_height()))
                elif self.start_select_row == self.select_rows[0]:
                    last_row = self.select_rows[-1]
                    self.set_select_rows(self.select_rows.remove(last_row))

                    (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                    vadjust = self.scrolled_window.get_vadjustment()
                    prev_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:prev_row]))
                    if offset_y > prev_row_height_count:
                        vadjust.set_value(max(vadjust.get_lower(),
                                              prev_row_height_count - self.visible_items[prev_row].get_height()))
            else:
                print "select_to_prev_item : impossible!"

    def select_to_next_item(self):
        '''
        Select to next item.
        '''
        if self.enable_multiple_select:
            if self.select_rows == []:
                self.select_first_item()
            elif self.start_select_row != None:
                if self.start_select_row == self.select_rows[0]:
                    last_row = self.select_rows[-1]
                    if last_row < len(self.visible_items) - 1:
                        next_row = last_row + 1
                        self.set_select_rows(self.select_rows + [next_row])

                        (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                        vadjust = self.scrolled_window.get_vadjustment()
                        next_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(next_row + 1)]))
                        if offset_y + vadjust.get_page_size() < next_row_height_count:
                            vadjust.set_value(max(vadjust.get_lower(),
                                                  next_row_height_count + self.visible_items[next_row].get_height() - vadjust.get_page_size()))
                elif self.start_select_row == self.select_rows[-1]:
                    first_row = self.select_rows[0]
                    self.set_select_rows(self.select_rows.remove(first_row))

                    (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
                    vadjust = self.scrolled_window.get_vadjustment()
                    next_row_height_count = sum(map(lambda i: i.get_height(), self.visible_items[:(next_row + 1)]))
                    if offset_y + vadjust.get_page_size() < next_row_height_count:
                        vadjust.set_value(max(vadjust.get_lower(),
                                              next_row_height_count - vadjust.get_page_size()))
            else:
                print "select_to_next_item : impossible!"

    def select_to_first_item(self):
        '''
        Select to first item.
        '''
        if self.enable_multiple_select:
            if self.select_rows == []:
                self.select_first_item()
            elif self.start_select_row != None:
                if self.start_select_row == self.select_rows[-1]:
                    self.set_select_rows(range(0, self.select_rows[-1] + 1))
                    vadjust = self.scrolled_window.get_vadjustment()
                    vadjust.set_value(vadjust.get_lower())
                elif self.start_select_row == self.select_rows[0]:
                    self.set_select_rows(range(0, self.select_rows[0] + 1))
                    vadjust = self.scrolled_window.get_vadjustment()
                    vadjust.set_value(vadjust.get_lower())
            else:
                print "select_to_first_item : impossible!"

    def select_to_last_item(self):
        '''
        Select to last item.
        '''
        if self.enable_multiple_select:
            if self.select_rows == []:
                self.select_first_item()
            elif self.start_select_row != None:
                if self.start_select_row == self.select_rows[0]:
                    self.set_select_rows(range(self.select_rows[0], len(self.visible_items)))
                    vadjust = self.scrolled_window.get_vadjustment()
                    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
                elif self.start_select_row == self.select_rows[-1]:
                    self.set_select_rows(range(self.select_rows[-1], len(self.visible_items)))
                    vadjust = self.scrolled_window.get_vadjustment()
                    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
            else:
                print "select_to_end_item : impossible!"

    def select_all_items(self):
        '''
        Select all items.
        '''
        if self.enable_multiple_select:
            if self.select_rows == []:
                self.start_select_row = 0

            self.set_select_rows(range(0, len(self.visible_items)))

    def delete_select_items(self):
        '''
        Delete selected items.
        '''
        delete_items = map(lambda row: self.visible_items[row], self.select_rows)
        self.start_select_row = None
        self.select_rows = []

        self.delete_items(delete_items)

    def press_return(self):
        '''
        Do return operation on selected item.
        '''
        self.emit("press-return", map(lambda row: self.visible_items[row], self.select_rows))

    def update_item_index(self):
        '''
        Update index of items.
        '''
        for (index, item) in enumerate(self.visible_items):
            item.row_index = index

    def update_item_widths(self):
        self.column_widths = []
        for item in self.visible_items:
            for (index, column_width) in enumerate(item.get_column_widths()):
                if index < len(self.column_widths):
                    self.column_widths[index] = max(self.column_widths[index], column_width)
                else:
                    self.column_widths.insert(index, column_width)

        if self.titles != None:
            self.title_box.set_widths(self.get_column_widths())

    def redraw_request(self, item, immediately=False):
        if not item in self.redraw_request_list:
            self.redraw_request_list.append(item)

        if immediately:
            self.update_redraw_request_list()

    def update_redraw_request_list(self):
        if len(self.redraw_request_list) > 0:
            self.scrolled_window.queue_draw()

        # Clear redraw request list.
        self.redraw_request_list = []

        return True

    def set_items(self, items):
        '''
        Set items of TreeView.

        @param items: The need items to set.
        '''
        if items != self.visible_items:
            self.visible_items = items
            self.emit("items-change")

    def add_items(self,
                  items,
                  insert_pos=None,
                  clear_first=False,
                  ):
        '''
        Add items.

        @param items: The items to add.
        @param insert_pos: The insert position, if it is None, insert at end, otherwise insert with given position.
        @param clear_first: Whether clear items before insert, default is False.
        '''
        if len(items) > 0:
            with self.keep_select_status():
                if clear_first:
                    self.set_items([])

                if insert_pos == None:
                    self.set_items(self.visible_items + items)
                else:
                    self.set_items(self.visible_items[0:insert_pos] + items + self.visible_items[insert_pos::])

                # Update redraw callback.
                # Callback is better way to avoid performance problem than gobject signal.
                for item in items:
                    item.redraw_request_callback = self.redraw_request
                    item.add_items_callback = self.add_items
                    item.delete_items_callback = self.delete_items
                    item.connect("redraw-request", self.redraw_item)

                self.update_item_index()

                self.update_item_widths()

                self.update_vadjustment()

    def redraw_item(self, list_item):
        '''
        Internal function to redraw item.
        '''
        self.redraw_request_list.append(list_item)
        self.update_redraw_request_list()

    def delete_item_by_index(self, index):
        '''
        Delete item with given index.

        @param index: The index of item that need to delete.
        '''
        item = self.visible_items[index]
        items_delete = []
        items_delete.append(item)
        self.delete_items(items_delete)

    def delete_items(self, items):
        '''
        Delete items.

        @param items: The items need to delete.
        '''
        if len(items) > 0:
            cache_remove_items = []
            with self.keep_select_status():
                for item in items:
                    if item in self.visible_items:
                        cache_remove_items.append(item)
                        self.visible_items.remove(item)

                self.emit("delete-select-items", cache_remove_items)

                self.update_item_index()

                self.update_item_widths()

                self.update_vadjustment()

                self.emit("items-change")

    def clear(self):
        '''
        Clear operation, same as function `delete_all_items`.
        '''
        self.delete_all_items()

    def delete_all_items(self):
        '''
        Delete all items.
        '''
        if len(self.visible_items) > 0:
            self.start_select_row = None
            self.select_rows = []

            self.set_items([])

            self.update_item_index()

            self.update_item_widths()

            self.update_vadjustment()

    def update_vadjustment(self):
        vadjust_height = sum(map(lambda i: i.get_height(), self.visible_items))
        self.draw_area.set_size_request(-1, vadjust_height)
        vadjust = self.scrolled_window.get_vadjustment()
        if vadjust.get_upper() != vadjust_height and self.scrolled_window.allocation.height < vadjust_height:
            vadjust.set_upper(vadjust_height)

    def expose_tree_view(self, widget):
        '''
        Internal callback to handle `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)

        # Update adjustment.
        self.update_vadjustment()

        # Draw background on widget cairo.
        self.draw_background(widget, cr)

        # # Draw background mask on widget cairo.
        vadjust = self.scrolled_window.get_vadjustment()
        vadjust_value = int(vadjust.get_value())
        hadjust = self.scrolled_window.get_hadjustment()
        hadjust_value = int(hadjust.get_value())
        self.draw_mask(cr, hadjust_value, vadjust_value, self.scrolled_window.allocation.width, self.scrolled_window.allocation.height)

        # We need clear render surface every time.
        with cairo_state(self.render_surface_cr):
            self.render_surface_cr.set_operator(cairo.OPERATOR_CLEAR)
            self.render_surface_cr.paint()

        # Draw items on render surface.
        if len(self.visible_items) > 0:
            self.draw_items(rect, self.render_surface_cr)

        # Draw bound mask.
        width = self.scrolled_window.allocation.width
        height = self.scrolled_window.allocation.height
        vadjust_value = int(self.scrolled_window.get_vadjustment().get_value())
        vadjust_upper = int(self.scrolled_window.get_vadjustment().get_upper())
        vadjust_page_size = int(self.scrolled_window.get_vadjustment().get_page_size())
        hadjust_value = int(self.scrolled_window.get_hadjustment().get_value())

        if vadjust_value == 0:
            with cairo_state(cr):
                cr.rectangle(hadjust_value, vadjust_value, width, self.mask_bound_height)
                cr.clip()
                cr.set_source_surface(self.render_surface, hadjust_value, vadjust_value)
                cr.paint()
        elif self.mask_bound_height > 0:
            i = 0
            while (i <= self.mask_bound_height):
                with cairo_state(cr):
                    cr.rectangle(hadjust_value, vadjust_value + i, width, 1)
                    cr.clip()

                    cr.set_source_surface(self.render_surface, hadjust_value, vadjust_value)
                    cr.paint_with_alpha(math.sin(i * math.pi / 2 / self.mask_bound_height))

                i += 1

        with cairo_state(cr):
            cr.rectangle(hadjust_value, vadjust_value + self.mask_bound_height, width, height - self.mask_bound_height * 2)
            cr.clip()
            cr.set_source_surface(self.render_surface, hadjust_value, vadjust_value)
            cr.paint()

        if vadjust_value + vadjust_page_size == vadjust_upper:
            with cairo_state(cr):
                cr.rectangle(hadjust_value, vadjust_value + height - self.mask_bound_height, width, self.mask_bound_height)
                cr.clip()
                cr.set_source_surface(self.render_surface, hadjust_value, vadjust_value)
                cr.paint()
        elif self.mask_bound_height > 0:
            i = 0
            while (i < self.mask_bound_height):
                with cairo_state(cr):
                    cr.rectangle(hadjust_value, vadjust_value + height - self.mask_bound_height + i, width, 1)
                    cr.clip()
                    cr.set_source_surface(self.render_surface, hadjust_value, vadjust_value)
                    cr.paint_with_alpha(1.0 - (math.sin(i * math.pi / 2 / self.mask_bound_height)))

                i += 1

        return False

    def draw_background(self, widget, cr):
        with cairo_state(cr):
            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            (offset_x, offset_y) = self.draw_area.translate_coordinates(self.draw_area.get_toplevel(), 0, 0)
            vadjust = self.scrolled_window.get_vadjustment()
            vadjust_value = int(vadjust.get_value())
            hadjust = self.scrolled_window.get_hadjustment()
            hadjust_value = int(hadjust.get_value())

            x = shadow_x - offset_x
            y = shadow_y - offset_y

            cr.rectangle(hadjust_value, vadjust_value, self.scrolled_window.allocation.width, self.scrolled_window.allocation.height)
            cr.clip()
            cr.translate(x, y)
            skin_config.render_background(cr, widget, 0, 0)

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

    def draw_items(self, rect, cr):
        with cairo_state(cr):
            vadjust_value = int(self.scrolled_window.get_vadjustment().get_value())
            hadjust_value = int(self.scrolled_window.get_hadjustment().get_value())

            # Draw items.
            (start_row, end_row, item_height_count) = self.get_expose_bound()

            column_widths = self.get_column_widths()

            for item in self.visible_items[start_row:end_row]:
                item_width_count = 0
                for (index, column_width) in column_widths:
                    render_x = rect.x + item_width_count - hadjust_value
                    render_y = rect.y + item_height_count - vadjust_value
                    render_width = column_width
                    render_height = item.get_height()

                    # Draw on drawing area cairo.
                    with cairo_state(cr):
                        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
                        cr.clip()

                        with cairo_state(cr):
                            cr.rectangle(render_x, render_y, render_width, render_height)
                            cr.clip()

                            item.get_column_renders()[index](cr, gtk.gdk.Rectangle(render_x, render_y, render_width, render_height))

                    item_width_count += column_width

                item_height_count += item.get_height()

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
        self.draw_area.grab_focus()

        if is_left_button(event):
            self.left_button_press = True
            self.click_item(event)
        elif is_right_button(event):
            self.left_button_press = False
            self.click_item(event)

    def click_item(self, event):
        cell = self.get_cell_with_event(event)
        if cell != None:
            (click_row, click_column, offset_x, offset_y) = cell

            if self.left_button_press:
                if click_row == None:
                    self.unselect_all()
                else:
                    if self.press_shift and self.enable_multiple_select:
                        self.shift_click(click_row)
                    elif self.press_ctrl and self.enable_multiple_select:
                        self.ctrl_click(click_row)
                    else:
                        if self.enable_drag_drop and click_row in self.select_rows:
                            self.start_drag = True

                            # Record press_in_select_rows, disable select rows if mouse not move after release button.
                            self.press_in_select_rows = click_row
                        else:
                            self.start_drag = False
                            self.start_select_row = click_row
                            self.set_select_rows([click_row])
                            self.emit("button-press-item", self.visible_items[click_row], click_column, offset_x, offset_y)
                            self.visible_items[click_row].button_press(click_column, offset_x, offset_y)

                if is_double_click(event):
                    self.double_click_row = copy.deepcopy(click_row)
                elif is_single_click(event):
                    self.single_click_row = copy.deepcopy(click_row)
            else:
                '''
                TODO: right_button press
                '''
                right_press_row = self.get_event_row(event)
                if right_press_row == None:
                    self.start_select_row = None
                    self.select_rows = []
                    self.queue_draw()
                elif right_press_row not in self.select_rows or self.start_select_row == None:
                    self.start_select_row = right_press_row
                    self.set_select_rows([right_press_row])
                    self.queue_draw()

                if self.start_select_row == None:
                    current_item = None
                else:
                    current_item = self.visible_items[self.start_select_row]

                select_items = []
                for row in self.select_rows:
                    select_items.append(self.visible_items[row])

                (wx, wy) = self.window.get_root_origin()
                (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)
                self.emit("right-press-items",
                          event.x_root,
                          event.y_root,
                          current_item,
                          select_items)
        else:
            '''
            TODO: some app wanna know the blank area right click x && y value
            '''
            if not self.left_button_press:
                self.emit("right-press-items", event.x_root, event.y_root, None, None)

    def shift_click(self, click_row):
        if self.select_rows == [] or self.start_select_row == None:
            self.start_select_row = click_row
            select_rows = [click_row]
        else:
            if len(self.select_rows) == 1:
                self.start_select_row = self.select_rows[0]

            if click_row < self.start_select_row:
                select_rows = range(click_row, self.start_select_row + 1)
            elif click_row > self.start_select_row:
                select_rows = range(self.start_select_row, click_row + 1)
            else:
                select_rows = [click_row]

        self.set_select_rows(select_rows)

    def ctrl_click(self, click_row):
        if click_row in self.select_rows:
            self.select_rows.remove(click_row)
            self.visible_items[click_row].unselect()
        else:
            self.start_select_row = click_row
            self.select_rows.append(click_row)
            self.visible_items[click_row].select()

    def unselect_all(self):
        '''
        Unselect all items.
        '''
        self.set_select_rows([])

    def button_release_tree_view(self, widget, event):
        if is_left_button(event):
            self.left_button_press = False
            self.release_item(event)

        # Remove auto scroll handler.
        remove_timeout_id(self.auto_scroll_id)

    def release_item(self, event):
        if is_left_button(event):
            cell = self.get_cell_with_event(event)
            if cell != None:
                (release_row, release_column, offset_x, offset_y) = cell

                if release_row != None:
                    if self.double_click_row == release_row:
                        self.emit("double-click-item", self.visible_items[release_row], release_column, offset_x, offset_y)
                        self.visible_items[release_row].double_click(release_column, offset_x, offset_y)
                    elif self.single_click_row == release_row:
                        self.emit("single-click-item", self.visible_items[release_row], release_column, offset_x, offset_y)
                        self.visible_items[release_row].single_click(release_column, offset_x, offset_y)

                if self.start_drag:
                    if self.is_in_visible_area(event):
                        self.drag_select_items_at_cursor()
                else:
                    if hasattr(self.visible_items[release_row], "button_release"):
                        self.visible_items[release_row].button_release(release_column, offset_x, offset_y)

                self.double_click_row = None
                self.single_click_row = None
                self.start_drag = False

                # Disable select rows when press_in_select_rows valid after button release.
                if self.press_in_select_rows:
                    self.set_select_rows([self.press_in_select_rows])
                    self.start_select_row = self.press_in_select_rows
                    self.press_in_select_rows = None

                self.set_drag_row(None)

    def is_in_visible_area(self, event):
        '''
        Is event coordinate in visible area.

        @param event: gtk.gdk.Event.

        @return: Return True if event coordinate in visible area.
        '''
        (event_x, event_y) = get_event_coords(event)
        vadjust = self.scrolled_window.get_vadjustment()
        return (-self.start_drag_offset <= event_x <= self.scrolled_window.allocation.width + self.start_drag_offset
                and vadjust.get_value() - self.start_drag_offset <= event_y <= vadjust.get_value() + vadjust.get_page_size() + self.start_drag_offset)

    def set_drag_row(self, row):
        if self.drag_reference_row != row:
            # Clear drag row.
            if self.drag_item != None:
                self.drag_item.draw_drag_line(False)

            # Draw new drag row.
            if row != None:
                if row < len(self.visible_items):
                    drag_line_at_bottom = False
                    self.drag_item = self.visible_items[row]
                else:
                    drag_line_at_bottom = True
                    self.drag_item = self.visible_items[-1]

                self.drag_item.draw_drag_line(True, drag_line_at_bottom)
            else:
                self.drag_item = None

            # Update drag row.
            self.drag_reference_row = row

    def drag_select_items_at_cursor(self):
        '''
        Internal function to drag select items at cursor position.
        '''
        if self.drag_reference_row != None:
            select_items = map(lambda row: self.visible_items[row], self.select_rows)
            before_items = self.visible_items[:self.drag_reference_row]
            after_items = self.visible_items[self.drag_reference_row::]

            for item in select_items:
                if item in before_items:
                    before_items.remove(item)

                if item in after_items:
                    after_items.remove(item)

            self.set_items(before_items + select_items + after_items)

            self.select_rows = range(len(before_items), len(before_items + select_items))

            self.update_item_index()

            self.queue_draw()

    def motion_tree_view(self, widget, event):
        self.hover_item(event)

        # Disable press_in_select_rows once move mouse.
        self.press_in_select_rows = None

    def hover_item(self, event):

        if self.left_button_press:
            if self.start_drag:
                if self.enable_drag_drop:
                    if self.is_in_visible_area(event):
                        self.auto_scroll_tree_view(event)

                        self.set_drag_row(self.get_drag_row(get_event_coords(event)[1]))
                    else:
                        # Begin drag is drag_data is not None.
                        if self.drag_data:
                            (targets, actions, button) = self.drag_data
                            self.drag_begin(targets, actions, button, event)

                        self.set_drag_row(None)
            else:
                if self.enable_multiple_select and (not self.press_ctrl and not self.press_shift):
                    # Get hover row.
                    hover_row = self.get_event_row(event)

                    # Highlight drag area.
                    if hover_row != None and self.start_select_row != None:
                        # Update select area.
                        if hover_row > self.start_select_row:
                            select_rows = range(self.start_select_row, hover_row + 1)
                        elif hover_row < self.start_select_row:
                            select_rows = range(hover_row, self.start_select_row + 1)
                        else:
                            select_rows = [hover_row]

                        # Scroll viewport when cursor almost reach bound of viewport.
                        self.auto_scroll_tree_view(event)

                        self.set_select_rows(select_rows)
        else:
            if self.enable_hover:
                cell = self.get_cell_with_event(event)
                if cell != None:
                    (hover_row, hover_column, offset_x, offset_y) = cell

                    if self.hover_row != hover_row:
                        if self.hover_row != None:
                            if self.hover_row < len(self.visible_items):
                                self.visible_items[self.hover_row].unhover(hover_column, offset_x, offset_y)

                        self.hover_row = hover_row

                        if self.hover_row != None:
                            self.visible_items[self.hover_row].hover(hover_column, offset_x, offset_y)

        cell = self.get_cell_with_event(event)
        if cell != None:
            (motion_row, motion_column, offset_x, offset_y) = cell

            if hasattr(self.visible_items[motion_row], "motion_notify"):
                self.visible_items[motion_row].motion_notify(motion_column, offset_x, offset_y)

            self.emit("motion-notify-item", self.visible_items[motion_row], motion_column, offset_x, offset_y)
        else:
            self.emit("motion-notify-item", None, 0, 0, 0)

    def auto_scroll_tree_view(self, event):
        '''
        Internal function to scroll list view automatically.
        '''
        # Remove auto scroll handler.
        remove_timeout_id(self.auto_scroll_id)

        vadjust = self.scrolled_window.get_vadjustment()
        if event.y > vadjust.get_value() + vadjust.get_page_size() - 2 * self.AUTO_SCROLL_HEIGHT:
            self.auto_scroll_id = gobject.timeout_add(self.auto_scroll_delay, lambda : self.auto_scroll_tree_view_down(vadjust))
        elif event.y < vadjust.get_value() + 2 * self.AUTO_SCROLL_HEIGHT:
            self.auto_scroll_id = gobject.timeout_add(self.auto_scroll_delay, lambda : self.auto_scroll_tree_view_up(vadjust))

    def get_drag_row(self, drag_y):
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
        if drag_y >= offset_y + self.scrolled_window.get_vadjustment().get_page_size():
            return len(self.visible_items)
        else:
            return self.get_row_with_coordinate(drag_y)

    def auto_scroll_tree_view_down(self, vadjust):
        '''
        Internal function to scroll list view down automatically.
        '''
        vadjust.set_value(min(vadjust.get_value() + self.AUTO_SCROLL_HEIGHT,
                              vadjust.get_upper() - vadjust.get_page_size()))

        if self.start_drag:
            self.set_drag_row(self.get_drag_row(self.draw_area.get_pointer()[1]))
        else:
            self.update_select_rows(self.get_row_with_coordinate(self.draw_area.get_pointer()[1]))

        return True

    def auto_scroll_tree_view_up(self, vadjust):
        '''
        Internal function to scroll list view up automatically.
        '''
        vadjust.set_value(max(vadjust.get_value() - self.AUTO_SCROLL_HEIGHT,
                              vadjust.get_lower()))

        if self.start_drag:
            self.set_drag_row(self.get_drag_row(self.draw_area.get_pointer()[1]))
        else:
            self.update_select_rows(self.get_row_with_coordinate(self.draw_area.get_pointer()[1]))

        return True

    def update_select_rows(self, hover_row):
        '''
        Internal function to update select rows.
        '''
        hover_row = self.get_row_with_coordinate(self.draw_area.get_pointer()[1])

        # Update select area.
        if hover_row != None and self.start_select_row != None:
            if hover_row > self.start_select_row:
                select_rows = range(self.start_select_row, hover_row + 1)
            elif hover_row < self.start_select_row:
                select_rows = range(hover_row, self.start_select_row + 1)
            else:
                select_rows = [hover_row]

            self.set_select_rows(select_rows)

    def key_press_tree_view(self, widget, event):
        if has_ctrl_mask(event):
            self.press_ctrl = True

        if has_shift_mask(event):
            self.press_shift = True

        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

        return True

    def key_release_tree_view(self, widget, event):
        '''
        Internal callback for `key-release-event` signal.

        @param widget: ListView widget.
        @param event: Key release event.
        '''
        if has_ctrl_mask(event):
            self.press_ctrl = False

        if has_shift_mask(event):
            self.press_shift = False

    def size_allocated_tree_view(self, widget, rect):
        self.update_item_widths()

        # Cairo temp surface.
        try:
            self.render_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.scrolled_window.allocation.width, self.scrolled_window.allocation.height)
            self.render_surface_cr = gtk.gdk.CairoContext(cairo.Context(self.render_surface))
        except Exception:
            pass

    def leave_tree_view(self, widget, event):
        if len(self.visible_items) > 0:
            self.unhover_row()

        # Rest.
        self.left_button_press = False

    def focus_out_tree_view(self, widget, event):
        self.left_button_press = False

    def unhover_row(self):
        if self.hover_row != None:
            if 0 <= self.hover_row < len(self.visible_items):
                self.visible_items[self.hover_row].unhover(0, 0, 0)
            self.hover_row = None

    def set_hover_row(self, index):
        self.unhover_row()
        if 0 <= index < len(self.visible_items):
            self.visible_items[index].hover(0, 0, 0)
            self.hover_row = index

    def get_event_row(self, event, offset_index=0):
        '''
        Get row at event.

        @param event: gtk.gdk.Event instance.
        @param offset_index: Offset index base on event row.
        @return: Return row at event coordinate, return None if haven't any row match event coordinate.
        '''
        (event_x, event_y) = get_event_coords(event)
        return self.get_row_with_coordinate(event_y)

    def set_hide_columns(self, hide_columns):
        '''
        Set the hide columns.

        @param hide_columns: The columns need to hide.
        '''
        self.hide_columns = hide_columns
        if self.hide_columns != None:
            if self.expand_column != None:
                if self.expand_column in self.hide_columns:
                    self.hide_columns.remove(self.expand_column)

        self.update_item_widths()
        self.queue_draw()

    def set_expand_column(self, column):
        '''
        Set expand column.

        @param column: The column to expand.
        '''
        self.expand_column = column
        if self.hide_columns != None:
            if column in self.hide_columns:
                self.hide_columns.remove(column)
        self.update_item_widths()
        self.queue_draw()

    def get_column_widths(self):
        '''
        Get the width of columns.

        @return: Return the all columns' width.
        '''
        rect = self.draw_area.allocation
        column_widths = []

        fixed_width_count = 0
        for index, column_width in enumerate(self.column_widths):
            if self.hide_columns != None:
                if index != self.expand_column and index not in self.hide_columns:
                    fixed_width_count += column_width
            else:
                if index != self.expand_column:
                    fixed_width_count += column_width

        for index, column_width in enumerate(self.column_widths):
            if index == self.expand_column:
                column_widths.append((index, rect.width - fixed_width_count))
            else:
                if self.hide_columns != None:
                    if index not in self.hide_columns:
                        column_widths.append((index, column_width))
                else:
                    column_widths.append((index, column_width))
        return column_widths

    def get_cell_with_event(self, event):
        (event_x, event_y) = get_event_coords(event)

        item_height_count = 0
        item_index_count = 0
        for item in self.visible_items:
            if item_height_count <= event_y <= item_height_count + item.get_height():
                event_row = item_index_count
                offset_y = event_y - item_height_count
                (event_column, offset_x) = get_disperse_index(zip(*self.get_column_widths())[-1], event_x)
                return (event_row, event_column, offset_x, offset_y)

            item_height_count += item.get_height()
            item_index_count += 1

        return None

    def get_row_with_coordinate(self, y):
        item_height_count = 0
        item_index_count = 0
        for item in self.visible_items:
            if item_height_count <= y <= item_height_count + item.get_height():
                return item_index_count

            item_height_count += item.get_height()
            item_index_count += 1

        return None

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

    @contextmanager
    def keep_select_status(self):
        '''
        Handy function that change listview and keep select status not change.
        '''
        # Save select items.
        start_select_item = None
        if self.start_select_row != None:
            start_select_item = self.visible_items[self.start_select_row]

        select_items = []
        for row in self.select_rows:
            select_items.append(self.visible_items[row])

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

                for (index, item) in enumerate(self.visible_items):
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

    def visible_highlight(self):
        '''
        Make highlight item in visible area.
        '''
        self.visible_highlight_item()

    def visible_highlight_item(self):
        '''
        Make highlight item in visible area.
        '''
        self.visible_item(self.highlight_item)

    def visible_item(self, item):
        '''
        Make item in visible area.

        @param item: The item need to visible.
        '''
        if item != None and item in self.visible_items:
            # Get coordinates.
            item_height = item.get_height()
            item_top = sum(map(lambda i: i.get_height(), self.visible_items[:item.row_index]))
            item_bottom = item_top + item_height
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self.draw_area)
            vadjust = self.scrolled_window.get_vadjustment()
            visible_area_top = vadjust.get_value()
            visible_area_bottom = vadjust.get_value() + vadjust.get_page_size()

            # Get height of previous item.
            if 0 < item.row_index <= len(self.visible_items) - 1:
                prev_item_height = self.visible_items[item.row_index - 1].get_height()
            else:
                prev_item_height = 0

            # Get height of next item.
            if 0 <= item.row_index < len(self.visible_items) - 1:
                next_item_height = self.visible_items[item.row_index + 1].get_height()
            else:
                next_item_height = 0

            # Make item in visible area.
            if item_top <= visible_area_top:
                vadjust.set_value(max(item_top - prev_item_height, vadjust.get_lower()))
            elif item_bottom >= visible_area_bottom:
                vadjust.set_value(item_bottom + next_item_height - vadjust.get_page_size())

    def get_highlight_item(self):
        '''
        Get highlight item.

        @return: Return highlight item.
        '''
        return self.highlight_item

    def set_highlight_item(self, item):
        '''
        Set highlight item.

        @param item: The item need to highlight.
        '''
        if self.enable_highlight and item != None:
            if self.highlight_item:
                if hasattr(self.highlight_item, "unhighlight"):
                    self.highlight_item.unhighlight()

            if hasattr(item, "highlight"):
                self.highlight_item = item
                self.highlight_item.highlight()
                try:
                    self.select_rows.append(self.visible_items.index(self.highlight_item))
                except: pass

                self.queue_draw()

    def clear_highlight(self):
        '''
        Clear highlight.
        '''
        if self.highlight_item and hasattr(self.highlight_item, "unhighlight"):
            self.highlight_item.unhighlight()
            self.highlight_item = None

            self.queue_draw()

gobject.type_register(TreeView)

class TreeItem(gobject.GObject):
    '''
    Tree item template use for L{ I{TreeView} <TreeView>}.

    This class just provide the interface that TreeView item need implement.
    Normal, you shouldn't use this class directly, instead you should use item that base on NodeItem,
    NodeItem provide more simple apis than TreeItem.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        '''
        Initialize TreeItem class.
        '''
        gobject.GObject.__init__(self)
        self.parent_item = None
        self.child_items = None
        self.row_index = None
        self.column_index = None
        self.redraw_request_callback = None
        self.add_items_callback = None
        self.delete_items_callback = None
        self.is_select = False
        self.is_hover = False
        self.is_expand = False
        self.is_highlight = False
        self.drag_line = False
        self.drag_line_at_bottom = False
        self.column_offset = 0
        self.height = None

    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.

        This is TreeView interface, you should implement it.
        '''
        self.emit("redraw-request")

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

    def unhover(self, column, offset_x, offset_y):
        pass

    def hover(self, column, offset_x, offset_y):
        pass

    def motion_notify(self, column, offset_x, offset_y):
        pass

    def button_press(self, column, offset_x, offset_y):
        pass

    def button_release(self, column, offset_x, offset_y):
        pass

    def single_click(self, column, offset_x, offset_y):
        pass

    def double_click(self, column, offset_x, offset_y):
        pass

    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        pass

    def highlight(self):
        pass

    def unhighlight(self):
        pass

    def release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is TreeView interface, you should implement it.

        @return: Return True if do release work, otherwise return False.

        When this function return True, TreeView will call function gc.collect() to release object to release memory.
        '''
        return False

gobject.type_register(TreeItem)

class NodeItem(TreeItem):
    '''
    NodeItem class to provide basic attribute of treeview node.
    '''

    def __init__(self):
        '''
        Initialize NodeItem class.
        '''
        TreeItem.__init__(self)

    def add_items(self, items):
        for item in items:
            item.column_index = self.column_index + 1
            item.parent_item = self

        if self.child_items == None:
            self.child_items = items
        else:
            self.child_items += items

    def double_click(self, column, offset_x, offset_y):
        if self.is_expand:
            self.unexpand()
        else:
            self.expand()

    def expand(self):
        self.is_expand = True

        self.add_child_item()

        if self.redraw_request_callback:
            self.redraw_request_callback(self)


    def unexpand(self):
        self.is_expand = False

        self.delete_chlid_item()

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def add_child_item(self):
        if self.child_items != None and len(self.child_items) > 0:
            self.add_items_callback(self.child_items, self.row_index + 1)

    def delete_chlid_item(self):
        if self.child_items != None:
            for child_item in self.child_items:
                if child_item.is_expand:
                    child_item.unexpand()

            self.delete_items_callback(self.child_items)

    def unselect(self):
        self.is_select = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def select(self):
        self.is_select = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhighlight(self):
        self.is_highlight = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def highlight(self):
        self.is_highlight = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(NodeItem)

def get_background_color(is_highlight, is_select, is_hover):
    if is_highlight:
        return "globalItemHighlight"
    elif is_select:
        return "globalItemSelect"
    elif is_hover:
        return "globalItemHover"
    else:
        return None

def get_text_color(is_select):
    if is_select:
        return ui_theme.get_color("label_select_text").get_color()
    else:
        return ui_theme.get_color("label_text").get_color()

def draw_background(item, cr, rect):
    # Draw select background.
    background_color = get_background_color(item.is_highlight, item.is_select, item.is_hover)
    if background_color:
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color(background_color).get_color()))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

class TextItem(NodeItem):
    '''
    TextItem class.
    '''

    def __init__(self, text, column_index=0):
        '''
        Initialize TextItem class.
        '''
        NodeItem.__init__(self)
        self.text = text
        self.column_index = column_index
        self.column_offset = 10
        self.text_size = DEFAULT_FONT_SIZE
        self.text_padding = 10
        self.alignment = pango.ALIGN_CENTER
        self.height = 24

    def get_height(self):
        return self.height

    def get_column_widths(self):
        return [-1]

    def get_column_renders(self):
        return [self.render_text]

    def render_text(self, cr, rect):
        # Draw select background.
        background_color = get_background_color(self.is_highlight, self.is_select, self.is_hover)
        if background_color:
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color(background_color).get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # Draw text.
        text_color = get_text_color(self.is_select)
        draw_text(cr,
                  self.text,
                  rect.x + self.text_padding + self.column_offset * self.column_index,
                  rect.y,
                  rect.width,
                  rect.height,
                  text_color=text_color,
                  text_size=self.text_size,
                  alignment=self.alignment,
                  )

gobject.type_register(TextItem)

class IconTextItem(NodeItem):
    '''
    TextItem class.
    '''

    def __init__(self,
                 text,
                 unexpand_icon_pixbufs=None,
                 expand_icon_pixbufs=None,
                 column_index=0,
                 ):
        '''
        Initialize TextItem class.
        '''
        NodeItem.__init__(self)
        self.text = text
        self.column_index = column_index
        self.column_offset = 10
        self.text_size = DEFAULT_FONT_SIZE
        self.text_padding = 10
        self.alignment = pango.ALIGN_CENTER
        self.icon_padding = 10
        self.unexpand_icon_pixbufs = unexpand_icon_pixbufs
        self.expand_icon_pixbufs = expand_icon_pixbufs
        self.height = 24

    def get_height(self):
        return self.height

    def get_column_widths(self):
        return [24, -1]

    def get_column_renders(self):
        return [self.render_icon,
                self.render_text]

    def render_icon(self, cr, rect):
        # Draw select background.
        background_color = get_background_color(self.is_highlight, self.is_select, self.is_hover)
        if background_color:
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color(background_color).get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # Draw icon.
        if self.is_expand:
            pixbufs = self.expand_icon_pixbufs
        else:
            pixbufs = self.unexpand_icon_pixbufs
        if self.unexpand_icon_pixbufs:
            (normal_dpixbuf, hover_dpixbuf) = pixbufs
            if self.is_select:
                pixbuf = hover_dpixbuf.get_pixbuf()
            else:
                pixbuf = normal_dpixbuf.get_pixbuf()
            draw_pixbuf(cr,
                        pixbuf,
                        rect.x + self.icon_padding + self.column_offset * self.column_index,
                        rect.y + (rect.height - pixbuf.get_height()) / 2,
                        )

    def render_text(self, cr, rect):
        # Draw select background.
        background_color = get_background_color(self.is_highlight, self.is_select, self.is_hover)
        if background_color:
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color(background_color).get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # Draw text.
        text_color = get_text_color(self.is_select)
        draw_text(cr,
                  self.text,
                  rect.x + self.text_padding + self.column_offset * self.column_index,
                  rect.y,
                  rect.width,
                  rect.height,
                  text_color=text_color,
                  text_size=self.text_size,
                  alignment=self.alignment,
                  )

gobject.type_register(IconTextItem)
