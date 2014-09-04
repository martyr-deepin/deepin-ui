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

from timeline import Timeline, CURVE_SINE
from box import EventBox
from utils import get_content_size, color_hex_to_cairo, cairo_state
from draw import draw_text
from theme import ui_theme

import pango
import gobject
import gtk

class TabSwitcher(EventBox):
    '''
    TabSwitcher class.

    @undocumented: realize_tab_switcher
    @undocumented: expose_tab_switcher
    @undocumented: button_press_tab_switcher
    @undocumented: start_animation
    @undocumented: update_animation
    @undocumented: completed_animation
    '''

    __gsignals__ = {
        "tab-switch-start" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
        "tab-switch-complete" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
        "click-current-tab" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
    }

    def __init__(self,
                 tab_names,
                 font_size=11,
                 padding_x=0,
                 padding_y=0,
                 ):
        '''
        Initialize TabSwitcher class.

        @param tab_names: The name of tabs.
        @param padding_x: The padding x around tab name, default is 0 pixel.
        @param padding_y: The padding y around tab name, default is 0 pixel.
        '''
        EventBox.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.tab_names = tab_names
        self.tab_name_size = font_size
        self.tab_number = len(self.tab_names)
        tab_sizes = map(lambda tab_name: get_content_size(tab_name, self.tab_name_size), self.tab_names)
        self.tab_name_padding_x = 10
        self.tab_name_padding_y = 2
        self.tab_width = max(map(lambda (width, height): width, tab_sizes)) + self.tab_name_padding_x * 2
        self.tab_height = tab_sizes[0][1] + self.tab_name_padding_y * 2
        self.tab_line_height = 3
        self.tab_index = 0

        self.tab_animation_x = 0
        self.tab_animation_time = 200 # milliseconds

        self.padding_x = padding_x
        self.padding_y = padding_y
        self.in_animiation = False
        self.line_dcolor = ui_theme.get_color("globalItemHighlight")

        self.set_size_request(-1, self.tab_height + self.tab_line_height)

        self.connect("realize", self.realize_tab_switcher)
        self.connect("expose-event", self.expose_tab_switcher)
        self.connect("button-press-event", self.button_press_tab_switcher)

    def realize_tab_switcher(self, widget):
        # Init.
        rect = widget.allocation
        self.tab_animation_x = rect.x + (rect.width - self.tab_width * self.tab_number) / 2

    def expose_tab_switcher(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        with cairo_state(cr):
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.clip()

            # Draw tab line.
            cr.set_source_rgb(*color_hex_to_cairo(self.line_dcolor.get_color()))
            cr.rectangle(rect.x + self.padding_x,
                         rect.y + self.tab_height,
                         rect.width - self.padding_x * 2,
                         self.tab_line_height)
            cr.fill()

            # Draw tab.
            draw_start_x = rect.x + (rect.width - self.tab_width * self.tab_number) / 2
            if self.in_animiation:
                cr.rectangle(self.tab_animation_x,
                             rect.y,
                             self.tab_width,
                             self.tab_height)
            else:
                cr.rectangle(draw_start_x + self.tab_index * self.tab_width,
                             rect.y,
                             self.tab_width,
                             self.tab_height)
            cr.fill()

            # Draw tab name.
            for (tab_index, tab_name) in enumerate(self.tab_names):
                if self.in_animiation:
                    tab_name_color = "#000000"
                elif tab_index == self.tab_index:
                    tab_name_color = "#FFFFFF"
                else:
                    tab_name_color = "#000000"
                draw_text(cr,
                          tab_name,
                          draw_start_x + tab_index * self.tab_width,
                          rect.y,
                          self.tab_width,
                          self.tab_height,
                          text_size=self.tab_name_size,
                          text_color=tab_name_color,
                          alignment=pango.ALIGN_CENTER,
                          )

    def button_press_tab_switcher(self, widget, event):
        # Init.
        rect = widget.allocation
        tab_start_x = (rect.width - self.tab_width * self.tab_number) / 2

        for tab_index in range(0, self.tab_number):
            if tab_start_x + tab_index * self.tab_width < event.x < tab_start_x + (tab_index + 1) * self.tab_width:
                if self.tab_index != tab_index:
                    self.start_animation(tab_index, tab_start_x + rect.x)
                else:
                    self.emit("click-current-tab", self.tab_index)
                break

    def start_animation(self, index, tab_start_x):
        if not self.in_animiation:
            self.in_animiation = True

            source_tab_x = tab_start_x + self.tab_index * self.tab_width
            target_tab_x = tab_start_x + index * self.tab_width

            timeline = Timeline(self.tab_animation_time, CURVE_SINE)
            timeline.connect('update', lambda source, status: self.update_animation(source, status, source_tab_x, (target_tab_x - source_tab_x)))
            timeline.connect("completed", lambda source: self.completed_animation(source, index))
            timeline.run()

            self.emit("tab-switch-start", index)

    def update_animation(self, source, status, animation_start_x, animation_move_offset):
        self.tab_animation_x = animation_start_x + animation_move_offset * status

        self.queue_draw()

    def completed_animation(self, source, index):
        self.tab_index = index
        self.in_animiation = False

        self.emit("tab-switch-complete", self.tab_index)

        self.queue_draw()

gobject.type_register(TabSwitcher)

