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
from window import Window
from draw import draw_window_shadow, draw_window_frame, draw_pixbuf
from utils import propagate_expose
from titlebar import Titlebar

class SkinWindow(Window):
    '''SkinWindow.'''
	
    def __init__(self, preview_width, preview_height, background_pixbuf):
        '''Init skin.'''
        Window.__init__(self)
        self.main_box = gtk.VBox()
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            "皮肤编辑")
        self.edit_area_align = gtk.Alignment()
        self.edit_area_align.set(0, 0, 1, 1)
        self.edit_area_align.set_padding(0, 1, 1, 1)
        self.edit_area = SkinEditArea(preview_width, preview_height, background_pixbuf)
        
        self.window_frame.add(self.main_box)
        self.main_box.pack_start(self.titlebar, False, False)
        self.main_box.pack_start(self.edit_area_align, True, True)
        self.edit_area_align.add(self.edit_area)
        
        self.titlebar.close_button.connect("clicked", lambda w: gtk.main_quit())
        self.connect("destroy", lambda w: gtk.main_quit())
        
gobject.type_register(SkinWindow)

class SkinEditArea(gtk.DrawingArea):
    '''Skin edit area.'''
	
    def __init__(self, preview_width, preview_height, background_pixbuf):
        '''Init skin edit area.'''
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.background_pixbuf = background_pixbuf
        self.padding_x = 10
        self.padding_y = 10
        self.shadow_radius = 6
        self.frame_radius = 2
        self.shadow_padding = self.shadow_radius - self.frame_radius
        
        self.set_size_request(
            self.preview_width + self.padding_x * 2,
            self.preview_height + self.padding_y * 2
            )
        
        self.connect("expose-event", self.expose_skin_edit_area)
        
    def expose_skin_edit_area(self, widget, event):
        '''Expose edit area.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        draw_pixbuf(
            cr,
            self.background_pixbuf,
            self.padding_x + self.shadow_padding,
            self.padding_y + self.shadow_padding)
        
        if self.is_composited():
            draw_window_shadow(
                cr, 
                self.padding_x, 
                self.padding_y, 
                w - self.padding_x * 2,
                h - self.padding_y * 2,
                self.shadow_radius, 
                self.shadow_padding)

        draw_window_frame(
            cr,
            self.padding_x + self.shadow_padding,
            self.padding_y + self.shadow_padding,
            w - (self.padding_x + self.shadow_padding) * 2,
            h - (self.padding_y + self.shadow_padding) * 2)    
        
        propagate_expose(widget, event)
        
        return True
        
gobject.type_register(SkinEditArea)
        
if __name__ == '__main__':
    skin_window = SkinWindow(600, 400, gtk.gdk.pixbuf_new_from_file("/data/Picture/壁纸/20080519100123935.jpg"))
    skin_window.move(200, 100)
    
    skin_window.show_all()
    
    gtk.main()
    
