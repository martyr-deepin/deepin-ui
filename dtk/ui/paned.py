#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
#
# Author:     Xia Bin <xiabin@gmail.com>
# Maintainer: Xia Bin <xiabin@gmail.com>
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

from utils import is_in_rect
import gobject
import gtk

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
    def __init__(self):
        '''
        Initialize Paned class.
        '''
        gtk.Paned.__init__(self)
        self.bheight = 60  #the button height or width;
        self.saved_position = -1
        self.handle_size = self.style_get_property('handle-size')

    def do_expose_event(self, e):
        '''
        To intercept the default expose event and draw custom handle
        after the **gtk.Container** expose evetn.
        So the gtk.Paned's expose event callback is ignore.
        '''
        #gtk.Paned.do_expose_event(self, e)
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
        cr.set_source_rgba(1, 0,0, 0.8)
        (width, height) = handle.get_size()
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            #draw line
            cr.rectangle(0, 0, line_width, height)

            #draw_button
            cr.rectangle(0, (height-self.bheight)/2,  width, self.bheight)
        else:
            cr.rectangle(0, 0, height, line_width)
            cr.rectangle((width-self.bheight)/2, 0, self.bheight, width)

        cr.fill()
        pass

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
        '''
        change the cursor style  when move in handler
        '''
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.is_in_button(e.x, e.y):
            handle.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
        else:
            handle.set_cursor(self.cursor_type)

        self.queue_draw()

    def do_button_press_event(self, e):
        '''
        when press the handler's button change the position.
        '''
        if self.is_in_button(e.x, e.y):
            if self.saved_position == -1:
                self.saved_position = self.get_position()
                self.set_position(0)
            else:
                self.set_position(self.saved_position)
                self.saved_position = -1
        else:
            gtk.Paned.do_button_press_event(self, e)
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
    def __init__(self):
        Paned.__init__(self)
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)

class VPaned(Paned):
    def __init__(self):
        Paned.__init__(self)
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
