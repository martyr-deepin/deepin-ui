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

# from dtk.ui.skin_config import skin_config
# from dtk.ui.theme import Theme, ui_theme
# normal_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png")
# press_pixbuf = ui_theme.get_pixbuf("treeview/arrow_down.png")

import gtk
import gobject
from collections import OrderedDict

from draw import draw_pixbuf, draw_vlinear, draw_font
from utils import (get_content_size, is_single_click, is_double_click, is_right_button,
                   get_match_parent, cairo_state)
from theme import ui_theme
from skin_config import skin_config

# (cr, text, font_size, font_color, x, y, width, height, font_align
class TreeView(gtk.DrawingArea):
    
    __gsignals__ = {
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "right-press-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_INT)),
        }
    
    def __init__(self, width=20, height = 30,
                 font_size = None, font_color="#000000", font_x_padding=5, font_width=120, font_height = 0,font_align=0):        
        gtk.DrawingArea.__init__(self)
        self.root = Tree()
        self.tree_list = []                
        self.tree_id_list = []
        self.tree_id_num = 0
        
        self.set_can_focus(True)
        # Init DrawingArea event.
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)        
        self.connect("button-press-event", self.tree_view_press_event)
        self.connect("motion-notify-event", self.tree_view_motion_event)
        self.connect("expose-event", self.tree_view_expose_event)
        self.connect("key-press-event", self.tree_view_key_press_event)
        self.connect("leave-notify-event", self.tree_view_leave_notify_event)
        
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        
        self.width = width
        self.height = height
        # Draw move background. 
        self.move_height = 0        
        self.move_draw_bool = True                            
        # Draw press background.
        self.press_height = 0
        self.press_draw_bool = False
        # Draw font.
        self.font_color = font_color
        self.font_x_padding = font_x_padding
        self.font_width = font_width
        self.font_height = font_height
        self.font_align = font_align
        self.font_size = font_size
        
        if not self.font_size:
            self.font_size = self.height/2 - 4
            
        if self.font_size > self.height - 15:    
            self.font_size = self.height - 15
            # print self.font_size
            
            
    # DrawingArea event function.           
    def tree_view_press_event(self, widget, event):
        self.press_notify_function(event) 

    def press_notify_function(self, event):    
        temp_press_height = self.press_height
        self.press_height = event.y
        index_len = len(self.tree_list)
        index = int(self.press_height / self.height)
        
        
        if index_len > index:
            if is_single_click(event):
                self.press_draw_bool = True
            
                if self.tree_list[index].child_itmes:                 
                    self.tree_list[index].show_child_items_bool = not self.tree_list[index].show_child_items_bool 
                    self.sort()
                # for list in self.tree_list:
                #     print list.text
                    self.queue_draw()
            
            if is_single_click(event):
                self.emit("single-click-item", self.tree_list[index].tree_view_item)
            elif is_double_click(event):    
                self.emit("double-click-item", self.tree_list[index].tree_view_item)
            elif is_right_button(event):    
                self.emit("right-press-item", self.tree_list[index].tree_view_item, event.x_root, event.y_root)
                
        else:
            self.press_height = temp_press_height
                    
    def tree_view_motion_event(self, widget, event):
        temp_move_height = self.move_height # Save move_height.
        self.move_height = event.y
        index_len = len(self.tree_list)
        index_num = int(self.move_height) / self.height 

        if index_len > index_num: 
            self.move_draw_bool = True                            
            self.queue_draw()       
        else:
            self.move_height = temp_move_height
            
    def get_offset_coordinate(self, widget):
        '''Get offset coordinate.'''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = get_match_parent(widget, "Viewport")
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)    

        else:
            return (0, 0, viewport)
            
    def draw_mask(self, cr, x, y, w, h):        
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linearBackground").get_color_info())
            
    def tree_view_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
            
        # Draw background.
        with cairo_state(cr):
            cr.translate(-viewport.allocation.x, -viewport.allocation.y)
            cr.rectangle(offset_x, offset_y, 
                         viewport.allocation.x + viewport.allocation.width, 
                         viewport.allocation.y + viewport.allocation.height)
            cr.clip()
            
            (shadow_x, shadow_y) = self.get_toplevel().get_shadow_size()
            skin_config.render_background(cr, self, offset_x + shadow_x, offset_y + shadow_y)
            
        # Draw mask.
        self.draw_mask(cr, offset_x, offset_y, viewport.allocation.width, viewport.allocation.height)
        
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
            
        if self.tree_list:    
            temp_height = 0
            # (cr, text, font_size, font_color, x, y, width, height, font_align
            for draw_widget in self.tree_list:                
                pass
                if draw_widget.text:
                    draw_font(cr, 
                              draw_widget.text,
                              self.font_size,
                              self.font_color,
                              self.font_x_padding + draw_widget.width,
                              temp_height + self.height/2, 
                              self.font_width, self.font_height, self.font_align)                     
                    
                    temp_height += self.height
                    
                    
    def tree_view_key_press_event(self, widget, event):
        pass
    
    
    def tree_view_leave_notify_event(self, widget, event):
        self.move_draw_bool = False
        self.queue_draw()            
    
    def add_item(self, parent_id, child_item):    
        temp_tree = self.create_tree(child_item)
        
        temp_child_id = self.tree_id_num

        if None == parent_id:            
            self.tree_id_list.append(self.tree_id_num)
            self.tree_list.append(temp_tree)
                        
        self.root.add_node(parent_id, temp_child_id, temp_tree)
        
        self.tree_id_num += 1
        
        return temp_child_id
    
    def create_tree(self, child_item):
        temp_tree = Tree()
        temp_tree.id = self.tree_id_num
        temp_tree.tree_view_item = child_item
        temp_tree.child_itmes = {}
        temp_tree.text = child_item.get_title()        
        return temp_tree
    
    def del_item(self, item):
        pass
    
    def set_text(self, item):
        pass
    def get_text(self, item):
        pass
    
    def clear(self):
        pass
    
    def sort(self):               
        self.tree_list = []
        for key in self.root.child_itmes.keys():
            self.tree_list.append(self.root.child_itmes[key])
            if self.root.child_itmes[key].child_itmes:
                self.sort2(self.root.child_itmes[key], self.width)                                        
            
    def sort2(self, node, width):
        for key in node.child_itmes.keys():            
            if node.child_itmes[key].parent_item.show_child_items_bool:                      
                node.child_itmes[key].width = width
                self.tree_list.append(node.child_itmes[key])
                if node.child_itmes[key].child_itmes:
                    self.sort2(node.child_itmes[key], width + self.width)                
    
