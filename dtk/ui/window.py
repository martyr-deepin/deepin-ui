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
from draw import *
from math import pi
from box import *
import cairo

class Window(gtk.Window):
    '''Window.'''
	
    def __init__(self, enable_resize=False, window_mask=None, shadow_radius=6, window_type=gtk.WINDOW_TOPLEVEL):
        '''Init window.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        self.set_decorated(False)
        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.window_shadow = gtk.Alignment()
        self.window_frame = gtk.VBox()
        self.shadow_radius = shadow_radius
        self.frame_radius = 2
        self.shadow_padding = self.shadow_radius - self.frame_radius
        self.shadow_is_visible = True
        self.cursor_type = None
        self.enable_resize = enable_resize
        self.window_mask = window_mask
        self.background_dpixbuf = ui_theme.get_pixbuf(BACKGROUND_IMAGE)
        
        # Init window frame.
        self.window_shadow.set(0.0, 0.0, 1.0, 1.0)
        self.window_shadow.set_padding(self.shadow_padding, self.shadow_padding, self.shadow_padding, self.shadow_padding)
        
        # Connect widgets.
        self.add(self.window_shadow)
        self.window_shadow.add(self.window_frame)
        
        # Handle signal.
        self.connect_after("expose-event", self.expose_window_background)
        self.window_shadow.connect("expose-event", self.expose_window_shadow)
        self.window_frame.connect("expose-event", self.expose_window_frame)
        self.window_frame.connect("size-allocate", self.shape_window_frame)
        self.connect("size-allocate", lambda w, r: self.queue_draw()) # redraw after size allocation changed
        self.connect("motion-notify-event", self.motion_notify)
        self.connect("button-press-event", self.resize_window)
        self.connect("window-state-event", self.monitor_window_state)
        
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
        with cairo_state(cr):
            if self.shadow_is_visible:
                x = rect.x + self.shadow_padding
                y = rect.y + self.shadow_padding
                w = rect.width - self.shadow_padding * 2
                h = rect.height - self.shadow_padding * 2
            else:
                x, y, w, h = rect.x, rect.y, rect.width, rect.height
            cr.rectangle(x + 2, y, w - 4, 1)
            cr.rectangle(x + 1, y + 1, w - 2, 1)
            cr.rectangle(x, y + 2, w, h - 4)
            cr.rectangle(x + 1, y + h - 2, w - 2, 1)
            cr.rectangle(x + 2, y + h - 1, w - 4, 1)
            cr.clip()
            
            # Draw background.
            draw_pixbuf(cr, pixbuf, rect.x, rect.y, 0.95)
            
            # Draw mask.
            if self.window_mask:
                cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color(self.window_mask).get_color_info()))
                cr.rectangle(0, 0, rect.width, rect.height)    
                cr.fill()
        
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
            
            # Get border width.
            color_infos = ui_theme.get_shadow_color("windowShadow").get_color_info()
            
            with cairo_state(cr):
                # Clip four corner.
                cr.rectangle(x, y, x + self.shadow_radius, y + self.shadow_radius)
                cr.rectangle(x + w - self.shadow_radius, y, x + w, y + self.shadow_radius)
                cr.rectangle(x, y + h - self.shadow_radius, x + self.shadow_radius, y + h)
                cr.rectangle(x + w - self.shadow_radius, y + h - self.shadow_radius, x + w, y + h)
                cr.clip()
                
                # Draw four round.
                draw_radial_round(cr, x + self.shadow_radius, y + self.shadow_radius, self.shadow_radius, color_infos)
                draw_radial_round(cr, x + self.shadow_radius, y + h - self.shadow_radius, self.shadow_radius, color_infos)
                draw_radial_round(cr, x + w - self.shadow_radius, y + self.shadow_radius, self.shadow_radius, color_infos)
                draw_radial_round(cr, x + w - self.shadow_radius, y + h - self.shadow_radius, self.shadow_radius, color_infos)
            
            with cairo_state(cr):
                # Clip four side.
                cr.rectangle(x, y + self.shadow_radius, x + self.shadow_padding, y + h - self.shadow_radius)
                cr.rectangle(x + w - self.shadow_padding, y + self.shadow_radius, x + w, y + h - self.shadow_radius)
                cr.rectangle(x + self.shadow_radius, y, x + w - self.shadow_radius, y + self.shadow_padding)
                cr.rectangle(x + self.shadow_radius, y + h - self.shadow_padding, x + w - self.shadow_radius, y + h)
                cr.clip()
                
                # Draw four side.
                draw_vlinear(
                    cr, 
                    x + self.shadow_radius, y, 
                    w - self.shadow_radius * 2, self.shadow_radius, color_infos)
                draw_vlinear(
                    cr, 
                    x + self.shadow_radius, y + h - self.shadow_radius, 
                    w - self.shadow_radius * 2, self.shadow_radius, color_infos, 0, False)
                draw_hlinear(
                    cr, 
                    x, y + self.shadow_radius, 
                    self.shadow_radius, h - self.shadow_radius * 2, color_infos)
                draw_hlinear(
                    cr, 
                    x + w - self.shadow_radius, y + self.shadow_radius, 
                    self.shadow_radius, h - self.shadow_radius * 2, color_infos, 0, False)
    
        # Propagate expose.
        propagate_expose(widget, event)
    
        return True
    
    def expose_window_frame(self, widget, event):
        '''Expose window frame.'''
        # Init.
        cr = widget.window.cairo_create()
        pixbuf = self.background_dpixbuf.get_pixbuf()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        with cairo_disable_antialias(cr):    
            # Set line width.
            cr.set_line_width(1)
            
            # Set OPERATOR_OVER operator.
            cr.set_operator(cairo.OPERATOR_OVER)
            
            # Draw frame.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("frame").get_color_info()))
            
            cr.rectangle(x + 2, y, w - 4, 1)         # top side
            cr.rectangle(x + w - 1, y + 2, 1, h - 4) # right side
            cr.rectangle(x + 2, y + h - 1, w - 4, 1) # bottom side
            cr.rectangle(x, y + 2, 1, h - 4)         # left side
            
            cr.fill()
            
            # Draw frame inner dot.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("frame").get_color_info()))
            
            cr.rectangle(x + 1, y + 1, 1, 1)         # top-left inner dot
            cr.rectangle(x + w - 2, y + 1, 1, 1)     # top-right inner dot
            cr.rectangle(x + w - 2, y + h - 2, 1, 1) # bottom-right inner dot
            cr.rectangle(x + 1, y + h - 2, 1, 1)     # bottom-left inner dot
            
            cr.fill()
            
            # Draw frame outter dot.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("frameDot").get_color_info()))
            
            cr.rectangle(x + 1, y, 1, 1) # top-left outter dot
            cr.rectangle(x, y + 1, 1, 1)
            
            cr.rectangle(x + w - 2, y, 1, 1) # top-right outter dot
            cr.rectangle(x + w - 1, y + 1, 1, 1)
            
            cr.rectangle(x + 1, y + h - 1, 1, 1) # bottom-left outter dot
            cr.rectangle(x, y + h - 2, 1, 1)
            
            cr.rectangle(x + w - 2, y + h - 1, 1, 1) # bottom-right outter dot
            cr.rectangle(x + w - 1, y + h - 2, 1, 1)
            
            cr.fill()
            
            # Draw frame light.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("frameLight").get_color_info()))
            
            cr.rectangle(x + 2, y + 1, w - 4, 1)     # top side
            cr.rectangle(x + w - 2, y + 2, 1, h - 4) # right side
            cr.rectangle(x + 2, y + h - 2, w - 4, 1) # bottom side
            cr.rectangle(x + 1, y + 2, 1, h - 4)     # left side
            
            cr.fill()
            
            # Draw frame light dot.
            cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("frameLightDot").get_color_info()))
            
            cr.rectangle(x + 2, y + 2, 1, 1)         # top-left light dot
            cr.rectangle(x + w - 3, y + 2, 1, 1)     # top-right light dot
            cr.rectangle(x + w - 3, y + h - 3, 1, 1) # bottom-right light dot
            cr.rectangle(x + 2, y + h - 3, 1, 1)     # bottom-left light dot
            
            cr.fill()
        
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
            
            # Redraw whole window.
            # self.queue_draw()   # redraw window, not redraw window frame
            
    def hide_shadow(self):
        '''Hide shadow.'''
        self.shadow_is_visible = False
        self.window_shadow.set_padding(0, 0, 0, 0)
        # self.queue_draw()
        
    def show_shadow(self):
        '''Show shadow.'''
        self.shadow_is_visible = True
        self.window_shadow.set_padding(self.shadow_padding, self.shadow_padding, self.shadow_padding, self.shadow_padding)
        # self.queue_draw()
        
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
