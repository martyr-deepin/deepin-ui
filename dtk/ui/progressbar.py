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

from draw import draw_round_rectangle, draw_vlinear, draw_text, draw_radial_round
from theme import ui_theme
from utils import alpha_color_hex_to_cairo, cairo_state, propagate_expose
import cairo
import gobject
import gtk
import pango

class ProgressBar(gtk.Button):
    '''Progress bar.'''
	
    def __init__(self):
        '''Progress bar.'''
        # Init.
        gtk.Button.__init__(self)
        self.progress = 0
        self.light_ticker = 0
        self.test_ticker = 0.0
        
        # Expose callback.
        self.connect("expose-event", self.expose_progressbar)
        gtk.timeout_add(20, self.update_light_ticker)
        
    def expose_progressbar(self, widget, event):
        '''Expose progressbar.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw frame.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("progressbar_frame").get_color_info()))
        cr.set_operator(cairo.OPERATOR_OVER)
        draw_round_rectangle(cr, rect.x, rect.y, rect.width, rect.height, 1)
        cr.stroke()
        
        # Draw background.
        draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                     ui_theme.get_shadow_color("progressbar_background").get_color_info(), 
                     1)
    
        # Draw foreground.
        draw_vlinear(cr, rect.x, rect.y, rect.width * self.progress / 100.0, rect.height, 
                     ui_theme.get_shadow_color("progressbar_foreground").get_color_info(), 
                     1)
        
        # Draw font.
        draw_text(cr, str(self.progress) + "%", 
                  rect.x, rect.y, rect.width, rect.height, 
                  rect.height - 5, "#000000",
                  alignment=pango.ALIGN_CENTER)
        
        # Draw light.
        light_radius = rect.height * 4
        light_offset_x = min(self.light_ticker % 150, 100) / 100.0 * (rect.width + light_radius * 2)
        with cairo_state(cr):
            cr.rectangle(rect.x, rect.y, rect.width * self.progress / 100.0, rect.height)
            cr.clip()
            draw_radial_round(cr, rect.x + light_offset_x - light_radius, rect.y - light_radius / 2, light_radius, 
                              ui_theme.get_shadow_color("progressbar_light").get_color_info())
               
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True        
        
    def update_light_ticker(self):
        '''Update light ticker.'''
        self.light_ticker += 1
        return True
            
    def test_progressbar(self):
        '''Test prorgressbar.'''
        self.test_ticker += 1
        self.progress = self.test_ticker % 101
        self.queue_draw()
        return True
        
gobject.type_register(ProgressBar)

if __name__ == "__main__":
    import pseudo_skin
    
    window = gtk.Window()    
    progressbar = ProgressBar()
    progressbar.set_size_request(200, 14)
    progressbar_align = gtk.Alignment()
    progressbar_align.set(0.5, 0.5, 0.0, 0.0)
    progressbar_align.add(progressbar)
    window.add(progressbar_align)
    window.set_size_request(300, 300)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    gtk.timeout_add(100, progressbar.test_progressbar)
    gtk.main()
