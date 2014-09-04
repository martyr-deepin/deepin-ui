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

from skin_config import skin_config
from theme import ui_theme
from utils import remove_timeout_id
import cairo
import gobject
import gtk

__all__ = ["Panel"]

class Panel(gtk.Window):
    '''
    Panel.

    @undocumented: stop_render
    @undocumented: start_show
    @undocumented: start_hide
    @undocumented: render_show
    @undocumented: render_hide
    @undocumented: shape_panel
    '''

    def __init__(self,
                 width,
                 height,
                 window_type=gtk.WINDOW_TOPLEVEL):
        '''
        Initialize Panel class.

        @param width: Initialize panel width.
        @param height: Initialize panel height.
        @param window_type: Window type, default is gtk.WINDOW_TOPLEVEL.
        '''
        # Init.
        gtk.Window.__init__(self, window_type)
        skin_config.wrap_skin_window(self)
        self.set_decorated(False)
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # make panel window don't switch in window manager
        self.start_show_id = None
        self.start_hide_id = None
        self.delay = 50         # milliseconds
        self.show_inc_opacity = 0.1
        self.hide_dec_opacity = 0.05
        self.width = width
        self.height = height
        self.set_size_request(self.width, self.height)

        # Change shape.
        self.connect("size-allocate", self.shape_panel)

    def stop_render(self):
        '''
        Internal function to stop render.
        '''
        # Stop callback.
        remove_timeout_id(self.start_show_id)
        remove_timeout_id(self.start_hide_id)

    def show_panel(self):
        '''
        Show panel.
        '''
        self.set_opacity(1)
        self.show_all()

    def hide_panel(self):
        '''
        Hide panel.
        '''
        self.set_opacity(0)
        self.hide_all()

    def start_show(self):
        '''
        Internal function to start show.
        '''
        if self.start_show_id == None and self.get_opacity() != 1:
            self.stop_render()
            self.start_show_id = gtk.timeout_add(self.delay, self.render_show)
            self.show_all()

    def start_hide(self):
        '''
        Internal function to start hide.
        '''
        if self.start_hide_id == None and self.get_opacity() != 0:
            self.stop_render()
            self.start_hide_id = gtk.timeout_add(self.delay, self.render_hide)

    def render_show(self):
        '''
        Internal function to render show effect.
        '''
        self.set_opacity(min(self.get_opacity() + self.show_inc_opacity, 1))

        if self.get_opacity() >= 1:
            self.stop_render()
            return False
        else:
            return True

    def render_hide(self):
        '''
        Internal function to render hide effect.
        '''
        self.set_opacity(max(self.get_opacity() - self.hide_dec_opacity, 0))

        if self.get_opacity() <= 0:
            self.stop_render()
            self.hide_panel()
            return False
        else:
            return True

    def resize_panel(self, w, h):
        '''
        Resize panel.

        @param w: Resize width.
        @param h: Resize height.
        '''
        self.width = w
        self.height = h
        self.set_size_request(self.width, self.height)
        self.shape_panel(self, self.get_allocation())

    def shape_panel(self, widget, rect):
        '''
        Internal callback for `size-allocate` signal.

        @param widget: Panel widget.
        @param rect: Size allocation.
        '''
        if widget.window != None and widget.get_has_window() and rect.width > 0 and rect.height > 0:
            # Init.
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            bitmap = gtk.gdk.Pixmap(None, w, h, 1)
            cr = bitmap.cairo_create()

            # Clear the bitmap
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.paint()

            # Draw our shape into the bitmap using cairo.
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.rectangle(0, 0, w, self.height)
            cr.fill()

            # Shape with given mask.
            widget.shape_combine_mask(bitmap, 0, 0)

gobject.type_register(Panel)

class TestWidget(object):
    '''class docs'''

    def __init__(self, panel):
        '''init docs'''
        self.panel = panel
        self.test_hide_id = None

    def show_panel(self):
        '''docs'''
        remove_timeout_id(self.test_hide_id)

        self.panel.start_show()
        self.test_hide_id = gtk.timeout_add(5000, self.panel.start_hide)

    def enter_notify_callback(self):
        '''docs'''
        remove_timeout_id(self.test_hide_id)

        self.panel.start_show()

    def leave_notify_callback(self):
        '''docs'''
        self.test_hide_id = gtk.timeout_add(5000, self.panel.start_hide)

if __name__ == "__main__":
    # Init window.
    window = gtk.Window()
    window.set_decorated(False)
    window.add_events(gtk.gdk.ALL_EVENTS_MASK)
    window.connect("destroy", lambda w: gtk.main_quit())
    window.move(100, 100)
    window.add(gtk.image_new_from_pixbuf(ui_theme.get_pixbuf("background12.png").get_pixbuf()))

    window.show_all()

    panel = Panel()
    panel.move(100, 592)
    panel.add(gtk.image_new_from_pixbuf(ui_theme.get_pixbuf("background13.png").get_pixbuf()))
    panel.hide_panel()

    test_widget = TestWidget(panel)
    window.connect("motion-notify-event", lambda w, e: test_widget.show_panel())
    panel.connect("enter-notify-event", lambda w, e: test_widget.enter_notify_callback())
    panel.connect("leave-notify-event", lambda w, e: test_widget.leave_notify_callback())

    gtk.main()
