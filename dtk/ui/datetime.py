#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Zhai Xiang
#
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from draw import draw_pixbuf, propagate_expose, cairo_state
from theme import ui_theme
import gobject
import gtk
from math import radians
import time
import threading as td

__all__ = ["DateTimeHTCStyle", "DateTime"]

class SecondThread(td.Thread):
    def __init__(self, ThisPtr):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = ThisPtr

    def run(self):
        try:
            while True:
                self.ThisPtr.invalidate()
                time.sleep(1)
        except Exception, e:
            print "class SecondThread got error %s" % e

class DateTimeHTCStyle(gtk.VBox):
    '''
    DateTime with HTC style.

    @undocumented: invalidate
    '''

    def __init__(self,
                 width=500,
                 height=125,
                 is_24hour=True,
                 pixbuf_spacing=10,
                 comma_spacing=30,
                 sec_visible=False):
        '''
        Initialize DateTimeHTCStyle class.

        @param width: Width of widget, default is 500 pixels.
        @param height: Height of widget, default is 125 pixels.
        @param is_24hour: Whether use 24 hours format, default is True.
        @param pixbuf_spacing: Spacing around widget pixbuf, default is 10 pixels.
        @param comma_spacing: Spacing around comma, default is 30 pixels.
        @param sec_visible: Whether display second, default is False.
        '''
        gtk.VBox.__init__(self)

        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)

        self.is_24hour = is_24hour
        self.pixbuf_spacing = pixbuf_spacing
        self.comma_spacing = comma_spacing
        self.sec_visible = sec_visible

        self.time_pixbuf = []
        i = 0
        while i < 10:
            self.time_pixbuf.append(ui_theme.get_pixbuf("datetime/%d.png" % i))

            i += 1

        self.connect("expose-event", self.__expose)

        SecondThread(self).start()

    def invalidate(self):
        self.queue_draw()

    def get_is_24hour(self):
        '''
        Whether is use 24 hour format.

        @return: Return True if is 24 hours format.
        '''
        return self.is_24hour

    def set_is_24hour(self, is_24hour):
        '''
        Set 24 hour format.

        @param is_24hour: Set this option as True to use 24 hours.
        '''
        self.is_24hour = is_24hour
        self.queue_draw()

    def get_sec_visible(self):
        '''
        Whether second is visible.

        @return: Return True if seconds is visible.
        '''
        return self.sec_visible

    def set_sec_visible(self, sec_visible):
        '''
        Set second visible.

        @param sec_visible: Set this option as True to make second visible.
        '''
        self.sec_visible = sec_visible
        self.queue_draw()

    def __time_split(self, value):
        ten = int(value / 10);
        bit = value - ten * 10;

        return (ten, bit)

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        hour = time.localtime().tm_hour
        hour_ten, hour_bit = self.__time_split(hour)
        if not self.is_24hour and hour > 12:
            hour_ten, hour_bit = self.__time_split(hour - 12)
        min_ten, min_bit = self.__time_split(time.localtime().tm_min)
        sec_ten, sec_bit = self.__time_split(time.localtime().tm_sec)

        time_pixbuf_width = 0

        draw_pixbuf(cr, self.time_pixbuf[hour_ten].get_pixbuf(), x, y)
        time_pixbuf_width = self.time_pixbuf[hour_ten].get_pixbuf().get_width() + self.pixbuf_spacing
        draw_pixbuf(cr,
                    self.time_pixbuf[hour_bit].get_pixbuf(),
                    x + time_pixbuf_width,
                    y)
        time_pixbuf_width += self.time_pixbuf[hour_bit].get_pixbuf().get_width() + self.comma_spacing
        draw_pixbuf(cr,
                    self.time_pixbuf[min_ten].get_pixbuf(),
                    x + time_pixbuf_width,
                    y)
        time_pixbuf_width += self.time_pixbuf[min_ten].get_pixbuf().get_width() + self.pixbuf_spacing
        draw_pixbuf(cr,
                    self.time_pixbuf[min_bit].get_pixbuf(),
                    x + time_pixbuf_width,
                    y)

        if not self.sec_visible:
             return False

        time_pixbuf_width += self.time_pixbuf[min_bit].get_pixbuf().get_width() + self.comma_spacing
        draw_pixbuf(cr,
                    self.time_pixbuf[sec_ten].get_pixbuf(),
                    x + time_pixbuf_width,
                    y)
        time_pixbuf_width += self.time_pixbuf[sec_ten].get_pixbuf().get_width() + self.pixbuf_spacing
        draw_pixbuf(cr,
                    self.time_pixbuf[sec_bit].get_pixbuf(),
                    x + time_pixbuf_width,
                    y)

        propagate_expose(widget, event)

        return True

