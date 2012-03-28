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
import cairo
from theme import *
from box import *
from window import *

class HPaned(gtk.HBox):
    '''HPaned.'''
	
    def __init__(self, left_child, right_child):
        '''Init hpaned.'''
        # Init.
        gtk.HBox.__init__(self)
        self.drag_flag = False
        
        self.left_box = gtk.EventBox()
        self.right_box = gtk.EventBox()
        # self.drag_box = gtk.EventBox()
        
        # self.left_box = EventBox()
        # self.right_box = EventBox()
        self.drag_box = EventBox()
        
        self.drag_x = 0
        self.drag_offset = 0
        self.left_child = left_child
        self.right_child = right_child
        
        # Connect widgets.
        self.left_box.add(left_child)
        self.right_box.add(right_child)
        self.drag_box.set_size_request(5, -1)
        self.pack_start(self.left_box, True, True)
        self.pack_start(self.drag_box, False, False)
        self.pack_start(self.right_box, True, True)
        
        # Signal.
        self.left_box.connect("expose-event", self.expose_child_box)
        self.right_box.connect("expose-event", self.expose_child_box)
        self.drag_box.connect("expose-event", self.expose_drag_box)
        self.drag_box.connect("button-press-event", self.button_press_hpaned)
        self.drag_box.connect("button-release-event", self.button_release_hpaned)
        self.drag_box.connect("motion-notify-event", self.motion_notify_hpaned)

    def expose_child_box(self, widget, event):
        '''Callback for `expose-event` signal.'''
        cr = widget.window.cairo_create()
        # cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        # cr.set_operator(cairo.OPERATOR_SOURCE)
        # cr.paint()

        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
    def expose_drag_box(self, widget, event):
        '''Callback for `expose-event` signal.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
        
    def button_press_hpaned(self, widget, event):
        '''Callback for `button-press-event` signal.'''
        self.drag_flag = True
        (drag_box_x, drag_box_y) = self.drag_box.window.get_origin()
        (x, y) = self.drag_box.translate_coordinates(self, drag_box_x, drag_box_y)
        self.drag_x = x
    
    def button_release_hpaned(self, widget, event):
        '''Callback for `button-release-event` signal.'''
        self.drag_flag = False
        
    def motion_notify_hpaned(self, widget, event):
        '''Callback for `motion-notify-event` signal.'''
        if self.drag_flag:
            self.drag_offset = int(event.x)
            self.update_shape()
            
    def update_shape(self):
        '''Update shape.'''
        # Init.
        hpaned_width = self.get_allocation().width
        drag_box_width = self.drag_box.get_allocation().width
        left_box_rect = self.left_box.get_allocation()
        right_box_rect = self.right_box.get_allocation()
        drag_offset = min(max(-self.drag_x, self.drag_offset), hpaned_width - self.drag_x - drag_box_width)
        
        # Update shape of left box.
        left_box_bitmap = gtk.gdk.Pixmap(None, left_box_rect.width, left_box_rect.height, 1)
        left_box_cr = left_box_bitmap.cairo_create()
        
        left_box_cr.set_source_rgb(0.0, 0.0, 0.0)
        left_box_cr.set_operator(cairo.OPERATOR_CLEAR)
        left_box_cr.paint()
        
        left_box_cr.set_source_rgb(1.0, 1.0, 1.0)
        left_box_cr.set_operator(cairo.OPERATOR_OVER)
        left_box_cr.rectangle(0, 0, self.drag_x + drag_offset, left_box_rect.height)
        left_box_cr.fill()
        
        self.left_box.shape_combine_mask(left_box_bitmap, 0, 0)
        # self.left_box.set_allocation(
        #     gtk.gdk.Rectangle(left_box_rect.x, left_box_rect.y, self.drag_x + drag_offset, left_box_rect.height))
        # print left_box_rect
        
        # Update shape of right box.
        right_box_bitmap = gtk.gdk.Pixmap(None, right_box_rect.width, right_box_rect.height, 1)
        right_box_cr = right_box_bitmap.cairo_create()
        
        right_box_cr.set_source_rgb(0.0, 0.0, 0.0)
        right_box_cr.set_operator(cairo.OPERATOR_CLEAR)
        right_box_cr.paint()
        
        right_box_cr.set_source_rgb(1.0, 1.0, 1.0)
        right_box_cr.set_operator(cairo.OPERATOR_OVER)
        right_box_cr.rectangle(
            drag_offset, 0, 
            hpaned_width - self.drag_x - drag_box_width - drag_offset, right_box_rect.height)
        right_box_cr.fill()
        
        self.right_box.shape_combine_mask(right_box_bitmap, 0, 0)
        # self.right_box.set_allocation(
        #     gtk.gdk.Rectangle(right_box_rect.x, right_box_rect.y, 
        #                       hpaned_width - self.drag_x - drag_box_width - drag_offset, right_box_rect.height))
        
        print (self.drag_x, drag_offset)
    
gobject.type_register(HPaned)

if __name__ == "__main__":
    window = Window()
    window.set_title('Panes')
    window.set_border_width(10)
    window.set_size_request(225, 150)
    window.connect('destroy', lambda w: gtk.main_quit())

    button1 = gtk.Button('Resize')
    button2 = gtk.Button('Me!')

    hpaned = HPaned(button1, button2)
    hpaned_align = gtk.Alignment()    
    hpaned_align.set(0, 0, 1, 1)
    hpaned_align.set_padding(1, 1, 1, 1)
    hpaned_align.add(hpaned)

    window.window_frame.pack_start(hpaned_align)
    window.show_all()

    gtk.main()

# class HPaned(gtk.HBox):
#     '''HPand.'''
	
#     def __init__(self):
#         '''Init.'''
#         super(HPaned, self).__init__()
        
#         # Init.
#         self.drag_flag = False
#         self.left_child = None
#         self.right_child = None
        
#         self.control_button = ImageBox (ui_theme.get_pixbuf("paned/v_control.png"))
#         self.control_button.connect("button-press-event", self.button_press_cb)
#         self.control_button.connect("motion-notify-event", self.button_motion_cb)
#         self.control_button.connect("button-release-event", self.button_release_cb)
        
#         self.__left_box = gtk.VBox()
#         self.__right_box = gtk.VBox()
#         self.pack_start(self.__left_box)
#         self.pack_start(self.control_button, False, False)
#         self.pack_end(self.__right_box)
        
#     def add1(self, child):    
#         self.left_child = child
#         self.__left_box.pack_start(child)
        
#     def add2(self, child):    
#         self.right_child = child
#         self.__right_box.pack_start(child)
        
#     def pack1(self, child, resize=False, shrink=True):
#         child.set_property("resizable", resize)
#         child.set_property("allow-shrink", shrink)
#         self.left_child = child
#         self.__left_box.pack_start(child)
        
#     def pack2(self, child, resize=True, shrink=True):    
#         child.set_property("resizable", resize)
#         child.set_property("allow-shrink", shrink)
#         self.right_child = child
#         self.__right_box.pack_start(child)
        
#     def button_press_cb(self, widget, event):    
#         self.drag_flag = True
        
#     def button_motion_cb(self, widget, event):    
        
#         '''Motion notify.'''
#         if self.drag_flag:
#             if event.x > 0:
#                 rect = self.left_child.get_allocation()
#                 new_rect = gtk.gdk.Rectangle(int(rect.x) , int(rect.y), int(rect.width + event.x), int(rect.height))
#                 self.left_child.set_allocation(new_rect)
#         self.queue_draw()        
        
#     def button_release_cb(self, widget, event):    
#         pass
        
