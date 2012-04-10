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

class CheckButton(gtk.Button):
    '''CheckButton.'''
    __gsignals__ = {
        "changed":(gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,))
        }
    
    def __init__(self):
        '''Init.'''        
        # Init.
        gtk.Button.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.size = 18
        self.set_size_request(self.size, self.size)
        self.select_flag = False
        self.hover_flag = False
        
        # Handle signal.
        self.connect("expose-event", self.expose_checkbox)
        self.connect("enter-notify-event", self.enter_notify_checkbox)
        self.connect("leave-notify-event", self.leave_notify_checkbox)
        self.connect("clicked", self.clicked_checkbox)
        
    def expose_checkbox(self, widget, event):
        '''Draw checkbox.'''     
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw light.
        if self.hover_flag:
            shadow_color_infos = ui_theme.get_shadow_color("checkButtonLight").get_color_info()
            shadow_radius = 4
            shadow_padding = 2
            
            with cairo_state(cr):
                cr.rectangle(x, y, shadow_radius, shadow_radius)
                cr.rectangle(x, y + h - shadow_radius, shadow_radius, shadow_radius)
                cr.rectangle(x + w - shadow_radius, y, shadow_radius, shadow_radius)
                cr.rectangle(x + w - shadow_radius, y + h - shadow_radius, shadow_radius, shadow_radius)
                cr.clip()
                    
                draw_radial_round(cr, x + shadow_radius, y + shadow_radius, shadow_radius, shadow_color_infos)
                draw_radial_round(cr, x + shadow_radius, y + h - shadow_radius, shadow_radius, shadow_color_infos)
                draw_radial_round(cr, x + w - shadow_radius, y + shadow_radius, shadow_radius, shadow_color_infos)
                draw_radial_round(cr, x + w - shadow_radius, y + h - shadow_radius, shadow_radius, shadow_color_infos)
            
            draw_vlinear(
                cr, 
                x + shadow_radius, y, 
                w - shadow_radius * 2, shadow_radius, shadow_color_infos)
            draw_vlinear(
                cr, 
                x + shadow_radius, y + h - shadow_radius, 
                w - shadow_radius * 2, shadow_radius, shadow_color_infos, 0, False)
            draw_hlinear(
                cr, 
                x, y + shadow_radius, 
                shadow_radius, h - shadow_radius * 2, shadow_color_infos)
            draw_hlinear(
                cr, 
                x + w - shadow_radius, y + shadow_radius, 
                shadow_radius, h - shadow_radius * 2, shadow_color_infos, 0, False)
        
        # Draw outside four points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("checkButtonAcme").get_color_info()))
        cr.rectangle(x + 2, y + 2, 1, 1)
        cr.rectangle(x + w - 3, y + 2, 1, 1)
        cr.rectangle(x + 2, y + h - 3, 1, 1)
        cr.rectangle(x + w - 3, y + h - 3, 1, 1)
        cr.fill()
        
        # Draw outside eight points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("checkButtonPoint").get_color_info()))
        cr.rectangle(x + 2, y + 3, 1, 1)
        cr.rectangle(x + 3, y + 2, 1, 1)

        cr.rectangle(x + w - 4, y + 2, 1, 1)
        cr.rectangle(x + w - 3, y + 3, 1, 1)

        cr.rectangle(x + 2, y + h - 4, 1, 1)
        cr.rectangle(x + 3, y + h - 3, 1, 1)

        cr.rectangle(x + w - 4, y + h - 3, 1, 1)
        cr.rectangle(x + w - 3, y + h - 4, 1, 1)
        
        cr.fill()

        # Draw outside.
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("checkButtonFrame").get_color()))
        cr.rectangle(x + 2, y + 4, 1, h - 8)
        cr.rectangle(x + w - 3, y + 4, 1, h - 8)
        cr.rectangle(x + 4, y + 2, w - 8, 1)
        cr.rectangle(x + 4, y + h - 3, w - 8, 1)
        cr.fill()

        # Draw inside background.
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("checkButtonBackground").get_color()))
        cr.rectangle(x + 3, y + 3, w - 6, h - 6)
        cr.fill()

        # Draw inside four points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("checkButtonInsidePoint").get_color_info()))
        cr.rectangle(x + 3, y + 3, 1, 1)
        cr.rectangle(x + w - 4, y + 3, 1, 1)
        cr.rectangle(x + 3, y + h - 4, 1, 1)
        cr.rectangle(x + w - 4, y + h - 4, 1, 1)
        cr.fill()

        # Draw select status.
        if self.select_flag:
            draw_pixbuf(cr, ui_theme.get_pixbuf("checkbutton/select.png").get_pixbuf(),
                        x + 4, y + 4)
                
        propagate_expose(widget, event)        
            
        return True
    
    def leave_notify_checkbox(self, widget, event):
        self.hover_flag = False

    def enter_notify_checkbox(self, widget, event):
        '''Press checkbox.'''
        self.hover_flag = True
        
    def clicked_checkbox(self, widget):
        '''Press checkbox'''
        self.select_flag = not self.select_flag
        self.hover_flag = True
            
        self.emit("changed", self.select_flag)
            
        self.queue_draw()
          
if __name__ == "__main__":
    # Test func.
    window = gtk.Window()    
    fixed  = gtk.Fixed()
    
    checkbox1 = CheckButton()
    checkbox2 = CheckButton()

    fixed.put(checkbox1, 30, 130)
    fixed.put(checkbox2, 30, 180)

    window.add(fixed)
    window.set_size_request(300, 300)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    gtk.main()

        