class Tree(object):
    def __init__(self):
        self.id = None
        
        self.tree_view_item = None
        self.parent_item = None
        
        self.child_itmes = OrderedDict()    
        self.child_itmes = {}
        self.text = ""
        self.show_child_items_bool = False
    
        self.has_arrow = True
        self.item_left_image = None
        
        self.width = 0
        
    def add_node(self, root_id, node_id, node_item):
        # Root node add child widget.
        if None == root_id:
            self.child_itmes[node_id] = node_item
        else:        
            for key in self.child_itmes.keys():
                if key == root_id:
                    node_item.parent_item = self.child_itmes[key] # Save parent Node.
                    self.child_itmes[key].child_itmes[node_id] = node_item
                    return True
        
                if self.scan_node(self.child_itmes[key], root_id, node_id, node_item):
                    return True
            
    def scan_node(self, root_node, root_id, node_id, node_item):
        if root_node.child_itmes:
            for key in root_node.child_itmes.keys():
                if key == root_id:                    
                    node_item.parent_item = root_node.child_itmes[key] # Save parent Node.
                    root_node.child_itmes[key].child_itmes[node_id] = node_item                
                    return True
                else:    
                    self.scan_node(root_node.child_itmes[key], root_id, node_id, node_item)        
                
gobject.type_register(TreeView)                    

class TreeViewItem(object):    
    def __init__(self, item_title, has_arrow=True, item_left_image=None):
        self.item_title = item_title
        self.has_arrow = has_arrow
        self.item_left_image = item_left_image
        
    def get_title(self):    
        return self.item_title
    
    def has_arrow(self):
        return self.has_arrow
    
    def get_left_image(self):
        return self.item_left_image                

    
if __name__ == "__main__":
    
    def single_click_cb(widget, item, x, y):
        print item.get_title(), x, y
    
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    tree_view = TreeView()    
    # tree_view.connect("single-click-item", single_click_cb)
    # tree_view.connect("double-click-item", single_click_cb)
    tree_view.connect("right-press-item", single_click_cb)
    
    a = tree_view.add_item(None, TreeViewItem("高中"))
    a1 =tree_view.add_item(a, TreeViewItem("高一"))
    b = tree_view.add_item(None, TreeViewItem("大学"))
    b1 = tree_view.add_item(b, TreeViewItem("软件学院"))
    c = tree_view.add_item(None, TreeViewItem("深度"))
    d = tree_view.add_item(None, TreeViewItem("社会大学"))
    d1 = tree_view.add_item(d, TreeViewItem("系统分析师"))        
    d2 = tree_view.add_item(d, TreeViewItem("系统架构师"))        
    d3 = tree_view.add_item(d, TreeViewItem("软件工程师"))        
    win.add(tree_view)
    win.show_all()
    gtk.main()
