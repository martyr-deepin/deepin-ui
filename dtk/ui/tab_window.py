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

from button import Button
from constant import DEFAULT_FONT_SIZE
from dialog import DialogBox, DIALOG_MASK_TAB_PAGE
from draw import draw_text, draw_round_rectangle
from skin_config import skin_config
from theme import ui_theme
from locales import _
import gobject
import gtk
from utils import (container_remove_all, get_content_size,
                   color_hex_to_cairo, alpha_color_hex_to_cairo,
                   cairo_disable_antialias, is_in_rect, cairo_state,
                   get_window_shadow_size)

class TabBox(gtk.VBox):
    '''
    Tab box.

    @undocumented: press_tab_title_box
    @undocumented: get_close_button_at_event
    @undocumented: motion_notify_tab_title_box
    @undocumented: update_tab_title_widths
    @undocumented: draw_title_background
    @undocumented: expose_tab_title_box
    @undocumented: expose_tab_content_align
    @undocumented: expose_tab_content_box
    '''

    __gsignals__ = {
        "switch-tab" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
    }

    def __init__(self,
                 can_close_tab=False,
                 dockfill=False,
                 current_tab_index=-1,
                 ):
        '''
        Initialize TabBox class.

        @param can_close_tab: Whether display close button on tab, default is False.
        @param dockfill: Whether make tab's width fill with TabBox's width.
        @param current_tab_index: The index of current tab, default is -1.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.tab_height = 29
        self.tab_padding_x = 19
        self.tab_padding_y = 9
        self.tab_select_bg_color = ui_theme.get_color("tab_select_bg")
        self.tab_select_frame_color = ui_theme.get_color("tab_select_frame")
        self.tab_unselect_bg_color = ui_theme.get_color("tab_unselect_bg")
        self.tab_unselect_frame_color = ui_theme.get_color("tab_unselect_bg")
        self.can_close_tab = can_close_tab
        self.close_button_size = 6
        self.close_button_frame_size = 3
        self.close_button_padding_x = 4
        self.close_button_padding_y = 6
        self.close_button_select_background_color = "#EE0000"
        self.close_button_select_foreground_color = "#FFFFFF"
        self.close_button_color = "#666666"
        self.hover_close_button_index = None
        self.dockfill = dockfill
        self.tab_box_width = -1
        self.current_tab_index = current_tab_index

        self.tab_title_box = gtk.DrawingArea()
        self.tab_title_box.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.tab_title_box.set_size_request(-1, self.tab_height)
        self.tab_title_align = gtk.Alignment()
        self.tab_title_align.set(0.0, 0.0, 1.0, 1.0)
        self.tab_title_align.set_padding(0, 0, 0, 0)
        self.tab_title_align.add(self.tab_title_box)
        self.tab_content_align = gtk.Alignment()
        self.tab_content_align.set(0.0, 0.0, 1.0, 1.0)
        self.tab_content_align.set_padding(0, 0, 0, 0)
        self.tab_content_box = gtk.VBox()
        self.tab_content_align.add(self.tab_content_box)

        self.tab_items = []
        self.tab_title_widths = []
        self.tab_index = -1

        self.default_widget = None

        self.pack_start(self.tab_title_align, False, False)
        self.pack_start(self.tab_content_align, True, True)

        self.tab_title_box.connect("button-press-event", self.press_tab_title_box)
        self.tab_title_box.connect("expose-event", self.expose_tab_title_box)
        self.tab_title_box.connect("motion-notify-event", self.motion_notify_tab_title_box)
        self.tab_content_align.connect("expose-event", self.expose_tab_content_align)
        self.tab_content_box.connect("expose-event", self.expose_tab_content_box)

    def show_default_page(self):
        '''
        Show default page.
        '''
        if self.default_widget != None and len(self.tab_items) == 0:
            container_remove_all(self.tab_content_box)
            self.tab_content_box.add(self.default_widget)
            self.tab_title_box.queue_draw()
            self.tab_content_box.queue_draw()

            self.show_all()

    def set_default_widget(self, widget):
        '''
        Set default page of tab window.

        @param widget: Widget for default page.
        '''
        self.default_widget = widget

        self.show_default_page()

    def add_items(self, items, default_index=0):
        '''
        Add items.

        @param items: A list of tab item, tab item format: (tab_name, tab_widget)
        @param default_index: Initialize index, default is 0.
        '''
        self.tab_items += items

        for item in items:
            self.tab_title_widths.append(get_content_size(item[0], DEFAULT_FONT_SIZE)[0] + self.tab_padding_x * 2)

        if self.current_tab_index < 0:
            self.switch_content(default_index)
        else:
            self.switch_content(self.current_tab_index)

    def delete_items(self, items):
        '''
        Delete given items.

        @param items: The item list need to delete.
        '''
        item_indexs = map(lambda item: self.tab_items.index(item), items)

        for item in items:
            self.tab_items.remove(item)

        for title_width in map(lambda item_index: self.tab_title_widths[item_index], item_indexs):
            self.tab_title_widths.remove(title_width)

        if len(self.tab_items) == 0:
            self.show_default_page()

        print self.tab_items

    def set_current_tab(self, index):
        '''
        Set current tab with given index.

        @param index: The index of current tab.
        '''
        self.switch_content(index)

    def switch_content(self, index):
        '''
        Switch content with given index.

        @param index: Tab index.
        '''
        if self.tab_index != index and len(self.tab_items):
            self.tab_index = index
            widget = self.tab_items[index][1]

            container_remove_all(self.tab_content_box)
            self.tab_content_box.add(widget)
            self.tab_title_box.queue_draw()
            self.tab_content_box.queue_draw()

            self.show_all()

    def press_tab_title_box(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.
        '''
        close_tab_index = self.get_close_button_at_event(event)

        if close_tab_index != None:
            self.delete_items([self.tab_items[close_tab_index]])
        else:
            for (index, item) in enumerate(self.tab_items):
                if is_in_rect((event.x, event.y),
                              (sum(self.tab_title_widths[0:index]),
                               0,
                               self.tab_title_widths[index],
                               self.tab_height)):
                    self.switch_content(index)
                    self.emit("switch-tab", index)
                    break

    def get_close_button_at_event(self, event):
        if self.can_close_tab:
            hover_index = None
            for (index, item) in enumerate(self.tab_items):
                button_x = sum(self.tab_title_widths[0:index + 1]) - self.close_button_padding_x - self.close_button_size
                button_y = self.close_button_padding_y
                if is_in_rect((event.x, event.y), (button_x, button_y, self.close_button_size, self.close_button_size)):
                    hover_index = index
                    break

            return hover_index
        # Return None if option can_close_tab is False.
        else:
            return None

    def motion_notify_tab_title_box(self, widget, event):
        hover_index = self.get_close_button_at_event(event)

        if hover_index != self.hover_close_button_index:
            self.hover_close_button_index = hover_index
            widget.queue_draw()

    def update_tab_title_widths(self, width):
        i = 0
        tab_title_len = len(self.tab_title_widths)
        for new_width in self.tab_title_widths:
            self.tab_title_widths[i] = width / tab_title_len
            i = i + 1

    def draw_title_background(self, cr, widget):
        (offset_x, offset_y) = widget.translate_coordinates(self.get_toplevel(), 0, 0)
        with cairo_state(cr):
            cr.translate(-offset_x, -offset_y)

            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            skin_config.render_background(cr, widget, shadow_x, shadow_y)

    def expose_tab_title_box(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        if self.dockfill:
            self.update_tab_title_widths(rect.width)

        # Draw background.
        self.draw_title_background(cr, widget)

        if len(self.tab_items) > 0:
            # Draw title unselect tab.
            tab_title_width = sum(self.tab_title_widths)

            with cairo_state(cr):
                with cairo_disable_antialias(cr):
                    cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_unselect_bg_color.get_color(), 0.7)))
                    cr.rectangle(1, 1, tab_title_width, self.tab_height)
                    cr.fill()

                    cr.set_line_width(1)
                    cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_unselect_frame_color.get_color(), 1.0)))
                    cr.rectangle(1, 1, tab_title_width, self.tab_height)
                    cr.stroke()

                    for (index, width) in enumerate(self.tab_title_widths[:-1]):
                        cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_unselect_frame_color.get_color(), 1.0)))
                        cr.rectangle(1 + sum(self.tab_title_widths[0:index]) + width,
                                     1,
                                     1,
                                     self.tab_height)
                        cr.fill()

                    cr.set_source_rgb(*color_hex_to_cairo(self.tab_select_frame_color.get_color()))
                    cr.rectangle(0,
                                 rect.height - 1,
                                 sum(self.tab_title_widths[0:self.tab_index]),
                                 1)
                    cr.fill()

                    cr.set_source_rgb(*color_hex_to_cairo(self.tab_select_frame_color.get_color()))
                    cr.rectangle(1 + sum(self.tab_title_widths[0:self.tab_index]),
                                 rect.height - 1,
                                 rect.width - sum(self.tab_title_widths[0:self.tab_index]),
                                 1)
                    cr.fill()

            for (index, item) in enumerate(self.tab_items):
                # Draw title background.
                title = item[0]

                # Draw title tab.
                with cairo_disable_antialias(cr):
                    if index == self.tab_index:
                        # Draw title select tab.
                        cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_select_bg_color.get_color(), 0.93)))
                        if index == 0:
                            cr.rectangle(sum(self.tab_title_widths[0:index]),
                                         1,
                                         self.tab_title_widths[index] + 1,
                                         self.tab_height)
                        else:
                            cr.rectangle(1 + sum(self.tab_title_widths[0:index]),
                                         1,
                                         self.tab_title_widths[index],
                                         self.tab_height)
                        cr.fill()

                        if index == 0:
                            cr.rectangle(0,
                                         0,
                                         rect.width,
                                         self.tab_height)
                            cr.clip()

                        cr.set_line_width(1)
                        cr.set_source_rgb(*color_hex_to_cairo(self.tab_select_frame_color.get_color()))
                        if index == 0:
                            cr.rectangle(sum(self.tab_title_widths[0:index]),
                                         1,
                                         self.tab_title_widths[index] + 2,
                                         self.tab_height)
                        else:
                            cr.rectangle(1 + sum(self.tab_title_widths[0:index]),
                                         1,
                                         self.tab_title_widths[index] + 1,
                                         self.tab_height)
                        cr.stroke()

                draw_text(cr, title,
                          sum(self.tab_title_widths[0:index]) + self.tab_padding_x,
                          self.tab_padding_y,
                          self.tab_title_widths[index] - self.tab_padding_x * 2,
                          self.tab_height - self.tab_padding_y * 2,
                          )

                # Draw close button.
                if self.can_close_tab:
                    button_x = sum(self.tab_title_widths[0:index + 1]) - self.close_button_padding_x - self.close_button_size
                    button_y = self.close_button_padding_y

                    if self.hover_close_button_index == index:
                        cr.set_source_rgb(*color_hex_to_cairo(self.close_button_select_background_color))
                        draw_round_rectangle(
                            cr,
                            button_x - self.close_button_frame_size,
                            button_y - self.close_button_frame_size,
                            self.close_button_size + self.close_button_frame_size * 2,
                            self.close_button_size + self.close_button_frame_size * 2,
                            2
                            )
                        cr.fill()

                    cr.set_line_width(1.5)
                    if self.hover_close_button_index == index:
                        cr.set_source_rgb(*color_hex_to_cairo(self.close_button_select_foreground_color))
                    else:
                        cr.set_source_rgb(*color_hex_to_cairo(self.close_button_color))
                    cr.move_to(button_x, button_y)
                    cr.line_to(button_x + self.close_button_size, button_y + self.close_button_size)
                    cr.stroke()

                    cr.move_to(button_x + self.close_button_size, button_y)
                    cr.line_to(button_x, button_y + self.close_button_size)
                    cr.stroke()
        else:
            cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_select_bg_color.get_color(), 0.93)))
            cr.rectangle(0, 0, rect.width, rect.height)
            cr.fill()

    def expose_tab_content_align(self, widget, event):
        '''
        Internal function to `expose-event` signal.
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation

        with cairo_disable_antialias(cr):
            cr.rectangle(rect.x, rect.y, sum(self.tab_title_widths[0:self.tab_index]), rect.height)
            cr.rectangle(rect.x + sum(self.tab_title_widths[0:self.tab_index + 1]),
                         rect.y,
                         rect.width - sum(self.tab_title_widths[0:self.tab_index + 1]),
                         rect.height)
            cr.clip()

            cr.set_source_rgb(*color_hex_to_cairo(self.tab_select_frame_color.get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()

    def expose_tab_content_box(self, widget, event):
        '''
        Internal function to `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        self.tab_box_width = rect.width

        # Draw background.
        toplevel = widget.get_toplevel()
        coordinate = widget.translate_coordinates(toplevel, 0, 0)
        (offset_x, offset_y) = coordinate

        with cairo_state(cr):
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.clip()

            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            skin_config.render_background(cr, self, shadow_x, shadow_y)

        # Draw mask.
        cr.set_source_rgba(*alpha_color_hex_to_cairo((self.tab_select_bg_color.get_color(), 0.93)))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

gobject.type_register(TabBox)

class TabWindow(DialogBox):
    '''
    TabWindow class.

    @undocumented: click_confirm_button
    @undocumented: click_cancel_button
    @undocumented: switched_tab
    '''

    def __init__(self, title, items,
                 confirm_callback=None,
                 cancel_callback=None,
                 window_width=458,
                 window_height=472,
                 dockfill=False,
                 current_tab_index=-1,
                 ):
        '''
        Initialize TabWindow clas.

        @param title: Tab window title.
        @param items: A list of tab item, tab item format: (tab_name, tab_widget)
        @param confirm_callback: Callback when user click ok button.
        @param cancel_callback: Callback when user click cancel button.
        @param window_width: Default window width.
        @param window_height: Default window height.
        @param dockfill: Fill the tab items
        @param current_tab_index: The index of current tab, default is -1.
        '''
        DialogBox.__init__(self,
                           title,
                           window_width,
                           window_height,
                           mask_type=DIALOG_MASK_TAB_PAGE)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback

        self.window_box = gtk.VBox()

        self.tab_window_width = window_width
        self.tab_window_height = window_height
        self.tab_box = TabBox(can_close_tab=True,
                              dockfill=dockfill,
                              current_tab_index=current_tab_index)
        self.tab_box.add_items(items)
        self.tab_box.connect("switch-tab", self.switched_tab)
        self.tab_align = gtk.Alignment()
        self.tab_align.set(0.5, 0.5, 1.0, 1.0)
        self.tab_align.set_padding(8, 0, 0, 0)
        self.tab_align.add(self.tab_box)

        self.confirm_button = Button(_("OK"))
        self.cancel_button = Button(_("Cancel"))

        self.window_box.pack_start(self.tab_align, True, True)

        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        self.connect("destroy", lambda w: self.destroy())

        self.body_box.pack_start(self.window_box, True, True)
        self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])

    def set_current_tab(self, index):
        '''
        Set current tab with given index.

        @param index: The index of current tab.
        '''
        self.tab_box.switch_content(index)

    def switched_tab(self, widget, index):
        pass

    def click_confirm_button(self):
        '''
        Internal function to response when user click confirm button.
        '''
        if self.confirm_callback != None:
            self.confirm_callback()

        self.destroy()

    def click_cancel_button(self):
        '''
        Internal function to response when user click cancel button.
        '''
        if self.cancel_callback != None:
            self.cancel_callback()

        self.destroy()

gobject.type_register(TabWindow)
