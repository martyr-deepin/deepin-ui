#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Hailong Qiu <qiuhailong@linuxdeepin.com>
# Maintainer: Hailong Qiu <qiuhailong@linuxdeepin.com>
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
import gobject
from collections import OrderedDict
from skin_config import skin_config
from theme import ui_theme
from draw import draw_pixbuf, draw_vlinear, draw_font

class TreeView(gtk.DrawingArea):
    __gsignals__ = {
        "single-click-view" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, int, )),
        "motion-notify-view" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, int)),
    }        
    
    def __init__(self, height = 30, width = 50,
                 font_x = 20, font_size = 10, font_color = "#000000",          
                 normal_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png"),
                 press_pixbuf= ui_theme.get_pixbuf("treeview/arrow_down.png")):        
        
        gtk.DrawingArea.__init__(self)
        # pixbuf.
        self.normal_pixbuf = normal_pixbuf
        self.press_pixbuf = press_pixbuf
        # root node.
        self.root = Tree()
        self.set_can_focus(True)
        # Init DrawingArea event.
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)        
        self.connect("button-press-event", self.press_notify_event)
        self.connect("motion-notify-event", self.move_notify_event)
        self.connect("expose-event", self.draw_expose_event)
        self.connect("key-press-event", self.key_press_tree_view)
        self.connect("leave-notify-event", self.clear_move_notify_event)
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        # 
        self.height = height # child widget height.
        self.width = width # draw widget width.
        self.move_height = 0 #
        self.press_height = 0
        # Position y.
        self.draw_y_padding = 0
        # Draw press move bool.
        self.press_draw_bool = False
        self.move_draw_bool = False
        # Font init.
        self.font_size = font_size
        self.font_color = font_color
        self.font_x = font_x
        # Draw tree view child widget(save postion and Tree).
        self.draw_widget_list = []
        
        # Key map dict.
        self.keymap = {
            "Up"     : self.up_key_press,
            "Down"   : self.down_key_press,
            "Return" : lambda :self.press_notify_function(self.move_height)
            }
        
    def set_draw_pixbuf_bool(self, draw_pixbuf_bool):    
        self.draw_pixbuf_bool = draw_pixbuf_bool
        
    def clear_move_notify_event(self, widget, event): # focus-out-event
        self.move_color = False
        self.queue_draw()
        
    def move_bool(self, operation):    
        temp_move_height = self.move_height
        
        if "-" == operation:
            temp_move_height -= self.height
        elif "+" == operation:    
            temp_move_height += self.height
            
        index = int(temp_move_height) / self.height
        index_len = len(self.draw_widget_list)
        
        if index_len > index:
            self.emit("motion-notify-view", self.draw_widget_list[index][0].name, index)
            return True
        else:
            return False
        
    def up_key_press(self):        
        if self.move_bool("-"):
            self.move_height -= self.height            
            
            
    def down_key_press(self):
        if self.move_bool("+"):
            self.move_height += self.height
            
            
    def key_press_tree_view(self, widget, event):
        keyval = gtk.gdk.keyval_name(event.keyval)
        
        # Up Left.
        if self.keymap.has_key(keyval):
            self.keymap[keyval]()
                
        # Set : 0 < self.move_height > self.allocation.height ->
        if (self.move_height < 0) or (self.move_height > self.allocation.height):
            if self.move_height < 0:
                self.move_height = 0
            elif self.move_height > self.allocation.height:
                self.move_height = int(self.allocation.height) / self.height * self.height
        # expose-evet queue_draw.
        self.queue_draw()
        
    def draw_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Draw background.
        cr.translate(x, y)
        try:
            (shadow_x, shadow_y) = self.get_toplevel().get_shadow_size()            
            skin_config.render_background(cr, self, shadow_x, shadow_y)
        except Exception, e:
            print e
            
        cr.rectangle(x, y, w, h)
        # cr.fill()
        cr.clip()
        
        # Draw mask.
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linearBackground").get_color_info())
        
        if self.press_draw_bool:
            cr.set_source_rgba(1, 0, 0, 0.3)
            self.draw_y_padding = int(self.press_height) / self.height * self.height
            cr.rectangle(x, y + self.draw_y_padding, w, self.height)
            cr.fill()
                                    
        if self.move_draw_bool:
            cr.set_source_rgba(0, 0, 1, 0.3)
            self.draw_y_padding = int(self.move_height) / self.height * self.height
            cr.rectangle(x, y + self.draw_y_padding, w, self.height)
            cr.fill()
        
        if self.draw_widget_list:    
            # (cr, text, font_size, font_color, x, y, width, height, 
            temp_height = 0
            for draw_widget in self.draw_widget_list:
                draw_pixbuf_x_padding = draw_widget[0].pixbuf_x
                
                if draw_widget[0].draw_pixbuf_bool:
                    if not draw_widget[0].child_show_bool:
                        pixbuf = draw_widget[0].tree_normal_pixbuf.get_pixbuf()#self.press_pixbuf.get_pixbuf()
                    else:    
                        pixbuf = draw_widget[0].tree_press_pixbuf.get_pixbuf()#self.normal_pixbuf.get_pixbuf()                                        
                    draw_pixbuf_x = 30                     
                    if 0 == draw_widget[0].pixbuf_x_align: # Left
                        draw_pixbuf_x = 0
                        
                    draw_pixbuf(cr, pixbuf,
                                draw_pixbuf_x + draw_widget[1] + draw_pixbuf_x_padding,
                                temp_height + self.height/2 - pixbuf.get_height()/2)
                
                if draw_widget[0].name:
                    draw_font_width = 80
                    draw_font(cr, 
                              draw_widget[0].name, 
                              self.font_size, 
                              self.font_color, 
                              self.font_x + draw_widget[1], 
                              temp_height + self.height/2, draw_font_width, 0, 0)
                                        
                temp_height += self.height
        return True
    
    def set_font_size(self, size):
        if size > self.height / 2:
            size = self.height / 2        
        self.font_size = size
        
    def press_notify_event(self, widget, event):        
        self.press_notify_function(event.y) 
        
    def press_notify_function(self, y):    
        temp_press_height = self.press_height
        self.press_height = y
        index_len = len(self.draw_widget_list)
        index = int(self.press_height / self.height)
        
        if index_len > index:
            self.press_draw_bool = True
            if self.draw_widget_list[index][0].child_dict:
                self.draw_widget_list[index][0].child_show_bool = not self.draw_widget_list[index][0].child_show_bool 
            self.sort()
            self.queue_draw()
            self.emit("single-click-view", self.draw_widget_list[index][0].name, index)
        else:
            self.press_height = temp_press_height
        
    def move_notify_event(self, widget, event):
        temp_move_height = self.move_height # Save move_height.
        self.move_height = event.y
        index_len = len(self.draw_widget_list)
        index_num = int(self.move_height) / self.height
        
        if index_len > index_num: 
            self.move_draw_bool = True                            
            self.queue_draw()
            self.emit("motion-notify-view", self.draw_widget_list[index_num][0].name, index_num)
        else:
            self.move_height = temp_move_height
            
    def add_node(self,root_name, node_name, 
                 draw_pixbuf_bool=True, pixbuf_x=50,pixbuf_x_align=1, 
                 normal_pixbuf=None, press_pixbuf=None):
                 # font_x = 20, font_size = 10, font_color = "#000000",):
        # self.font_x = font_x
        # self.font_size = font_size
        # self.font_color = font_color        
        if not normal_pixbuf:
            normal_pixbuf = self.normal_pixbuf
        if not press_pixbuf:    
            press_pixbuf = self.press_pixbuf            

        self.root.add_node(root_name, node_name, Tree(), 
                           draw_pixbuf_bool, pixbuf_x, pixbuf_x_align,
                           normal_pixbuf, press_pixbuf)
        self.sort()
        
    def sort(self):                
        self.draw_widget_list = []
        for key in self.root.child_dict.keys():
            temp_list = [] 
            temp_list.append(self.root.child_dict[key])
            temp_list.append(0)
            self.draw_widget_list.append(temp_list)            
            
            if self.root.child_dict[key].child_dict:
                self.sort2(self.root.child_dict[key], self.width)
                
        self.queue_draw()
                    
    def sort2(self, node, width):        
        for key in node.child_dict.keys():
            if node.child_show_bool:
                temp_list = [] 
                temp_list.append(node.child_dict[key])
                temp_list.append(width)
                self.draw_widget_list.append(temp_list)            
            
                if node.child_dict[key].child_dict:
                    self.sort2(node.child_dict[key], width+self.width)
                
        
