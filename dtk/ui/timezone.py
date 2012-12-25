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

class TimeZone(gtk.EventBox):
    __gsignals__ = {
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),}
    
    def __init__(self, timezone=0, width=800, height=409, padding_top=0, padding_left=0):
        gtk.EventBox.__init__(self)
        
        self.__timezone = timezone + 9
        
        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)

        self.padding_top = padding_top
        self.padding_left = padding_left

        self.__const_width = 800
        self.__const_height = 409

        self.bg_pixbuf = ui_theme.get_pixbuf("timezone/bg.png")
        self.timezone_pixbuf = []
        i = -9
        while i <= 13:
            self.timezone_pixbuf.append(ui_theme.get_pixbuf("timezone/timezone_%d.png" % i))

            i += 1

        self.connect("button-press-event", self.__button_press)
        self.connect("expose-event", self.__expose)
   
    def set_timezone(self, timezone):
        self.__timezone = timezone + 9
        if self.__timezone < 0:
            self.__timezone = 0

        if self.__timezone > 23:
            self.__timezone = 23

        self.queue_draw()
    
    def __button_press(self, widget, event):
        if event.x > self.width or event.y > self.height:
            return

        self.__timezone = int(event.x * 24 / self.width) - 2;
        if self.__timezone < 0:
            self.__timezone = 0

        if self.__timezone > 23:
            self.__timezone = 23

        self.emit("changed", self.__timezone - 9)

        self.window.invalidate_rect(self.allocation, True)

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y = rect.x, rect.y
        x -= self.padding_left
        y -= self.padding_top

        with cairo_state(cr):
            bg_dpixbuf = self.bg_pixbuf.get_pixbuf()
            timezone_dpixbuf = []
            i = 0
            while i < len(self.timezone_pixbuf):
                timezone_dpixbuf.append(self.timezone_pixbuf[i].get_pixbuf())

                i += 1

            if self.width < self.__const_width or self.height < self.__const_height:
                bg_dpixbuf = bg_dpixbuf.scale_simple(self.width, self.height, gtk.gdk.INTERP_BILINEAR)

                i = 0
                while i < len(timezone_dpixbuf):
                    timezone_dpixbuf[i] = timezone_dpixbuf[i].scale_simple(self.width, self.height, gtk.gdk.INTERP_BILINEAR)

                    i += 1
            
            draw_pixbuf(cr, bg_dpixbuf, x, y)
            draw_pixbuf(cr, 
                        timezone_dpixbuf[self.__timezone], 
                        x, y)

        return True

gobject.type_register(TimeZone)
