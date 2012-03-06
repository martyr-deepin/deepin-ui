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

class RadioButton(gtk.Button):
    '''Radio.'''
    __gsignals__ = {
        "changed":(gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,(gobject.TYPE_INT,))
        }
    
    def __init__(self):
        '''Init.'''        
        gtk.Button.__init__(self)
        
        self.checked = False
        self.size = 20,20
        self.motion = False
        
        self.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.set_size_request(20, 20)
        self.connect("expose-event", self.expose_radio_button)
        self.connect("enter-notify-event", self.enter_notify_radio_button)
        self.connect("leave-notify-event", self.leave_notify_radio_button)
        self.connect("button-press-event", self.button_press_radio_button)
        
    def expose_radio_button(self, widget, event):
        '''Expose radio.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        (x, y, w, h) = (rect.x, rect.y, rect.width, rect.height)
        
        # Draw Background.
        if self.motion: 
            draw_radial_round(cr, x+w/2, y+h/2, w/2+1, ui_theme.get_dynamic_shadow_color("hSeparator").get_color_info())
        
        # Draw round.
        cr.set_line_width(0.5)
        cr.set_source_rgb(0,0.4,0)
        cr.arc(x+w/2, y+h/2, w/2-4, 0, 2*math.pi)
        cr.stroke()
        
        if self.motion:
            draw_radial_round(cr, x+w/2, y+h/2, w/2, ui_theme.get_dynamic_shadow_color("hSeparator").get_color_info())

        # Radio round Background 
        cr.set_source_rgb(1,1,1)
        cr.arc(x+w/2, y+h/2, w/2-5, 0, 2*math.pi)
        cr.fill()
        
        # Draw radio checked.
        if self.checked:
            draw_radial_round(cr, x+w/2, y+h/2, w/6, ui_theme.get_dynamic_shadow_color("progressbarForeground").get_color_info())
            
        # Propagate expose.
        propagate_expose(widget, event)
        
        return True
            
    def leave_notify_radio_button(self, widget, event):
        self.motion = False
        print 'leave radio event'

    def button_press_radio_button(self, widget, event):
        '''Press radio'''
        if event.button == 1:
            for w in get_match_widgets(widget, type(self).__name__):
                w.toggle(False)

            self.checked = True
            self.motion = True
            print 'clicked radio event %s' % self.checked
        
    def enter_notify_radio_button(self, widget, event):
        '''Press radio.'''
        self.motion = True
        print 'motion radio event'

    def toggle(self, radio_bool):
        '''Toggle radio button status.'''
        self.checked = radio_bool
        self.emit("changed", int(self.checked))
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
