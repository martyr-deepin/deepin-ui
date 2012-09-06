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

from draw import draw_vlinear
from theme import ui_theme
from utils import cairo_state, propagate_expose, color_hex_to_cairo, cairo_disable_antialias
import cairo
import gobject
import gtk

class ProgressBuffer(gobject.GObject):
	
    def __init__(self):
        gobject.GObject.__init__(self)
        self.progress = 0
        
    def render(self, cr, rect):
        # Init.
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw background frame.
        with cairo_state(cr):
            cr.rectangle(x, y + 1, w, h - 2)
            cr.rectangle(x + 1, y, w - 2, h)
            cr.clip()
            
            cr.set_source_rgb(*color_hex_to_cairo("#b3b3b3"))
            cr.rectangle(x, y, w, h)
            cr.set_line_width(1)
            cr.stroke()
            
        # Draw background.
        with cairo_state(cr):
            cr.rectangle(x + 1, y + 1, w - 2, h - 2)
            cr.clip()
            
            draw_vlinear(cr, x + 1, y + 1, w - 2, h - 2,
                         ui_theme.get_shadow_color("progressbar_background").get_color_info(), 
                         )
    
        # Draw foreground frame.
        with cairo_state(cr):
            cr.rectangle(x, y + 1, w, h - 2)
            cr.rectangle(x + 1, y, w - 2, h)
            cr.clip()

            cr.set_antialias(cairo.ANTIALIAS_NONE)
            cr.set_source_rgb(*color_hex_to_cairo("#2e7599"))
            cr.rectangle(x + 1, y + 1, int(w * self.progress / 100) - 1, h - 1)
            cr.set_line_width(1)
            cr.stroke()
            
        # Draw foreground.
        with cairo_state(cr):
            cr.rectangle(x + 1, y + 1, w - 2, h - 2)
            cr.clip()
            
            draw_vlinear(cr, x + 1, y + 1, int(w * self.progress / 100) - 2, h - 2,
                         ui_theme.get_shadow_color("progressbar_foreground").get_color_info(), 
                         )
            
        # Draw light.
        with cairo_disable_antialias(cr):
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(x + 1, y + 1, w - 2, 1)
            cr.fill()

gobject.type_register(ProgressBuffer)

class ProgressBar(gtk.Button):
    '''
    Progress bar.
    
    @undocumented: expose_progressbar
    @undocumented: update_light_ticker
    '''
	
    def __init__(self):
        '''
        Initialize progress bar.
        '''
        # Init.
        gtk.Button.__init__(self)
        self.progress_buffer = ProgressBuffer()
        
        # Expose callback.
        self.connect("expose-event", self.expose_progressbar)
        
    def expose_progressbar(self, widget, event):
        '''
        Internal callback for `expose` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        self.progress_buffer.render(cr, rect)
               
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True        
        
gobject.type_register(ProgressBar)

if __name__ == "__main__":
    import pseudo_skin
    
    window = gtk.Window()    
    progressbar = ProgressBar()
    progressbar.progress_buffer.progress = 100
    progressbar.set_size_request(112, 12)
    progressbar_align = gtk.Alignment()
    progressbar_align.set(0.5, 0.5, 0.0, 0.0)
    progressbar_align.add(progressbar)
    window.add(progressbar_align)
    window.set_size_request(300, 300)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    gtk.main()