class Tree(object):
    def __init__(self):
        self.parent_node = None
        self.child_dict = OrderedDict()
        self.child_show_bool = False        
        self.name = ""
        self.pixbuf = None
        self.draw_pixbuf_ = 1 # 0 -> Left : 1 -> Right.
        self.draw_pixbuf_bool = True # True -> draw icon.
        self.tree_normal_pixbuf = None
        self.tree_press_pixbuf = None
        self.pixbuf_x = 50
        self.pixbuf_x_align = 1 # 0-> left: 1 -> Right
        
    def add_node(self, root_name, node_name, node, 
                 draw_pixbuf_bool=True, pixbuf_x = 50, pixbuf_x_align = 1,
                 normal_pixbuf=None, press_pixbuf=None):
        # Root node add child widget.
        if not root_name:
            if node_name and node:
                # Set node.
                node.name = node_name
                node.draw_pixbuf_bool = draw_pixbuf_bool
                node.pixbuf_x_align = pixbuf_x_align
                node.pixbuf_x = pixbuf_x
                node.tree_normal_pixbuf = normal_pixbuf
                node.tree_press_pixbuf = press_pixbuf                
                
                # node.parent_node = None
                self.child_dict[node_name] = node
        else:    
            for key in self.child_dict.keys():                
                if key == root_name:                    
                    # Set node.
                    node.name = node_name
                    node.draw_pixbuf_bool = draw_pixbuf_bool
                    node.pixbuf_x = pixbuf_x
                    node.pixbuf_x_align = pixbuf_x_align                    
                    node.tree_normal_pixbuf = normal_pixbuf
                    node.tree_press_pixbuf = press_pixbuf
                    # print node.tree_press_pixbuf
                    # self.parent_node = None
                    self.child_dict[key].child_dict[node_name] = node
                    break                
                
                self.scan_node(self.child_dict[key], root_name, node_name, node, 
                               draw_pixbuf_bool, pixbuf_x, pixbuf_x_align,
                               normal_pixbuf, press_pixbuf)
                    
    def scan_node(self, node, scan_root_name, node_name, save_node, 
                  draw_pixbuf_bool, pixbuf_x = 50, pixbuf_x_align=1,
                  normal_pixbuf=None, press_pixbuf=None):
        if node.child_dict:
            for key in node.child_dict.keys():
                if key == scan_root_name:                    
                    save_node.name = node_name
                    save_node.draw_pixbuf_bool = draw_pixbuf_bool
                    save_node.pixbuf_x = pixbuf_x                        
                    save_node.tree_normal_pixbuf = normal_pixbuf
                    save_node.tree_press_pixbuf = press_pixbuf
                    
                    save_node.pixbuf_x_align = pixbuf_x_align
                    
                    node.child_dict[key].child_dict[node_name] = save_node                
                else:    
                    self.scan_node(node.child_dict[key], scan_root_name, node_name, save_node, 
                                   draw_pixbuf_bool, pixbuf_x, pixbuf_x_align)
                    
    def sort(self):                
        for key in self.child_dict.keys():
            if self.child_dict[key].child_dict:
                self.sort2(self.child_dict[key])
        
    def sort2(self, node):        
        for key in node.child_dict.keys():
            if node.child_dict[key].child_dict:
                self.sort2(node.child_dict[key])
                
                
