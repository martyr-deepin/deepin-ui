#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Zhai Xiang
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

from draw import draw_pixbuf, cairo_state
from theme import ui_theme
import gobject
import gtk
from math import radians
import time
import threading as td

class HourThread(td.Thread):
    def __init__(self, ThisPtr):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = ThisPtr

    def run(self):
        try:
            while True:
                self.ThisPtr.queue_draw()
                time.sleep(3600)
        except Exception, e:
            print "class HourThread got error %s" % e

class MinuteThread(td.Thread):
    def __init__(self, ThisPtr):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = ThisPtr

    def run(self):
        try:
            while True:
                self.ThisPtr.queue_draw()
                time.sleep(60)
        except Exception, e:
            print "class MinuteThread got error %s" % e

class SecondThread(td.Thread):
    def __init__(self, ThisPtr):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = ThisPtr

    def run(self):
        try:
            while True:
                self.ThisPtr.queue_draw()
                time.sleep(1)
        except Exception, e:
            print "class SecondThread got error %s" % e

class DateTimeHTCStyle(gtk.VBox):
    def __init__(self, 
                 width=180, 
                 height=180, 
                 spacing=20, 
                 sec_visible=False):
        gtk.VBox.__init__(self)

        self.spacing = spacing
        self.sec_visible = sec_visible

        self.time_pixbuf = []
        i = 0
        while i < 10:
            self.time_pixbuf.append(ui_theme.get_pixbuf("datetime/%d.png" % i))

            i += 1

        self.connect("expose-event", self.__expose)

        SecondThread(self).start()
        MinuteThread(self).start()                                              
        HourThread(self).start()

    def __time_split(self, value):
        ten = int(value / 10);
        bit = value - ten * 10;
        return (ten, bit)

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()                                       
        rect = widget.allocation                                                
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        hour_ten, hour_bit = self.__time_split(time.localtime().tm_hour)
        min_ten, min_bit = self.__time_split(time.localtime().tm_min)
        sec_ten, sec_bit = self.__time_split(time.localtime().tm_sec)

        draw_pixbuf(cr, self.time_pixbuf[hour_ten].get_pixbuf(), x, y)
        time_pixbuf_width = self.time_pixbuf[hour_ten].get_pixbuf().get_width()
        draw_pixbuf(cr, 
                    self.time_pixbuf[hour_bit].get_pixbuf(), 
                    x + time_pixbuf_width, 
                    y)
        time_pixbuf_width += self.time_pixbuf[hour_bit].get_pixbuf().get_width() + self.spacing
        draw_pixbuf(cr, 
                    self.time_pixbuf[min_ten].get_pixbuf(), 
                    x + time_pixbuf_width, 
                    y)
        time_pixbuf_width += self.time_pixbuf[min_ten].get_pixbuf().get_width()
        draw_pixbuf(cr, 
                    self.time_pixbuf[min_bit].get_pixbuf(), 
                    x + time_pixbuf_width, 
                    y)
        if not self.sec_visible:
            return False

        time_pixbuf_width += self.time_pixbuf[min_bit].get_pixbuf().get_width() + self.spacing
        draw_pixbuf(cr, 
                    self.time_pixbuf[sec_ten].get_pixbuf(), 
                    x + time_pixbuf_width, 
                    y)
        time_pixbuf_width += self.time_pixbuf[sec_ten].get_pixbuf().get_width()
        draw_pixbuf(cr, 
                    self.time_pixbuf[sec_bit].get_pixbuf(), 
                    x + time_pixbuf_width, 
                    y)

gobject.type_register(DateTimeHTCStyle)

class DateTime(gtk.VBox):
    def __init__(self, 
                 width=180, 
                 height=180):
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
        MinuteThread(self).start()
        HourThread(self).start()

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
        '''
        hour
        '''
        with cairo_state(cr):
            oy = y + self.hourhand_height * 0.5
            cr.translate(ox, oy)
            cr.rotate(radians(360 * self.hour_value / 12))
            cr.translate(-self.hourhand_width * 0.5, -self.hourhand_height * 0.5)
            draw_pixbuf(cr, self.hourhand.get_pixbuf(), 0, 0)
        '''
        minute
        '''
        with cairo_state(cr):
            oy = y + self.minhand_height * 0.5
            cr.translate(ox, oy)
            cr.rotate(radians(360 * self.minute_value / 60))
            cr.translate(-self.minhand_width * 0.5, -self.minhand_height * 0.5)
            draw_pixbuf(cr, self.minhand.get_pixbuf(), 0, 0)
        '''
        second
        '''
        with cairo_state(cr):
            oy = y + self.sechand_height * 0.5
            cr.translate(ox, oy) 
            cr.rotate(radians(360 * self.second_value / 60))
            cr.translate(-self.sechand_width * 0.5, -self.sechand_height * 0.5)
            draw_pixbuf(cr, self.sechand.get_pixbuf(), 0, 0)

gobject.type_register(DateTime)
