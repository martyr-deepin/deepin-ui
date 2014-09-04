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
from constant import PANED_HANDLE_SIZE
import gobject
import gtk
import math
from theme import ui_theme

# Load customize rc style before any other.
gtk.rc_parse_string("style 'my_style' {\n    GtkPaned::handle-size = %s\n }\nwidget '*' style 'my_style'" % (PANED_HANDLE_SIZE))

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
    def __init__(self,
                 shrink_first,
                 enable_animation=False,
                 always_show_button=False,
                 enable_drag=False,
                 handle_color=ui_theme.get_color("paned_line")
                 ):
        '''
        Initialize Paned class.
        '''
        gtk.Paned.__init__(self)
        self.shrink_first = shrink_first
        self.enable_animation = enable_animation
        self.always_show_button = always_show_button
        self.enable_drag = enable_drag
        self.handle_color = handle_color
        self.bheight = ui_theme.get_pixbuf("paned/paned_up_normal.png").get_pixbuf().get_width()
        self.saved_position = -1
        self.handle_size = PANED_HANDLE_SIZE - 1
        self.show_button = False
        self.init_button("normal")
        self.animation_delay = 20 # milliseconds
        self.animation_times = 10
        self.animation_position_frames = []
        self.press_coordinate = None

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
        cr.set_source_rgb(*color_hex_to_cairo(self.handle_color.get_color()))
        (width, height) = handle.get_size()
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            if self.shrink_first:
                if self.get_position() != 0:
                    cr.rectangle(0, 0, line_width, height)
                    cr.fill()

                if self.always_show_button or self.show_button:
                    if self.get_position() == 0:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_right_normal.png").get_pixbuf()
                    else:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_left_normal.png").get_pixbuf()
                    draw_pixbuf(cr,
                                pixbuf,
                                0,
                                (height - self.bheight)  / 2)
            else:
                cr.rectangle(width - line_width, 0, line_width, height)
                cr.fill()

                if self.always_show_button or self.show_button:
                    if self.get_position() == 0:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_left_normal.png").get_pixbuf()
                    else:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_right_normal.png").get_pixbuf()
                    draw_pixbuf(cr,
                                pixbuf,
                                0,
                                (height - self.bheight)  / 2)
        else:
            if self.shrink_first:
                cr.rectangle(0, 0, width, line_width)
                cr.fill()

                if self.always_show_button or self.show_button:
                    if self.get_position() == 0:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_down_normal.png").get_pixbuf()
                    else:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_up_normal.png").get_pixbuf()
                    draw_pixbuf(cr,
                                pixbuf,
                                (width - self.bheight) / 2,
                                0)
            else:
                cr.rectangle(0, height - line_width, width, line_width)
                cr.fill()

                if self.always_show_button or self.show_button:
                    if self.get_position() == 0:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_up_normal.png").get_pixbuf()
                    else:
                        pixbuf = ui_theme.get_pixbuf("paned/paned_down_normal.png").get_pixbuf()
                    draw_pixbuf(cr,
                                pixbuf,
                                (width - self.bheight) / 2,
                                0)

    def is_in_button(self, x, y):
        '''
        Detection of wheter the mouse pointer is in the handler's button.
        '''
        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            rect =  (0, (height - self.bheight) / 2, width, self.bheight)
        else:
            rect =  ((width - self.bheight) / 2, 0, self.bheight, height)

        return is_in_rect((x, y), rect)

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
        # Reset press coordinate if motion mouse after press event.
        self.press_coordinate = None

        handle = self.get_handle_window()
        (width, height) = handle.get_size()
        if self.is_in_button(e.x, e.y):
            handle.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))

            self.init_button("hover")
        else:
            if self.enable_drag:
                handle.set_cursor(self.cursor_type)
                gtk.Paned.do_motion_notify_event(self, e)
            else:
                handle.set_cursor(None)
            self.init_button("normal")

    def do_button_press_event(self, e):
        '''
        when press the handler's button change the position.
        '''
        handle = self.get_handle_window()
        if e.window == handle:
            if self.is_in_button(e.x, e.y):
                self.init_button("press")

                self.do_press_actoin()
            else:
                (width, height) = handle.get_size()
                if is_in_rect((e.x, e.y), (0, 0, width, height)):
                    self.press_coordinate = (e.x, e.y)

                gtk.Paned.do_button_press_event(self, e)
        else:
            gtk.Paned.do_button_press_event(self, e)

        return True

    def do_button_release_event(self, e):
        '''
        docs
        '''
        gtk.Paned.do_button_release_event(self, e)

        # Do press event if not in button and finish `click` event.
        if (not self.is_in_button(e.x, e.y)) and self.press_coordinate == (e.x, e.y):
            self.do_press_actoin()

        return True

    def do_press_actoin(self):
        '''
        docs
        '''
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

    def change_position(self, new_position):
        current_position = self.get_position()
        if self.enable_animation:
            if new_position != current_position:
                for i in range(0, self.animation_times + 1):
                    step = int(math.sin(math.pi * i / 2 / self.animation_times) * (new_position - current_position))
                    self.animation_position_frames.append(current_position + step)

                if self.animation_position_frames[-1] != new_position:
                    self.animation_position_frames.append(new_position)

                gtk.timeout_add(self.animation_delay, self.update_position)
        else:
            self.set_position(new_position)

    def update_position(self):
        self.set_position(self.animation_position_frames.pop(0))

        if self.animation_position_frames == []:
            return False
        else:
            return True

    def do_size_allocate(self, e):
        gtk.Paned.do_size_allocate(self, e)

        if self.shrink_first:
            child = self.get_child2()
        else:
            child = self.get_child1()

        if child == None: return

        rect = child.allocation

        offset = self.handle_size

        if self.get_orientation() == gtk.ORIENTATION_HORIZONTAL:
            if self.shrink_first:
                rect.x -= offset
                rect.width += offset
            else:
                rect.width += offset
        else:
            if self.shrink_first:
                rect.y -= offset
                rect.height += offset
            else:
                rect.height += offset

        child.size_allocate(rect)

class HPaned(Paned):
    def __init__(self,
                 shrink_first=True,
                 enable_animation=False,
                 always_show_button=False,
                 enable_drag=False,
                 handle_color=ui_theme.get_color("paned_line")
                 ):
        Paned.__init__(self, shrink_first, enable_animation, always_show_button, enable_drag, handle_color)
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.cursor_type = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)

class VPaned(Paned):
    def __init__(self,
                 shrink_first=True,
                 enable_animation=False,
                 always_show_button=False,
                 enable_drag=False,
                 handle_color=ui_theme.get_color("paned_line")
                 ):
        Paned.__init__(self, shrink_first, enable_animation, always_show_button, enable_drag, handle_color)
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
