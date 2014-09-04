#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
#             Long Changjin <admin@longchangjin.cn>
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

from theme import ui_theme
from cache_pixbuf import CachePixbuf
from draw import draw_pixbuf, draw_text
from utils import (is_left_button, get_content_size, color_hex_to_cairo,
                   cairo_disable_antialias)
from constant import DEFAULT_FONT_SIZE
import gobject
import gtk

class HScalebar(gtk.Button):
    '''
    HScalebar class.

    @undocumented: draw_bg_and_fg
    @undocumented: draw_point
    @undocumented: draw_value
    '''

    __gsignals__ = {
        "value-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self,
                 point_dpixbuf=ui_theme.get_pixbuf("hscalebar/point.png"),
                 show_value=False,
                 show_value_type=gtk.POS_TOP,
                 show_point_num=0,
                 format_value="",
                 value_min = 0,
                 value_max = 100,
                 line_height=6,
                 gray_progress=False
                 ):
        '''
        @param point_dpixbuf: a DynamicPixbuf object.
        @param show_value: If True draw the current value next to the slider.
        @param show_value_type: The position where the current value is displayed. gtk.POS_TOP or gtk.POS_BOTTOM.
        @param show_point_num: The accuracy of the value. If 0 value is int type.
        @param format_value: A string that displayed after the value.
        @param value_min: The min value, default is 0.
        @param value_max: The max value, default is 100.
        @param line_height: The line height, default is 6 pixels.
        @param gray_progress: If True the HScalebar looks gray, default is False.
        '''
        gtk.Button.__init__(self)
        self.position_list = []
        self.mark_check = False
        self.enable_check = True
        self.new_mark_x = 0
        self.next_mark_x = 0
        self.value = 0
        self.show_value_type = show_value_type
        self.show_point_num = show_point_num
        self.value_max = value_max - value_min
        self.value_min = value_min
        self.drag = False
        self.gray_progress = gray_progress
        self.magnetic_values = []

        # Init color.
        self.fg_side_color = "#0071B3"
        self.bg_side_color = "#B3B3B3"
        self.fg_inner_color = "#30ABEE"
        self.bg_inner1_color = "#CCCCCC"
        self.bg_inner2_color = "#E6E6E6"
        self.fg_corner_color = "#2E84B7"
        self.bg_corner_color = "#C1C5C6"

        self.point_pixbuf = point_dpixbuf
        self.line_height = line_height
        self.line_width = 1.0
        self.progress_border = 1
        self.mark_height = 6
        self.mark_width = 1
        self.bottom_space = 2 # vertical space between bottom mark line and drag point
        self.format_value = format_value
        self.show_value = show_value

        self.point_width = self.point_pixbuf.get_pixbuf().get_width()
        self.point_height = self.point_pixbuf.get_pixbuf().get_height()
        self.text_height_factor = 2
        self.set_size_request(-1, self.point_height + get_content_size("0")[1] * self.text_height_factor + self.bottom_space)

        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("expose-event", self.__progressbar_expose_event)
        self.connect("button-press-event", self.__progressbar_press_event)
        self.connect("button-release-event", self.__progressbar_release_event)
        self.connect("motion-notify-event", self.__progressbar_motion_notify_event)
        self.connect("scroll-event", self.__progressbar_scroll_event)

    def __progressbar_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.clip()
        # Draw background and foreground.
        self.draw_bg_and_fg(cr, rect)

        # Draw mark.
        for position in self.position_list:
            self.draw_value(cr, rect,  "%s" % (str(position[2])), position[0] - self.value_min, position[1], mark_check=True)

        # Draw value.
        if self.show_value:
            if self.show_point_num:
                draw_value_temp = round(self.value + self.value_min, self.show_point_num)
            else:
                draw_value_temp = int(round(self.value + self.value_min, self.show_point_num))

            self.draw_value(cr, rect,
                            "%s%s" % (draw_value_temp, self.format_value),
                            self.value,
                            self.show_value_type)
        # Draw point.
        self.draw_point(cr, rect)

        return True

    def draw_bg_and_fg(self, cr, rect):
        with cairo_disable_antialias(cr):
            x, y, w, h = rect
            progress_x = rect.x
            progress_y = rect.y + (rect.height-self.bottom_space)/2 - self.line_height/2
            progress_width = rect.width
            value_width = int(float(self.value) / self.value_max * (rect.width - self.point_width/2))
            if int(float(self.value)) == self.value_max:
                value_width = value_width - 1 # there is less 1px for 100% mark line

            # Background inner.
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_inner2_color))
            cr.rectangle(progress_x+value_width,
                    progress_y+self.progress_border,
                    progress_width-value_width-self.progress_border,
                    self.line_height-self.progress_border*2)
            cr.fill()

            # Background border.
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_side_color))

            # Top border.
            cr.rectangle(
                    progress_x+value_width,
                    progress_y,
                    progress_width-value_width-self.progress_border,
                    self.progress_border)
            cr.fill()

            # Bottom border.
            cr.rectangle(
                    progress_x+value_width,
                    progress_y+self.line_height-self.progress_border,
                    progress_width-value_width-self.progress_border,
                    self.progress_border)
            cr.fill()

            # Right border.
            cr.rectangle(
                    progress_x+progress_width-self.progress_border,
                    progress_y+self.progress_border,
                    self.progress_border,
                    self.line_height-self.progress_border*2)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo(self.bg_corner_color))

            # Top right corner.
            cr.rectangle(
                    progress_x+progress_width-self.progress_border,
                    progress_y,
                    self.progress_border,
                    self.progress_border)
            cr.fill()

            # Bottom right corner.
            cr.rectangle(
                    progress_x+progress_width-self.progress_border,
                    progress_y+self.line_height-self.progress_border,
                    self.progress_border,
                    self.progress_border)
            cr.fill()

            if self.enable_check:
                fg_inner_color = self.fg_inner_color
                fg_side_color  = self.fg_side_color
                fg_corner_color = self.fg_corner_color
            else:
                fg_inner_color = self.bg_inner1_color
                fg_side_color  = self.bg_side_color
                fg_corner_color = self.bg_corner_color

            if self.gray_progress:
                fg_inner_color = self.bg_inner2_color
                fg_side_color  = self.bg_side_color
                fg_corner_color = self.bg_corner_color

            # Foreground inner.
            cr.set_source_rgb(*color_hex_to_cairo(fg_inner_color))
            cr.rectangle(progress_x+self.progress_border,
                    progress_y+self.progress_border,
                    value_width-self.progress_border,
                    self.line_height-self.progress_border*2)
            cr.fill()

            # Foreground border.
            cr.set_source_rgb(*color_hex_to_cairo(fg_side_color))

            # Top border.
            cr.rectangle(
                    progress_x+self.progress_border,
                    progress_y,
                    value_width-self.progress_border,
                    self.progress_border)
            cr.fill()

            # Bottom border.
            cr.rectangle(
                    progress_x+self.progress_border,
                    progress_y+self.line_height-self.progress_border,
                    value_width-self.progress_border,
                    self.progress_border)
            cr.fill()

            # Left border.
            cr.rectangle(
                    progress_x,
                    progress_y+self.progress_border,
                    self.progress_border,
                    self.line_height-self.progress_border*2)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo(fg_corner_color))

            # Top left corner.
            cr.rectangle(
                    progress_x,
                    progress_y,
                    self.progress_border,
                    self.progress_border)
            cr.fill()

            # Bottom left corner.
            cr.rectangle(
                    progress_x,
                    progress_y+self.line_height-self.progress_border,
                    self.progress_border,
                    self.progress_border)
            cr.fill()

    def draw_point(self, cr, rect):
        pixbuf_w_average = self.point_pixbuf.get_pixbuf().get_width() / 2
        x = rect.x + self.point_width / 2 + int(float(self.value) / self.value_max * (rect.width - self.point_width)) - pixbuf_w_average

        draw_pixbuf(cr,
                    self.point_pixbuf.get_pixbuf(),
                    x,
                    rect.y + (rect.height-self.bottom_space)/2 - self.point_pixbuf.get_pixbuf().get_height()/2)

    def draw_value(self, cr, rect, text, value, type_=None, mark_check=False):
        text_width, text_height = get_content_size(text)
        text_y = rect.y
        if gtk.POS_TOP == type_:
            text_y = text_y
        if gtk.POS_BOTTOM == type_:
            text_y = rect.y + (rect.height-self.bottom_space)/2 + self.point_height + self.bottom_space - text_height/2

        x = rect.x + int(float(value) / self.value_max * (rect.width - self.point_width))
        max_value = max(x - (text_width/2 - self.point_width/2), rect.x)
        min_value = min(max_value, rect.x + rect.width - text_width)

        if self.enable_check:
            draw_text(cr, text, min_value, text_y, rect.width, 0)
        else:
            draw_text(cr, text, min_value, text_y, rect.width, 0, DEFAULT_FONT_SIZE, self.bg_side_color)

        mark_y = text_y-self.bottom_space/2-(self.point_height-self.line_height)/2
        if mark_check:
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_side_color))
            cr.rectangle(x + self.point_width/2, mark_y, self.mark_width, self.mark_height)
            cr.fill()

    def __progressbar_scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_DOWN or event.direction == gtk.gdk.SCROLL_LEFT:
            step = -5
        elif event.direction == gtk.gdk.SCROLL_UP or event.direction == gtk.gdk.SCROLL_RIGHT:
            step = 5
        else:
            step = 0

        # one step increase/decrease 5%
        value = self.value + step * (self.value_max - self.value_min) / 100.0
        if value > self.value_max:
            value = self.value_max
        if value < 0:
            value = 0
        self.set_value(value + self.value_min)
        self.emit("value-changed", self.value + self.value_min)

        return True

    def __progressbar_press_event(self, widget, event):
        widget.grab_add()
        temp_value = float(widget.allocation.width - self.point_width)
        temp_value = ((float((event.x - self.point_width/2)) / temp_value) * self.value_max) # get value.
        value = max(min(self.value_max, temp_value), 0)
        if value != self.value:
            self.set_enable(True)
        self.drag = True

        print value, self.magnetic_values
        for (magnetic_value, magnetic_range) in self.magnetic_values:
            if magnetic_value - magnetic_range <= value <= magnetic_value + magnetic_range:
                value = magnetic_value
                break

        self.value = value
        self.set_value(self.value + self.value_min)
        self.emit("value-changed", self.value + self.value_min)

    def __progressbar_release_event(self, widget, event):
        widget.grab_remove()
        self.drag = False

    def __progressbar_motion_notify_event(self, widget, event):
        if self.drag:
            self.set_enable(True)
            width = float(widget.allocation.width - self.point_width)
            temp_value = (float((event.x - self.point_width/2)) /  width) * self.value_max
            self.value = max(min(self.value_max, temp_value), 0) # get value.
            self.set_value(self.value + self.value_min)
            self.emit("value-changed", self.value + self.value_min)

    def add_mark(self, value, position_type, markup):
        '''
        Add mark at value.

        @param value: the value at which the mark is placed, must be between the lower and upper limits of the scales' adjustment.
        @param position_type: Where to draw the mark.
        @param markup: Text to be shown at the mark, using Pango markup, or None.
        '''
        if self.value_min <= value <= self.value_max+self.value_min:
            self.position_list.append((value, position_type, markup))
        else:
            print "error:input value_min <= value <= value_max!!"

    def set_value(self, value):
        '''
        Set value.

        @param value: The new value of the range.
        '''
        self.value = max(min(self.value_max, value - self.value_min), 0)
        self.queue_draw()

    def get_value(self):
        '''
        Get value.

        @return: Return the value of range.
        '''
        return self.value + self.value_min

    def set_enable(self, enable_bool):
        '''
        Grey scalebar, the effect of this function is different with set_sensitive.
        set_sensitive will grey widget and make user can't interact with widget.
        set_enable just grey widget, widget will active again when you interact it.

        @param enable_bool: Set as False to grey widget.
        '''
        self.enable_check = enable_bool
        self.queue_draw()

    def get_enable(self, enable_bool):
        '''
        Get the enable status of scalebar.

        @return: Return True if scalebar is enable.
        '''
        return self.enable_check

    def set_magnetic_values(self, magnetic_values):
        self.magnetic_values = magnetic_values