gobject.type_register(DateTimeHTCStyle)

class DateTime(gtk.VBox):
    '''
    DateTime class.

    @undocumented: invalidate
    '''

    def __init__(self,
                 width=180,
                 height=180):
        '''
        Initialize DateTime class.

        @param width: Width of widget, default is 180 pixels.
        @param height: Height of widget, default is 180 pixels.
        '''
        gtk.VBox.__init__(self)

        self.hour_value = time.localtime().tm_hour
        self.minute_value = time.localtime().tm_min
        self.second_value = time.localtime().tm_sec

        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)

        self.clockface = ui_theme.get_pixbuf("datetime/clockface.png")
        self.clockface_width = self.clockface.get_pixbuf().get_width()
        self.clockface_height = self.clockface.get_pixbuf().get_height()
        self.hourhand = ui_theme.get_pixbuf("datetime/hourhand.png")
        self.hourhand_width = self.hourhand.get_pixbuf().get_width()
        self.hourhand_height = self.hourhand.get_pixbuf().get_height()
        self.minhand = ui_theme.get_pixbuf("datetime/minhand.png")
        self.minhand_width = self.minhand.get_pixbuf().get_width()
        self.minhand_height = self.minhand.get_pixbuf().get_height()
        self.sechand = ui_theme.get_pixbuf("datetime/sechand.png")
        self.sechand_width = self.sechand.get_pixbuf().get_width()
        self.sechand_height = self.sechand.get_pixbuf().get_height()

        self.connect("expose-event", self.__expose)

        SecondThread(self).start()

    def invalidate(self):
        self.queue_draw()

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        ox = x + self.clockface_width * 0.5

        self.hour_value = time.localtime().tm_hour
        self.minute_value = time.localtime().tm_min
        self.second_value = time.localtime().tm_sec

        with cairo_state(cr):
            draw_pixbuf(cr, self.clockface.get_pixbuf(), x, y)

        #hour
        with cairo_state(cr):
            oy = y + self.hourhand_height * 0.5
            cr.translate(ox, oy)
            cr.rotate(radians(360 * self.hour_value / 12))
            cr.translate(-self.hourhand_width * 0.5, -self.hourhand_height * 0.5)
            draw_pixbuf(cr, self.hourhand.get_pixbuf(), 0, 0)

        #minute
        with cairo_state(cr):
            oy = y + self.minhand_height * 0.5
            cr.translate(ox, oy)
            cr.rotate(radians(360 * self.minute_value / 60))
            cr.translate(-self.minhand_width * 0.5, -self.minhand_height * 0.5)
            draw_pixbuf(cr, self.minhand.get_pixbuf(), 0, 0)

        #second
        with cairo_state(cr):
            oy = y + self.sechand_height * 0.5
            cr.translate(ox, oy)
            cr.rotate(radians(360 * self.second_value / 60))
            cr.translate(-self.sechand_width * 0.5, -self.sechand_height * 0.5)
            draw_pixbuf(cr, self.sechand.get_pixbuf(), 0, 0)

gobject.type_register(DateTime)
