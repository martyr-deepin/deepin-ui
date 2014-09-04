#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Wang Yong
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

from draw import (draw_pixbuf, propagate_expose, draw_vlinear, cairo_state,
                  cairo_disable_antialias, draw_text)
from theme import ui_theme
from skin_config import skin_config
from utils import get_window_shadow_size, color_hex_to_cairo, set_cursor
import gobject
import gtk

class EventBox(gtk.EventBox):
    '''
    Event box, not like Gtk.EventBox, it don't show visible window default.
    '''

    def __init__(self):
        '''
        Initialize the EventBox class.
        '''
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)

class ImageBox(gtk.EventBox):
    '''
    ImageBox.

    @undocumented: expose_image_box
    '''

    def __init__(self, image_dpixbuf):
        '''
        Initialize the ImageBox class.

        @param image_dpixbuf: Image dynamic pixbuf.
        '''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.image_dpixbuf = image_dpixbuf

        # Set size.
        pixbuf = self.image_dpixbuf.get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())

        # Connect expose signal.
        self.connect("expose-event", self.expose_image_box)

    def expose_image_box(self, widget, event):
        '''
        Callback for `expose-event` signal.

        @param widget: Gtk.Widget instance.
        @param event: Expose event.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        pixbuf = self.image_dpixbuf.get_pixbuf()

        # Draw.
        draw_pixbuf(cr, pixbuf, rect.x, rect.y)

        # Propagate expose.
        propagate_expose(widget, event)

        return True

gobject.type_register(ImageBox)

class BackgroundBox(gtk.VBox):
    '''
    BackgroundBox is container for clip background.
    We use this widget as container to handle background render.

    @undocumented: expose_background_box
    '''

    def __init__(self):
        '''
        Initialize the BackgroundBox class.
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.set_can_focus(True)

        self.connect("expose-event", self.expose_background_box)

    def draw_mask(self, cr, x, y, w, h):
        '''
        Mask render function.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linear_background").get_color_info()
                     )

    def expose_background_box(self, widget, event):
        '''
        Callback for `expose-event` signal.

        @param widget: BackgroundBox self.
        @param event: Expose event.
        @return: Always return False.
        '''
        cr = widget.window.cairo_create()
        with cairo_state(cr):
            rect = widget.allocation
            toplevel = widget.get_toplevel()
            (offset_x, offset_y) = widget.translate_coordinates(toplevel, 0, 0)
            (shadow_x, shadow_y) = get_window_shadow_size(toplevel)

            x = shadow_x - offset_x
            y = shadow_y - offset_y

            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.clip()
            cr.translate(x, y)
            skin_config.render_background(cr, widget, 0, 0)

        self.draw_mask(cr, rect.x, rect.y, rect.width, rect.height)

        return False

gobject.type_register(BackgroundBox)

class ResizableBox(gtk.EventBox):
    '''
    Resizable box.

    Use as container that need resizable it's size.

    @undocumented: invalidate
    @undocumented: expose_override
    '''

    __gsignals__ = {
        "resize" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
        }

    def __init__(self,
                 width=690,
                 height=160,
                 min_height=160,
                 padding_x=50,
                 padding_y=18,
                 resizable=True,
                 ):
        '''
        Initialize.

        @param width: The width of widget, default is 690 pixels.
        @param height: The height of widget, default is 160 pixels.
        @param min_height: The minimum height that widget's height can't less than this value, default is 160 pixels.
        @param padding_x: The horizontal padding value, default is 50 pixels.
        @param padding_y: The vertical padding value, default is 18 pixels.
        @param resizable: The option the control whether resize widget, default is True.
        '''
        gtk.EventBox.__init__(self)

        self.padding_x = padding_x
        self.padding_y = padding_y
        self.line_width = 1.0

        self.width = width
        self.height = height
        self.min_height = min_height
        self.set_size_request(self.width, self.height)

        self.button_pressed = False
        self.resizable = resizable

        self.connect("button-press-event", self.__button_press)
        self.connect("button-release-event", self.__button_release)
        self.connect("motion-notify-event", self.__motion_notify)
        self.connect("expose-event", self.__expose)

        self.set_events(gtk.gdk.POINTER_MOTION_MASK)

    def get_resizable(self):
        '''
        Get the resizable status of widget.

        @return: Return True if box can resizable.
        '''
        return self.resizable

    def set_resizable(self, resizable):
        '''
        Set the resizable option.

        @param resizable: Set as True if you want widget can resize, or set False if you want fixed it's size temporary.
        '''
        self.resizable = resizable
        self.queue_draw()

    def __button_press(self, widget, event):
        self.button_pressed = True

    def __button_release(self, widget, event):
        self.button_pressed = False

    def __motion_notify(self, widget, event):
        if event.y < self.min_height:
            if event.y < self.min_height - 10:
                set_cursor(widget, None)
            else:
                set_cursor(widget, gtk.gdk.SB_V_DOUBLE_ARROW)
            return

        if self.resizable:
            set_cursor(widget, gtk.gdk.SB_V_DOUBLE_ARROW)
            self.height = event.y
        else:
            self.height = self.min_height

        if self.button_pressed:
            # redraw the widget
            self.queue_draw()

    def invalidate(self):
        self.queue_draw()

    def expose_override(self, cr, rect):
        pass

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y = rect.x, rect.y

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
            cr.rectangle(x - self.padding_x,
                         y - self.padding_y,
                         rect.width + self.padding_x,
                         rect.height + self.padding_y)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo("#FAFAFA"))
            cr.set_line_width(self.line_width)
            cr.rectangle(x,
                         y,
                         self.width,
                         self.height - self.padding_y)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo("#E2E2E2"))
            cr.set_line_width(self.line_width)
            cr.rectangle(x,
                         y,
                         self.width,
                         self.height - self.padding_y)
            cr.stroke()

            self.emit("resize", y + self.height)

        self.expose_override(cr, rect)

        return True

gobject.type_register(ResizableBox)

class Markbox(EventBox):
    '''
    class docs
    '''

    def __init__(self, value, font_color="#FFFFFF"):
        '''
        init docs
        '''
        EventBox.__init__(self)

        self.value = value
        self.font_color = font_color

        self.start_value = 0
        self.range = 0
        self.in_animation = False

        self.big_number_size = 18
        self.small_number_size = 15
        self.dot_number_offset_x = 13
        self.dot_number_offset_y = 1
        self.small_number_offset_y = 1

        self.connect("expose-event", self.expose_mark_bar)

        self.set_size_request(30, 30)

    def set_value(self, value):
        if (not self.in_animation) and value != self.value:
            self.start_value = self.value
            self.range = value - self.value
            times = int(abs(self.range)) * 10
            if times != 0:
                from timeline import Timeline, CURVE_SINE
                timeline = Timeline(times * 10, CURVE_SINE)
                timeline.connect("start", self.start_animation)
                timeline.connect("stop", self.stop_animation)
                timeline.connect("update", self.update_animation)
                timeline.run()
            else:
                self.value = value
                self.queue_draw()

        return False

    def start_animation(self, timeline):
        self.in_animation = True

    def stop_animation(self, timeline):
        self.in_animation = False

    def update_animation(self, timeline, percent):
        self.value = round(self.start_value + self.range * percent, 1)

        self.queue_draw()

    def expose_mark_bar(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        split_result = str(self.value).split(".")
        if len(split_result) == 1:
            big_number_str = split_result[0]
            dot_str = None
            small_number_str = None
        else:
            (big_number_str, small_number_str) = split_result
            dot_str = "."

        draw_text(
            cr,
            "<b>%s</b>" % big_number_str,
            rect.x,
            rect.y,
            rect.width,
            rect.height,
            text_size=self.big_number_size,
            text_color=self.font_color,
            )

        if dot_str:
            draw_text(
                cr,
                dot_str,
                rect.x + self.dot_number_offset_x,
                rect.y + self.dot_number_offset_y,
                rect.width,
                rect.height,
                text_size=self.small_number_size,
                text_color=self.font_color,
                )

        if small_number_str:
            draw_text(
                cr,
                small_number_str,
                rect.x + self.big_number_size,
                rect.y,
                rect.width,
                rect.height + self.small_number_offset_y,
                text_size=self.small_number_size,
                text_color=self.font_color,
                )

gobject.type_register(Markbox)