gobject.type_register(HScalebar)

class VScalebar(gtk.VScale):
    '''
    VScalebar.

    @undocumented: expose_v_scalebar
    @undocumented: press_progressbar
    '''

    def __init__(self,
                 upper_fg_dpixbuf,
                 upper_bg_dpixbuf,
                 middle_fg_dpixbuf,
                 middle_bg_dpixbuf,
                 bottom_fg_dpixbuf,
                 bottom_bg_dpixbuf,
                 point_dpixbuf,
                 ):
        '''
        Initialize VScalebar class.

        @param upper_fg_dpixbuf: Upper foreground pixbuf.
        @param upper_bg_dpixbuf: Upper background pixbuf.
        @param middle_fg_dpixbuf: Middle foreground pixbuf.
        @param middle_bg_dpixbuf: Middle background pixbuf.
        @param bottom_fg_dpixbuf: Bottom foreground pixbuf.
        @param bottom_bg_dpixbuf: Bottom background pixbuf.
        @param point_dpixbuf: Pointer pixbuf.
        '''
        gtk.VScale.__init__(self)

        self.set_draw_value(False)
        self.set_range(0, 100)
        self.__has_point = True
        self.set_inverted(True)
        self.upper_fg_dpixbuf = upper_fg_dpixbuf
        self.upper_bg_dpixbuf = upper_bg_dpixbuf
        self.middle_fg_dpixbuf = middle_fg_dpixbuf
        self.middle_bg_dpixbuf = middle_bg_dpixbuf
        self.bottom_fg_dpixbuf = bottom_fg_dpixbuf
        self.bottom_bg_dpixbuf = bottom_bg_dpixbuf
        self.point_dpixbuf = point_dpixbuf
        self.cache_bg_pixbuf = CachePixbuf()
        self.cache_fg_pixbuf = CachePixbuf()

        self.set_size_request(self.point_dpixbuf.get_pixbuf().get_height(), -1)

        self.connect("expose-event", self.expose_v_scalebar)
        self.connect("button-press-event", self.press_progressbar)

    def expose_v_scalebar(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Init pixbuf.
        upper_fg_pixbuf = self.upper_fg_dpixbuf.get_pixbuf()
        upper_bg_pixbuf = self.upper_bg_dpixbuf.get_pixbuf()
        middle_fg_pixbuf = self.middle_fg_dpixbuf.get_pixbuf()
        middle_bg_pixbuf = self.middle_bg_dpixbuf.get_pixbuf()
        bottom_fg_pixbuf = self.bottom_fg_dpixbuf.get_pixbuf()
        bottom_bg_pixbuf = self.bottom_bg_dpixbuf.get_pixbuf()
        point_pixbuf = self.point_dpixbuf.get_pixbuf()

        upper_value = self.get_adjustment().get_upper()
        lower_value = self.get_adjustment().get_lower()
        total_length = max(upper_value - lower_value, 1)
        point_width = point_pixbuf.get_width()
        point_height = point_pixbuf.get_height()

        line_width = upper_bg_pixbuf.get_width()
        side_height = upper_bg_pixbuf.get_height()

        x, y, w, h  = rect.x, rect.y + point_height, rect.width, rect.height - point_height - point_height / 2
        line_x = x + (point_width - line_width / 1.5) / 2
        point_y = h - int((self.get_value() - lower_value ) / total_length * h)
        value = int((self.get_value() - lower_value ) / total_length * h)

        self.cache_bg_pixbuf.scale(middle_bg_pixbuf, line_width, h - side_height * 2 + point_height / 2)
        draw_pixbuf(cr, upper_bg_pixbuf, line_x, y - point_height / 2)
        draw_pixbuf(cr, self.cache_bg_pixbuf.get_cache(), line_x, y + side_height - point_height / 2)
        draw_pixbuf(cr, bottom_bg_pixbuf, line_x, y + h - side_height)

        if value > 0:
            self.cache_fg_pixbuf.scale(middle_fg_pixbuf, line_width, value)
            draw_pixbuf(cr, self.cache_fg_pixbuf.get_cache(), line_x, y + point_y - side_height)
        draw_pixbuf(cr, bottom_fg_pixbuf, line_x, y + h - side_height)

        if self.get_value() == upper_value:
            draw_pixbuf(cr, upper_fg_pixbuf, line_x, y - point_height / 2)

        if self.__has_point:
            draw_pixbuf(cr, point_pixbuf, x, y + point_y - side_height / 2 - point_height / 2)

        return True

    def press_progressbar(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.
        '''
        if is_left_button(event):
            rect = widget.allocation
            lower_value = self.get_adjustment().get_lower()
            upper_value = self.get_adjustment().get_upper()
            point_height = self.point_dpixbuf.get_pixbuf().get_height()
            self.set_value(upper_value - ((event.y - point_height / 2) / (rect.height - point_height)) * (upper_value - lower_value) )
            self.queue_draw()

        return False

    def set_has_point(self, value):
        '''
        Set has point.

        @param value: Set True to make scalebar have point.
        '''
        self.__has_point = value

    def get_has_point(self):
        '''
        Get has point.

        @return: Return True if scalebar have point.
        '''
        return self.__has_point

gobject.type_register(VScalebar)
