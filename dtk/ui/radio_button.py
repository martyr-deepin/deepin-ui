#! /usr/bin/env python

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Qiu Hailong
# 
# Author:     Qiu Hailong <qiuhailong@linuxdeepin.com>
# Maintainer: Qiu Hailong <qiuhailong@linuxdeepin.com>
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

from draw import *
import math
import gobject
import dtk_cairo_blur    

class RadioButton(gtk.Button):
    '''Radio.'''
    __gsignals__ = {
        "changed":(gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,(gobject.TYPE_BOOLEAN,))
        }
    
    def __init__(self):
        '''Init.'''        
        # Init.
        gtk.Button.__init__(self)
        self.select_flag = False
        self.light_radius = 8
        self.size = self.light_radius * 2
        self.round_background_radius = 5
        self.round_frame_radius = 6
        self.round_dot_radius = 3
        self.hover_flag = False
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_size_request(self.size, self.size)
        
        # Handle signal.
        self.connect("expose-event", self.expose_radio_button)
        self.connect("enter-notify-event", self.enter_notify_radio_button)
        self.connect("leave-notify-event", self.leave_notify_radio_button)
        self.connect("clicked", self.clicked_radio_button)
        
    def expose_radio_button(self, widget, event):
        '''Expose radio.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw background.
        if self.hover_flag: 
            draw_radial_round(
                cr, x + w / 2, y + h / 2, 
                self.light_radius,
                ui_theme.get_shadow_color("radioButtonLight").get_color_info())
        
        # Radio round background 
        cr.set_source_rgb(1, 1, 1)
        cr.arc(x + w / 2, y + h / 2, self.round_background_radius, 0, 2 * math.pi)
        cr.fill()
        
        # Draw round.
        cr.set_line_width(1)
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("radioButtonFrame").get_color()))
        cr.arc(x + w / 2, y + h / 2, self.round_frame_radius, 0, 2 * math.pi)
        cr.stroke()
        
        # Draw radio select dot.
        if self.select_flag:
            draw_radial_round(
                cr, x + w / 2, y + h / 2, 
                self.round_dot_radius, 
                ui_theme.get_shadow_color("radioButtonDot").get_color_info())
            
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
            
    def leave_notify_radio_button(self, widget, event):
        self.hover_flag = False

    def enter_notify_radio_button(self, widget, event):
        '''Press radio.'''
        self.hover_flag = True

    def clicked_radio_button(self, widget):
        '''Press radio'''
        for w in get_match_widgets(widget, type(self).__name__):
            w.set_select_flag_status(False)

        self.select_flag = True
        self.hover_flag = True
        
    def set_select_flag_status(self, status):
        '''Set select status of radio button.'''
        self.select_flag = status
        self.emit("changed", self.select_flag)
        self.queue_draw()
        
gobject.type_register(RadioButton)
    
if __name__ == "__main__":
    window = gtk.Window()    
    fixed  = gtk.Fixed()
    
    radio = RadioButton()
    radio1 = RadioButton()
    radio2 = RadioButton()
    
    fixed.put(radio,  30, 40)
    fixed.put(radio1, 30, 70)
    fixed.put(radio2, 30, 100)
    
    window.add(fixed)
    window.set_size_request(300, 300)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    gtk.main()
