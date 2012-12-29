#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
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
from draw import draw_pixbuf, draw_text, draw_line
from utils import color_hex_to_cairo, get_content_size, cairo_state
import gtk
import gobject

#/* HScalebar
# * @ point_dpixbuf : 设置图标 -> point_dpixbuf=app_theme.get_pixbuf("文件夹名字/图标名字.png")
# * @ show_value : 是否显示 value.
# * @ show_value_type : 显示 value 的位置[ gtk.POS_TOP 上面 | gtk.POS_BOTTOM 下面].
# * @ show_point_num : 取小数点位数, 0 为整形.
# * @ format_value : 跟在 value 后面的参数. 如果 format_value = "%%" value%%
# * @ value_min: 最小值
# * @ value_max: 最大值
# * @ line_height: 进度条的前景和背景的线高.
# * @ add_mark: 添加标记位置 value(位置), position_type(显示类型,gtk.POS_TOP, gtk.POS_BOTTOM), mar(显示文本).
#*/

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
                 line_height=6
                 ):
        gtk.Button.__init__(self)
        #        
        self.position_list = []
        self.mark_check = False
        self.new_mark_x = 0
        self.next_mark_x = 0
        self.value = 0
        self.show_value_type = show_value_type
        self.show_point_num = show_point_num
        self.value_max = value_max - value_min
        self.value_min = value_min
        self.drag = False
        # init color.
        self.fg_side_color = "#2670B2"
        self.bg_side_color = "#BABABA"
        self.fg_inner_color = "#59AFEE"
        self.bg_inner1_color = "#DCDCDC"
        self.bg_inner2_color = "#E6E6E6"
        self.fg_corner_color = "#3F85B6"
        self.bg_corner_color = "#C2C4C5"
        #
        self.point_pixbuf = point_dpixbuf
        self.line_height = line_height
        self.format_value = format_value
        self.trg_by_grab = False
        self.show_value = show_value
        #
        self.set_size_request(-1, 
                               line_height + get_content_size("0")[1]*2 + get_content_size("0")[1]/2)
        #
        self.point_width = self.point_pixbuf.get_pixbuf().get_width()
        self.point_height = self.point_pixbuf.get_pixbuf().get_height()
        # init events.
        self.init_events()
                
    def init_events(self):     
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)        
        self.connect("expose-event", self.__progressbar_expose_event)
        self.connect("button-press-event", self.__progressbar_press_event)
        self.connect("button-release-event", self.__progressbar_release_event)
        self.connect("motion-notify-event", self.__progressbar_motion_notify_event)        
                
    def __progressbar_expose_event(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        #
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.clip()
        # draw bg and fg.
        self.draw_bg_and_fg(cr, rect)
        # draw point.
        self.draw_point(cr, rect)
        # draw mark.
        for position in self.position_list:
            self.draw_value(cr, rect,  "%s" % (str(position[2])), position[0] - self.value_min, position[1])
        # draw value.
        if self.show_value:
            if self.show_point_num:
                draw_value_temp = round(self.value + self.value_min, self.show_point_num)
            else:    
                draw_value_temp = int(round(self.value + self.value_min, self.show_point_num))
            #
            self.draw_value(cr, rect, 
                            "%s%s" % (draw_value_temp, self.format_value), 
                            self.value, 
                            self.show_value_type)
            
        return True
                    
    def draw_bg_and_fg(self, cr, rect):    
        with cairo_state(cr):
            '''
            background y
            '''
            x, y, w, h = rect         
            bg_x = rect.x + self.point_width/2
            bg_y = rect.y + rect.height/2 - self.line_height/2
            bg_w = rect.width - self.point_width
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_inner2_color))
            cr.rectangle(bg_x, 
                         bg_y, 
                         bg_w, 
                         self.line_height)
            cr.fill()
            
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_side_color))
            cr.rectangle(bg_x, bg_y, bg_w, self.line_height)
            cr.stroke()

            cr.set_source_rgb(*color_hex_to_cairo(self.bg_corner_color))
            draw_line(cr, 
                      x + self.point_width/2, 
                      bg_y, 
                      x + self.point_width/2 + 1, 
                      bg_y)
            draw_line(cr, 
                      x + w - self.point_width/2, 
                      bg_y, 
                      x + w - self.point_width/2- 1, 
                      bg_y)
            draw_line(cr, x + self.point_width/2, bg_y + self.line_height, x + self.point_width/2 + 1, bg_y + self.line_height)
            draw_line(cr, x + w - self.point_width/2, bg_y + self.line_height, x + w - self.point_width/2 - 1, bg_y + self.line_height)        
            '''
            background
            '''
            cr.set_source_rgb(*color_hex_to_cairo(self.bg_inner1_color))
            cr.rectangle(x + self.point_width/2, 
                         bg_y,
                         w - self.point_width, 
                         self.line_height)
            cr.fill()
            '''
            foreground
            '''
            bg_w = int(float(self.value) / self.value_max * (rect.width - self.point_width/2))
            cr.set_source_rgb(*color_hex_to_cairo(self.fg_inner_color))
            cr.rectangle(x + self.point_width/2, 
                         bg_y, 
                         bg_w, 
                         self.line_height)
            cr.fill()

            cr.set_source_rgb(*color_hex_to_cairo(self.fg_side_color))
            cr.rectangle(x + self.point_width/2, 
                         bg_y, 
                         bg_w, 
                         self.line_height)
            cr.stroke()
            
            cr.set_source_rgb(*color_hex_to_cairo(self.fg_corner_color))         
            draw_line(cr, 
                      x + self.point_width/2,
                      bg_y, 
                      x + self.point_width/2 + 1, 
                      bg_y)                                  
            draw_line(cr, 
                      x + self.line_height,
                      bg_y, 
                      x + self.line_height + 1, 
                      bg_y)
                
    
    def draw_point(self, cr, rect):
        pixbuf_w_average = self.point_pixbuf.get_pixbuf().get_width()/2
        x = (rect.x + self.point_width/2) + int(float(self.value) / self.value_max * (rect.width - self.point_width)) - pixbuf_w_average
        draw_pixbuf(cr,
                    self.point_pixbuf.get_pixbuf(), 
                    x, 
                    rect.y + rect.height/2 - self.point_pixbuf.get_pixbuf().get_height()/2)
        
    def draw_value(self, cr, rect, text, value, type_=None):
        text_x_padding = -15
        y_padding = rect.y + rect.height/2 - self.point_pixbuf.get_pixbuf().get_height()/2 + text_x_padding
        if gtk.POS_TOP == type_:
            y_padding = y_padding
        if gtk.POS_BOTTOM == type_:
            y_padding = rect.y + rect.height/2 + self.line_height
            
        pixbuf_w_average = self.point_pixbuf.get_pixbuf().get_width()/2
        x = (rect.x + self.point_width/2) + int(float(value) / self.value_max * (rect.width - self.point_width)) - pixbuf_w_average
        max_value = max(x - (get_content_size(text)[0]/2 - self.point_width/2), rect.x)
        min_value = min(max_value, rect.x + rect.width - get_content_size(text)[0])
        draw_text(cr, 
                  text, 
                  min_value, 
                  y_padding, 
                  rect.width, 
                  0
                  )                
        
    def __progressbar_press_event(self, widget, event):
        temp_value = float(widget.allocation.width - self.point_width)
        temp_value = ((float((event.x - self.point_width/2)) / temp_value) * self.value_max) # get value.
        self.value = max(min(self.value_max, temp_value), 0)
        self.drag = True        
        self.set_value(self.value)
        self.emit("value-changed", self.value + self.value_min)
        self.grab_add()
        
    def __progressbar_release_event(self, widget, event):    
        self.drag = False
        self.grab_remove()
        
    def __progressbar_motion_notify_event(self, widget, event):    
        if self.drag:
            width = float(widget.allocation.width - self.point_width)
            temp_value = (float((event.x - self.point_width/2)) /  width) * self.value_max
            self.value = max(min(self.value_max, temp_value), 0) # get value.
            self.set_value(self.value)
            self.emit("value-changed", self.value + self.value_min)
            # mark set.
            # mark_x_padding = 10
            # for mark in self.position_list:
            #     mark_value = ((mark[0]) + (self.value_min))
            #     if (mark_value) == int(self.value) and (round(int(self.value) - self.value, 1) in [0.0, -0.1, -0.2, -0.2]):
            #         if not self.mark_check:
            #             self.mark_check = True
            #             self.new_mark_x = event.x                                                
            #     if self.mark_check:
            #         self.next_mark_x = event.x
            #         if self.next_mark_x > self.new_mark_x: # right.
            #             if self.new_mark_x + mark_x_padding >= self.next_mark_x >= self.new_mark_x:
            #                 self.value = mark_value
            #             else:    
            #                 self.mark_check = False                            
            #         else:
            #             if self.new_mark_x - mark_x_padding <= self.next_mark_x <= self.new_mark_x:
            #                 self.value = mark_value
            #             else:
            #                 self.mark_check = False
                            
            
    def add_mark(self, value, position_type, markup):
        if self.value_min <= value <= self.value_max:
            self.position_list.append((value, position_type, markup))
        else:    
            print "error:input value_min <= value <= value_max!!"
        
    def set_value(self, value):    
        self.value = max(min(self.value_max, value), 0) 
        self.queue_draw()     
        
    def get_value(self):    
        self.value
        
gobject.type_register(HScalebar)
