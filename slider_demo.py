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

import gtk
import gobject
from dtk.ui.new_slider import HSlider
from dtk.ui.utils import color_hex_to_cairo

class TestWidget(gtk.DrawingArea):
    '''
    class docs
    '''
	
    def __init__(self, color):
        '''
        init docs
        '''
        gtk.DrawingArea.__init__(self)
        self.color = color
        
        self.connect("expose-event", self.expose)
        
    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        cr.set_source_rgb(*color_hex_to_cairo(self.color))
        cr.rectangle(0, 0, rect.width, rect.height)
        cr.fill()
        
        return True

if __name__ == "__main__":
    window = gtk.Window()
    window.set_size_request(400, 300)
    
    slider = HSlider()
    
    # widget1 = TestWidget("#FF0000")
    # widget2 = TestWidget("#00FF00")
    # widget3 = TestWidget("#0000FF")

    widget1 = gtk.Button("Button1")
    widget2 = gtk.Button("Button2")
    widget3 = gtk.Button("Button3")

    slider.append_page(widget1)
    slider.append_page(widget2)
    slider.append_page(widget3)
    
    window.add(slider)
    
    window.connect("destroy", lambda w: gtk.main_quit())
    gobject.timeout_add(3000, lambda : slider.slide_to_page(widget3, "right"))
    
    window.show_all()
    
    gtk.main()
