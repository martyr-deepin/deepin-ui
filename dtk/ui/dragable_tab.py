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

import gtk
import cairo
from theme import ui_theme
import pango
import gobject
from skin_config import skin_config
from utils import (get_content_size, cairo_state, cairo_disable_antialias,
                   alpha_color_hex_to_cairo, get_window_shadow_size)
from draw import draw_text
import math

class TabBox(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)
        
        self.tabbox = Tabbar()
        self.tab_content_box = gtk.VBox()
        
        self.pack_start(self.tabbox, False, False)
        self.pack_start(self.tab_content_box, True, True)
        
        self.tab_content_box.connect("expose-event", self.test)
        
    def test(self, widget, event):
        '''
        docs
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        cr.set_source_rgba(1, 1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()
        
    def add_tabs(self, tabs):
        '''
        docs
        '''
        pass
    
    def remove_tabs(self, tabs):
        '''
        docs
        '''
        pass

gobject.type_register(TabBox)               

class Tabbar(gtk.DrawingArea):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.height = 29
        self.tab_name_padding_x = 10
        self.tab_angle = 63
        self.tab_radious = 4
        self.tab_radious_offset_x = self.tab_radious * math.cos(math.radians(self.tab_angle))
        self.tab_radious_offset_y = self.tab_radious * math.sin(math.radians(self.tab_angle))
        self.triangle_width = int(self.height / math.tan(math.radians(self.tab_angle)))
        self.set_size_request(-1, self.height)
        # self.names = ["标签1", "标签2", "标签2", "标签3"]
        self.names = map(lambda i: "标签%s" % (i), range(1, 10))
        self.name_widths = map(self.get_tab_width, self.names)
        self.active_index = 4
        
        self.connect("expose-event", self.expose_dragable_tabbar)
        
    def add_items(self, items):
        '''
        docs
        '''
        pass
    
    def expose_dragable_tabbar(self, widget, event):
        '''
        docs
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, w, h = rect.x, rect.width, rect.height
        y = 0
        
        # Draw background.
        (offset_x, offset_y) = widget.translate_coordinates(self.get_toplevel(), 0, 0)
        with cairo_state(cr):
            cr.translate(-offset_x, -offset_y)
            
            (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
            skin_config.render_background(cr, widget, shadow_x, shadow_y)
        
        # Draw inactive tab.
        draw_x_list = []
        width_offset = 0
        for (index, tab_name) in enumerate(self.names):
            draw_x_list.append(x + width_offset)
            width_offset += (self.name_widths[index] - (self.triangle_width + self.tab_radious * 2))
            
        for (index, tab_name) in enumerate(reversed(self.names)):
            tab_index = len(self.names) - index - 1
            if tab_index != self.active_index:
                self.draw_tab(cr, draw_x_list[tab_index], y, tab_name, tab_index)
                
        # Draw active tab.
        self.draw_tab(cr, draw_x_list[self.active_index], y, self.names[self.active_index], self.active_index)        
        
        # Draw bottom line.
        frame_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_bottom_active_frame").get_color_info())        
        cr.set_source_rgba(*frame_color)
        cr.rectangle(x, 
                     y + h - 1, 
                     draw_x_list[self.active_index],
                     1)
        cr.rectangle(x + draw_x_list[self.active_index] + self.name_widths[self.active_index], 
                     y + h - 1,
                     w - draw_x_list[self.active_index] - self.name_widths[self.active_index],
                     1)
        cr.fill()
        
        return True
    
    def get_tab_width(self, tab_name):
        '''
        docs
        '''
        (text_width, text_height) = get_content_size(tab_name)
        tab_height = self.height
        triangle_width = int(tab_height / math.tan(math.radians(self.tab_angle)))
        middle_width = text_width + self.tab_name_padding_x * 2
        return middle_width + self.tab_radious * 4 + triangle_width * 2
    
    def draw_tab(self, cr, x, y, tab_name, tab_index):
        # Init.
        (text_width, text_height) = get_content_size(tab_name)
        tab_x = x
        tab_y = y
        tab_height = self.height
        triangle_width = int(tab_height / math.tan(math.radians(self.tab_angle)))
        middle_width = text_width + self.tab_name_padding_x * 2
        tab_width = middle_width + self.tab_radious * 4 + triangle_width * 2
        round_radious = self.tab_radious * math.tan(math.radians((180 - self.tab_angle) / 2))
        round_angle = self.tab_angle
        
        if tab_index == self.active_index:
            frame_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_active_frame").get_color_info())        
            background_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_active_background").get_color_info())        
            top_frame_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_top_active_frame").get_color_info())        
        else:
            frame_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_inactive_frame").get_color_info())        
            background_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_inactive_background").get_color_info())        
            top_frame_color = alpha_color_hex_to_cairo(ui_theme.get_alpha_color("dragable_tab_top_inactive_frame").get_color_info())        
            
        # Init round coordinate.
        round_left_bottom_x = tab_x
        round_left_bottom_y = tab_y + tab_height - round_radious

        round_left_up_x = tab_x + self.tab_radious * 2 + triangle_width
        round_left_up_y = tab_y + round_radious

        round_right_bottom_x = tab_x + tab_width
        round_right_bottom_y = tab_y + tab_height - round_radious

        round_right_up_x = tab_x + tab_width - (self.tab_radious * 2 + triangle_width)
        round_right_up_y = tab_y + round_radious
        
        # Clip.
        with cairo_state(cr):
            # Clip.
            if tab_index != self.active_index and tab_index != 0:
                clip_offset_x = tab_width - (self.triangle_width + self.tab_radious * 2)
                cr.move_to(tab_x + tab_width - clip_offset_x, tab_y + tab_height)
                cr.arc(round_right_bottom_x - clip_offset_x,
                       round_right_bottom_y,
                       round_radious,
                       math.radians(90),
                       math.radians(90 + round_angle),
                       )
                
                cr.line_to(tab_x + tab_width - self.tab_radious - self.triangle_width + self.tab_radious_offset_x - clip_offset_x,
                           tab_y)
                
                cr.line_to(tab_x + tab_width, tab_y)
                cr.line_to(tab_x + tab_width, tab_y + tab_height)
                cr.line_to(tab_x + tab_width - clip_offset_x, tab_y + tab_height)
            else:
                cr.rectangle(tab_x, tab_y, tab_width, tab_height)
            cr.clip()
                
            # Draw background.
            # Draw left area.
            with cairo_state(cr):
                cr.move_to(tab_x, tab_y + tab_height)
                cr.arc_negative(round_left_bottom_x,
                                round_left_bottom_y,
                                round_radious,
                                math.radians(90),
                                math.radians(90 - round_angle),
                                )
                
                cr.line_to(tab_x + self.tab_radious + self.tab_radious_offset_x,
                           tab_y + tab_height - self.tab_radious_offset_y)
                
                cr.arc(round_left_up_x,
                       round_left_up_y,
                       round_radious,
                       math.radians(270 - round_angle),
                       math.radians(270))
            
            # Draw top area.
            with cairo_disable_antialias(cr):    
                cr.set_source_rgba(*frame_color)
                cr.set_line_width(1)
                cr.line_to(tab_x + self.tab_radious * 2 + triangle_width + middle_width, tab_y + 1)
            
            # Draw right area.
            with cairo_state(cr):
                cr.arc(round_right_up_x,
                       round_right_up_y,
                       round_radious,
                       math.radians(270),
                       math.radians(270 + round_angle),
                       )
                
                cr.line_to(tab_x + tab_width - (self.tab_radious + self.tab_radious_offset_x),
                           tab_y + tab_height - self.tab_radious_offset_y)
                
                cr.arc_negative(round_right_bottom_x,
                                round_right_bottom_y,
                                round_radious,
                                math.radians(90 + round_angle),
                                math.radians(90))
                
            cr.line_to(tab_x, tab_y + tab_height)
            
            cr.set_source_rgba(*background_color)
            cr.fill()
            
            # Draw frame.
            # Draw left area.
            with cairo_state(cr):
                cr.move_to(tab_x, tab_y + tab_height)
                cr.arc_negative(round_left_bottom_x,
                                round_left_bottom_y,
                                round_radious,
                                math.radians(90),
                                math.radians(90 - round_angle),
                                )
                
                cr.line_to(tab_x + self.tab_radious + self.tab_radious_offset_x,
                           tab_y + tab_height - self.tab_radious_offset_y)
                
                cr.arc(round_left_up_x,
                       round_left_up_y,
                       round_radious,
                       math.radians(270 - round_angle),
                       math.radians(270))
            
                cr.set_source_rgba(*frame_color)
                cr.set_line_width(1)
                cr.stroke()
                
            # Draw top area.
            with cairo_disable_antialias(cr):    
                offset = 1
                cr.set_source_rgba(*top_frame_color)
                cr.set_line_width(1)
                cr.move_to(tab_x + self.tab_radious * 2 + triangle_width - offset, tab_y + 1)
                cr.line_to(tab_x + self.tab_radious * 2 + triangle_width + middle_width + offset * 2, tab_y + 1)
                cr.stroke()
            
            # Draw right area.
            with cairo_state(cr):
                cr.move_to(tab_x + tab_width - (self.tab_radious * 2 + triangle_width), tab_y)
                cr.arc(round_right_up_x,
                       round_right_up_y,
                       round_radious,
                       math.radians(270),
                       math.radians(270 + round_angle),
                       )
                
                cr.line_to(tab_x + tab_width - (self.tab_radious + self.tab_radious_offset_x),
                           tab_y + tab_height - self.tab_radious_offset_y)
                
                cr.arc_negative(round_right_bottom_x,
                                round_right_bottom_y,
                                round_radious,
                                math.radians(90 + round_angle),
                                math.radians(90))
            
                cr.set_source_rgba(*frame_color)
                cr.set_line_width(1)
                cr.stroke()
            
            # Draw text.
            draw_text(cr, tab_name, tab_x, tab_y, tab_width, tab_height, alignment=pango.ALIGN_CENTER)
            
gobject.type_register(Tabbar)               
