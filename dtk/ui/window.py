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
from theme import ui_theme
from window_base import WindowBase
import cairo
import gobject
import gtk
from deepin_utils.xutils import set_window_property_by_id
from utils import (cairo_state, propagate_expose, set_cursor,
                   get_event_root_coords,
                   enable_shadow, alpha_color_hex_to_cairo)

class Window(WindowBase):
    '''
    The Window class is a subclass of gtk.Window. It adds some features that deepin-ui have to gtk.Window.

    @undocumented: init
    @undocumented: get_cursor_type
    @undocumented: expose_window_background
    @undocumented: expose_window_shadow
    @undocumented: expose_window_frame
    @undocumented: shape_window_frame
    @undocumented: motion_notify
    @undocumented: leave_notify
    @undocumented: double_click_window
    @undocumented: monitor_window_state
    '''
    def __init__(self,
                 enable_resize=False,
                 shadow_radius=6,
                 window_type=gtk.WINDOW_TOPLEVEL,
                 shadow_visible=True,
                 shape_frame_function=None,
                 expose_frame_function=None,
                 expose_background_function=None,
                 expose_shadow_function=None,
                 frame_radius=2,
                 ):
        '''
        Initialise the Window class.

        @param enable_resize: If True, the window will be set resizable. By default, it's False.
        @param shadow_radius: The radius of the shadow. By default, it's 6.
        @param window_type: A flag of type gtk.WindowType, which indicates the type of the window. By default, it's gtk.WINDOW_TOPLEVEL.
        @param shadow_visible: If True, the shadow is visible. By default, it's True, just disable when your program not allow manipulate colormap, such as mplayer.
        @param shape_frame_function: The function to define the shape of frame.
        @param expose_frame_function: The function to render frame.
        '''
        # Init.
        WindowBase.__init__(self, window_type)
        self.shadow_radius = shadow_radius
        self.enable_resize = enable_resize
        self.shadow_visible = shadow_visible
        self.shape_frame_function = shape_frame_function
        self.expose_frame_function = expose_frame_function
        self.expose_background_function = expose_background_function
        self.expose_shadow_function = expose_shadow_function
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.background_color = (0, 0, 0, 0)
        self.frame_radius = frame_radius

        self.init()

    def init(self):
        skin_config.wrap_skin_window(self)
        self.set_decorated(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.window_shadow = gtk.Alignment()
        self.window_frame = gtk.VBox()
        self.shadow_is_visible = True
        self.cursor_type = None

        # Shadow setup.
        if enable_shadow(self) and self.shadow_visible:
            self.shadow_padding = self.shadow_radius - self.frame_radius
            self.window_frame.connect("size-allocate", self.shape_window_frame)
            self.window_shadow.connect("expose-event", self.expose_window_shadow)
        else:
            # Disable shadow when composited is false.
            self.shadow_padding = 0
            self.connect("size-allocate", self.shape_window_frame)

        # Init window frame.
        self.window_shadow.set(0.0, 0.0, 1.0, 1.0)
        self.window_shadow.set_padding(self.shadow_padding, self.shadow_padding, self.shadow_padding, self.shadow_padding)

        # Connect widgets.
        self.add(self.window_shadow)
        self.window_shadow.add(self.window_frame)

        # Handle signal.
        self.connect_after("expose-event", self.expose_window_background)
        self.connect_after("size-allocate", lambda w, e: self.queue_draw())
        self.connect("motion-notify-event", self.motion_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.connect("button-press-event", self.resize_window)
        self.connect("window-state-event", self.monitor_window_state)
        self.window_frame.connect("expose-event", self.expose_window_frame)

    def expose_window_background(self, widget, event):
        '''
        Internal function to expose the window background.

        @param widget: A window of type Gtk.Widget.
        @param event: The expose event of type gtk.gdk.Event.
        @return: Always return True.
        '''
        if self.expose_background_function:
            self.expose_background_function(widget, event)
        else:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation

            # Draw background.
            self.draw_background(cr, rect.x, rect.y, rect.width, rect.height)

            # Save cairo context.
            if self.shadow_is_visible:
                x = rect.x + self.shadow_padding
                y = rect.y + self.shadow_padding
                w = rect.width - self.shadow_padding * 2
                h = rect.height - self.shadow_padding * 2
            else:
                x, y, w, h = rect.x, rect.y, rect.width, rect.height

            # Draw skin and mask.
            with cairo_state(cr):
                if self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED != gtk.gdk.WINDOW_STATE_MAXIMIZED:
                    cr.rectangle(x + 2, y, w - 4, 1)
                    cr.rectangle(x + 1, y + 1, w - 2, 1)
                    cr.rectangle(x, y + 2, w, h - 4)
                    cr.rectangle(x + 2, y + h - 1, w - 4, 1)
                    cr.rectangle(x + 1, y + h - 2, w - 2, 1)

                    cr.clip()

                # Draw background.
                self.draw_skin(cr, x, y, w, h)

                # Draw mask.
                self.draw_mask(cr, x, y, w, h)

            # Draw corner shadow.
            with cairo_state(cr):
                cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("window_shadow_corner").get_color_info()))

                cr.rectangle(x, y + 1, 1, 1) # top-left
                cr.rectangle(x + 1, y, 1, 1)

                cr.rectangle(x + w - 1, y + 1, 1, 1) # top-right
                cr.rectangle(x + w - 2, y, 1, 1)

                cr.rectangle(x, y + h - 2, 1, 1) # bottom-left
                cr.rectangle(x + 1, y + h - 1, 1, 1)

                cr.rectangle(x + w - 1, y + h - 2, 1, 1) # bottom-right
                cr.rectangle(x + w - 2, y + h - 1, 1, 1)

                cr.fill()

            # Draw background corner.
            with cairo_state(cr):
                cr.rectangle(x, y + 1, 1, 1) # top-left
                cr.rectangle(x + 1, y, 1, 1)

                cr.rectangle(x + w - 1, y + 1, 1, 1) # top-right
                cr.rectangle(x + w - 2, y, 1, 1)

                cr.rectangle(x, y + h - 2, 1, 1) # bottom-left
                cr.rectangle(x + 1, y + h - 1, 1, 1)

                cr.rectangle(x + w - 1, y + h - 2, 1, 1) # bottom-right
                cr.rectangle(x + w - 2, y + h - 1, 1, 1)

                cr.clip()

                self.draw_skin(cr, x, y, w, h)

            # Propagate expose.
            propagate_expose(widget, event)

        return True

    def expose_window_shadow(self, widget, event):
        '''
        Internal function to expose the window shadow.

        @param widget: the window of gtk.Widget.
        @param event: The expose event of type gtk.gdk.Event.
        '''
        if self.expose_shadow_function:
            self.expose_shadow_function(widget, event)
        elif self.shadow_is_visible:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            x, y, w, h = rect.x, rect.y, rect.width, rect.height

            # Draw window shadow.
            draw_window_shadow(cr, x, y, w, h, self.shadow_radius, self.shadow_padding, ui_theme.get_shadow_color("window_shadow"))

    def expose_window_frame(self, widget, event):
        '''
        Internal function to expose the window frame.

        @param widget: the window of gtk.Widget.
        @param event: The expose event of type gtk.gdk.Event.
        '''
        if self.expose_frame_function:
            self.expose_frame_function(widget, event)
        elif (self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED != gtk.gdk.WINDOW_STATE_MAXIMIZED and
              self.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN != gtk.gdk.WINDOW_STATE_FULLSCREEN):
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            x, y, w, h = rect.x, rect.y, rect.width, rect.height

            draw_window_frame(cr, x, y, w, h,
                              ui_theme.get_alpha_color("window_frame_outside_1"),
                              ui_theme.get_alpha_color("window_frame_outside_2"),
                              ui_theme.get_alpha_color("window_frame_outside_3"),
                              ui_theme.get_alpha_color("window_frame_inside_1"),
                              ui_theme.get_alpha_color("window_frame_inside_2"),
                              )

    def shape_window_frame(self, widget, rect):
        '''
        Internal function to draw non-rectangular window frame.

        @param widget: A widget of type gtk.Widget.
        @param rect: The bounding region of the window.
        '''
        if self.shape_frame_function:
            self.shape_frame_function(widget, rect)
        elif widget.window != None and widget.get_has_window() and rect.width > 0 and rect.height > 0:
            if self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED != gtk.gdk.WINDOW_STATE_MAXIMIZED:
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

                if (self.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN == gtk.gdk.WINDOW_STATE_FULLSCREEN or
                    self.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED):
                    cr.rectangle(x, y, w, h)
                else:
                    cr.rectangle(x + 1, y, w - 2, 1)
                    cr.rectangle(x, y + 1, w, h - 2)
                    cr.rectangle(x + 1, y + h - 1, w - 2, 1)

                cr.fill()

                # Shape with given mask.
                widget.shape_combine_mask(bitmap, 0, 0)

    def hide_shadow(self):
        '''
        Hide the window shadow.
        '''
        self.shadow_is_visible = False
        self.window_shadow.set_padding(0, 0, 0, 0)

        # This code use for tag deepin-ui window for delete window shadow in deepin-screenshot.
        set_window_property_by_id(self.get_window().xid, "DEEPIN_WINDOW_SHADOW", "0")

    def show_shadow(self):
        '''
        Show the window shadow.
        '''
        self.shadow_is_visible = True
        self.window_shadow.set_padding(self.shadow_padding, self.shadow_padding, self.shadow_padding, self.shadow_padding)

        # This code use for tag deepin-ui window for delete window shadow in deepin-screenshot.
        set_window_property_by_id(self.get_window().xid, "DEEPIN_WINDOW_SHADOW", str(self.shadow_padding))

    def motion_notify(self, widget, event):
        '''
        Internal callback for `motion-notify` signal.

        @param widget: A widget of gtk.Widget.
        @param event: The motion-notify-event of type gtk.gdk.Event
        '''
        if self.enable_resize and self.shadow_is_visible:
            cursor_type = self.get_cursor_type(event)
            if cursor_type != None:
                set_cursor(self, self.cursor_type)
            elif self.cursor_type != None:
                set_cursor(self, None)

            self.cursor_type = cursor_type

    def leave_notify(self, widget, event):
        set_cursor(self, None)

    def get_cursor_type(self, event):
        '''
        Get the cursor position.

        @param event: An event of type gtk.gdk.Event.
        @return: If the cursor is on the frame of the window, return the cursor position. Otherwise return None.
        '''
        # Get event coordinate.
        (ex, ey) = get_event_root_coords(event)

        # Get window allocation.
        rect = self.get_allocation()
        (wx, wy) = self.get_position()
        ww = rect.width
        wh = rect.height

        # Return cursor position.
        return self.get_cursor_type_with_coordinate(ex, ey, wx, wy, ww, wh)

    def get_shadow_size(self):
        '''
        Get the shadow size.

        @return: return the shadow size or (0, 0)
        '''
        if enable_shadow(self) and self.shadow_visible:
            window_state = self.window.get_state()
            if (window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN == gtk.gdk.WINDOW_STATE_FULLSCREEN or
                window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED):
                return (0, 0)
            else:
                return (self.shadow_padding, self.shadow_padding)
        else:
            return (0, 0)

gobject.type_register(Window)

class EmbedWindow(gtk.Plug):
    def __init__(self,
                 enable_resize=False,
                 shadow_radius=6,
                 shadow_visible=True):
        gtk.Plug.__init__(self, 0)
        self.shadow_radius = shadow_radius
        self.enable_resize = enable_resize
        self.shadow_visible = shadow_visible
        self.background_color = (1, 1, 1, 0.93)

        self.init()

# Mix-in Window methods (except __init__) to EmbedWindow
EmbedWindow.__bases__ += (Window,)

gobject.type_register(EmbedWindow)

if __name__ == "__main__":
    import pseudo_skin

    window = Window()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_all()

    gtk.main()
