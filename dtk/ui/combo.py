#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Hou ShaoHui
#
# Author:     Hou ShaoHui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
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
import pango
import gobject

from entry import Entry
from button import DisableButton
from poplist import Poplist
from theme import ui_theme
from label import Label
from treeview import TreeItem as AbstractItem
from draw import draw_text, draw_vlinear
from utils import (propagate_expose, cairo_disable_antialias,
                   color_hex_to_cairo, alpha_color_hex_to_cairo, get_content_size)
from constant import DEFAULT_FONT_SIZE

class ComboTextItem(AbstractItem):
    '''
    ComboTextItem class.

    @undocumented: get_height
    @undocumented: get_column_widths
    @undocumented: get_width
    @undocumented: get_column_renders
    @undocumented: unselect
    @undocumented: emit_redraw_request
    @undocumented: select
    @undocumented: render_title
    @undocumented: unhover
    @undocumented: hover
    '''

    def __init__(self,
                 title,
                 item_value,
                 item_width=None,
                 font_size=DEFAULT_FONT_SIZE,
                 ):
        '''
        Initialize ComboTextItem class.

        @param title: Title of item, we use this for display name (include internationalization).
        @param item_value: The value of item, use for index item in program.
        @param item_width: The width of item, default is None to calculate width with item content.
        @param font_size: Font size of item, default is DEFAULT_FONT_SIZE.
        '''
        AbstractItem.__init__(self)
        self.column_index = 0
        self.item_height = 22
        self.spacing_x = 15
        self.padding_x = 5
        self.font_size = font_size
        if item_width == None:
            self.item_width, _ = get_content_size(title, font_size)
            self.item_width += self.spacing_x * 2
        else:
            self.item_width = item_width
        self.title = title
        self.item_value = item_value

    def get_height(self):
        return self.item_height

    def get_column_widths(self):
        return (self.item_width,)

    def get_width(self):
        return self.item_width

    def get_column_renders(self):
        return (self.render_title,)

    def unselect(self):
        self.is_select = False
        self.emit_redraw_request()

    def emit_redraw_request(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def select(self):
        self.is_select = True
        self.emit_redraw_request()

    def render_title(self, cr, rect):
        font_color = ui_theme.get_color("menu_font").get_color()

        if self.is_hover:
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, ui_theme.get_shadow_color("menu_item_select").get_color_info())
            font_color = ui_theme.get_color("menu_select_font").get_color()

        draw_text(cr, self.title, rect.x + self.padding_x,
                  rect.y, rect.width - self.padding_x * 2,
                  rect.height, text_size=self.font_size,
                  text_color = font_color,
                  alignment=pango.ALIGN_LEFT)

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_redraw_request()

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.emit_redraw_request()

gobject.type_register(ComboTextItem)

class ComboList(Poplist):
    '''
    ComboList class.

    @undocumented: draw_treeview_mask
    @undocumented: reset_status
    @undocumented: hover_select_item
    @undocumented: shape_combo_list_frame
    @undocumented: expose_combo_list_frame
    '''

    def __init__(self,
                 items=[],
                 min_width=80,
                 max_width=None,
                 fixed_width=None,
                 min_height=100,
                 max_height=None):
        '''
        Initialize ComboList class.

        @param items: Initialize item list, default is empty list.
        @param min_width: The minimum width of combo list, default is 80 pixels.
        @param max_width: The maximum width of combo list, default is None to calculate maximum width with item content.
        @param fixed_width: The fixed width of combo list, default is None, set this option to fixed width and combo list won't care the width of items.
        @param min_height: The minimum height of combo list, default is 100 pixels.
        @param max_height: The maximum height of combo list, default is None.
        '''
        Poplist.__init__(self,
                         items=items,
                         min_width=min_width,
                         max_width=max_width,
                         fixed_width=fixed_width,
                         min_height=min_height ,
                         max_height=max_height,
                         shadow_visible=False,
                         shape_frame_function=self.shape_combo_list_frame,
                         expose_frame_function=self.expose_combo_list_frame,
                         align_size=2,
                         window_type=gtk.WINDOW_POPUP,
                         )

        self.treeview.draw_mask = self.draw_treeview_mask
        self.treeview.set_expand_column(0)
        self.expose_window_frame = self.expose_combo_list_frame

    def get_select_index(self):
        '''
        Get index of selected item.

        @return: Return index of selected item in combo list.
        '''
        select_rows = self.treeview.select_rows
        if len(select_rows) > 0:
            return select_rows[0]
        return 0

    def set_select_index(self, index):
        '''
        Set selected index of combo list.

        @param index: Combo list will selected item with given index.
        '''
        self.treeview.set_select_rows([index])
        self.treeview.set_hover_row(index)

    def draw_treeview_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def reset_status(self):
        self.treeview.left_button_press = False

    def hover_select_item(self):
        self.treeview.set_hover_row(self.get_select_index())

    def shape_combo_list_frame(self, widget, event):
        pass

    def expose_combo_list_frame(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(*rect)
        cr.fill()

        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("droplist_frame").get_color()))
            cr.rectangle(rect.x + 1, rect.y + 1, rect.width - 1, rect.height - 1)
            cr.stroke()

