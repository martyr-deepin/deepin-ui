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

from theme import DynamicPixbuf
from theme import ui_theme
from window import Window
from draw import draw_text, draw_vlinear, draw_pixbuf
from utils import get_content_size, get_screen_size
from new_treeview import TreeView, TreeItem
from constant import DEFAULT_FONT_SIZE, ALIGN_START, ALIGN_MIDDLE
import gobject
import gtk
from popup_grab_window import PopupGrabWindow, wrap_grab_window

class Poplist(Window):
    '''
    class docs
    '''
	
    def __init__(self,
                 items,
                 max_height=None,
                 max_width=None,
                 shadow_visible=True,
                 shape_frame_function=None,
                 expose_frame_function=None,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 min_width=130,
                 align_size=0,
                 ):
        '''
        init docs
        '''
        # Init.
        Window.__init__(self, 
                        shadow_visible=shadow_visible,
                        shape_frame_function=shape_frame_function,
                        expose_frame_function=expose_frame_function)
        self.items = items
        self.max_height = max_height
        self.max_width = max_width
        self.x_align = x_align
        self.y_align = y_align
        self.min_width = min_width
        self.align_size = align_size
        self.window_width = self.window_height = 0
        self.treeview_align = gtk.Alignment()
        self.treeview_align.set(0.5, 0.5, 0, 0)
        self.treeview_align.set_padding(self.align_size, self.align_size, self.align_size, self.align_size)
        self.treeview = TreeView(self.items,
                                 enable_highlight=False,
                                 enable_multiple_select=False,
                                 enable_drag_drop=False)
        
        # Connect widgets.
        self.treeview_align.add(self.treeview)
        self.window_frame.pack_start(self.treeview_align, True, False)
        
        self.connect("realize", self.realize_poplist)
        
        # Wrap self in poup grab window.
        wrap_grab_window(poplist_grab_window, self)
        
    def get_scrolledwindow(self):
        return self.treeview.scrolled_window
        
    def realize_poplist(self, widget):
        treeview_width = self.min_width
        for item in self.treeview.visible_items:
            if hasattr(item, "get_width"):
                treeview_width = max(treeview_width, item.get_width())
                
        treeview_height = int(self.treeview.scrolled_window.get_vadjustment().get_upper())
                
        if self.max_width != None and self.max_height != None: 
            adjust_width = self.max_width
            adjust_height = self.max_height
        elif self.max_height != None:
            adjust_width = treeview_width
            adjust_height = self.max_height
        elif self.max_width != None:
            adjust_width = self.max_width
            adjust_height = treeview_height
        else:
            adjust_width = treeview_width
            adjust_height = treeview_height
            
        self.treeview.set_size_request(adjust_width, adjust_height)
        
        (shadow_padding_x, shadow_padding_y) = self.get_shadow_size()
        self.window_width = adjust_width + shadow_padding_x * 2 + self.align_size * 2
        self.window_height = adjust_height + shadow_padding_y * 2 + self.align_size * 2
        self.set_default_size(self.window_width, self.window_height)
        self.set_geometry_hints(
            None,
            self.window_width,       # minimum width
            self.window_height,       # minimum height
            self.window_width,
            self.window_height,
            -1, -1, -1, -1, -1, -1
            )
        
    def show(self, (expect_x, expect_y), (offset_x, offset_y)=(0, 0)):
        (screen_width, screen_height) = get_screen_size(self)
        
        if self.x_align == ALIGN_START:
            dx = expect_x
        elif self.x_align == ALIGN_MIDDLE:
            dx = expect_x - self.window_width / 2
        else:
            dx = expect_x - self.window_width
            
        if self.y_align == ALIGN_START:
            dy = expect_y
        elif self.y_align == ALIGN_MIDDLE:
            dy = expect_y - self.window_height / 2
        else:
            dy = expect_y - self.window_height

        if expect_x + self.window_width > screen_width:
            dx = expect_x - self.window_width + offset_x
        if expect_y + self.window_height > screen_height:
            dy = expect_y - self.window_height + offset_y
            
        self.move(dx, dy)
        
        self.show_all()
                            
gobject.type_register(Poplist)        

class TextItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, 
                 text, 
                 text_size = DEFAULT_FONT_SIZE,
                 padding_x = 10,
                 padding_y = 6):
        '''
        init docs
        '''
        # Init.
        TreeItem.__init__(self)
        self.text = text
        self.text_size = text_size
        self.padding_x = padding_x
        self.padding_y = padding_y
        (self.text_width, self.text_height) = get_content_size(self.text)
        
    def render_text(self, cr, rect):
        font_color = ui_theme.get_color("menu_font").get_color()
        if self.is_hover:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menu_item_select").get_color_info())
        
            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()
            
        draw_text(cr, 
                  self.text,
                  rect.x + self.padding_x, 
                  rect.y + self.padding_y, 
                  rect.width - self.padding_x * 2, 
                  rect.height - self.padding_y * 2,
                  text_color=font_color)
        
    def get_width(self):
        return self.text_width + self.padding_x * 2
        
    def get_height(self):
        return self.text_size + self.padding_y * 2
    
    def get_column_widths(self):
        return [-1]
    
    def get_column_renders(self):
        return [self.render_text]

    def unhover(self):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self):
        self.is_hover = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
gobject.type_register(TextItem)

class IconTextItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, 
                 icon_dpixbufs,
                 text, 
                 text_size = DEFAULT_FONT_SIZE,
                 icon_width = 16,
                 padding_x = 10,
                 padding_y = 6):
        '''
        init docs
        '''
        # Init.
        TreeItem.__init__(self)
        (self.icon_normal_dpixbuf, self.icon_hover_dpixbuf, self.icon_disable_dpixbuf) = icon_dpixbufs
        self.text = text
        self.text_size = text_size
        self.icon_width = 16
        self.padding_x = padding_x
        self.padding_y = padding_y
        (self.text_width, self.text_height) = get_content_size(self.text)
        
    def render(self, cr, rect):
        font_color = ui_theme.get_color("menu_font").get_color()
        if isinstance(self.icon_normal_dpixbuf, gtk.gdk.Pixbuf):
            icon_pixbuf = self.icon_normal_dpixbuf
        elif isinstance(self.icon_normal_dpixbuf, DynamicPixbuf):
            icon_pixbuf = self.icon_normal_dpixbuf.get_pixbuf()
            
        if self.is_hover:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menu_item_select").get_color_info())
        
            # Set icon pixbuf.
            if isinstance(self.icon_hover_dpixbuf, gtk.gdk.Pixbuf):
                icon_pixbuf = self.icon_hover_dpixbuf
            elif isinstance(self.icon_hover_dpixbuf, DynamicPixbuf):
                icon_pixbuf = self.icon_hover_dpixbuf.get_pixbuf()
            
            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()
            
        draw_pixbuf(cr, icon_pixbuf, 
                    rect.x + self.padding_x,
                    rect.y + (rect.height - icon_pixbuf.get_height()) / 2)    
            
        draw_text(cr, 
                  self.text,
                  rect.x + self.padding_x * 2 + self.icon_width, 
                  rect.y + self.padding_y, 
                  rect.width - self.padding_x * 2, 
                  rect.height - self.padding_y * 2,
                  text_color=font_color)
        
    def get_width(self):
        return self.icon_width + self.text_width + self.padding_x * 3
        
    def get_height(self):
        return self.text_size + self.padding_y * 2
    
    def get_column_widths(self):
        return [-1]
    
    def get_column_renders(self):
        return [self.render]

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
gobject.type_register(IconTextItem)

poplist_grab_window = PopupGrabWindow(Poplist)
