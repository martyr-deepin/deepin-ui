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

import math
import gobject
import gtk
import cairo

MODE_SPINNING = 0
MODE_STATIC = 1


def lighten_color(c):

    return gtk.gdk.Color(int(c.red * 1.1), int(c.green * 1.1), int(c.blue * 1.1))


class Throbber(gtk.Widget):

    __gtype_name__ = 'Throbber'

    def __init__(self):

        gtk.Widget.__init__(self)

        style = self.get_style()
        background = style.dark[gtk.STATE_NORMAL]
        self.color = style.dark[gtk.STATE_NORMAL]

        self.mode = MODE_STATIC
        self.progress = 0

        self.tmp_rotation = 0.0


    def do_realize(self):

        self.set_flags(self.flags() | gtk.REALIZED | gtk.NO_WINDOW)
        self.window = self.get_parent_window()
        self.style.attach(self.window)

        style = self.get_style()
        background = style.dark[gtk.STATE_NORMAL]
        self.color = style.dark[gtk.STATE_NORMAL]


    def do_size_request(self, requisition):

        width, height = 32, 32
        requisition.width = width
        requisition.height = height


    def do_size_allocate(self, allocation):
        self.allocation = allocation


    def do_expose_event(self, event):
        self._draw()


    def set_progress(self, progress):

        self.progress = progress
        if self.flags() & gtk.REALIZED:
            self.draw()


    def set_mode(self, mode):

        if self.mode == mode:
            return

        self.mode = mode

        if self.mode == MODE_SPINNING:
            gobject.timeout_add(50, self.update_spinning)


    def update_spinning(self):

        self.tmp_rotation += .1
        self.draw()

        if self.mode == MODE_SPINNING:
            return True
        else:
            return False


    def draw(self):

        if self.window:
            self.window.invalidate_rect(self.allocation, True)


    def _draw(self):

        def draw_tortenstueck(rotation, alpha=1):

            rotation *= 2 * math.pi

            ctx.save()

            ctx.arc(.5 * width, .5 * height, .45 * factor, -.555 * math.pi + rotation, -.445 * math.pi + rotation)
            ctx.arc_negative(.5 * width, .5 * height, .15 * factor, -.465 * math.pi + rotation, -.535 * math.pi + rotation)
            ctx.close_path()

            ctx.set_source_rgba(self.color.red / 65535.0, self.color.green / 65535.0, self.color.blue / 65535.0, alpha)
            ctx.fill()

            ctx.restore()

        width = self.allocation.width
        height = self.allocation.height

        factor = min(width, height)

        ctx = self.window.cairo_create()
        ctx.set_operator(cairo.OPERATOR_OVER)

        ctx.translate(self.allocation.x, self.allocation.y)
        ctx.set_line_width(1)


        if self.mode == MODE_STATIC:
            for i in xrange(0, int(self.progress * 10.0)):
                draw_tortenstueck(i / 10.0)
        else:
            draw_tortenstueck(self.tmp_rotation)

            for i in xrange(0, 10):
                alpha = math.cos((i / 10.0) * math.pi / 2.0)
                draw_tortenstueck(self.tmp_rotation - i * .1, alpha)


if __name__ == '__main__':
    win = gtk.Window()
    t = Throbber()
    t.set_mode(MODE_SPINNING)
    t.set_progress(.3)
    win.add(t)
    win.show_all()
    gtk.main()