gobject.type_register(ComboList)

class ComboBox(gtk.VBox):
    '''
    ComboBox class.

    @undocumented: set_size_request
    @undocumented: auto_set_size
    @undocumented: on_drop_button_press
    @undocumented: on_combo_single_click
    @undocumented: on_focus_in_combo
    @undocumented: on_focus_out_combo
    @undocumented: items
    @undocumented: on_expose_combo_frame
    '''

    __gsignals__ = {
        "item-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
        "key-release" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
    }

    def __init__(self,
                 items=[],
                 droplist_height=None,
                 select_index=0,
                 max_width=None,
                 fixed_width=None,
                 min_width = 120,
                 min_height = 100,
                 editable=False,
                 ):
        '''
        Initialize ComboBox class.

        @param items: Init item list, default is empty list.
        @param droplist_height: The height of droplist, default is None that droplist's height will calculate with items' height automatically.
        @param select_index: Init index of selected item, default is 0.
        @param max_width: Maximum width of combobox, default is None.
        @param fixed_width: Fixed width of combobox, after you set this value combobox won't care the width of droplist and items, default is None.
        @param min_width: Minimum width of combobox, default is 120 pixels.
        @param min_height: Minimum height of combobox, default is 100 pixels.
        @param editable: Set True to make combobox can edit, default is False.
        '''
        gtk.VBox.__init__(self)
        self.set_can_focus(True)

        # Init variables.
        self.focus_flag = False
        self.select_index = select_index
        self.editable = editable
        if self.editable:
            self.padding_x = 0
        else:
            self.padding_x = 5

        self.combo_list = ComboList(min_width=min_width,
                                    max_width=max_width,
                                    fixed_width=fixed_width,
                                    min_height=min_height,
                                    max_height=droplist_height)

        self.drop_button = DisableButton(
            (ui_theme.get_pixbuf("combo/dropbutton_normal.png"),
             ui_theme.get_pixbuf("combo/dropbutton_hover.png"),
             ui_theme.get_pixbuf("combo/dropbutton_press.png"),
             ui_theme.get_pixbuf("combo/dropbutton_disable.png")),
            )
        self.drop_button_width = ui_theme.get_pixbuf("combo/dropbutton_normal.png").get_pixbuf().get_width()
        self.panel_align = gtk.Alignment()
        self.panel_align.set(0.5, 0.5, 0.0, 0.0)

        if self.editable:
            self.label = Entry()
        else:
            self.label = Label("", enable_select=False, enable_double_click=False)

            self.label.connect("button-press-event", self.on_drop_button_press)
            self.panel_align.set_padding(0, 0, self.padding_x, 0)

        self.panel_align.add(self.label)

        # Init items.
        self.add_items(items)

        # set selected index
        if len(items) > 0:
            self.set_select_index(select_index)

        hbox = gtk.HBox()
        hbox.pack_start(self.panel_align, True, False)
        hbox.pack_start(self.drop_button, False, False)
        box_align = gtk.Alignment()
        box_align.set(0.5, 0.5, 0.0, 0.0)
        box_align.add(hbox)
        self.add(box_align)

        # Connect signals.
        box_align.connect("expose-event", self.on_expose_combo_frame)
        self.drop_button.connect("button-press-event", self.on_drop_button_press)
        self.connect("focus-in-event", self.on_focus_in_combo)
        self.connect("focus-out-event", self.on_focus_out_combo)
        self.combo_list.treeview.connect("button-press-item", self.on_combo_single_click)

    def set_size_request(self, width, height):
        pass

    def auto_set_size(self):
        valid_width = self.combo_list.get_adjust_width()
        remained_width = valid_width - self.drop_button_width - self.padding_x
        if self.editable:
            self.label.set_size_request(remained_width, -1)
        else:
            self.label.set_fixed_width(remained_width)
        self.combo_list.auto_set_size()

    def add_items(self,
                  items,
                  select_index=0,
                  pos=None,
                  clear_first=True,
                  ):
        '''
        Add items with given index.

        @param items: Item list that need add is combo box.
        @param select_index: The index of select item, default is 0.
        @param pos: Position to insert, except you specified index, items will insert at end by default.
        @param clear_first: Whether clear existing items before insert anymore, default is True.
        '''
        # Init combo widgets.
        if clear_first:
            self.combo_list.treeview.clear()
        combo_items = [ComboTextItem(item[0], item[1]) for item in items]
        self.combo_list.treeview.add_items(combo_items, insert_pos=pos)
        self.auto_set_size()
        self.set_select_index(select_index)

    def on_drop_button_press(self, widget, event):

        self.combo_list.hover_select_item()
        height = self.allocation.height
        x, y = self.window.get_root_origin()

        if self.combo_list.get_visible():
            self.combo_list.hide()
        else:
            wx, wy = int(event.x), int(event.y)
            (offset_x, offset_y) = widget.translate_coordinates(self, 0, 0)
            (_, px, py, modifier) = widget.get_display().get_pointer()
            droplist_x, droplist_y = px - wx - offset_x - 1, py - wy - offset_y + height - 1
            self.combo_list.show((droplist_x, droplist_y), (0, -height))

    def on_combo_single_click(self, widget, item, column, x, y):
        self.label.set_text(item.title)
        self.combo_list.reset_status()
        if item:
            index = self.combo_list.get_select_index()
            self.combo_list.hide_self()
            self.emit("item-selected", item.title, item.item_value, index)

    def on_focus_in_combo(self, widget, event):
        self.focus_flag = True
        self.queue_draw()

    def on_focus_out_combo(self, widget, event):
        self.focus_flag = False
        self.queue_draw()

    def set_select_index(self, item_index):
        '''
        Set select item with given index.

        @param item_index: The index of selected item.
        '''
        if 0 <= item_index < len(self.items):
            self.combo_list.set_select_index(item_index)
            self.label.set_text(self.items[item_index].title)

    @property
    def items(self):
        return self.combo_list.items

    def get_item_with_index(self, item_index):
        '''
        Get item with given index.

        @param item_index: The index of item that you want get.
        @return: Return item with given index, return None if given index is invalid.
        '''
        if 0 <= item_index < len(self.items):
            item = self.items[item_index]
            return (item.title, item.item_value)
        else:
            return None

    def get_current_item(self):
        '''
        Get current selected item.

        @return: Return current selected item.
        '''
        return self.get_item_with_index(self.get_select_index())

    def get_select_index(self):
        '''
        Get index of select item.

        @return: Return index of selected item.
        '''
        return self.combo_list.get_select_index()

    def set_sensitive(self, sensitive):
        super(ComboBox, self).set_sensitive(sensitive)
        self.label.set_sensitive(sensitive)

    def on_expose_combo_frame(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            if self.get_sensitive():
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            else:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("disable_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()

            if self.focus_flag:
                color = (ui_theme.get_color("combo_entry_select_background").get_color(), 0.9)
                cr.set_source_rgba(*alpha_color_hex_to_cairo(color))
                cr.rectangle(rect.x, rect.y, rect.width - 1 - self.drop_button_width, rect.height - 1)
                cr.fill()
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x + rect.width - 1 - self.drop_button_width, rect.y, self.drop_button_width, rect.height - 1)
                cr.fill()
            else:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
                cr.fill()

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

gobject.type_register(ComboBox)
