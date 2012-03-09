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

from utils import *
from draw import *
from box import *
import gtk
import gobject

class VolumeButton(gtk.HBox):
    '''Volume button.'''
	
    def __init__(self, 
                 init_value=100,
                 min_value=0,
                 max_value=100,
                 volume_padding=0,
                 play_status=True,
                 play_normal_dpixbuf=ui_theme.get_pixbuf("volumebutton/play_normal.png"),
                 play_hover_dpixbuf=ui_theme.get_pixbuf("volumebutton/play_hover.png"),
                 mute_normal_dpixbuf=ui_theme.get_pixbuf("volumebutton/mute_normal.png"),
                 mute_hover_dpixbuf=ui_theme.get_pixbuf("volumebutton/mute_hover.png"),
                 volume_fg_dpixbuf=ui_theme.get_pixbuf("volumebutton/volume_fg.png"),
                 volume_bg_dpixbuf=ui_theme.get_pixbuf("volumebutton/volume_bg.png"),
                 ):
        '''Init volume button.'''
        # Init.
        gtk.HBox.__init__(self)
        self.play_normal_dpixbuf = play_normal_dpixbuf
        self.play_hover_dpixbuf = play_hover_dpixbuf
        self.mute_normal_dpixbuf = mute_normal_dpixbuf
        self.mute_hover_dpixbuf = mute_hover_dpixbuf
        self.volume_fg_dpixbuf = volume_fg_dpixbuf
        self.volume_bg_dpixbuf = volume_bg_dpixbuf
        self.bg_num = 10
        self.middle_padding = 4
        self.volume_padding = volume_padding
        self.volume_button = gtk.ToggleButton()
        self.volume_progressbar = gtk.HScale()
        self.volume_progressbar.set_range(min_value, max_value)
        self.volume_progressbar.set_value(init_value)
        self.volume_progressbar.set_draw_value(False)
        self.focus_status = False
        self.set_play_status(play_status)
        set_clickable_cursor(self.volume_progressbar)
        
        # Init size and child widgets.
        self.set_size_request(
            self.play_normal_dpixbuf.get_pixbuf().get_width() + self.volume_bg_dpixbuf.get_pixbuf().get_width() * self.bg_num + self.volume_padding * (self.bg_num - 1) + self.middle_padding,
            self.play_normal_dpixbuf.get_pixbuf().get_height()
            )
        self.volume_button_align = gtk.Alignment()
        self.volume_button_align.set(0.0, 0.0, 0.0, 0.0)
        self.volume_button_align.set_padding(0, 0, 0, self.middle_padding)
        self.volume_button_align.add(self.volume_button)
        self.pack_start(self.volume_button_align, False, False)
        self.pack_start(self.volume_progressbar, True, True)
        
        # Expose event.
        self.volume_button.connect("toggled", self.toggle_volume_button)
        self.volume_button.connect("enter-notify-event", self.enter_volume_button)
        self.volume_button.connect("leave-notify-event", self.leave_volume_button)
        self.volume_button.connect("expose-event", self.expose_volume_button)
        self.volume_progressbar.connect("expose-event", self.expose_volume_progressbar)
        self.volume_progressbar.connect("button-press-event", self.press_volume_progressbar)
        self.volume_progressbar.get_adjustment().connect("value-changed", self.monitor_volume_change)
        
    def set_play_status(self, play_status):
        '''Set play status.'''
        self.play_status = play_status
        self.volume_button.set_active(play_status)
        
    def toggle_volume_button(self, widget):
        '''Toggle volume button.'''
        self.play_status = self.volume_button.get_active()
        self.queue_draw()
        
        return False        
    
    def enter_volume_button(self, widget, event):
        '''Enter volume button.'''
        self.focus_status = True
        self.queue_draw()
        
        return False
    
    def leave_volume_button(self, widget, event):
        '''Leave volume button.'''
        self.focus_status = False
        self.queue_draw()
        
        return False
        
    def expose_volume_button(self, widget, event):
        '''Callback for `expose-event` event.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw.
        if self.play_status:
            if self.focus_status:
                draw_pixbuf(cr, self.play_hover_dpixbuf.get_pixbuf(), x, y)
            else:
                draw_pixbuf(cr, self.play_normal_dpixbuf.get_pixbuf(), x, y)
        else:
            if self.focus_status:
                draw_pixbuf(cr, self.mute_hover_dpixbuf.get_pixbuf(), x, y)
            else:
                draw_pixbuf(cr, self.mute_normal_dpixbuf.get_pixbuf(), x, y)

        # Propagate expose to children.
        propagate_expose(widget, event)
    
        return True
    
    def expose_volume_progressbar(self, widget, event):
        '''Callback for `expose-event` event.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw background.
        for i in range(0, self.bg_num):
            draw_pixbuf(cr, self.volume_bg_dpixbuf.get_pixbuf(), 
                        x + i * (self.volume_bg_dpixbuf.get_pixbuf().get_width() + self.volume_padding),
                        y + (h - self.volume_bg_dpixbuf.get_pixbuf().get_height()) / 2)
            
        # Draw foreground.
        if self.play_status:
            upper = self.volume_progressbar.get_adjustment().get_upper() 
            lower = self.volume_progressbar.get_adjustment().get_lower() 
            value = self.volume_progressbar.get_adjustment().get_value()
            total_length = upper - lower
            pos = value - lower
            value = int((pos / total_length * w / (self.volume_bg_dpixbuf.get_pixbuf().get_width() + self.volume_padding)) + 1)
            
            for i in range(0, value):
                draw_pixbuf(cr, self.volume_fg_dpixbuf.get_pixbuf(), 
                            x + i * (self.volume_fg_dpixbuf.get_pixbuf().get_width() + self.volume_padding),
                            y + (h - self.volume_fg_dpixbuf.get_pixbuf().get_height()) / 2)

        # Propagate expose to children.
        propagate_expose(widget, event)
    
        return True
    
    def press_volume_progressbar(self, widget, event):
        '''Press volume progressbar.'''
        # Init.
        rect = widget.allocation
        lower = self.volume_progressbar.get_adjustment().get_lower()
        upper = self.volume_progressbar.get_adjustment().get_upper()
        value = self.volume_progressbar.get_adjustment().get_value()
        
        # Change to play status.
        if value != lower:
            self.set_play_status(True)
        
        # Set value.
        self.volume_progressbar.set_value(lower + (event.x / rect.width) * (upper - lower))
        self.queue_draw()
        
        return False
    
    def monitor_volume_change(self, adjustment):
        '''Monitor volume change.'''
        # Disable play status when drag to lower position.
        if adjustment.get_value() == adjustment.get_lower():
            self.set_play_status(False)
            self.queue_draw()

gobject.type_register(VolumeButton)
