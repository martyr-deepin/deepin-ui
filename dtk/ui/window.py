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

from constant import EDGE_DICT, BACKGROUND_IMAGE
from draw import draw_pixbuf, draw_window_shadow, draw_window_frame
from theme import ui_theme
from utils import cairo_state, propagate_expose, set_cursor, resize_window, get_event_root_coords, enable_shadow, alpha_color_hex_to_cairo
import cairo
import gobject
import gtk

class Window(gtk.Window):
    '''Window.'''
	
    def __init__(self, enable_resize=False, window_mask=None, shadow_radius=6, window_type=gtk.WINDOW_TOPLEVEL):
        '''Init window.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        self.window_mask = window_mask
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
        self.background_dpixbuf = ui_theme.get_pixbuf(BACKGROUND_IMAGE)
        
        # Shadow setup.
        if enable_shadow(self):
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
        self.connect("size-allocate", lambda w, r: self.queue_draw()) # redraw after size allocation changed
        self.connect("motion-notify-event", self.motion_notify)
        self.connect("button-press-event", self.resize_window)
        self.connect("window-state-event", self.monitor_window_state)
        self.window_frame.connect("expose-event", self.expose_window_frame)
        
    def show_window(self):
        '''Show.'''
        self.show_all()
        
    def change_background(self, background_dpixbuf):
        '''Change background.'''
        self.background_dpixbuf = background_dpixbuf                
        
    def expose_window_background(self, widget, event):
        '''Expose window background.'''
        # Init.
        cr = widget.window.cairo_create()
        pixbuf = self.background_dpixbuf.get_pixbuf()
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
            
            draw_pixbuf(cr, pixbuf, x, y)
        
            # Draw mask.
            if self.window_mask:
                cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color(self.window_mask).get_color_info()))
                cr.rectangle(x, y, w, h)    
                cr.fill()
            
        # Draw corner shadow.
        with cairo_state(cr):
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("windowShadowCorner").get_color_info()))
            
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
            
            draw_pixbuf(cr, pixbuf, x, y, 0.5)
            
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
        
    def expose_window_shadow(self, widget, event):
        '''Callback for 'expose-event' event of window shadow.'''
        if self.shadow_is_visible:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            
            # Draw window shadow.
            draw_window_shadow(cr, x, y, w, h, self.shadow_radius, self.shadow_padding)
    
        # Propagate expose.
        propagate_expose(widget, event)
    
        return True
    
    def expose_window_frame(self, widget, event):
        '''Expose window frame.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        draw_window_frame(cr, x, y, w, h)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return False

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
            self.cursor_type = self.get_cursor_type(event)
            set_cursor(self, self.cursor_type)
            
    def resize_window(self, widget, event):
        '''Resize window.'''
        if self.enable_resize:
            edge = self.get_edge()            
            if edge != None:
                resize_window(widget, event, self, edge)
                
    def monitor_window_state(self, widget, event):
        '''Monitor window state, add shadow when window at maximized or fullscreen status.
Otherwise hide shadow.'''
        window_state = self.window.get_state()
        if window_state in [gtk.gdk.WINDOW_STATE_MAXIMIZED, gtk.gdk.WINDOW_STATE_FULLSCREEN]:
            self.hide_shadow()
        else:
            self.show_shadow()
        
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

gobject.type_register(Window)
    
if __name__ == "__main__":
    window = Window()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_all()
    
    gtk.main()
