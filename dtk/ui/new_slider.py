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
from timeline import Timeline, CURVE_SINE

class HSlider(gtk.Viewport):
    '''
    class docs
    '''
	
    __gsignals__ = {
        "completed_slide" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, slide_time=500):
        '''
        init docs
        '''
        gtk.Viewport.__init__(self)
        self.slide_time = slide_time
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.page_width = 0
        self.page_height = 0
        self.active_widget = None
        self.pre_widget = None
        self.pages = []
        
        self.layout = gtk.HBox(True)
        self.event_box = gtk.EventBox()
        
        self.event_box.add(self.layout)
        self.add(self.event_box)
        
        self.connect("realize", self.slider_realize)
        self.connect("size-allocate", self.slider_allocate)
        
    def slider_realize(self, widget):
        self.update_size()

    def slider_allocate(self, widget, rect):
        self.update_size()
        
    def update_size(self):
        rect = self.get_allocation()
        self.page_width = rect.width
        self.page_height = rect.height
        
        self.get_hadjustment().set_upper(rect.width*2)
        for c in self.pages:
            c.set_size_request(self.page_width, self.page_height)

    def append_page(self, widget):
        self.pages.append(widget)
        
        #if self.active_widget == None:
            #self.active_widget = widget
        
    def slide_to_page(self, target_widget, direction):
        if self.active_widget != target_widget:
            self.set_to_page(target_widget)
            timeline = Timeline(self.slide_time, CURVE_SINE)
            if direction == "right":
                timeline.connect('update', lambda source, status: 
                                self.get_hadjustment().set_value(int(round(status*self.page_width))))
            else:
                self.layout.reorder_child(self.active_widget, 0)
                timeline.connect('update', lambda source, status: 
                                self.get_hadjustment().set_value(self.page_width - int(round(status*self.page_width))))

            timeline.connect("completed", lambda source: self.completed(target_widget))
            timeline.run()
        
    def completed(self, widget):    
        if self.pre_widget:
            self.layout.remove(self.pre_widget)
        
        self.emit("completed_slide")
    
    def set_to_page(self, widget):
        if self.pre_widget == None:
            self.pre_widget = widget
            self.active_widget = widget
        elif self.pre_widget != self.active_widget:
            self.pre_widget = self.active_widget
            self.active_widget = widget
        else:
            self.active_widget = widget

        if not self.active_widget.parent:
            self.layout.pack_start(self.active_widget, True, True, 0)
        self.layout.show_all()

gobject.type_register(HSlider)
