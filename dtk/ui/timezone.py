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
from skin_config import skin_config
import gobject
import gtk

'''
TODO: Resizable can be drag toward downward
'''
class TimeZone(gtk.EventBox):
    def __init__(self, timezone=11, width=800, height=409):
        gtk.EventBox.__init__(self)
        
        self.timezone = timezone
        
        self.width = width
        self.height = height
        self.__const_width = 800
        self.__const_height = 409

        self.bg_pixbuf = ui_theme.get_pixbuf("timezone/bg.png")
        self.timezone_pixbuf = []
        i = -11
        while i < 14:
            self.timezone_pixbuf.append(ui_theme.get_pixbuf("timezone/timezone_%d.png" % i))

            i += 1

        self.connect("button-press-event", self.__button_press)
        self.connect("expose-event", self.__expose)
   
    def __button_press(self, widget, event):
        if event.x > self.width or event.y > self.height:
            return

        self.timezone = int(event.x * 25 / self.width);

        self.window.invalidate_rect(self.allocation, True)

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y = rect.x, rect.y

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
                        timezone_dpixbuf[self.timezone], 
                        x, y)

        return True

gobject.type_register(TimeZone)
