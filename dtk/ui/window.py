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

from constant import EDGE_DICT
from draw import draw_window_shadow, draw_window_frame
from skin_config import skin_config
from theme import ui_theme
import cairo
import gobject
import gtk
from utils import (cairo_state, propagate_expose, set_cursor, 
                   resize_window, get_event_root_coords, 
                   enable_shadow, alpha_color_hex_to_cairo, 
                   is_double_click, move_window)

class Window(gtk.Window):
    '''Window.'''
	
    def __init__(self, enable_resize=False, shadow_radius=6, window_type=gtk.WINDOW_TOPLEVEL, shadow_visible=True):
        '''Init window.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        skin_config.wrap_skin_window(self)
        self.set_decorated(False)
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.window_shadow = gtk.Alignment()
        self.window_frame = gtk.VBox()
        self.shadow_radius = shadow_radius
        self.frame_radius = 2
        self.shadow_is_visible = True
        self.cursor_type = None
        self.enable_resize = enable_resize
        self.shadow_visible = shadow_visible
        
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
        self.connect("button-press-event", self.resize_window)
        self.connect("window-state-event", self.monitor_window_state)
        self.window_frame.connect("expose-event", self.expose_window_frame)
        
    def show_window(self):
        '''Show.'''
        self.show_all()
        
    def expose_window_background(self, widget, event):
        '''Expose window background.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Clear color to transparent window.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        
        # Save cairo context.
        if self.shadow_is_visible:
            x = rect.x + self.shadow_padding
            y = rect.y + self.shadow_padding
            w = rect.width - self.shadow_padding * 2
            h = rect.height - self.shadow_padding * 2
        else:
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            
        # Draw background.
        with cairo_state(cr):
            cr.rectangle(x + 2, y, w - 4, 1)
            cr.rectangle(x + 1, y + 1, w - 2, 1)
            cr.rectangle(x, y + 2, w, h - 4)
            cr.rectangle(x + 2, y + h - 1, w - 4, 1)
            cr.rectangle(x + 1, y + h - 2, w - 2, 1)
            
            cr.clip()
            
            skin_config.render_background(cr, self, x, y)
        
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
            
            skin_config.render_background(cr, self, x, y)
            
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
        
    def draw_mask(self, cr, x, y, w, h):
        '''Draw mask.'''
        pass
    
    def expose_window_shadow(self, widget, event):
        '''Callback for 'expose-event' event of window shadow.'''
        if self.shadow_is_visible:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            
            # Draw window shadow.
            draw_window_shadow(cr, x, y, w, h, self.shadow_radius, self.shadow_padding, ui_theme.get_shadow_color("window_shadow"))
    
    def expose_window_frame(self, widget, event):
        '''Expose window frame.'''
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
        '''Shap window frame.'''
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
            
            cr.rectangle(x + 1, y, w - 2, 1)
            cr.rectangle(x, y + 1, w, h - 2)
            cr.rectangle(x + 1, y + h - 1, w - 2, 1)
            
            cr.fill()
            
            # Shape with given mask.
            widget.shape_combine_mask(bitmap, 0, 0)
            
    def hide_shadow(self):
        '''Hide shadow.'''
        self.shadow_is_visible = False
        self.window_shadow.set_padding(0, 0, 0, 0)
        
    def show_shadow(self):
        '''Show shadow.'''
        self.shadow_is_visible = True
        self.window_shadow.set_padding(self.shadow_padding, self.shadow_padding, self.shadow_padding, self.shadow_padding)
        
    def min_window(self):
        '''Min window.'''
        self.iconify()
        
    def toggle_max_window(self):
        '''Toggle window.'''
        window_state = self.window.get_state()
        if window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
            self.unmaximize()
        else:
            self.maximize()
            
    def toggle_fullscreen_window(self):
        '''Toggle fullscreen window.'''
        window_state = self.window.get_state()
        if window_state == gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.unfullscreen()
        else:
            self.fullscreen()
            
    def close_window(self):
        '''Close window.'''
        # Hide window immediately when user click close button,
        # user will feeling this software very quick, ;p
        self.hide_all()

        self.emit("destroy")
    
        return False
        
    def motion_notify(self, widget, event):
        '''Callback for motion-notify event.'''
        if self.enable_resize and self.shadow_is_visible:
            cursor_type = self.get_cursor_type(event)
            if cursor_type != None:
                set_cursor(self, self.cursor_type)
            elif self.cursor_type != None:
                set_cursor(self, None)
                
            self.cursor_type = cursor_type
            
    def resize_window(self, widget, event):
        '''Resize window.'''
        if self.enable_resize:
            edge = self.get_edge()            
            if edge != None:
                resize_window(widget, event, self, edge)
                
    def is_disable_window_maximized(self):
        '''Disable window maximized.'''
        return False                
                
    def monitor_window_state(self, widget, event):
        '''Monitor window state, add shadow when window at maximized or fullscreen status.
Otherwise hide shadow.'''
        window_state = self.window.get_state()
        if window_state in [gtk.gdk.WINDOW_STATE_MAXIMIZED, gtk.gdk.WINDOW_STATE_FULLSCREEN]:
            self.hide_shadow()
            
            if self.is_disable_window_maximized():
                self.unmaximize()
        else:
            self.show_shadow()
        
    def add_move_event(self, widget):
        '''Add move window event.'''
        widget.connect("button-press-event", lambda w, e: move_window(w, e, self))            
        
    def add_toggle_event(self, widget):
        '''Add toggle window event.'''
        widget.connect("button-press-event", self.double_click_window)        
        
    def double_click_window(self, widget, event):
        '''Handle double click on window.'''
        if is_double_click(event):
            self.toggle_max_window()
            
        return False    
            
    def get_edge(self):
        '''Get edge.'''
        if EDGE_DICT.has_key(self.cursor_type):
            return EDGE_DICT[self.cursor_type]
        else:
            return None

    def get_cursor_type(self, event):
        '''Get cursor position.'''
        # Get event coordinate.
        (ex, ey) = get_event_root_coords(event)
        
        # Get window allocation.
        rect = self.get_allocation()
        (wx, wy) = self.get_position()
        ww = rect.width
        wh = rect.height
        
        # Return cursor position. 
        if wx <= ex <= wx + self.shadow_padding:
            if wy <= ey <= wy + self.shadow_padding * 2:
                return gtk.gdk.TOP_LEFT_CORNER
            elif wy + wh - (self.shadow_padding * 2) <= ey <= wy + wh:
                return gtk.gdk.BOTTOM_LEFT_CORNER
            elif wy + self.shadow_padding < ey < wy + wh - self.shadow_padding:
                return gtk.gdk.LEFT_SIDE
            else:
                return None
        elif wx + ww - self.shadow_padding <= ex <= wx + ww:
            if wy <= ey <= wy + self.shadow_padding * 2:
                return gtk.gdk.TOP_RIGHT_CORNER
            elif wy + wh - (self.shadow_padding * 2) <= ey <= wy + wh:
                return gtk.gdk.BOTTOM_RIGHT_CORNER
            elif wy + self.shadow_padding < ey < wy + wh - self.shadow_padding:
                return gtk.gdk.RIGHT_SIDE
            else:
                return None
        elif wx + self.shadow_padding < ex < wx + ww - self.shadow_padding:
            if wy <= ey <= wy + self.shadow_padding:
                return gtk.gdk.TOP_SIDE
            elif wy + wh - self.shadow_padding <= ey <= wy + wh:
                return gtk.gdk.BOTTOM_SIDE
            else: 
                return None
        else:
            return None
        
    def get_shadow_size(self):
        '''Get shadow size.'''
        if enable_shadow(self) and self.shadow_visible:
            window_state = self.window.get_state()
            if window_state in [gtk.gdk.WINDOW_STATE_MAXIMIZED, gtk.gdk.WINDOW_STATE_FULLSCREEN]:
                return (0, 0)
            else:
                return (self.shadow_padding, self.shadow_padding)
        else:
            return (0, 0)
        
gobject.type_register(Window)
    
if __name__ == "__main__":
    import pseudo_skin
    
    window = Window()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_all()
    
    gtk.main()
