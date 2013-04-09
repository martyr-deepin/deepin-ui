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

import dtk.ui
import dtk.ui.application
import dtk.ui.slider
import dtk.ui.entry
import dtk.ui.button
import dtk.ui.label 

import gtk
import gobject

def slider_loop(slider, widget_list):
    global i
    widget_num = len(widget_list)
    slider.slide_to_page(widget_list[i % widget_num], None)
    i += 1
    return True

if __name__ == "__main__":

    #win = gtk.Window()
    #win.connect("destroy", gtk.main_quit)
    #win.set_size_request(400, 250)

    app = dtk.ui.application.Application()
    app.set_default_size(400, 250)
    app.add_titlebar(
        ["theme", "menu", "max", "min", "close"], 
        None, 
        "深度图形库",
        "/home/andy/deepin-ui/loooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooony.py",
    )
    
    slider = dtk.ui.new_slider.HSlider()
    label = dtk.ui.label.Label("Slider Demo")
    label_align = gtk.Alignment(0.5, 0.5, 0, 0)
    label_align.add(label)
    slider.to_page_now(label_align)
    
    widget1 = gtk.Alignment(0.5, 0.5, 0, 0)
    button1 = dtk.ui.button.Button()
    button1.set_size_request(200, 22)
    widget1.add(button1)

    widget2 = gtk.Alignment(0.5, 0.5, 0, 0)
    button2 = gtk.Button("Button2")
    widget2.add(button2)

    widget3 = gtk.Alignment(0.5, 0.5, 0, 0)
    text_entry = dtk.ui.new_entry.InputEntry()
    text_entry.set_size(100, 22)
    widget3.add(text_entry)

    widget_list = [label_align, widget1, widget2, widget3]
    
    global i
    i = 1
    gobject.timeout_add(3000, slider_loop, slider, widget_list)

    #win.add(slider)
    #win.show_all()
    #gtk.main()
    app.main_box.pack_start(slider)
    app.run()
