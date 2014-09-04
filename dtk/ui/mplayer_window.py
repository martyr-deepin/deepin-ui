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

from draw import draw_window_shadow, draw_window_frame
from skin_config import skin_config
from window_base import WindowBase
from theme import ui_theme
import cairo
import gobject
import gtk
from utils import (cairo_state, propagate_expose, set_cursor,
                   get_event_root_coords,
                   enable_shadow)

class MplayerWindow(WindowBase):
    '''
    Special Window class for mplayer.

    Generally speaking, compared with Window class, it uses a different shadow mechanism.

    @undocumented: adjust_window_shadow
    @undocumented: get_cursor_type
    @undocumented: expose_window
    @undocumented: shape_window
    @undocumented: shape_window_frame
    @undocumented: shape_window_shadow
    @undocumented: expose_window_background
    @undocumented: expose_window_shadow
    @undocumented: expose_window_frame
    @undocumented: motion_notify
    @undocumented: double_click_window
    @undocumented: monitor_window_state
    '''

    def __init__(self,
                 enable_resize=False,
                 shadow_radius=6,
                 window_type=gtk.WINDOW_TOPLEVEL):
        '''
        Initialise the Window class.

        @param enable_resize: If True, the window will be set resizable. By default, it's False.
        @param shadow_radius: The radius of the shadow.
        @param window_type: A flag of type gtk._gtk.WindowType, which indicates the type of the window. By default, it's gtk.WINDOW_TOPLEVEL.
        '''
        # Init.
        WindowBase.__init__(self, window_type)
        self.shadow_radius = shadow_radius
        self.enable_resize = enable_resize
        self.background_color = (0, 0, 0, 0)
        # FIXME: Because mplayer don't allowed window redirect colormap to screen.
        # We build shadow window to emulate it, but shadow's visual effect
        # is not good enough, so we disable shadow temporary for future fixed.
        self.shadow_visible = False
        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.set_colormap(gtk.gdk.Screen().get_rgba_colormap())

        self.init()

    def init(self):
        skin_config.wrap_skin_window(self)
        self.set_decorated(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.frame_radius = 2
        self.shadow_is_visible = True
        self.window_frame = gtk.VBox()
        self.add(self.window_frame)
        self.shape_flag = True

        if enable_shadow(self) and self.shadow_visible:
            self.shadow_padding = self.shadow_radius - self.frame_radius
        else:
            self.shadow_padding = 0

        # Init shadow window.
        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window_shadow.add_events(gtk.gdk.ALL_EVENTS_MASK)
            self.window_shadow.set_decorated(False)
            self.window_shadow.set_transient_for(self)
            self.window_shadow.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)

        # Handle signal.
        self.connect_after("expose-event", self.expose_window)
        self.connect("size-allocate", self.shape_window)
        self.connect("window-state-event", self.monitor_window_state)
        self.connect("configure-event", self.adjust_window_shadow)

        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.connect("expose-event", self.expose_window_shadow)
            self.window_shadow.connect("size-allocate", self.shape_window_shadow)
            self.window_shadow.connect("button-press-event", self.resize_window)
            self.window_shadow.connect("motion-notify-event", self.motion_notify)

    def adjust_window_shadow(self, widget, event):
        '''
        Internal function to adjust postion and size of the shadow of the window.

        @param widget: the widget of type gtk.Widget.
        @param event: the event of gtk.gdk.Event.
        '''
        if enable_shadow(self) and self.shadow_visible:
            (x, y) = self.get_position()
            (width, height) = self.get_size()

            self.window_shadow.get_window().move_resize(
                x - self.shadow_padding, y - self.shadow_padding,
                width + self.shadow_padding * 2, height + self.shadow_padding * 2
                )

        # NOTE: Some desktop environment will disable window minimum operation instead with hide window operation
        # to get the realtime preview of application, then window will got wrong shape mask after un-minimum.
        # So we do shape window when `configure-event` event emit to fixed the compatible problem.
        self.shape_window(widget, widget.allocation)

    def show_window(self):
        '''
        Show the window.
        '''
        self.show_all()

        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.show_all()

    def expose_window(self, widget, event):
        '''
        Internal function to expose the window.

        @param widget: A window of type Gtk.Widget.
        @param event: The expose event of type gtk.gdk.Event.

        @return: Always return True.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Draw background.
        self.draw_background(cr, rect.x, rect.y, rect.width, rect.height)

        # Draw skin and mask.
        with cairo_state(cr):
            if self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED != gtk.gdk.WINDOW_STATE_MAXIMIZED:
                cr.rectangle(x + 2, y, w - 4, 1)
                cr.rectangle(x + 1, y + 1, w - 2, 1)
                cr.rectangle(x, y + 2, w, h - 4)
                cr.rectangle(x + 2, y + h - 1, w - 4, 1)
                cr.rectangle(x + 1, y + h - 2, w - 2, 1)

                cr.clip()

            self.draw_skin(cr, x, y, w, h)

            # Draw mask.
            self.draw_mask(cr, x, y, w, h)

        # Draw window frame.
        if self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED != gtk.gdk.WINDOW_STATE_MAXIMIZED:
            draw_window_frame(cr, x, y, w, h,
                              ui_theme.get_alpha_color("window_frame_outside_1"),
                              ui_theme.get_alpha_color("window_frame_outside_2"),
                              ui_theme.get_alpha_color("window_frame_outside_3"),
                              ui_theme.get_alpha_color("window_frame_inside_1"),
                              ui_theme.get_alpha_color("window_frame_inside_2"),
                              )

        # Propagate expose.
        propagate_expose(widget, event)

        return True

    def set_window_shape(self, shape_flag):
        '''
        Enable window shape.

        @param shape_flag: The flag that indicates the shape.
        '''
        self.shape_flag = shape_flag
        self.shape_window(self, self.get_allocation())

    def shape_window(self, widget, rect):
        '''
        Internal function to draw the shaped window.

        @param widget: A widget of type gtk.Widget.
        @param rect: The bounding region of the window.
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

            if not self.shape_flag:
                # Don't clip corner when window is fullscreen state.
                cr.rectangle(x, y, w, h)
            elif (self.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN == gtk.gdk.WINDOW_STATE_FULLSCREEN or
                  self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED):
                # Don't clip corner when window is fullscreen state.
                cr.rectangle(x, y, w, h)
            else:
                cr.rectangle(x + 2, y, w - 4, 1)
                cr.rectangle(x + 1, y + 1, w - 2, 1)
                cr.rectangle(x, y + 2, w, h - 4)
                cr.rectangle(x + 1, y + h - 2, w - 2, 1)
                cr.rectangle(x + 2, y + h - 1, w - 4, 1)
            cr.fill()

            # Shape with given mask.
            widget.shape_combine_mask(bitmap, 0, 0)

            # Redraw whole window.
            self.queue_draw()

            if enable_shadow(self) and self.shadow_visible:
                self.window_shadow.queue_draw()

    def shape_window_shadow(self, widget, rect):
        '''
        Internal function to draw the shaped window's shadow.

        @param widget: A widget of type gtk.Widget.
        @param rect: The bounding region of the window.
        '''
        if rect.width > 0 and rect.height > 0:
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

            # Four side.
            cr.rectangle(x, y, w, self.shadow_padding)
            cr.rectangle(x, y + self.shadow_padding, self.shadow_padding, h - self.shadow_padding * 2)
            cr.rectangle(x + w - self.shadow_padding, y + self.shadow_padding, self.shadow_padding, h - self.shadow_padding * 2)
            cr.rectangle(x, y + h - self.shadow_padding, w, self.shadow_padding)

            # Four 2-pixel rectange.
            cr.rectangle(x + self.shadow_padding, y + self.shadow_padding, 2, 1)
            cr.rectangle(x + w - self.shadow_padding - 2, y + self.shadow_padding, 2, 1)
            cr.rectangle(x + self.shadow_padding, y + h - self.shadow_padding - 1, 2, 1)
            cr.rectangle(x + w - self.shadow_padding - 2, y + h - self.shadow_padding - 1, 2, 1)

            # Four 1-pixel rectange.
            cr.rectangle(x + self.shadow_padding, y + self.shadow_padding + 1, 1, 1)
            cr.rectangle(x + w - self.shadow_padding - 1, y + self.shadow_padding + 1, 1, 1)
            cr.rectangle(x + self.shadow_padding, y + h - self.shadow_padding - 2, 1, 1)
            cr.rectangle(x + w - self.shadow_padding - 1, y + h - self.shadow_padding - 2, 1, 1)

            cr.fill()

            # Shape with given mask.
            widget.shape_combine_mask(bitmap, 0, 0)

            # Redraw whole window.
            self.queue_draw()

            if enable_shadow(self) and self.shadow_visible:
                self.window_shadow.queue_draw()

    def expose_window_shadow(self, widget, event):
        '''
        Internal fucntion to expose the window shadow.

        @param widget: the window of gtk.Widget.
        @param event: The expose event of type gtk.gdk.Event.
        '''
        if self.shadow_is_visible:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            x, y, w, h = rect.x, rect.y, rect.width, rect.height

            # Clear color to transparent window.
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()

            # Draw window shadow.
            draw_window_shadow(cr, x, y, w, h, self.shadow_radius, self.shadow_padding, ui_theme.get_shadow_color("window_shadow"))

    def hide_shadow(self):
        '''
        Hide the window shadow.
        '''
        self.shadow_is_visible = False

        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.hide_all()

    def show_shadow(self):
        '''
        Show the window shadow.
        '''
        self.shadow_is_visible = True

        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.show_all()

    def monitor_window_state(self, widget, event):
        '''
        Monitor window state, add shadow when window at maximized or fullscreen status. Otherwise hide shadow.

        @param widget: The window of type gtk.Widget.
        @param event: The event of gtk.gdk.Event.
        '''
        super(MplayerWindow, self).monitor_window_state(widget, event)

        self.adjust_window_shadow(widget, event)

    def motion_notify(self, widget, event):
        '''
        Internal callback for `motion-notify-event` signal.

        @param widget: A widget of gtk.Widget.
        @param event: The motion-notify-event of type gtk.gdk.Event
        '''
        if self.enable_resize and self.shadow_is_visible:
            self.cursor_type = self.get_cursor_type(event)
            set_cursor(self.window_shadow, self.cursor_type)

    def get_cursor_type(self, event):
        '''
        Get the cursor position.

        @param event: An event of type gtk.gdk.Event.
        @return: If the cursor is on the frame of the window, return the cursor position. Otherwise return None.
        '''
        # Get event coordinate.
        (ex, ey) = get_event_root_coords(event)

        # Get window allocation.
        rect = self.window_shadow.get_allocation()
        (wx, wy) = self.window_shadow.get_position()
        ww = rect.width
        wh = rect.height

        # Return cursor position.
        return self.get_cursor_type_with_coordinate(ex, ey, wx, wy, ww, wh)

    def get_shadow_size(self):
        '''
        Get the shadow size.

        @return: Always return (0, 0)
        '''
        return (0, 0)

gobject.type_register(MplayerWindow)

class EmbedMplayerWindow(gtk.Plug):
    def __init__(self,
                 enable_resize=False,
                 shadow_radius=6,
                 ):
        gtk.Plug.__init__(self, 0)
        self.shadow_radius = shadow_radius
        self.enable_resize = enable_resize
        self.background_color = (1, 1, 1, 0.93)
        # FIXME: Because mplayer don't allowed window redirect colormap to screen.
        # We build shadow window to emulate it, but shadow's visual effect
        # is not good enough, so we disable shadow temporary for future fixed.
        self.shadow_visible = False

        self.init()

# Mix-in MplayerWindow methods (except __init__) to EmbedMplayerWindow
EmbedMplayerWindow.__bases__ += (MplayerWindow,)

gobject.type_register(EmbedMplayerWindow)

if __name__ == "__main__":
    window = MplayerWindow()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    window.move(100, 100)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_window()

    gtk.main()
