#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
#
# Author:     Xia Bin <xiabin@linuxdeepin.com>
# Maintainer: Xia Bin <xiabin@linuxdeepin.com>
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

import gtk
import gobject
from utils import is_in_rect

class Paned(gtk.Paned):
    def __init__(self):
        gtk.Paned.__init__(self)
        self.bheight = 60
        self.saved_position = -1

    def do_expose_event(self, e):
        #gtk.Paned.do_expose_event(self, e)
        self.draw_handle(e)
        gtk.Container.do_expose_event(self, e)

        return False

    def draw_handle(self, e):
        handle = self.get_handle_window()
        cr = handle.cairo_create()
        cr.set_source_rgba(1, 0,0, 0.8)
        #cr.paint()
        (width, height) = handle.get_size()
        cr.rectangle(0, 0, 1, height)
        cr.rectangle(0, (height-self.bheight)/2,  width, self.bheight)
        cr.fill()
        pass

    def is_in_button(self, x, y):
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if is_in_rect((x, y), (0, (height-self.bheight)/2, width, self.bheight)):
            return True
        else:
            return False

    def do_enter_notify_event(self, e):
        print e
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.is_in_button(e.x, e.y):
            handle.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
            print "enter button"
        else:
            handle.set_cursor(self.cursor_type)
            print "...."


    def do_button_press_event(self, e):
        if self.is_in_button(e.x, e.y):
            print "enter button"
            if self.saved_position == -1:
                self.saved_position = self.get_position()
                self.set_position(0)
            else:
                self.set_position(self.saved_position)
                self.saved_position = -1
        else:
            gtk.Paned.do_button_press_event(self, e)
        return True

    def do_size_allocate(self, e):
        print "do_size"
        gtk.Paned.do_size_allocate(self, e)
        self.handle_size = 1

class HPaned(Paned):
    def __init__(self):
        Paned.__init__(self)
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)

class VPaned(Paned):
    def __init__(self):
        Paned.__init__(self)
        self.set_orientation(gtk.ORIENTATION_VERTICAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_V_DOUBLE_ARROW)



gobject.type_register(Paned)
gobject.type_register(HPaned)
gobject.type_register(VPaned)



if __name__ == '__main__':
    w = gtk.Window()
    w.set_size_request(700, 400)
    p = HPaned()
    p.add1(gtk.Label("1222111111111111111111111111111"))
    p.add2(gtk.Label("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
    w.add(p)
    w.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('yellow'))
    w.connect('destroy', gtk.main_quit)
    w.show_all()
    gtk.main()
