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

from draw import draw_vlinear, draw_pixbuf
from theme import ui_theme
from window import Window
import gobject
import gtk

HPANED_DIRECTION_LEFT = 0
HPANED_DIRECTION_RIGHT = 1
VPANED_DIRECTION_TOP = 2
VPANED_DIRECTION_BOTTOM = 3

class HPaned(gtk.HPaned):
    '''HPaned.'''
	
    def __init__(self,
                 init_pos,
                 slide_direction=HPANED_DIRECTION_LEFT,
                 arrow_left_hover_dpixbuf=ui_theme.get_pixbuf("paned/arrow_left_hover.png"),
                 arrow_right_hover_dpixbuf=ui_theme.get_pixbuf("paned/arrow_right_hover.png"),
                 ):
        '''Init hpaned.'''
        # Init.
        gtk.HPaned.__init__(self)
        self.slide_pos = init_pos
        self.slide_direction = slide_direction
        self.arrow_left_hover_dpixbuf = arrow_left_hover_dpixbuf
        self.arrow_right_hover_dpixbuf = arrow_right_hover_dpixbuf
        self.hover_drag_button = False
        self.set_position(self.slide_pos)
        self.button_press_x = None
        
        # Signal.
        self.connect_after("expose-event", self.expose_hpaned)
        self.connect("enter-notify-event", self.enter_notify_hpaned)
        self.connect("leave-notify-event", self.leave_notify_hpaned)
        self.connect("button-press-event", self.button_press_hpaned)
        self.connect("button-release-event", self.button_release_hpaned)
        
    def button_press_hpaned(self, widget, event):
        '''Callback for `button-press-event` signal.'''
        self.button_press_x = self.get_position()
        
    def button_release_hpaned(self, widget, event):
        '''Callback for `button-release-event` signal.'''
        rect = widget.allocation
        grip_width = rect.width - self.get_child1().get_allocation().width - self.get_child2().get_allocation().width

        if int(event.x) <= grip_width and self.button_press_x == self.get_position():
            
            self.button_press_x = None
            if self.slide_direction == HPANED_DIRECTION_LEFT:
                if self.is_slide_left():
                    self.slide_pos = self.get_position()
                    self.set_position(0)
                else:
                    if self.slide_pos > 0:
                        self.set_position(self.slide_pos)
                    else:
                        self.set_position(rect.width / 2)
            elif self.slide_direction == HPANED_DIRECTION_RIGHT:
                if self.is_slide_left():
                    if self.slide_pos < rect.width - grip_width:
                        self.set_position(self.slide_pos)
                    else:
                        self.set_position(rect.width / 2)
                else:
                    self.slide_pos = self.get_position()
                    self.set_position(rect.width - grip_width)
            
    def is_slide_left(self):
        '''Whether slide left.'''
        rect = self.get_allocation()
        grip_x = self.get_position()
        grip_width = rect.width - self.get_child1().get_allocation().width - self.get_child2().get_allocation().width

        if self.slide_direction == HPANED_DIRECTION_LEFT:
            if grip_x == 0:
                return False
            else:
                return True
        elif self.slide_direction == HPANED_DIRECTION_RIGHT:
            if grip_x == rect.width - grip_width or grip_x == rect.width - grip_width - 1:
                return True
            else:
                return False
        
    def expose_hpaned(self, widget, event):
        '''Expose hapend.'''
        # Init.
        rect = widget.allocation
        grip_x = self.get_position()
        grip_width = rect.width - self.get_child1().get_allocation().width - self.get_child2().get_allocation().width
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw drag bar background.
        if self.hover_drag_button:
            draw_vlinear(cr, rect.x + grip_x, rect.y, grip_width, rect.height, 
                         ui_theme.get_shadow_color("panedSeparatorHover").get_color_info())
        else:
            draw_vlinear(cr, rect.x + grip_x, rect.y, grip_width, rect.height, 
                         ui_theme.get_shadow_color("panedSeparator").get_color_info())
        
        # Draw drag button.
        if self.hover_drag_button:
            if self.is_slide_left():
                grip_button_pixbuf = self.arrow_left_hover_dpixbuf.get_pixbuf()
            else:
                grip_button_pixbuf = self.arrow_right_hover_dpixbuf.get_pixbuf()
            
            draw_pixbuf(cr, grip_button_pixbuf, 
                        rect.x + grip_x + (grip_width - grip_button_pixbuf.get_width()) / 2,
                        rect.y + (rect.height - grip_button_pixbuf.get_height()) / 2,
                        )

        return False
    
    def enter_notify_hpaned(self, widget, event):
        '''Callback for `enter-notify-event` signal.'''
        self.hover_drag_button = True
        
        self.queue_draw()
        
    def leave_notify_hpaned(self, widget, event):
        '''Callback for `leave-notify-event` signal.'''
        self.hover_drag_button = False
        
        self.queue_draw()
    
gobject.type_register(HPaned)

if __name__ == "__main__":
    window = Window()
    window.set_title('Panes')
    window.set_border_width(10)
    window.set_size_request(225, 150)
    window.connect('destroy', lambda w: gtk.main_quit())

    button1 = gtk.Button('Resize')
    button2 = gtk.Button('Me!')
    
    hpaned = HPaned(100)
    hpaned.add1(button1)
    hpaned.add2(button2)
    
    hpaned_align = gtk.Alignment()    
    hpaned_align.set(0, 0, 1, 1)
    hpaned_align.set_padding(1, 1, 1, 1)
    hpaned_align.add(hpaned)

    window.window_frame.pack_start(hpaned_align)
    window.show_all()

    gtk.main()
