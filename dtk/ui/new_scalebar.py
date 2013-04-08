#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Hailong Qiu
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
#             Long Changjin <admin@longchangjin.cn>
#             Hailong Qiu <356752238@qq.com>
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

from theme import ui_theme
from constant import DEFAULT_FONT_SIZE
from draw import draw_pixbuf, draw_text, draw_line, draw_round_rectangle
from utils import (color_hex_to_cairo, get_content_size, cairo_state, 
                   cairo_disable_antialias)
import gtk
import gobject

class HScalebar(gtk.Button):    
    __gsignals__ = {
        "value-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }        
    def __init__(self,
                 point_dpixbuf=ui_theme.get_pixbuf("hscalebar/point.png"),
                 show_value=False,
                 show_value_type=gtk.POS_TOP,
                 show_point_num=0,
                 format_value="",
                 value_min = 0,
                 value_max = 100,  
                 line_height=6,
                 gray_progress=False
                 ):
        '''
        @point_dpixbuf: a DynamicPixbuf object.
        @show_value: If True draw the current value next to the slider
        @show_value_type: the position where the current value is displayed. gtk.POS_TOP or gtk.POS_BOTTOM
        @show_point_num: the accuracy of the value. If 0 value is int type.
        @format_value: a string that displayed after the value
        @value_min: the min value
        @value_max: the max value
        @line_height: the line height
        @gray_progress: If True the HScalebar looks gray
        '''
        gtk.Button.__init__(self)
        #        
        self.position_list = []
        self.mark_check = False
        self.enable_check = True
        self.new_mark_x = 0
        self.next_mark_x = 0
        self.value = 0
        self.show_value_type = show_value_type
        self.show_point_num = show_point_num
        self.value_max = value_max - value_min
        self.value_min = value_min
        self.drag = False
        self.gray_progress = gray_progress
        # init color.
        self.fg_side_color = "#0071B3"
        self.bg_side_color = "#B3B3B3"
        self.fg_inner_color = "#30ABEE"
        self.bg_inner1_color = "#CCCCCC"
        self.bg_inner2_color = "#E6E6E6"
        self.fg_corner_color = "#2E84B7"
        self.bg_corner_color = "#C1C5C6"
        #
        self.point_pixbuf = point_dpixbuf
        self.line_height = line_height
        self.line_width = 1.0
        self.progress_border = 1
        self.mark_height = 6
        self.mark_width = 1
        self.bottom_space = 2 # vertical space between bottom mark line and drag point
        self.format_value = format_value
        self.trg_by_grab = False
        self.show_value = show_value
        
        self.point_width = self.point_pixbuf.get_pixbuf().get_width()
        self.point_height = self.point_pixbuf.get_pixbuf().get_height()
        self.text_height_factor = 2
        self.set_size_request(-1, self.point_height + get_content_size("0")[1] * self.text_height_factor + self.bottom_space)
        
        # init events.
        self.init_events()
                
    def init_events(self):     
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)        
        self.connect("expose-event", self.__progressbar_expose_event)
        self.connect("button-press-event", self.__progressbar_press_event)
        self.connect("button-release-event", self.__progressbar_release_event)
        self.connect("motion-notify-event", self.__progressbar_motion_notify_event)        
        self.connect("scroll-event", self.__progressbar_scroll_event)
                
    def __progressbar_expose_event(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.clip()
        # draw bg and fg.
        self.draw_bg_and_fg(cr, rect)
        # draw mark.
        for position in self.position_list:
            self.draw_value(cr, rect,  "%s" % (str(position[2])), position[0] - self.value_min, position[1], mark_check=True)
        # draw value.
        if self.show_value:
            if self.show_point_num:
                draw_value_temp = round(self.value + self.value_min, self.show_point_num)
            else:    
                draw_value_temp = int(round(self.value + self.value_min, self.show_point_num))
            
            self.draw_value(cr, rect, 
                            "%s%s" % (draw_value_temp, self.format_value), 
                            self.value, 
                            self.show_value_type)
        # draw point.
        self.draw_point(cr, rect)
            
        return True
                    
    def draw_bg_and_fg(self, cr, rect):    
        with cairo_disable_antialias(cr):
            x, y, w, h = rect         
            progress_x = rect.x + self.point_width/2
            progress_y = rect.y + (rect.height-self.bottom_space)/2 - self.line_height/2
            progress_width = rect.width - self.point_width
            value_width = int(float(self.value) / self.value_max * (rect.width - self.point_width/2))
            if int(float(self.value)) == self.value_max:
                value_width = value_width - 1 # there is less 1px for 100% mark line

            '''
            background
            '''
            # background inner
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_inner2_color))
            cr.rectangle(progress_x+value_width, 
                    progress_y+self.progress_border, 
                    progress_width-value_width-self.progress_border, 
                    self.line_height-self.progress_border*2)
            cr.fill()

            # background border
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_side_color))
            # top border
            cr.rectangle(
                    progress_x+value_width, 
                    progress_y,
                    progress_width-value_width-self.progress_border, 
                    self.progress_border)
            cr.fill()
            # bottom border
            cr.rectangle(
                    progress_x+value_width, 
                    progress_y+self.line_height-self.progress_border, 
                    progress_width-value_width-self.progress_border, 
                    self.progress_border)
            cr.fill()
            # right border
            cr.rectangle(
                    progress_x+progress_width-self.progress_border, 
                    progress_y+self.progress_border, 
                    self.progress_border,
                    self.line_height-self.progress_border*2)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo(self.bg_corner_color))
            # top right corner
            cr.rectangle(
                    progress_x+progress_width-self.progress_border, 
                    progress_y,
                    self.progress_border, 
                    self.progress_border)
            cr.fill()
            # bottom right corner
            cr.rectangle(
                    progress_x+progress_width-self.progress_border, 
                    progress_y+self.line_height-self.progress_border,
                    self.progress_border, 
                    self.progress_border)
            cr.fill()

            '''
            foreground color setting
            '''
            
            if self.enable_check:
                fg_inner_color = self.fg_inner_color
                fg_side_color  = self.fg_side_color
                fg_corner_color = self.fg_corner_color
            else:
                fg_inner_color = self.bg_inner1_color 
                fg_side_color  = self.bg_side_color 
                fg_corner_color = self.bg_corner_color 
            
            if self.gray_progress:
                fg_inner_color = self.bg_inner2_color 
                fg_side_color  = self.bg_side_color 
                fg_corner_color = self.bg_corner_color 
            '''
            foreground
            '''
            # foreground inner
            cr.set_source_rgb(*color_hex_to_cairo(fg_inner_color))
            cr.rectangle(progress_x+self.progress_border, 
                    progress_y+self.progress_border, 
                    value_width-self.progress_border, 
                    self.line_height-self.progress_border*2)
            cr.fill()

            # foreground border
            cr.set_source_rgb(*color_hex_to_cairo(fg_side_color))
            # top border
            cr.rectangle(
                    progress_x+self.progress_border, 
                    progress_y, 
                    value_width-self.progress_border, 
                    self.progress_border)
            cr.fill()
            # bottom border
            cr.rectangle(
                    progress_x+self.progress_border, 
                    progress_y+self.line_height-self.progress_border, 
                    value_width-self.progress_border, 
                    self.progress_border)
            cr.fill()
            # left border
            cr.rectangle(
                    progress_x, 
                    progress_y+self.progress_border, 
                    self.progress_border, 
                    self.line_height-self.progress_border*2)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo(fg_corner_color))
            # top left corner
            cr.rectangle(
                    progress_x,
                    progress_y,
                    self.progress_border, 
                    self.progress_border)
            cr.fill()
            # bottom left corner
            cr.rectangle(
                    progress_x,
                    progress_y+self.line_height-self.progress_border,
                    self.progress_border, 
                    self.progress_border)
            cr.fill()

    def draw_point(self, cr, rect):
        pixbuf_w_average = self.point_pixbuf.get_pixbuf().get_width() / 2
        x = rect.x + self.point_width / 2 + int(float(self.value) / self.value_max * (rect.width - self.point_width)) - pixbuf_w_average
        if int(float(self.value)) == self.value_max:
            x = x - 1 # there is less 1px for 100% mark line
        draw_pixbuf(cr,
                    self.point_pixbuf.get_pixbuf(), 
                    x, 
                    rect.y + (rect.height-self.bottom_space)/2 - self.point_pixbuf.get_pixbuf().get_height()/2)
        
    def draw_value(self, cr, rect, text, value, type_=None, mark_check=False):
        text_width, text_height = get_content_size(text)
        text_y = rect.y 
        if gtk.POS_TOP == type_:
            text_y = text_y
        if gtk.POS_BOTTOM == type_:
            text_y = rect.y + (rect.height-self.bottom_space)/2 + self.point_height + self.bottom_space - text_height/2
            
        x = rect.x + int(float(value) / self.value_max * (rect.width - self.point_width))
        max_value = max(x - (text_width/2 - self.point_width/2), rect.x)
        min_value = min(max_value, rect.x + rect.width - text_width)
        
        if self.enable_check:
            draw_text(cr, text, min_value, text_y, rect.width, 0)                
        else:
            draw_text(cr, text, min_value, text_y, rect.width, 0, DEFAULT_FONT_SIZE, self.bg_side_color)
        
        if int(float(value)) == self.value_max:
            x = x - 1 # there is less 1px for 100% mark line
        mark_y = text_y-self.bottom_space/2-(self.point_height-self.line_height)/2
        if mark_check:
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_side_color))
            cr.rectangle(x + self.point_width/2, mark_y, self.mark_width, self.mark_height) 
            cr.fill()

    def __progressbar_scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP or event.direction == gtk.gdk.SCROLL_LEFT:
            step = -5
        elif event.direction == gtk.gdk.SCROLL_DOWN or event.direction == gtk.gdk.SCROLL_RIGHT:
            step = 5
        else:
            step = 0
        # one step increase/decrease 5%
        value = self.value + step * (self.value_max - self.value_min) / 100.0
        if value > self.value_max:
            value = self.value_max
        if value < 0:
            value = 0
        self.set_value(value + self.value_min)
        self.emit("value-changed", self.value + self.value_min)

    def __progressbar_press_event(self, widget, event):
        temp_value = float(widget.allocation.width - self.point_width)
        temp_value = ((float((event.x - self.point_width/2)) / temp_value) * self.value_max) # get value.
        value = max(min(self.value_max, temp_value), 0)
        if value != self.value:
            self.set_enable(True)
        self.value = value       
        self.drag = True        
        self.set_value(self.value + self.value_min)
        self.emit("value-changed", self.value + self.value_min)
        # self.grab_add()
        
    def __progressbar_release_event(self, widget, event):    
        self.drag = False
        # self.grab_remove()
        
    def __progressbar_motion_notify_event(self, widget, event):    
        if self.drag:
            self.set_enable(True)
            width = float(widget.allocation.width - self.point_width)
            temp_value = (float((event.x - self.point_width/2)) /  width) * self.value_max
            self.value = max(min(self.value_max, temp_value), 0) # get value.
            self.set_value(self.value + self.value_min)
            self.emit("value-changed", self.value + self.value_min)
            
    def add_mark(self, value, position_type, markup):
        if self.value_min <= value <= self.value_max+self.value_min:
            self.position_list.append((value, position_type, markup))
        else:    
            print "error:input value_min <= value <= value_max!!"
        
    def set_value(self, value):    
        self.value = max(min(self.value_max, value - self.value_min), 0) 
        self.queue_draw()     
        
    def get_value(self):    
        return self.value + self.value_min
        
    def set_enable(self, enable_bool):
        self.enable_check = enable_bool
        self.queue_draw()

    def get_enable(self, enable_bool):
        return self.enable_check 

gobject.type_register(HScalebar)
