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
import gobject
import copy

def LinerInterpolator(factor, lower, upper):
    return factor * (upper - lower)
def RandomInterpolator(base, offset, *args):
    import random
    return random.randint(base-offset/2, base+offset/2)


class Animation:
    def __init__(self, widgets, property, duration, ranges, interpolator=LinerInterpolator):
        self.delay = 50
        try:
            widgets[0]
            #   FIXME: should use weakset or other things
            self.widgets = widgets
            #self.widgets = copy.weakref.WeakSet(widgets)
        except:
            self.widgets = [copy.weakref.ref(widgets)]

        if isinstance(ranges, tuple):
            self.ranges = ranges
        else:
            self.ranges = (ranges,)


        self.duration = duration
        self.interpolator = interpolator
        self.time = 0
        self.animation_id = None
        self.start_id = None
        self.other_concurent = []
        self.other_after = []

        def set_method1(*values):
            for widget in self.widgets:
                if isinstance(widget, copy.weakref.ref):
                    property(widget(), *values)
                else:
                    property(widget, *values)

        def set_method2(*values):
            for widget in self.widgets:
                if isinstance(widget, copy.weakref.ref):
                    widget().set_property(property, *values)
                else:
                    widget.set_property(property, *values)


        if callable(property):
            self.set_method = set_method1
        else:
            self.set_method = set_method2

    def set_delay(self, delay):
        self.delay = delay

    def init(self, values=None):
        if isinstance(values, list):
            self.set_method(*values)
        else:
            self.set_method(values)
        self.time = 0
    def init_all(self, values):
        if isinstance(values, list):
            values.reverse()
            self.init(values.pop())
            for o in self.other_concurent:
                value = values.pop()
                o.init(value)
        else:
            raise Warning("init_all should init multi animation")

    def start_after(self, time):
        if self.start_id:
            gobject.source_remove(self.start_id)
        self.start_id = gobject.timeout_add(time, self.start)
        for o in self.other_concurent:
            o.start_after(time)


    def start(self):
        self.time = 0
        self.animation_id = gobject.timeout_add(self.delay, self.compute)
        for o in self.other_concurent:
            o.start()
        return False

    def stop(self):
        if self.animation_id:
            gobject.source_remove(self.animation_id)
        for o in self.other_concurent:
            o.start()

    def compute(self):
        if self.time >= self.duration+self.delay:
            return False

        values = []
        for r in self.ranges:
            factor = float(self.time) / self.duration
            value = self.interpolator(factor, r[0], r[1])
            values.append(r[0]+value)

        self.set_method(*values)

        for o in self.other_concurent:
            o.compute()

        self.time += self.delay

        return True

    def __mul__(self, other):
        r = copy.deepcopy(self)
        r.other_concurent.append(other)
        return r

    def __add__(self, other):
        raise NotImplemented

if __name__ == "__main__":
    import gtk
    win = gtk.Window()
    win.set_position(gtk.WIN_POS_CENTER)

    box = gtk.VBox()

    ani1 = Animation(win, lambda widget, v1, v2: widget.move(int(v1), int(v2)), 1000, ([200, 400], [200, 400]))
    b1 = gtk.Button("moving....(set multip value)")
    b1.connect('clicked', lambda w: ani1.start())
    box.add(b1)

    ani2 = Animation(win, "opacity", 1000, [0, 1])
    b2 = gtk.Button("opacity(set single value)")
    b2.connect('clicked', lambda w: ani2.start())
    box.add(b2)

    ani3 = ani2 * ani1  # animation  composite
    b3 = gtk.Button("composited animation")
    b3.connect('clicked', lambda w: ani3.start())
    box.add(b3)

    ani4 = Animation(win,
            lambda w, v1, v2: w.move(w.get_position()[0]+int(v1), w.get_position()[1]+int(v2)),
            800, ([0, 0], [0,0]), lambda *args : RandomInterpolator(00, 20))
    b4 = gtk.Button("vibration")
    b4.connect('clicked', lambda w: ani4.start())
    box.add(b4)

    ani5 = Animation(win, lambda w, v1, v2: w.resize(int(v1), int(v2)), 300, ([20, 300], [20, 300]))
    b5 = gtk.Button("smaller")
    b5.connect('clicked', lambda w: ani5.start())
    box.add(b5)

    win.add(box)
    win.show_all()
    win.connect('destroy', gtk.main_quit)

    gtk.main()
