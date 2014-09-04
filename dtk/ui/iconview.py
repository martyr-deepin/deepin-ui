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

import cairo
import math
from draw import draw_vlinear, draw_text
from keymap import get_keyevent_name
from skin_config import skin_config
from theme import ui_theme
from locales import _
import gc
import gobject
import gtk
from utils import (get_match_parent, cairo_state, get_event_coords,
                   is_left_button, is_double_click, is_right_button,
                   is_single_click, get_window_shadow_size, get_content_size)

class IconView(gtk.DrawingArea):
    '''
    Icon view.

    @undocumented: realize_icon_view
    @undocumented: button_release_scrolled_window
    @undocumented: size_allocated_icon_view
    @undocumented: expose_icon_view
    @undocumented: motion_icon_view
    @undocumented: icon_view_get_event_index
    @undocumented: button_press_icon_view
    @undocumented: button_release_icon_view
    @undocumented: leave_icon_view
    @undocumented: key_press_icon_view
    @undocumented: key_release_icon_view
    @undocumented: update_redraw_request_list
    @undocumented: redraw_item
    @undocumented: get_offset_coordinate
    @undocumented: get_render_item_indexes
    @undocumented: get_render_item_info
    @undocumented: return_item
    @undocumented: draw_background
    @undocumented: draw_items
    @undocumented: draw_row_mask
    '''

    __gsignals__ = {
        "items-change" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "lost-focus-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "motion-notify-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "motion-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "highlight-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "normal-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "button-press-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "button-release-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
        "right-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, int, int)),
    }

    def __init__(self,
                 padding_x=0,
                 padding_y=0,
                 mask_bound_height=12,
                 ):
        '''
        Initialize IconView class.

        @param padding_x: Horizontal padding value.
        @param padding_y: Vertical padding value.
        @param mask_bound_height: The height of mask bound, default is 12 pixels.
        '''
        # Init.
        gtk.DrawingArea.__init__(self)
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.mask_bound_height = mask_bound_height
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.items = []
        self.focus_index = None
        self.highlight_item = None
        self.double_click_item = None
        self.single_click_item = None
        self.right_click_item = None
        self.is_loading = False

        # Signal.
        self.connect("realize", self.realize_icon_view)
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        self.connect("size-allocate", self.size_allocated_icon_view)
        self.connect("expose-event", self.expose_icon_view)
        self.connect("motion-notify-event", self.motion_icon_view)
        self.connect("button-press-event", self.button_press_icon_view)
        self.connect("button-release-event", self.button_release_icon_view)
        self.connect("leave-notify-event", self.leave_icon_view)
        self.connect("key-press-event", self.key_press_icon_view)

        # Add item singal.
        self.connect("lost-focus-item", lambda view, item: item.icon_item_lost_focus())
        self.connect("motion-notify-item", lambda view, item, x, y: item.icon_item_motion_notify(x, y))
        self.connect("highlight-item", lambda view, item: item.icon_item_highlight())
        self.connect("normal-item", lambda view, item: item.icon_item_normal())
        self.connect("button-press-item", lambda view, item, x, y: item.icon_item_button_press(x, y))
        self.connect("button-release-item", lambda view, item, x, y: item.icon_item_button_release(x, y))
        self.connect("single-click-item", lambda view, item, x, y: item.icon_item_single_click(x, y))
        self.connect("double-click-item", lambda view, item, x, y: item.icon_item_double_click(x, y))

        # Redraw.
        self.redraw_request_list = []
        self.redraw_delay = 50 # 50 milliseconds should be enough for redraw
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)

        self.keymap = {
            "Home" : self.select_first_item,
            "End" : self.select_last_item,
            "Return" : self.return_item,
            "Up" : self.select_up_item,
            "Down" : self.select_down_item,
            "Left" : self.select_left_item,
            "Right" : self.select_right_item,
            "Page_Up" : self.scroll_page_up,
            "Page_Down" : self.scroll_page_down,
            }

    def realize_icon_view(self, widget):
        '''
        Realize icon view.
        '''
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        scrolled_window.connect("button-release-event", self.button_release_scrolled_window)

    def button_release_scrolled_window(self, widget, event):
        '''
        Internal callback for `button-release-event` signal of scrolled window.
        '''
        # Get items information.
        (item_width, item_height, columns, start_index, end_index) = self.get_render_item_info()

        # Release item resource.
        need_gc_collect = False
        for item in self.items[0:start_index] + self.items[end_index:-1]:
            if hasattr(item, "icon_item_release_resource") and item.icon_item_release_resource():
                need_gc_collect = True

        # Just do gc work when need collect.
        if need_gc_collect:
            gc.collect()

    def select_first_item(self):
        '''
        Select first item.
        '''
        if len(self.items) > 0:
            self.clear_focus_item()
            self.focus_index = 0

            self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

            # Scroll to top.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            vadjust.set_value(vadjust.get_lower())

    def select_last_item(self):
        '''
        Select last item.
        '''
        if len(self.items) > 0:
            self.clear_focus_item()
            self.focus_index = len(self.items) - 1

            self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

            # Scroll to bottom.
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

    def return_item(self):
        '''
        Do return action.

        This function will emit `double-click-item` signal.
        '''
        if self.focus_index != None:
            self.emit("double-click-item", self.items[self.focus_index], 0, 0)

    def select_up_item(self):
        '''
        Select up row item.
        '''
        if len(self.items) > 0:
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()

            if self.focus_index == None:
                self.focus_index = 0
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_lower())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)

                if self.focus_index - columns >= 0:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index -= columns
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to item.
                row = int(self.focus_index / columns)
                if vadjust.get_value() - self.padding_y > row * item_height:
                    vadjust.set_value(vadjust.get_lower() + row * item_height + self.padding_y)
                elif vadjust.get_value() - self.padding_y == row * item_height:
                    vadjust.set_value(vadjust.get_lower())

    def select_down_item(self):
        '''
        Select next row item.
        '''
        if len(self.items) > 0:
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            if self.focus_index == None:
                self.focus_index = 0
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_lower())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)

                if self.focus_index + columns <= len(self.items) - 1:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index += columns
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to item.
                row = int(self.focus_index / columns)
                if vadjust.get_value() + vadjust.get_page_size() - self.padding_y < (row + 1) * item_height:
                    vadjust.set_value(vadjust.get_lower() + (row + 1) * item_height - vadjust.get_page_size() + self.padding_y)
                elif vadjust.get_value() + vadjust.get_page_size() - self.padding_y == (row + 1) * item_height:
                    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

    def select_left_item(self):
        '''
        Select left item.
        '''
        if len(self.items) > 0:
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            if self.focus_index == None:
                self.focus_index = 0
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_lower())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
                row = int(self.focus_index / columns)
                min_index = row * columns

                if self.focus_index - 1 >= min_index:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index -= 1
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

    def select_right_item(self):
        '''
        Select right item.
        '''
        if len(self.items) > 0:
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            if self.focus_index == None:
                self.focus_index = 0
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_lower())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
                row = int(self.focus_index / columns)
                max_index = min((row + 1) * columns - 1, len(self.items) - 1)

                if self.focus_index + 1 <= max_index:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index += 1
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

    def scroll_page_up(self):
        '''
        Scroll page up of iconview.
        '''
        if len(self.items) > 0:
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            if self.focus_index == None:
                self.focus_index = 0
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_lower())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
                column = int(self.focus_index % columns)
                if (vadjust.get_value() - vadjust.get_lower()) % item_height == 0:
                    row = int((vadjust.get_value() - vadjust.get_lower() - self.padding_y) / item_height) - 1
                else:
                    row = int((vadjust.get_value() - vadjust.get_lower() - self.padding_y) / item_height)
                if row * columns + column >= 0:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index = row * columns + column
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)
                else:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index = column
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                vadjust.set_value(max(0, vadjust.get_value() - vadjust.get_page_size() + self.padding_y))

    def scroll_page_down(self):
        '''
        Scroll page down of iconview.
        '''
        if len(self.items):
            vadjust = get_match_parent(self, ["ScrolledWindow"]).get_vadjustment()
            if self.focus_index == None:
                self.focus_index = len(self.items) - 1
                self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                # Scroll to top.
                vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())
            else:
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
                column = int(self.focus_index % columns)
                if (vadjust.get_value() - vadjust.get_lower() + vadjust.get_page_size()) % item_height == 0:
                    row = int((vadjust.get_value() - vadjust.get_lower() + vadjust.get_page_size() - self.padding_y) / item_height) - 1
                else:
                    row = int((vadjust.get_value() - vadjust.get_lower() + vadjust.get_page_size() - self.padding_y) / item_height)
                if row * columns + column <= len(self.items) - 1:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index = row * columns + column
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)
                else:
                    self.emit("lost-focus-item", self.items[self.focus_index])
                    self.focus_index = (row - 1) * columns + column
                    self.emit("motion-notify-item", self.items[self.focus_index], 0, 0)

                vadjust.set_value(min(vadjust.get_upper() - vadjust.get_page_size(),
                                      vadjust.get_value() + vadjust.get_page_size() - self.padding_y))

    def set_items(self, items):
        '''
        Set items of IconView.

        @param items: The items that need set.
        '''
        if items != self.items:
            self.items = items
            self.emit("items-change")

    def add_items(self, items, insert_pos=None):
        '''
        Add items to iconview.

        @param items: A list of item that follow the rule of IconItem.
        @param insert_pos: Insert position, default is None to insert new item at B{end} position.
        '''
        if insert_pos == None:
            self.set_items(self.items + items)
        else:
            self.set_items(self.items[0:insert_pos] + items + self.items[insert_pos::])

        for item in items:
            item.connect("redraw-request", self.redraw_item)

        self.queue_draw()

    def delete_items(self, items):
        '''
        Delete items.

        @param items: Items need to remove.
        '''
        if len(items) > 0:
            match_item = False
            for item in items:
                if item in self.items:
                    self.items.remove(item)
                    match_item = True

            if match_item:
                self.emit("items-change")
                self.queue_draw()

    def clear(self):
        '''
        Clear all items.
        '''
        self.set_items([])
        self.queue_draw()

    def size_allocated_icon_view(self, widget, rect):
        # Cairo render surface.
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])

        try:
            self.render_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, scrolled_window.allocation.width, scrolled_window.allocation.height)
            self.render_surface_cr = gtk.gdk.CairoContext(cairo.Context(self.render_surface))
        except Exception:
            pass

    def set_loading(self, is_loading):
        '''
        Set loading status of icon view.

        @param is_loading: Set as True to make loading status active.
        '''
        self.is_loading = is_loading
        self.queue_draw()

    def expose_icon_view(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Update vadjustment.
        self.update_vadjustment()

        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)

        # Draw background on widget cairo.
        self.draw_background(widget, cr)

        # Draw mask on widget cairo.
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        vadjust = scrolled_window.get_vadjustment()
        vadjust_value = int(vadjust.get_value())
        hadjust = scrolled_window.get_hadjustment()
        hadjust_value = int(hadjust.get_value())
        self.draw_mask(cr, hadjust_value, vadjust_value, viewport.allocation.width, viewport.allocation.height)

        # We need clear render surface every time.
        with cairo_state(self.render_surface_cr):
            self.render_surface_cr.set_operator(cairo.OPERATOR_CLEAR)
            self.render_surface_cr.paint()

        if self.is_loading:
            load_text = _("Loading...")
            load_width, load_height = get_content_size(load_text)
            draw_text(cr,
                      load_text,
                      rect.x + (rect.width - load_width) / 2,
                      rect.y + rect.height - load_height,
                      rect.width,
                      load_height)

        # Draw items on surface cairo.
        self.draw_items(self.render_surface_cr, rect)

        # Draw bound mask.
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        width = scrolled_window.allocation.width
        height = scrolled_window.allocation.height
        vadjust_value = int(scrolled_window.get_vadjustment().get_value())
        vadjust_upper = int(scrolled_window.get_vadjustment().get_upper())
        vadjust_page_size = int(scrolled_window.get_vadjustment().get_page_size())
        hadjust_value = int(scrolled_window.get_hadjustment().get_value())

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
            scrolled_window = get_match_parent(self, ["ScrolledWindow"])
            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            (offset_x, offset_y) = self.translate_coordinates(self.get_toplevel(), 0, 0)
            vadjust = scrolled_window.get_vadjustment()
            vadjust_value = int(vadjust.get_value())
            hadjust = scrolled_window.get_hadjustment()
            hadjust_value = int(hadjust.get_value())

            x = shadow_x - offset_x
            y = shadow_y - offset_y

            cr.rectangle(hadjust_value, vadjust_value, scrolled_window.allocation.width, scrolled_window.allocation.height)
            cr.clip()
            cr.translate(x, y)
            skin_config.render_background(cr, widget, 0, 0)

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

    def draw_items(self, cr, rect):
        # Draw items.
        if len(self.items) > 0:
            with cairo_state(cr):
                scrolled_window = get_match_parent(self, ["ScrolledWindow"])
                vadjust_value = int(scrolled_window.get_vadjustment().get_value())
                hadjust_value = int(scrolled_window.get_hadjustment().get_value())

                # Draw on drawing area.
                (item_width, item_height, columns, start_index, end_index) = self.get_render_item_info()
                for (index, item) in enumerate(self.items[start_index:end_index]):
                    row = int((start_index + index) / columns)
                    column = (start_index + index) % columns
                    render_x = self.padding_x + column * item_width - hadjust_value
                    render_y = self.padding_y + row * item_height - vadjust_value

                    # Draw row background.
                    self.draw_row_mask(cr, gtk.gdk.Rectangle(render_x, render_y, rect.width, item_height), row)

                    item.row_index = row

                    with cairo_state(cr):
                        # Don't allow draw out of item area.
                        cr.rectangle(render_x, render_y, item_width, item_height)
                        cr.clip()

                        item.render(cr, gtk.gdk.Rectangle(render_x, render_y, item_width, item_height))

    def draw_row_mask(self, cr, rect, row):
        pass

    def get_render_item_info(self):
        '''
        Internal function to get information of render items.
        '''
        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)

        # Get item size.
        item_width = 1
        item_height = 1
        if len(self.items):
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])
        columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)

        # Get viewport index.
        start_y = offset_y - self.padding_y
        start_row = max(int(start_y / item_height), 0)
        start_index = start_row * columns

        end_y = offset_y - self.padding_y + viewport.allocation.height
        if end_y % item_height == 0:
            end_row = end_y / item_height - 1
        else:
            end_row = end_y / item_height
        end_index = min((end_row + 1) * columns, len(self.items))

        return (item_width, item_height, columns, start_index, end_index)

    def clear_focus_item(self):
        '''
        Clear item's focus status.
        '''
        if self.focus_index != None:
            if 0 <= self.focus_index < len(self.items):
                self.emit("lost-focus-item", self.items[self.focus_index])
            self.focus_index = None

    def motion_icon_view(self, widget, event):
        '''
        Internal callback for `motion-notify-event` signal.
        '''
        if len(self.items) > 0:
            index_info = self.icon_view_get_event_index(event)
            if index_info == None:
                self.clear_focus_item()
            else:
                (row_index, column_index, item_index, offset_x, offset_y) = index_info

                # Don't clear focus item when motion index is current one.
                '''
                TODO: it need to consider about self.focus_index == None
                      otherwisese it acts like lian lian kan
                '''
                if self.focus_index != item_index:
                    self.clear_focus_item()

                self.focus_index = item_index
                '''
                TODO: get rid of list index out of range when self.focus_index < 0
                '''
                if self.focus_index >= 0:
                    self.emit("motion-notify-item", self.items[self.focus_index], offset_x - self.padding_x, offset_y - self.padding_y)
                    self.emit("motion-item",
                              self.items[self.focus_index],
                              event.x_root - (offset_x - self.padding_x),
                              event.y_root - (offset_y - self.padding_y))

    def icon_view_get_event_index(self, event):
        '''
        Internal function to get item index at event coordinate..
        '''
        if len(self.items) > 0:
            (event_x, event_y) = get_event_coords(event)
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            scrolled_window = get_match_parent(self, ["ScrolledWindow"])
            columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
            if columns == 0:
                return None
            if len(self.items) % max(columns, 1) == 0:
                rows = int(len(self.items) / columns)
            else:
                rows = int(len(self.items) / columns) + 1

            if event_x > columns * item_width + self.padding_x:
                return None
            elif event_y > rows * item_height + self.padding_y:
                return None
            else:

                '''
                TODO: total_width % item_width is item count in the row, but when padding_x reduce the total_width,
                      event_x need to -self.padding_x
                '''
                padding_event_x = event_x - self.padding_x
                padding_event_y = event_y - self.padding_y
                if padding_event_x % item_width == 0:
                    column_index = max(padding_event_x / item_width - 1, 0)
                else:
                    column_index = min(padding_event_x / item_width, columns - 1)

                if padding_event_y % item_height == 0:
                    row_index = max(padding_event_y / item_height - 1, 0)
                else:
                    row_index = min(padding_event_y / item_height, rows - 1)

                item_index = row_index * columns + column_index
                if item_index > len(self.items) - 1:
                    return None
                else:
                    '''
                    TODO: it need to use event_x NOT padding_event_x return the item pos_x
                    '''
                    return (row_index, column_index, item_index,
                            event_x - column_index * item_width,
                            event_y - row_index * item_height)

    def button_press_icon_view(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.
        '''
        # Grab focus when button press, otherwise key-press signal can't response.
        self.grab_focus()

        if len(self.items) > 0:

            index_info = self.icon_view_get_event_index(event)

            if index_info:
                (row_index, column_index, item_index, offset_x, offset_y) = index_info

                if is_left_button(event):
                    self.emit("button-press-item", self.items[item_index], offset_x - self.padding_x, offset_y - self.padding_y)
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

                elif is_right_button(event):
                    if index_info:
                        self.right_click_item = index_info[2]
                    else:
                        self.right_click_item = None

                # Set highlight.
                if index_info:
                    self.clear_highlight()

                    self.set_highlight(self.items[index_info[2]])



    def set_highlight(self, item):
        '''
        Set highlight status with given item.

        @param item: Item need highlight.
        '''
        self.highlight_item = item
        self.emit("highlight-item", self.highlight_item)

    def clear_highlight(self):
        '''
        Clear all highlight status.
        '''
        if self.highlight_item != None:
            self.emit("normal-item", self.highlight_item)
            self.highlight_item = None

    def button_release_icon_view(self, widget, event):
        '''
        Internal callback for `button-release-event` signal.
        '''
        if len(self.items) > 0:
            index_info = self.icon_view_get_event_index(event)
            if index_info:
                (row_index, column_index, item_index, offset_x, offset_y) = index_info

                if is_left_button(event):
                    self.emit("button-release-item", self.items[item_index], offset_x - self.padding_x, offset_y - self.padding_y)

                    if self.double_click_item == item_index:
                        self.emit("double-click-item", self.items[self.double_click_item], offset_x - self.padding_x, offset_y - self.padding_y)
                    elif self.single_click_item == item_index:
                        self.emit("single-click-item", self.items[self.single_click_item], offset_x - self.padding_x, offset_y - self.padding_y)
                elif is_right_button(event):
                    if self.right_click_item == item_index:
                        self.emit("right-click-item", self.items[self.right_click_item], event.x_root, event.y_root)

            self.double_click_item = None
            self.single_click_item = None
            self.right_click_item = None

    def leave_icon_view(self, widget, event):
        '''
        Internal callback for `leave-notify` signal.
        '''
        self.clear_focus_item()

    def key_press_icon_view(self, widget, event):
        '''
        Internal callback for `key-press-event` signal.
        '''
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

        return True

    def key_release_icon_view(self, widget, event):
        '''
        Internal callback for `key-release-event` signal.
        '''
        pass

    def update_redraw_request_list(self):
        '''
        Internal function to update redraw request list.
        '''
        # Redraw when request list is not empty.
        if len(self.redraw_request_list) > 0:
            # Get offset.
            (offset_x, offset_y, viewport) = self.get_offset_coordinate(self)

            # Get viewport index.
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            scrolled_window = get_match_parent(self, ["ScrolledWindow"])
            columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)

            start_y = offset_y - self.padding_y
            start_row = max(int(start_y / item_height), 0)
            start_index = start_row * columns

            end_y = offset_y - self.padding_y + viewport.allocation.height
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
        '''
        Internal function to redraw item.
        '''
        self.redraw_request_list.append(list_item)

    def get_offset_coordinate(self, widget):
        '''
        Internal function to get offset coordinate.
        '''
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
        '''
        Update vertical adjustment.
        '''
        scrolled_window = get_match_parent(self, ["ScrolledWindow"])

        if len(self.items) > 0:
            item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
            columns = int((scrolled_window.allocation.width - self.padding_x * 2) / item_width)
            if columns > 0:
                if len(self.items) % columns == 0:
                    view_height = int(len(self.items) / columns) * item_height
                else:
                    view_height = (int(len(self.items) / columns) + 1) * item_height

                self.set_size_request(columns * item_width + self.padding_x * 2,
                                      view_height + self.padding_y * 2)
                if scrolled_window != None:
                    vadjust = scrolled_window.get_vadjustment()
                    vadjust.set_upper(max(view_height + self.padding_y * 2,
                                          scrolled_window.allocation.height))
        else:
            self.set_size_request(scrolled_window.allocation.width,
                                  scrolled_window.allocation.height)
            vadjust = scrolled_window.get_vadjustment()
            vadjust.set_upper(scrolled_window.allocation.height)

gobject.type_register(IconView)

class IconItem(gobject.GObject):
    '''
    Icon item.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        '''
        Initialize ItemIcon class.
        '''
        gobject.GObject.__init__(self)
        self.hover_flag = False
        self.highlight_flag = False

    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.

        This is IconView interface, you should implement it.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get item width.

        This is IconView interface, you should implement it.
        '''
        pass

    def get_height(self):
        '''
        Get item height.

        This is IconView interface, you should implement it.
        '''
        pass

    def render(self, cr, rect):
        '''
        Render item.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True

        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = False

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is IconView interface, you should implement it.

        @return: Return True if do release work, otherwise return False.

        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        return False

gobject.type_register(IconItem)
