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

from box import EventBox
from constant import DEFAULT_FONT_SIZE
from draw import draw_line, draw_pixbuf, draw_text, draw_round_rectangle
from utils import color_hex_to_cairo
from theme import ui_theme
from utils import widget_fix_cycle_destroy_bug, propagate_expose, get_content_size
import gobject
import gtk
import pango

class Navigatebar(EventBox):
    '''
    Navigatebar.

    @undocumented: expose_nav_separator.
    '''

    def __init__(self,
                 items,
                 add_separator=False,
                 font_size=DEFAULT_FONT_SIZE,
                 padding_x=10,
                 padding_y=10,
                 vertical=True,
                 item_hover_pixbuf=ui_theme.get_pixbuf("navigatebar/nav_item_hover.png"),
                 item_press_pixbuf=ui_theme.get_pixbuf("navigatebar/nav_item_press.png"),
                 ):
        '''
        Initialize Navigatebar class.

        @param items: A list of navigate item, item format: (item_icon_dpixbuf, item_content, clicked_callback)
        @param add_separator: Whether add separator between navigatebar and body, default is False.
        @param font_size: Font size, default is DEFAULT_FONT_SIZE.
        @param padding_x: Padding value horizontal.
        @param padding_y: Padding value vertical.
        @param vertical: Draw direction, default is vertical.
        @param item_hover_pixbuf: Item hover dpixbuf.
        @param item_press_pixbuf: Item press dpixbuf.
        '''
        # Init event box.
        EventBox.__init__(self)
        self.nav_index = 0
        self.item_hover_pixbuf = item_hover_pixbuf
        self.item_press_pixbuf = item_press_pixbuf
        self.nav_items = []

        # Init nav box.
        self.nav_box = gtk.VBox()
        self.add(self.nav_box)

        # Init item box.
        self.nav_item_box = gtk.HBox()
        self.nav_box.pack_start(self.nav_item_box, False, False)

        # Add navigate item.
        if items:
            for (index, item) in enumerate(items):
                nav_item = NavItem(item, index, font_size, padding_x, padding_y, vertical,
                                   self.set_index, self.get_index,
                                   self.item_hover_pixbuf,
                                   self.item_press_pixbuf)
                self.nav_items.append(nav_item)
                self.nav_item_box.pack_start(nav_item.item_box, False, False)

        # Add separator.
        if add_separator:
            self.separator = gtk.HBox()
            self.separator.set_size_request(-1, 2)
            self.separator.connect("expose-event", self.expose_nav_separator)
            self.nav_box.pack_start(self.separator, False, False)

        # Show.
        self.show_all()

    def set_index(self, index):
        '''
        Set selected item with given index.

        @param index: Item index.
        '''
        self.nav_item_box.queue_draw()
        self.nav_index = index

    def get_index(self):
        '''
        Get selected index.

        @return: Return selected item index.
        '''
        return self.nav_index

    def expose_nav_separator(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw separator.
        cr.set_source_rgba(1, 1, 1, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 1, rect.x + rect.width - 1, rect.y + 1)

        cr.set_source_rgba(0, 0, 0, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 2, rect.x + rect.width - 1, rect.y + 2)

        return True

    def update_notify_num(self, item, notify_num):
        '''
        Update notify number.

        @param item: The item need to notify.
        @param notify_num: Notify number.
        '''
        item.notify_num = notify_num

        item.item_box.queue_draw()

gobject.type_register(Navigatebar)

class NavItem(object):
    '''
    Navigate item.

    @undocumented: wrap_nav_item_clicked_action
    @undocumented: expose_nav_item
    '''

    def __init__(self,
                 element,
                 index,
                 font_size,
                 padding_x,
                 padding_y,
                 vertical,
                 set_index, get_index,
                 item_hover_pixbuf,
                 item_press_pixbuf,
                 ):
        '''
        Initialize NavItem class.

        @param element: Item format: (item_icon_dpixbuf, item_content, clicked_callback)
        @param index: Item index.
        @param font_size: Font size.
        @param padding_x: Padding value horizontal.
        @param padding_y: Padding value vertical.
        @param vertical: Draw direction.
        @param set_index: Set index callback.
        @param get_index: Get index callback.
        @param item_hover_pixbuf: Item hover pixbuf.
        @param item_press_pixbuf: Item press pixbuf.
        '''
        # Init.
        self.index = index
        self.font_size = font_size
        self.vertical = vertical
        self.set_index = set_index
        self.get_index = get_index
        self.item_hover_pixbuf = item_hover_pixbuf
        self.item_press_pixbuf = item_press_pixbuf
        self.notify_num = 0
        (self.icon_dpixbuf, self.content, self.clicked_callback) = element
        self.nav_item_pixbuf = self.icon_dpixbuf.get_pixbuf()
        pixbuf = self.item_hover_pixbuf.get_pixbuf()
        (self.text_width, self.text_height) = get_content_size(self.content, self.font_size)

        # Init item button.
        self.pixbuf_width_scale = False
        self.item_button = gtk.Button()
        if self.text_width + self.nav_item_pixbuf.get_width() > pixbuf.get_width():
            self.item_button.set_size_request(
                    self.text_width + self.nav_item_pixbuf.get_width()+ 10,
                    pixbuf.get_height())
            self.pixbuf_width_scale = True
        else:
            self.item_button.set_size_request(pixbuf.get_width(), pixbuf.get_height())

        widget_fix_cycle_destroy_bug(self.item_button)

        self.item_button.connect("expose-event", self.expose_nav_item)
        self.item_button.connect("clicked", lambda w: self.wrap_nav_item_clicked_action())

        # Init item box.
        self.item_box = gtk.Alignment()
        self.item_box.set(0.5, 0.5, 1.0, 1.0)
        self.item_box.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_box.add(self.item_button)

    def wrap_nav_item_clicked_action(self):
        '''
        Internal function to wrap clicked action.
        '''
        self.set_index(self.index)

        if self.clicked_callback:
            self.clicked_callback()

    def expose_nav_item(self, widget, event):
        '''
        Internal callback `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        select_index = self.get_index()
        hover_pixbuf = self.item_hover_pixbuf.get_pixbuf()
        press_pixbuf = self.item_press_pixbuf.get_pixbuf()

        # Draw background.
        if widget.state == gtk.STATE_NORMAL:
            if select_index == self.index:
                select_pixbuf = press_pixbuf
            else:
                select_pixbuf = None
        elif widget.state == gtk.STATE_PRELIGHT:
            if select_index == self.index:
                select_pixbuf = press_pixbuf
            else:
                select_pixbuf = hover_pixbuf
        elif widget.state == gtk.STATE_ACTIVE:
            select_pixbuf = press_pixbuf

        if select_pixbuf:
            select_pixbuf = select_pixbuf.scale_simple(
                    rect.width, rect.height, gtk.gdk.INTERP_BILINEAR)
            draw_pixbuf(cr, select_pixbuf, rect.x, rect.y)

        # Draw navigate item.
        if self.vertical:
            draw_pixbuf(
                cr, self.nav_item_pixbuf,
                rect.x + (rect.width - self.nav_item_pixbuf.get_width()) / 2,
                rect.y)

            draw_text(cr,
                      self.content,
                      rect.x,
                      rect.y + self.nav_item_pixbuf.get_height() - 3,
                      rect.width,
                      rect.height - self.nav_item_pixbuf.get_height(),
                      text_size=self.font_size,
                      text_color="#FFFFFF",
                      alignment=pango.ALIGN_CENTER,
                      gaussian_radious=2, gaussian_color="#000000",
                      border_radious=1, border_color="#000000",
                      )
        else:
            padding_x = (rect.width - self.nav_item_pixbuf.get_width() - self.text_width) / 2

            draw_pixbuf(
                cr,
                self.nav_item_pixbuf,
                rect.x + padding_x,
                rect.y + (rect.height - self.nav_item_pixbuf.get_height()) / 2)

            draw_text(cr,
                      self.content,
                      rect.x + self.nav_item_pixbuf.get_width() + padding_x,
                      rect.y,
                      rect.width,
                      rect.height,
                      text_size=self.font_size,
                      text_color="#FFFFFF",
                      gaussian_radious=2, gaussian_color="#000000",
                      border_radious=1, border_color="#000000",
                      )

        # Draw notify number.
        text_size = 8
        (number_width, number_height) = get_content_size(str(self.notify_num), text_size)
        padding_x = 2
        padding_y = 0
        radious = 3
        draw_offset_x = -5
        draw_offset_y = 8
        draw_x = rect.x + self.nav_item_pixbuf.get_width() + padding_x + draw_offset_x
        draw_y = rect.y + draw_offset_y
        if self.notify_num > 0:
            cr.set_source_rgb(*color_hex_to_cairo("#BF0000"))
            draw_round_rectangle(
                cr,
                draw_x,
                draw_y,
                number_width + padding_x * 2,
                number_height + padding_y * 2,
                radious)
            cr.fill()

            draw_text(
                cr,
                str(self.notify_num),
                draw_x + padding_x,
                draw_y + padding_y,
                number_width,
                number_height,
                text_color="#FFFFFF",
                text_size=text_size,
                )

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

