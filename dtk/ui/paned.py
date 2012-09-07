#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
#               2011 ~ 2012 Wang Yong
#
# Author:     Xia Bin <xiabin@linuxdeepin.com>
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

from draw import draw_pixbuf
from utils import is_in_rect, color_hex_to_cairo
import gobject
import gtk
import math
from theme import ui_theme
        
class Paned(gtk.Paned):
    '''
    Paned.
    
    @undocumented: do_enter_notify_event
    @undocumented: do_button_press_event
    @undocumented: do_size_allocate
    @undocumented: do_enter_notify_event
    @undocumented: is_in_button
    @undocumented: draw_handle
    @undocumented: do_expose_event

    gtk.Paned with custom better apperance.
    '''
    def __init__(self, shrink_first):
        '''
        Initialize Paned class.
        '''
        gtk.Paned.__init__(self)
        self.shrink_first = shrink_first
        self.bheight = ui_theme.get_pixbuf("paned/paned_up_normal.png").get_pixbuf().get_width()
        self.saved_position = -1
        self.handle_size = self.style_get_property('handle-size')
        self.show_button = False
        self.init_button("normal")
        self.animation_delay = 20 # milliseconds
        self.animation_times = 80
        self.animation_position_frames = []
        
    def init_button(self, status):
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            if self.shrink_first:
                self.button_pixbuf = ui_theme.get_pixbuf("paned/paned_left_%s.png" % status).get_pixbuf()
            else:
                self.button_pixbuf = ui_theme.get_pixbuf("paned/paned_right_%s.png" % status).get_pixbuf()
        else:
            if self.shrink_first:
                self.button_pixbuf = ui_theme.get_pixbuf("paned/paned_up_%s.png" % status).get_pixbuf()
            else:
                self.button_pixbuf = ui_theme.get_pixbuf("paned/paned_down_%s.png" % status).get_pixbuf()
            
    def do_expose_event(self, e):
        '''
        To intercept the default expose event and draw custom handle
        after the **gtk.Container** expose evetn.
        So the gtk.Paned's expose event callback is ignore.
        '''
        gtk.Container.do_expose_event(self, e)
        self.draw_handle(e)

        return False

    def draw_handle(self, e):
        '''
        Draw the cusom handle apperance.
        '''
        handle = self.get_handle_window()
        line_width = 1
        cr = handle.cairo_create()
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("paned_line").get_color()))
        (width, height) = handle.get_size()
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            if self.shrink_first:
                cr.rectangle(0, 0, line_width, height)
                cr.fill()

                if self.show_button:
                    draw_pixbuf(cr, 
                                ui_theme.get_pixbuf("paned/paned_left_normal.png").get_pixbuf(),
                                0,
                                (height - self.bheight)  / 2)
            else:
                cr.rectangle(width - line_width, 0, line_width, height)
                cr.fill()
                
                if self.show_button:
                    draw_pixbuf(cr, 
                                ui_theme.get_pixbuf("paned/paned_right_normal.png").get_pixbuf(),
                                0,
                                (height - self.bheight)  / 2)
        else:
            if self.shrink_first:
                cr.rectangle(0, 0, width, line_width)
                cr.fill()
                
                if self.show_button:
                    draw_pixbuf(cr, 
                                ui_theme.get_pixbuf("paned/paned_up_normal.png").get_pixbuf(),
                                (width - self.bheight) / 2,
                                0)
            else:
                cr.rectangle(0, height - line_width, width, line_width)
                cr.fill()

                if self.show_button:
                    draw_pixbuf(cr, 
                                ui_theme.get_pixbuf("paned/paned_down_normal.png").get_pixbuf(),
                                (width - self.bheight) / 2,
                                0)

    def is_in_button(self, x, y):
        '''
        Detection of wheter the mouse pointer is in the handler's button.
        '''
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            rect =  (0, (height-self.bheight)/2, width, self.bheight)
        else:
            rect =  ((width-self.bheight)/2, 0, self.bheight, height)

        if is_in_rect((x, y), rect):
            return True
        else:
            return False

    def do_enter_notify_event(self, e):
        self.show_button = True
        
        self.queue_draw()
    
    def do_leave_notify_event(self, e):
        self.show_button = False
        self.init_button("normal")
        
        self.queue_draw()
        
    def do_motion_notify_event(self, e):
        '''
        change the cursor style  when move in handler
        '''
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.is_in_button(e.x, e.y):
            handle.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
            
            self.init_button("hover")
        else:
            handle.set_cursor(self.cursor_type)
            
            self.init_button("normal")

        self.queue_draw()
        
        gtk.Paned.do_motion_notify_event(self, e)

    def do_button_press_event(self, e):
        '''
        when press the handler's button change the position.
        '''
        if self.is_in_button(e.x, e.y):
            self.init_button("press")
            
            if self.saved_position == -1:
                self.saved_position = self.get_position()
                if self.shrink_first:
                    self.change_position(0)
                else:
                    if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
                        self.change_position(self.allocation.width)
                    else:
                        self.change_position(self.allocation.height)
            else:
                self.change_position(self.saved_position)
                self.saved_position = -1
        else:
            gtk.Paned.do_button_press_event(self, e)
            
        return True
    
    def change_position(self, new_position):
        current_position = self.get_position()
        if new_position != current_position:
            for i in range(0, self.animation_times + 1):
                step = int(math.sin(math.pi * i / 2 / self.animation_times) * (new_position - current_position))
                self.animation_position_frames.append(current_position + step)
                
            if self.animation_position_frames[-1] != new_position:
                self.animation_position_frames.append(new_position)
                
            gtk.timeout_add(self.animation_delay, self.update_position)
        
    def update_position(self):
        self.set_position(self.animation_position_frames.pop(0))        
        
        if self.animation_position_frames == []:
            return False
        else:
            return True

    def do_size_allocate(self, e):
        gtk.Paned.do_size_allocate(self, e)

        c2 = self.get_child2()

        if c2 == None: return

        a2 = c2.allocation

        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            a2.x -= self.handle_size
            a2.width += self.handle_size
        else:
            a2.y -= self.handle_size
            a2.height += self.handle_size
        c2.size_allocate(a2)

class HPaned(Paned):
    def __init__(self, shrink_first=True):
        Paned.__init__(self, shrink_first)
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)

class VPaned(Paned):
    def __init__(self, shrink_first=True):
        Paned.__init__(self, shrink_first)
        self.set_orientation(gtk.ORIENTATION_VERTICAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_V_DOUBLE_ARROW)
        
gobject.type_register(Paned)
gobject.type_register(HPaned)
gobject.type_register(VPaned)
        
if __name__ == '__main__':
    w = gtk.Window()
    w.set_size_request(700, 400)
    #w.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('yellow'))
    box = gtk.VBox()

    p = VPaned()
    c1 = gtk.Button("11111111111111111111111")
    c1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('blue'))
    c2 = gtk.Button("122222222222222222222222")
    c1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
    p.add1(c1)
    p.add2(c2)
    box.pack_start(p)

    p = HPaned()
    c1 = gtk.Button("11111111111111111111111")
    c1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('blue'))
    c2 = gtk.Button("122222222222222222222222")
    c1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
    p.add1(c1)
    p.add2(c2)
    box.pack_start(p)

    w.add(box)
    w.connect('destroy', gtk.main_quit)
    w.show_all()
    gtk.main()
