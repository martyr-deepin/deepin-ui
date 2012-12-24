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
from button import Button
from label import Label
from constant import ALIGN_START, ALIGN_MIDDLE
import threading as td
import time

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

class DateTime(gtk.VBox):
    def __init__(self, 
                 hour_value, 
                 minute_value, 
                 second_value = None, 
                 width=200, 
                 height=100, 
                 box_spacing=100):
        gtk.VBox.__init__(self)
        
        self.hour_value = hour_value
        self.minute_value = minute_value
        self.second_value = second_value
        
        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)

        self.clockface = ui_theme.get_pixbuf("datetime/clockface.png")
        self.hourhand = ui_theme.get_pixbuf("datetime/hourhand.png")
        self.minhand = ui_theme.get_pixbuf("datetime/minhand.png")
        self.sechand = ui_theme.get_pixbuf("datetime/sechand.png")

        self.connect("expose-event", self.__expose)

        SecondThread(self).start()

    def __expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        self.hour_value = time.localtime().tm_hour
        self.minute_value = time.localtime().tm_min
        self.second_value = time.localtime().tm_sec

        with cairo_state(cr):
            draw_pixbuf(cr, self.clockface.get_pixbuf(), x, y)
            draw_pixbuf(cr, 
                        self.hourhand.get_pixbuf(), 
                        x + (self.clockface.get_pixbuf().get_width() - self.hourhand.get_pixbuf().get_width()) / 2, 
                        y)
            draw_pixbuf(cr, 
                        self.minhand.get_pixbuf(), 
                        x + (self.clockface.get_pixbuf().get_width() - self.minhand.get_pixbuf().get_width()) / 2, 
                        y)
            draw_pixbuf(cr, 
                        self.sechand.get_pixbuf(), 
                        x + (self.clockface.get_pixbuf().get_width() - self.sechand.get_pixbuf().get_width()) / 2, 
                        y)

gobject.type_register(DateTime)
