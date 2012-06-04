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
from utils import get_content_size


# 滚动窗口对 treeview 无效. 

# class TreeView(gtk.DrawingArea):
class TreeView(gtk.Button):
    __gsignals__ = {
        "single-click-view" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, int, )),
        "motion-notify-view" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, int)),
    }        
    def __init__(self, height = 30, width = 50, 
                 font_size = 10, font_color = "#000000", 
                 normal_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png"),
                 press_pixbuf= ui_theme.get_pixbuf("treeview/arrow_down.png")):
        
        # gtk.DrawingArea.__init__(self)
        gtk.Button.__init__(self)
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
        # Draw tree view child widget(save postion and Tree).
        self.draw_widget_list = []
        
        # Key map dict.
        self.keymap = {
            "Up"     : self.up_key_press,
            "Down"   : self.down_key_press,
            "Return" : lambda :self.press_notify_function(self.move_height)
            }
        
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
            pass
            
        cr.rectangle(x-4, y-4, w, h)
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
                
                if draw_widget[0].name:
                    draw_font_width = 80
                    draw_font(cr, 
                              draw_widget[0].name, 
                              self.font_size, 
                              self.font_color, 
                              draw_widget[1], 
                              temp_height + self.height/2, draw_font_width, 0)
                                        
                if draw_widget[0].child_show_bool:
                    pixbuf = self.press_pixbuf.get_pixbuf()
                else:    
                    pixbuf = self.normal_pixbuf.get_pixbuf()                                        
                draw_pixbuf_x = 30    
                draw_pixbuf(cr, pixbuf,
                            draw_pixbuf_x + draw_widget[1] + get_content_size(draw_widget[0].name, self.font_size)[0],
                            temp_height + self.height/2 - pixbuf.get_height()/2)
                    
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
            
    def add_node(self,root_name, node_name):
        self.root.add_node(root_name, node_name, Tree())
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
        
        
    def add_node(self, root_name, node_name, node):
        # Root node add child widget.
        if not root_name:
            if node_name and node:
                # Set node.
                node.name = node_name
                self.parent_node = None
                self.child_dict[node_name] = node
        else:    
            for key in self.child_dict.keys():                
                if key == root_name:                    
                    # Set node.
                    node.name = node_name
                    self.parent_node = None
                    self.child_dict[key].child_dict[node_name] = node
                    break                
                
                self.scan_node(self.child_dict[key], root_name, node_name, node)
                    
    def scan_node(self, node, scan_root_name, node_name, save_node):
        if node.child_dict:
            for key in node.child_dict.keys():
                if key == scan_root_name:                    
                    save_node.name = node_name
                    node.child_dict[key].child_dict[node_name] = save_node
                
                else:    
                    self.scan_node(node.child_dict[key], scan_root_name, node_name, save_node)
                    
                    
    def sort(self):                
        for key in self.child_dict.keys():
            if self.child_dict[key].child_dict:
                self.sort2(self.child_dict[key])
        
    def sort2(self, node):        
        for key in node.child_dict.keys():
            if node.child_dict[key].child_dict:
                self.sort2(node.child_dict[key])
                
                
#======== Test ===============
from dtk.ui.scrolled_window import ScrolledWindow

def test_show_tree_view(TreeView, name, index):
    print name
    print index
        
    if dict_widget.has_key(name):
        for widget in vbox.get_children():
            vbox.remove(widget)        
    
        vbox.pack_start(dict_widget[name])    
        vbox.show_all()
def tree_view_clicked(widget):    
    print "************"
if __name__ == "__main__":    
    hbox = gtk.HBox()
    vbox = gtk.VBox()
    dict_widget = {"小学":gtk.Button("小学显示来看看"),
                   "初中":gtk.Button("初中你上过来啦吗"),
                   "大学":gtk.Button("就是培养垃圾的地方呢"),
                   "深度":gtk.Button("深度人你布是布指导的")}
    
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)        
    win.set_size_request(200, 500)
    win.connect("destroy", gtk.main_quit)
    tree_view = TreeView()
    tree_view.connect("single-click-view", test_show_tree_view)
    tree_view.connect("clicked", tree_view_clicked)
    # tree_view.connect("motion-notify-view", test_show_tree_view)
    
    hbox.pack_start(tree_view)
    hbox.pack_start(vbox, False, False)
    
    win.add(hbox)
    win.show_all()    
    
    tree_view.add_node(None, "小学")
    tree_view.add_node(None, "初中")
    tree_view.add_node(None, "大学")
    tree_view.add_node(None, "深度")
    
    tree_view.add_node("小学", "1年级")
    tree_view.add_node("1年级", "1:1:2")    
    tree_view.add_node("小学", "2年级")
    tree_view.add_node("小学", "3年级")
    
    tree_view.add_node("大学", "软件学院")
    tree_view.add_node("软件学院", "ZB48901")
    tree_view.add_node("软件学院", "ZB48902")
    tree_view.add_node("软件学院", "ZB48903")
    tree_view.add_node("大学", "工商学院")
    tree_view.add_node("大学", "理工学院")
    tree_view.add_node("大学", "机电学院")
    
    tree_view.add_node("深度", "开发部")
    tree_view.add_node("开发部", "王勇")
    tree_view.add_node("开发部", "猴哥")
    tree_view.add_node("开发部", "邱海龙")        
    gtk.main()

    
