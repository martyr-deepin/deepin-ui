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

from constant import BACKGROUND_IMAGE, EDGE_DICT
from draw import draw_pixbuf, draw_window_shadow
from theme import ui_theme
from utils import cairo_state, alpha_color_hex_to_cairo, cairo_disable_antialias, propagate_expose, resize_window, set_cursor, get_event_root_coords
import cairo
import gobject
import gtk

class MplayerWindow(gtk.Window):
    '''Window for mplayer or any software that can't running when window redirect colormap from screen.'''
	
    def __init__(self, enable_resize=False, window_mask=None, shadow_radius=6, window_type=gtk.WINDOW_TOPLEVEL):
        '''Init mplayer window.'''
        # Init.
        gtk.Window.__init__(self, window_type)
        self.set_decorated(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.shadow_radius = shadow_radius
        self.frame_radius = 2
        self.shadow_is_visible = True
        self.enable_resize = enable_resize
        self.window_mask = window_mask
        self.background_dpixbuf = ui_theme.get_pixbuf(BACKGROUND_IMAGE)
        self.window_frame = gtk.VBox()
        self.add(self.window_frame)
        self.shape_flag = True
        
        # FIXME: Because mplayer don't allowed window redirect colormap to screen.
        # We build shadow window to emulate it, but shadow's visual effect 
        # is not good enough, so we disable shadow temporary for future fixed.
        self.enable_shadow = False
        
        if self.is_composited() and self.enable_shadow:
            self.shadow_padding = self.shadow_radius - self.frame_radius
        else:
            self.shadow_padding = 0
        
        # Init shadow window.
        if self.is_composited() and self.enable_shadow:    
            # Have two reasons use WINDOW_POPUP here:
            # 1. Make window shadow can move to negative position.
            # 2. Make user can't close window through Alt+Space keystroke.
            # self.window_shadow = gtk.Window(gtk.WINDOW_POPUP)
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
        
        if self.is_composited() and self.enable_shadow:    
            self.window_shadow.connect("expose-event", self.expose_window_shadow)
            self.window_shadow.connect("size-allocate", self.shape_window_shadow)
            self.window_shadow.connect("button-press-event", self.resize_window)
            self.window_shadow.connect("motion-notify-event", self.motion_notify)
        
    def adjust_window_shadow(self, widget, event):
        '''Adjust window shadow position and size. '''
        if self.is_composited() and self.enable_shadow:    
            (x, y) = self.get_position()
            (width, height) = self.get_size()
            
            print (x - self.shadow_padding, y - self.shadow_padding,
                   width + self.shadow_padding * 2, height + self.shadow_padding * 2)
            
            self.window_shadow.get_window().move_resize(
                x - self.shadow_padding, y - self.shadow_padding,
                width + self.shadow_padding * 2, height + self.shadow_padding * 2
                )
        
    def show_window(self):
        '''Show.'''
        self.show_all()
        
        if self.is_composited() and self.enable_shadow:
            self.window_shadow.show_all()
        
    def change_background(self, background_dpixbuf):
        '''Change background.'''
        self.background_dpixbuf = background_dpixbuf                
        
    def expose_window(self, widget, event):
        '''Expose window.'''
        # Init.
        cr = widget.window.cairo_create()
        pixbuf = self.background_dpixbuf.get_pixbuf()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Clear color to transparent window.
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        
        # Save cairo context.
        with cairo_state(cr):
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
        
        return True
    
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
                if self.is_composited() and self.enable_shadow:
                    cr.rectangle(x + 2, y, w - 4, 1)
                    cr.rectangle(x + 1, y + 1, w - 2, 1)
                    cr.rectangle(x, y + 2, w, h - 4)
                    cr.rectangle(x + 1, y + h - 2, w - 2, 1)
                    cr.rectangle(x + 2, y + h - 1, w - 4, 1)
                else:
                    cr.rectangle(x + 1, y, w - 2, 1)
                    cr.rectangle(x, y + 1, w, h - 2)
                    cr.rectangle(x + 1, y + h - 1, w - 2, 1)
            cr.fill()
            
            # Shape with given mask.
            widget.shape_combine_mask(bitmap, 0, 0)
            
            # Redraw whole window.
            self.queue_draw()
            
            if self.is_composited() and self.enable_shadow:
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
            
            if self.is_composited() and self.enable_shadow:
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
            draw_window_shadow(cr, x, y, w, h, self.shadow_radius, self.shadow_padding)
    
        # Propagate expose.
        propagate_expose(widget, event)
    
        return True
            
    def hide_shadow(self):
        '''Hide shadow.'''
        self.shadow_is_visible = False
        
        if self.is_composited() and self.enable_shadow:
            self.window_shadow.hide_all()
        
    def show_shadow(self):
        '''Show shadow.'''
        self.shadow_is_visible = True
        
        if self.is_composited() and self.enable_shadow:
            self.window_shadow.show_all()
        
    def monitor_window_state(self, widget, event):
        '''Monitor window state, add shadow when window at maximized or fullscreen status.
Otherwise hide shadow.'''
        window_state = self.window.get_state()
        if window_state in [gtk.gdk.WINDOW_STATE_MAXIMIZED, gtk.gdk.WINDOW_STATE_FULLSCREEN]:
            self.hide_shadow()
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
        
gobject.type_register(MplayerWindow)
    
if __name__ == "__main__":
    window = MplayerWindow()
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(500, 500)
    window.move(100, 100)
    # window.window_frame.add(gtk.Button("Linux Deepin"))
    window.show_window()
    
    gtk.main()
