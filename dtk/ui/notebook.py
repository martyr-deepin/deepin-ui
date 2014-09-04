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

from cache_pixbuf import CachePixbuf
from constant import DEFAULT_FONT_SIZE
from draw import draw_pixbuf, draw_text
from theme import ui_theme
from utils import get_content_size, propagate_expose
import gtk

class Notebook(gtk.EventBox):
    '''
    Notebook.

    @undocumented: calculate_tab_width
    @undocumented: expose_notebook
    @undocumented: button_press_notebook
    '''

    def __init__(self,
                 items,
                 foreground_left_pixbuf = ui_theme.get_pixbuf("notebook/foreground_left.png"),
                 foreground_middle_pixbuf = ui_theme.get_pixbuf("notebook/foreground_middle.png"),
                 foreground_right_pixbuf = ui_theme.get_pixbuf("notebook/foreground_right.png"),
                 background_left_pixbuf = ui_theme.get_pixbuf("notebook/background_left.png"),
                 background_middle_pixbuf = ui_theme.get_pixbuf("notebook/background_middle.png"),
                 background_right_pixbuf = ui_theme.get_pixbuf("notebook/background_right.png"),
                 ):
        '''
        Initialize Notebook class.

        @param items: Notebook item, foramt (item_icon, item_content, item_callback).
        @param foreground_left_pixbuf: Left foreground pixbuf.
        @param foreground_middle_pixbuf: Middle foreground pixbuf.
        @param foreground_right_pixbuf: Right foreground pixbuf.
        @param background_left_pixbuf: Left background pixbuf.
        @param background_middle_pixbuf: Middle background pixbuf.
        @param background_right_pixbuf: Right background pixbuf.
        '''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)

        self.items = items
        self.current_item_index = 0
        self.padding_side = 27  # pixel
        self.padding_middle = 10 # pixel
        self.foreground_left_pixbuf = foreground_left_pixbuf
        self.foreground_middle_pixbuf = foreground_middle_pixbuf
        self.foreground_right_pixbuf = foreground_right_pixbuf
        self.background_left_pixbuf = background_left_pixbuf
        self.background_middle_pixbuf = background_middle_pixbuf
        self.background_right_pixbuf = background_right_pixbuf
        self.cache_bg_pixbuf = CachePixbuf()
        self.cache_fg_pixbuf = CachePixbuf()

        # Calcuate tab width.
        (self.tab_width, self.tab_height) = self.calculate_tab_width()
        self.set_size_request(-1, self.tab_height)

        # Expose.
        self.connect("expose-event", self.expose_notebook)
        self.connect("button-press-event", self.button_press_notebook)

    def calculate_tab_width(self):
        '''
        Internal function to calculate tab width.
        '''
        self.icon_width = 0
        max_tab_content_width = 0
        for (item_icon, item_content, item_callback) in self.items:
            if self.icon_width == 0 and item_icon != None:
                self.icon_width = item_icon.get_pixbuf().get_width()

            (content_width, content_height) = get_content_size(item_content, DEFAULT_FONT_SIZE)
            if content_width > max_tab_content_width:
                max_tab_content_width = content_width

        tab_image_height = self.foreground_left_pixbuf.get_pixbuf().get_height()

        if self.icon_width == 0:
            tab_width = self.padding_side * 2 + max_tab_content_width
        else:
            tab_width = self.padding_side * 2 + self.padding_middle + self.icon_width + max_tab_content_width

        return (tab_width, tab_image_height)

    def expose_notebook(self, widget, event):
        '''
        Internal callback for `expose-event` signal.

        @param widget: Notebook wiget.
        @param event: Expose event.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        foreground_left_pixbuf = self.foreground_left_pixbuf.get_pixbuf()
        self.cache_fg_pixbuf.scale(self.foreground_middle_pixbuf.get_pixbuf(),
                             self.tab_width - foreground_left_pixbuf.get_width() * 2,
                             self.tab_height)
        foreground_middle_pixbuf = self.cache_fg_pixbuf.get_cache()
        foreground_right_pixbuf = self.foreground_right_pixbuf.get_pixbuf()
        background_left_pixbuf = self.background_left_pixbuf.get_pixbuf()
        self.cache_bg_pixbuf.scale(self.background_middle_pixbuf.get_pixbuf(),
                                   self.tab_width - background_left_pixbuf.get_width() * 2,
                                   self.tab_height)
        background_middle_pixbuf = self.cache_bg_pixbuf.get_cache()
        background_right_pixbuf = self.background_right_pixbuf.get_pixbuf()

        # Draw tab.
        for (index, (item_icon, item_content, item_callback)) in enumerate(self.items):
            # Draw background.
            if self.current_item_index == index:
                draw_pixbuf(cr,
                            foreground_left_pixbuf,
                            rect.x + index * self.tab_width,
                            rect.y)
                draw_pixbuf(cr,
                            foreground_middle_pixbuf,
                            rect.x + index * self.tab_width + foreground_left_pixbuf.get_width(),
                            rect.y)
                draw_pixbuf(cr,
                            foreground_right_pixbuf,
                            rect.x + (index + 1) * self.tab_width - foreground_left_pixbuf.get_width(),
                            rect.y)
            else:
                draw_pixbuf(cr,
                            background_left_pixbuf,
                            rect.x + index * self.tab_width,
                            rect.y)
                draw_pixbuf(cr,
                            background_middle_pixbuf,
                            rect.x + index * self.tab_width + background_left_pixbuf.get_width(),
                            rect.y)
                draw_pixbuf(cr,
                            background_right_pixbuf,
                            rect.x + (index + 1) * self.tab_width - background_left_pixbuf.get_width(),
                            rect.y)

            # Draw content.
            (content_width, content_height) = get_content_size(item_content, DEFAULT_FONT_SIZE)
            if item_icon != None:
                tab_render_width = self.icon_width + self.padding_middle + content_width
                draw_pixbuf(cr,
                            item_icon.get_pixbuf(),
                            rect.x + index * self.tab_width + (self.tab_width - tab_render_width) / 2,
                            rect.y + (self.tab_height - item_icon.get_pixbuf().get_height()) / 2)

                draw_text(cr,
                            item_content,
                            rect.x + index * self.tab_width + (self.tab_width - tab_render_width) / 2 + self.icon_width + self.padding_middle,
                            rect.y + (self.tab_height - content_height) / 2,
                            content_width,
                            content_height,
                            DEFAULT_FONT_SIZE,
                            ui_theme.get_color("notebook_font").get_color(),
                            )
            else:
                tab_render_width = content_width
                draw_text(cr,
                            item_content,
                            rect.x + index * self.tab_width + (self.tab_width - tab_render_width) / 2 + self.icon_width + self.padding_middle,
                            rect.y + (self.tab_height - content_height) / 2,
                            content_width,
                            content_height,
                            DEFAULT_FONT_SIZE,
                            ui_theme.get_color("notebook_font").get_color(),
                            )

        propagate_expose(widget, event)

        return True

    def button_press_notebook(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.

        @param widget: Notebook widget.
        @param event: Button press event.
        '''
        # Get tab index.
        tab_index = int(event.x / self.tab_width)
        if tab_index < len(self.items):
            self.current_item_index = tab_index

            # Redraw.
            self.queue_draw()

            # Callback.
            if self.items[tab_index][2] != None:
                self.items[tab_index][2]()

