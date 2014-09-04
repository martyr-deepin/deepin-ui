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

import pseudo_skin
import gtk
from color_selection import ColorButton
from gtk import gdk
import tooltip as TT

__all__ = []

def customTooltip_cb():
    box = gtk.VBox()
    #box.set_size_request(800, 400)
    b = gtk.Button("abcdsdf")
    l = gtk.Label("huhuhuhuhuhulabellooooooooooooooooooooooooooooooooooooooooooooA")
    #b.connect('destroy', show_d)
    #l.connect('destroy', show_d)
    box.add(b)
    box.add(l)
    return box

def show_d(w, e):
    print "destroing..", type(w), id(w)

def gen_control(widget):
    box = gtk.VBox()
    t = gtk.CheckButton("NeedShadow")
    t.set_active(True)
    t.connect('toggled', lambda w: TT.has_shadow(widget, w.get_active()))
    box.pack_start(t, False, False)
    TT.text(t, "toggle the shadow")

    winfo = TT.WidgetInfo.get_info(widget)
    t1 = gtk.Entry()
    t1.set_text(winfo.text or "")
    t1.connect('activate', lambda w: TT.text(widget, w.get_text()))
    box.pack_start(t1, False, False)

    t2 = gtk.SpinButton()
    t2.set_range(0, 10)
    t2.set_value((winfo.show_delay / 1000))
    t2.connect('value-changed', lambda w: TT.show_delay(widget, w.get_value_as_int() * 1000 + 100))
    box.pack_start(t2, False, False)

    t3 = ColorButton()
    t3.set_color(str(winfo.background))
    t3.connect('color-select', lambda w, e: TT.background(widget, gtk.gdk.Color(w.get_color())))
    box.pack_start(t3)

    t4 = gtk.SpinButton()
    t4.set_range(0, 100)
    t4.set_value(winfo.padding_r)
    t4.connect('value-changed', lambda w: TT.padding(widget, -1, -1, -1, w.get_value()))
    box.pack_start(t4, False, False)

    t5 = gtk.CheckButton("disable")
    t5.set_active(False)
    t5.connect('toggled', lambda w: TT.disable(widget, w.get_active()))
    box.pack_start(t5, False, False)

    #----------------------------------------------------------------------#
    TT.text(t1, "The text value if tooltip didn't has custom property")\
           (t2, "The show delay value")\
           (t3, "The background color")\
           (t4, "The pading right value")\
           (t5, "tmp disable tooltip")\
       .show_delay([t1,t2,t3,t4,t5], 200)\
       .background([t1,t2], gdk.Color("red"))\
       .set_value([t1,t2,t3,t4,t5], {'text_kargs': {"text_size":15}})
    #_____________________________________________________________________#
    return box


w = gtk.Window()
w.set_size_request(500, 500)
box = gtk.VBox()

b1 = gtk.Button("button")
b2 = gtk.Button("button1")

ls = gtk.HBox()
l1 = gtk.Label("label1")
l2 = gtk.Label("label2")
ls.add(l1)
ls.add(l2)

#----------------------how to use tooltip api-------------------------#
TT.show_delay([b1,b2,l1,l2], 1000)\
  .background(b1, gdk.Color("yellow"))(b2, gdk.Color("#95BE0D"))(l1,gdk.Color("blue"))\
  .custom(b1, customTooltip_cb)\
  .text([l1, l2], "tooliiiiit")(b2, "button2222", enable_gaussian=True)\
  .padding(l1, -1, -1, -1, 50)(b2, -1, -1, -1, 0)(b1, 0, 50, 50, 50)
#_____________________________________________________________________#



b1c = gen_control(b1)
b = gtk.HBox()
b.add(b1)
b.pack_start(b1c, False)
box.pack_start(b)

b2c = gen_control(b2)
b = gtk.HBox()
b.add(b2)
b.pack_start(b2c, False)
box.pack_start(b)

lc = gen_control(l1)
b = gtk.HBox()
b.add(ls)
b.pack_start(lc, False)
box.pack_start(b)

w.add(box)
w.connect('destroy', gtk.main_quit)
w.show_all()
gtk.main()
#run_with_profile(gtk.main, '/dev/shm/ttt')
