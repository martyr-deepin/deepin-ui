#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Hailong Qiu <qiuhailong@linuxdeepin.com>
# Maintainer: Hailong Qiu <qiuhailong@linuxdeepin.com>
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

from constant import DEFAULT_FONT_SIZE
from draw import draw_vlinear, draw_font
from theme import ui_theme
from utils import get_content_size, propagate_expose
from window import Window
import gobject
import gtk
        
class Tooltip(Window):
    '''Tooltip.'''
    
    def __init__ (self, text, x, y, text_size=DEFAULT_FONT_SIZE, text_color="tooltipText",
                  paddingX=10, paddingY=10):
        '''Init tooltip.'''
        # Init.
        Window.__init__(self)
        self.text = text
        self.text_size = text_size
        self.text_color = text_color
        self.opacity = 0.0
        self.animation_delay = 50 # milliseconds
        self.animation_ticker = 0
        self.animation_start_times = 5 
        self.animation_stay_times = 40 
        self.animation_end_times = 47
        (font_width, font_height) = get_content_size(text, text_size)
        
        # Init Window.
        self.set_opacity(self.opacity)
        self.set_modal(True)
        self.set_size_request(
            font_width + paddingX * 2, 
            font_height + paddingY * 2)
        self.move(x, y)
        
        # Init signal.
        self.connect("focus-out-event", lambda w,e: self.exit())
        
        self.tooltip_box = gtk.VBox()
        self.window_frame.add(self.tooltip_box)
        self.tooltip_box.connect("expose-event", self.expose_tooltip) 
        
        # Add time show tooltip.
        self.animation_id = gtk.timeout_add(self.animation_delay, self.start_animation)
        
        # Show.
        self.show_all()
        
    def start_animation(self):
        '''Start animation.'''
        # Increase opacity.
        if self.animation_ticker < self.animation_start_times:
            self.opacity = (1.0 / self.animation_start_times) * self.animation_ticker
        # Wait some time.
        elif self.animation_ticker < self.animation_stay_times:
            self.opacity = 1
        # Decrease opacity.
        else:
            self.opacity = 1.0 / (self.animation_end_times - self.animation_stay_times) * (self.animation_end_times - self.animation_ticker)
            
        # Update animation ticker.
        self.animation_ticker += 1
        
        # Exit when reach end times.
        if self.animation_ticker == self.animation_end_times:
            self.exit()
        # Otherw update window opacity.
        else:
            self.set_opacity(self.opacity)
            
        return True
    
    def exit(self):
        '''Exit.'''
        # Make sure animation callback is remove.
        gobject.source_remove(self.animation_id)
        
        # Destroy window.
        self.destroy()
        
    def hide_tooltip(self):
        '''Hide.'''
        # Make sure animation callback is remove.
        gobject.source_remove(self.animation_id)
        
        # Destroy window.
        self.hide_all()

    def expose_tooltip(self, widget, event):
        '''Expose tooltip.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                     ui_theme.get_shadow_color("tooltipBackground").get_color_info())
        
        # Draw font.
        draw_font(cr, self.text, self.text_size, 
                  ui_theme.get_color(self.text_color).get_color(),
                  rect.x, rect.y, rect.width, rect.height)
        
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
    
gobject.type_register(Tooltip)
