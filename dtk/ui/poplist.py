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

from theme import DynamicPixbuf
from theme import ui_theme
from window import Window
from draw import draw_text, draw_vlinear, draw_pixbuf
from utils import get_content_size, get_screen_size
from treeview import TreeView, TreeItem
from constant import DEFAULT_FONT_SIZE, ALIGN_START, ALIGN_MIDDLE
import gobject
import gtk
from popup_grab_window import PopupGrabWindow, wrap_grab_window

class Poplist(Window):
    '''
    Poplist class.

    @undocumented: hide_self
    @undocumented: auto_set_size
    @undocumented: realize_poplist
    '''

    def __init__(self,
                 items,
                 min_width=80,
                 max_width=None,
                 fixed_width=None,
                 min_height=100,
                 max_height=None,
                 shadow_visible=True,
                 shape_frame_function=None,
                 expose_frame_function=None,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 align_size=0,
                 grab_window=None,
                 window_type=gtk.WINDOW_TOPLEVEL,
                 ):
        '''
        Initialize Poplist class.

        @param items: The item list to initialize.
        @param min_width: The minimum width of poplist, default is 80 pixels.
        @param max_width: The maximum width of poplist, default is None.
        @param fixed_width: The fixed width of poplist, default is None.
        @param min_height: The minimum height of poplist, default is 100 pixels.
        @param max_height: The maximum height of poplist, default is None.
        @param shadow_visible: Set it with True to make shadow visible.
        @param shape_frame_function: The function to shape frame.
        @param expose_frame_function: The function to draw frame.
        @param x_align: The horizontal alignment value, default is ALIGN_START.
        @param y_align: The vertical alignment value, default is ALIGN_START.
        @param align_size: The alignment size, default is 0.
        @param grab_window: Window to handle grab event, default is None that use poplist_grab_window.
        @param window_type: The type of window, default is gtk.WINDOW_TOPLEVEL.
        '''
        # Init.
        Window.__init__(self,
                        shadow_visible=shadow_visible,
                        window_type=window_type,
                        shape_frame_function=shape_frame_function,
                        expose_frame_function=expose_frame_function)
        self.max_height = max_height
        self.min_height = min_height
        self.x_align = x_align
        self.y_align = y_align
        self.min_width = min_width
        self.max_width = max_width
        self.fixed_width = fixed_width
        self.align_size = align_size
        self.window_width = self.window_height = 0
        self.treeview_align = gtk.Alignment()
        self.treeview_align.set(1, 1, 1, 1)
        self.treeview_align.set_padding(self.align_size, self.align_size, self.align_size, self.align_size)
        self.treeview = TreeView(items,
                                 enable_highlight=False,
                                 enable_multiple_select=False,
                                 enable_drag_drop=False)

        # Connect widgets.
        self.treeview_align.add(self.treeview)
        self.window_frame.pack_start(self.treeview_align, True, True)

        self.connect("realize", self.realize_poplist)

        # Wrap self in poup grab window.
        if grab_window:
            wrap_grab_window(grab_window, self)
        else:
            wrap_grab_window(poplist_grab_window, self)

    def get_scrolledwindow(self):
        '''
        Get scrolled window.

        @return: Return the scrolled window.
        '''
        return self.treeview.scrolled_window

    @property
    def items(self):
        return self.treeview.get_items()

    def get_adjust_width(self):
        '''
        Get width of adjustment.

        @return: Return the width of adjustment.
        '''
        if self.fixed_width:
            return self.fixed_width
        if len(self.items) > 0:
            adjust_width = max([item.get_width() for item in self.items])
        else:
            adjust_width = self.min_width

        if self.max_width:
            return min(self.max_width, adjust_width)
        return adjust_width

    def get_adjust_height(self):
        '''
        Get height of adjustment.

        @return: Return the height of adjustment.
        '''
        if len(self.items) > 0:
            adjust_height = sum([item.get_height() for item in self.items])
        else:
            adjust_height = 0

        if self.max_height != None:
            adjust_height = min(adjust_height, self.max_height)

        if adjust_height <= 0:
            adjust_height = self.min_height
        return adjust_height

    def get_adjust_size(self):
        '''
        Get size of adjustment.

        @return: Return the size of adjustment.
        '''
        return (self.get_adjust_width(), self.get_adjust_height())

    def hide_self(self):
        poplist_grab_window.popup_grab_window_focus_out()

    def auto_set_size(self):
        self.set_size(*self.get_adjust_size())

    def set_size(self, width, height):
        '''
        Set size.

        @param width: The width.
        @param height: The height.
        '''
        (shadow_padding_x, shadow_padding_y) = self.get_shadow_size()
        self.window_height = height + self.align_size * 2 + shadow_padding_x * 2 + 1
        self.window_width = width + shadow_padding_x * 2 + 1
        if self.get_realized():
            self.unrealize()

    def realize_poplist(self, widget):
        if self.window_height <= 0 or self.window_height <=0:
            self.auto_set_size()

        self.set_default_size(self.window_width, self.window_height)
        self.set_geometry_hints(
            None,
            self.window_width,       # minimum width
            self.window_height,       # minimum height
            self.window_width,
            self.window_height,
            -1, -1, -1, -1, -1, -1
            )

    def show(self, (expect_x, expect_y), (offset_x, offset_y)=(0, 0)):
        '''
        Show poplist.

        @param expect_x: Expect x coordinate.
        @param expect_y: Expect y coordinate.
        @param offset_x: The offset x.
        @param offset_y: The offset y.
        '''
        (screen_width, screen_height) = get_screen_size(self)

        if not self.get_realized():
            self.realize()

        if self.x_align == ALIGN_START:
            dx = expect_x
        elif self.x_align == ALIGN_MIDDLE:
            dx = expect_x - self.window_width / 2
        else:
            dx = expect_x - self.window_width

        if self.y_align == ALIGN_START:
            dy = expect_y
        elif self.y_align == ALIGN_MIDDLE:
            dy = expect_y - self.window_height / 2
        else:
            dy = expect_y - self.window_height

        if expect_x + self.window_width > screen_width:
            dx = expect_x - self.window_width + offset_x
        if expect_y + self.window_height > screen_height:
            dy = expect_y - self.window_height + offset_y

        self.move(dx, dy)

        self.show_all()

