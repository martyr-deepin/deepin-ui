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
from utils import (cairo_state, propagate_expose, resize_window, 
                   set_cursor, get_event_root_coords, enable_shadow, 
                   is_double_click, move_window)

class MplayerWindow(gtk.Window):
    '''Window for mplayer or any software that can't running when window redirect colormap from screen.'''
	
    def __init__(self, enable_resize=False, shadow_radius=6, window_type=gtk.WINDOW_TOPLEVEL):
        '''Init mplayer window.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        skin_config.wrap_skin_window(self)
        self.set_decorated(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.shadow_radius = shadow_radius
        self.frame_radius = 2
        self.shadow_is_visible = True
        self.enable_resize = enable_resize
        self.window_frame = gtk.VBox()
        self.add(self.window_frame)
        self.shape_flag = True
        
        # FIXME: Because mplayer don't allowed window redirect colormap to screen.
        # We build shadow window to emulate it, but shadow's visual effect 
        # is not good enough, so we disable shadow temporary for future fixed.
        self.shadow_visible = False
        
        if enable_shadow(self) and self.shadow_visible:
            self.shadow_padding = self.shadow_radius - self.frame_radius
        else:
            self.shadow_padding = 0
        
        # Init shadow window.
        if enable_shadow(self) and self.shadow_visible:    
            self.window_shadow = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window_shadow.add_events(gtk.gdk.ALL_EVENTS_MASK)
            self.window_shadow.set_decorated(False)
            self.window_shadow.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
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
        '''Adjust window shadow position and size. '''
        if enable_shadow(self) and self.shadow_visible:    
            (x, y) = self.get_position()
            (width, height) = self.get_size()
            
            self.window_shadow.get_window().move_resize(
                x - self.shadow_padding, y - self.shadow_padding,
                width + self.shadow_padding * 2, height + self.shadow_padding * 2
                )
        
    def show_window(self):
        '''Show.'''
        self.show_all()
        
        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.show_all()
        
    def expose_window(self, widget, event):
        '''Expose window.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Clear color to transparent window.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        
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
            
        # Draw window frame.
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
    
    def draw_mask(self, cr, x, y, w, h):
        '''Draw mask.'''
        pass
    
    def set_window_shape(self, shape_flag):
        '''Enable window shape.'''
        self.shape_flag = shape_flag
        self.shape_window(self, self.get_allocation())
        
    def shape_window(self, widget, rect):
        '''Shap window.'''
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
            
            if not self.shape_flag:
                # Don't clip corner when window is fullscreen state.
                cr.rectangle(x, y, w, h)
            elif self.window != None and self.window.get_state() == gtk.gdk.WINDOW_STATE_FULLSCREEN:
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
        '''Shap window shadow.'''
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
        '''Callback for 'expose-event' event of window shadow.'''
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
        '''Hide shadow.'''
        self.shadow_is_visible = False
        
        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.hide_all()
        
    def show_shadow(self):
        '''Show shadow.'''
        self.shadow_is_visible = True
        
        if enable_shadow(self) and self.shadow_visible:
            self.window_shadow.show_all()
        
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
            
        self.adjust_window_shadow(widget, event)    
            
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
        
    def resize_window(self, widget, event):
        '''Resize window.'''
        if self.enable_resize:
            edge = self.get_edge()            
            if edge != None:
                resize_window(self, event, self, edge)
                
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
            
    def motion_notify(self, widget, event):
        '''Callback for motion-notify event.'''
        if self.enable_resize and self.shadow_is_visible:
            self.cursor_type = self.get_cursor_type(event)
            set_cursor(self.window_shadow, self.cursor_type)
            
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
        rect = self.window_shadow.get_allocation()
        (wx, wy) = self.window_shadow.get_position()
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
        return (0, 0)
    
gobject.type_register(MplayerWindow)
    
if __name__ == "__main__":
    window = MplayerWindow()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    window.move(100, 100)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_window()
    
    gtk.main()
