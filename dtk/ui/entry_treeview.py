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

from treeview import TreeView, TreeItem
from draw import draw_text
from utils import color_hex_to_cairo, is_left_button, is_right_button
from entry import EntryBuffer, Entry
import gobject
import gtk

class EntryTreeView(TreeView):
    '''
    EntryTreeView class.

    @undocumented: button_press
    @undocumented: button_release
    @undocumented: motion_notify
    @undocumented: double_click
    @undocumented: edit_done
    @undocumented: entry_focus_changed
    @undocumented: release_item
    '''

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
                 mask_bound_height=12,
                 right_space=0,
                 top_bottom_space=3,
                 ):
        '''
        Initialize EntryTreeView class.

        @param items: Items for EntryTreeView, default is empty list.
        @param drag_data: Data use for DND, format is (targets, actions, button)
         - targets: the list of targets supported by the widget drag
         - actions: the allowed drag operations for the drag
         - button: the button the user pressed to start the drag
        @param enable_hover: Whether support hover action, default is False.
        @param enable_highlight: Whether support highlight action, default is True.
        @param enable_multiple_select: Whether support multiple selection, default is False.
        @param enable_drag_drop: Whether support DND, default is False.
        @param drag_icon_pixbuf: The icon when drag items.
        @param start_drag_offset: The offset to trigger drag action.
        @param mask_bound_height: The height of mask bound.
        @param right_space: Right space, default is 0.
        @param top_bottom_space: Vertical space, default is 3.
        '''
        super(EntryTreeView, self).__init__(
            items, drag_data, enable_hover,
            enable_highlight, enable_multiple_select,
            enable_drag_drop, drag_icon_pixbuf,
            start_drag_offset, mask_bound_height,
            right_space, top_bottom_space)

        self.connect("double-click", self.double_click)
        self.draw_area.connect("button-press-event", self.button_press)
        self.draw_area.connect("button-release-event", self.button_release)
        self.draw_area.connect("motion-notify-event", self.motion_notify)

    def button_press(self, widget, event):
        if self.get_data("entry_widget") is None:
            return
        cell = self.get_cell_with_event(event)
        entry = self.get_data("entry_widget")
        item = entry.get_data("item")
        # if pressed outside entry column area, destroy entry
        if cell is None:
            entry.get_parent().destroy()
            return
        (row, column, offset_x, offset_y) = cell
        if self.visible_items[row] != item or column != item.ENTRY_COLUMN:
            entry.get_parent().destroy()
            return
        # right button the show menu
        if is_right_button(event):
            entry.right_menu.show((int(event.x_root), int(event.y_root)))
            return
        entry.set_data("button_press", True)
        send_event = event.copy()
        send_event.send_event = True
        send_event.x = float(offset_x)
        send_event.y = 1.0
        send_event.window = entry.window
        entry.event(send_event)
        send_event.free()

    def button_release(self, widget, event):
        if self.get_data("entry_widget") is None:
            return
        entry = self.get_data("entry_widget")
        # has not been pressed
        if not entry.get_data("button_press"):
            return
        cell = self.get_cell_with_event(event)
        if cell is None:
            offset_x = 1
        else:
            (row, column, offset_x, offset_y) = cell
        entry.grab_focus()
        entry.set_data("button_press", False)
        send_event = event.copy()
        send_event.send_event = True
        send_event.x = float(offset_x)
        send_event.y = 1.0
        send_event.window = entry.window
        entry.event(send_event)
        send_event.free()

    def motion_notify(self, widget, event):
        if self.get_data("entry_widget") is None:
            return
        entry = self.get_data("entry_widget")
        # has not been pressed
        if not entry.get_data("button_press"):
            return
        cell = self.get_cell_with_event(event)
        item = entry.get_data("item")
        if cell is None:
            offset_x = 1
        else:
            (row, column, offset_x, offset_y) = cell
            if column != item.ENTRY_COLUMN:
                offset_x = 1
        send_event = event.copy()
        send_event.send_event = True
        send_event.x = float(offset_x)
        send_event.y = 1.0
        send_event.window = entry.window
        entry.event(send_event)
        send_event.free()

    def double_click(self, widget, item, column):
        print "DEBUG double_click"
        if not column == item.ENTRY_COLUMN:
            return
        if item.entry:
            item.entry.grab_focus()
            return
        item.entry_buffer.set_property('cursor-visible', True)
        hbox = gtk.HBox(False)
        align = gtk.Alignment(0, 0, 1, 1)
        entry = Entry()
        entry.set_data("item", item)
        entry.set_data("button_press", False)
        entry.set_buffer(item.entry_buffer)
        entry.set_size_request(item.get_column_widths()[column]-4, 0)
        entry.connect("press-return", lambda w: hbox.destroy())
        entry.connect("destroy", self.edit_done, hbox, item)
        entry.connect_after("focus-in-event", self.entry_focus_changed, item)
        entry.connect_after("focus-out-event", self.entry_focus_changed, item)
        self.pack_start(hbox, False, False)
        self.set_data("entry_widget", entry)
        hbox.pack_start(entry, False, False)
        hbox.pack_start(align)
        hbox.show_all()
        entry.set_can_focus(True)
        entry.grab_focus()
        entry.select_all()
        item.entry = entry

    def edit_done(self, entry, box, item):
        item.entry = None
        item.entry_buffer.set_property('cursor-visible', False)
        item.entry_buffer.move_to_start()
        item.redraw_request_callback(item)
        self.draw_area.grab_focus()
        self.set_data("entry_widget", None)

    def entry_focus_changed(self, entry, event, item):
        if event.in_:
            item.entry_buffer.set_property('cursor-visible', True)
        else:
            item.entry_buffer.set_property('cursor-visible', False)

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
                        self.emit("single-click-item", self.visible_items[release_row], release_column, offset_x, offset_y)

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
    '''
    EntryTreeItem class.

    @undocumented: entry_buffer_changed
    @undocumented: get_height
    @undocumented: get_column_widths
    @undocumented: get_column_renders
    @undocumented: render_title
    @undocumented: render_content
    @undocumented: unselect
    @undocumented: select
    @undocumented: hover
    @undocumented: unhover
    @undocumented: single_click
    @undocumented: double_click
    @undocumented: expand
    @undocumented: unexpand
    '''

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