gobject.type_register(Poplist)

class IconTextItem(TreeItem):
    '''
    IconTextItem class.
    '''

    def __init__(self,
                 icon_dpixbufs,
                 text,
                 text_size = DEFAULT_FONT_SIZE,
                 icon_width = 16,
                 padding_x = 10,
                 padding_y = 6):
        '''
        Initialize IconTextItem class.
        '''
        # Init.
        TreeItem.__init__(self)
        (self.icon_normal_dpixbuf, self.icon_hover_dpixbuf, self.icon_disable_dpixbuf) = icon_dpixbufs
        self.item_width = 160
        self.text = text
        self.text_size = text_size
        self.icon_width = 16
        self.padding_x = padding_x
        self.padding_y = padding_y
        (self.text_width, self.text_height) = get_content_size(self.text)

    def render(self, cr, rect):
        font_color = ui_theme.get_color("menu_font").get_color()
        if isinstance(self.icon_normal_dpixbuf, gtk.gdk.Pixbuf):
            icon_pixbuf = self.icon_normal_dpixbuf
        elif isinstance(self.icon_normal_dpixbuf, DynamicPixbuf):
            icon_pixbuf = self.icon_normal_dpixbuf.get_pixbuf()

        if self.is_hover:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("menu_item_select").get_color_info())

            # Set icon pixbuf.
            if isinstance(self.icon_hover_dpixbuf, gtk.gdk.Pixbuf):
                icon_pixbuf = self.icon_hover_dpixbuf
            elif isinstance(self.icon_hover_dpixbuf, DynamicPixbuf):
                icon_pixbuf = self.icon_hover_dpixbuf.get_pixbuf()

            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()

        draw_pixbuf(cr, icon_pixbuf,
                    rect.x + self.padding_x,
                    rect.y + (rect.height - icon_pixbuf.get_height()) / 2)

        draw_text(cr,
                  self.text,
                  rect.x + self.padding_x * 2 + self.icon_width,
                  rect.y,
                  rect.width - self.padding_x * 2,
                  rect.height,
                  text_color=font_color)

    def get_width(self):
        return self.icon_width + self.text_width + self.padding_x * 3

    def get_height(self):
        return self.text_size + self.padding_y * 2

    def get_column_widths(self):
        return [self.item_width]

    def get_column_renders(self):
        return [self.render]

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(IconTextItem)

poplist_grab_window = PopupGrabWindow(Poplist)
