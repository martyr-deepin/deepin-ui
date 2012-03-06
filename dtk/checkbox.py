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
import gobject

class CheckBox(gtk.Button):
    '''CheckBox.'''
    __gsignals__ = {
        "changed":(gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,(gobject.TYPE_INT,))
        }
    
    def __init__(self):
        '''Init.'''        
        gtk.Button.__init__(self)
        self.checked = False
        self.motion = False
        
        self.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.set_size_request(20, 20)
        
        # Add events mask
        self.connect("expose-event", self.expose_checkbox)
        self.connect("enter-notify-event", self.enter_notify_checkbox)
        self.connect("leave-notify-event", self.leave_notify_checkbox)
        self.connect("button-press-event", self.button_press_checkbox)
        
    def expose_checkbox(self, widget, event):
        '''Expose radio.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        (x, y, w, h) = rect.x, rect.y, rect.width, rect.height
        
        '''Draw checkbox.'''     
        # CheckBox linear.
        if self.motion:
            draw_vlinear(cr, x, y, w, h, ui_theme.get_dynamic_shadow_color("progressbarBackground").get_color_info())
        
        # Checkbox border.
        cr.set_line_width(0.2)
        cr.set_source_rgb(0, 0.3, 0)
        draw_round_rectangle(cr, x+2, y+2, w-4, h-4, 0.5)
        cr.stroke()
        
        # Checkbox border backgourd.
        cr.set_source_rgb(1,1,1)
        cr.rectangle(x+3, y+3, w-6, h-6)
        cr.fill()
    
        if self.checked:
            print self.checked
            #draw checked state
            cr.set_line_width(0.5)
            cr.set_source_rgba(0,0.6,0,0.5)
            for i in range(0,4):
                cr.move_to(x+i+4, y+h/2)
                cr.line_to(x+w/2, y+h-i-4)
                cr.line_to(x+w-i-4, y+i+4)
            
                cr.stroke()
            
        return True
    
    def leave_notify_checkbox(self, widget, event):
        self.motion = False

    def button_press_checkbox(self, widget, event):
        '''Press checkbox'''
        if event.button == 1:
            self.checked = (not self.checked)
            self.motion = True

    def enter_notify_checkbox(self, widget, event):
        '''Press checkbox.'''
        self.motion = True
        
    def toggle(self, radio_bool):
        '''Checked radio'''
        self.emit("changed", int(self.checked))
        self.checked = radio_bool
        self.queue_draw()
        
          
if __name__ == "__main__":
    # Test func.
    window = gtk.Window()    
    fixed  = gtk.Fixed()
    
    checkbox = CheckBox()
    checkbox1 = CheckBox()
    checkbox2 = CheckBox()

    checkbox.set_size_request(80, 80)
    fixed.put(checkbox,  30, 40)
    fixed.put(checkbox1, 30, 130)
    fixed.put(checkbox2, 30, 180)

    window.add(fixed)
    window.set_size_request(300, 300)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    gtk.main()

        
