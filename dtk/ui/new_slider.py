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
        
        self.layout = gtk.HBox(True)
        self.event_box = gtk.EventBox()
        
        self.event_box.add(self.layout)
        self.add(self.event_box)
        
        self.connect("realize", self.slider_realize)
        self.connect("size-allocate", self.slider_allocate)
        
    def slider_realize(self, widget):
        self.update_size(self.get_allocation())        
        
    def slider_allocate(self, widget, rect):
        self.update_size(rect)
        
    def update_size(self, rect):
        self.page_width = rect.width
        self.page_height = rect.height
        
        width = self.page_width * len(self.layout.get_children())
        self.event_box.set_size_request(width, self.page_height)
        self.layout.set_size_request(width, self.page_height)
        self.get_hadjustment().set_upper(width)
        
        for (index, child) in enumerate(self.layout.get_children()):
            child.set_size_request(self.page_width, self.page_height)
        
        if self.active_widget:
            self.set_to_page(self.active_widget)
            
    def append_page(self, widget):
        self.layout.pack_start(widget, True, True, 0)
        
        if self.active_widget == None:
            self.active_widget = widget
        
    def slide_to_page(self, target_widget, direction):
        if self.active_widget != target_widget:
            if not direction in ["left", "right"]:
                raise Exception, "slide_to_page: please pass valid value of direction `left` or `right`"

            active_index = self.layout.get_children().index(self.active_widget)
            target_index = self.layout.get_children().index(target_widget)

            if active_index > target_index:
                if direction == "left":
                    reoreder_index = active_index - 1
                else:
                    reoreder_index = active_index
            else:
                if direction == "left":
                    reoreder_index = active_index
                else:
                    reoreder_index = active_index + 1
            
            self.layout.reorder_child(target_widget, reoreder_index)    
            self.set_to_page(self.active_widget)
            
            start_index = self.layout.get_children().index(self.active_widget)
            end_index = self.layout.get_children().index(target_widget)
            start_position = start_index * self.page_width
            end_position = end_index * self.page_width
            
            if start_position != end_position:
                timeline = Timeline(self.slide_time, CURVE_SINE)
                timeline.connect('update', lambda source, status: 
                                 self.update(source,
                                             status, 
                                             start_position,
                                             end_position - start_position))
                timeline.connect("completed", lambda source: self.completed(target_widget))
                timeline.run()
                
    def update(self, source, status, start_position, pos):
        self.get_hadjustment().set_value(start_position + int(round(status * pos)))
        
    def completed(self, widget):    
        self.active_widget = widget
        
        self.emit("completed_slide")
    
    def set_to_page(self, widget):
        self.active_widget = widget
        widget_index = self.layout.get_children().index(widget)
        self.get_hadjustment().set_value(widget_index * self.page_width)

gobject.type_register(HSlider)
