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
from utils import *
from draw import *
from line import *
from window import *

MENU_POS_TOP_CENTER = 0
MENU_POS_TOP_LEFT = 1
MENU_POS_TOP_RIGHT = 2

class Menu(object):
    '''Menu.'''
	
    def __init__(self, items, menu_pos=MENU_POS_TOP_CENTER, font_size=DEFAULT_FONT_SIZE, opacity=0.9, 
                 padding_x=4, padding_y=10, item_padding_x=10, item_padding_y=4):
        '''Init menu, item format: (item_icon, itemName, item_node).'''
        # Init.
        self.menu_pos = menu_pos
        self.submenu_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")
        self.submenu = None
        self.root_menu = None
        self.in_menu_area = False
        
        # Init menu window.
        self.menu_window = Window(False, "menuMask")
        self.menu_window.set_opacity(opacity)
        self.menu_window.set_skip_taskbar_hint(True)
        self.menu_window.connect("enter-notify-event", self.enter_notify_menu)
        self.menu_window.connect("leave-notify-event", self.leave_notify_menu)
        self.menu_window.connect("focus-out-event", self.focus_out_menu)
        
        # Add menu item.
        self.item_box = gtk.VBox()
        self.item_align = gtk.Alignment()
        self.item_align.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_align.add(self.item_box)
        self.menu_window.window_frame.add(self.item_align)
        
        if items:
            (have_icon, icon_width, icon_height, have_submenu, submenu_width, submenu_height) = self.get_menu_icon_info(items)
            
            for item in items:
                self.item_box.pack_start(
                    MenuItem(item, font_size, self.show_submenu, self.hide_submenu, self.get_root_menu,
                             have_icon, icon_width, icon_height,
                             have_submenu, submenu_width, submenu_height,
                             item_padding_x, item_padding_y).item_box, False, False)
                
    def enter_notify_menu(self, widget, event):
        '''Enter notify menu.'''
        self.get_root_menu().in_menu_area = True
        
    def leave_notify_menu(self, widget, event):
        '''Leave notify menu.'''
        in_area = False
        all_menus = self.get_root_menu().get_submenus() + [self.get_root_menu()]
        for menu in all_menus:
            (ex, ey) = event.get_root_coords()
            (wx, wy) = widget.window.get_root_origin()
            ww, wh = widget.get_allocation().width, widget.get_allocation().height
            if is_in_rect((ex, ey), (wx, wy, ww, wh)):
                in_area = True
                break
            
        self.get_root_menu().in_menu_area = in_area    
        
    def focus_out_menu(self, widget, event):
        '''Focus out menu.'''
        menu = self.get_root_menu()
        if not menu.in_menu_area:
            menu.in_menu_area = False
            menu.hide()

    def get_submenus(self):
        '''Get submenus.'''
        if self.submenu:
            return [self.submenu] + self.submenu.get_submenus()
        else:
            return []
                
    def get_menu_icon_info(self, items):
        '''Get menu icon information.'''
        have_icon = False
        icon_width = 0
        icon_height = 0
        have_submenu = False
        submenu_width = 0
        submenu_height = 0
        
        for item in items:
            if item:
                (item_dpixbuf, item_content, item_node) = item[0:3]
                if item_dpixbuf:
                    have_icon = True
                    icon_width = item_dpixbuf.get_pixbuf().get_width()
                    icon_height = item_dpixbuf.get_pixbuf().get_height()
                
                if isinstance(item_node, Menu):
                    have_submenu = True
                    submenu_width = self.submenu_dpixbuf.get_pixbuf().get_width()
                    submenu_height = self.submenu_dpixbuf.get_pixbuf().get_height()
                    
                if have_icon and have_submenu:
                    break
                
        return (have_icon, icon_width, icon_height, have_submenu, submenu_width, submenu_height)
        
    def show(self, (x, y)):
        '''Show menu.'''
        # Show menu.
        self.menu_window.show_all()
        
        # Set menu position.
        rect = self.menu_window.get_allocation()
        if self.menu_pos == MENU_POS_TOP_CENTER:
            self.menu_window.move(x - rect.width / 2, y)
        elif self.menu_pos == MENU_POS_TOP_LEFT:
            self.menu_window.move(x, y)
        elif self.menu_pos == MENU_POS_TOP_RIGHT:
            self.menu_window.move(x + rect.width, y)
            
    def hide(self):
        '''Hide menu.'''
        # Hide submenu.
        self.hide_submenu()
        
        # Hide current menu window.
        self.menu_window.hide_all()
        
        # Reset.
        self.submenu = None
        self.root_menu = None
        self.in_menu_area = False
        
    def show_submenu(self, submenu, coordinate):
        '''Show submenu.'''
        if self.submenu != submenu:
            # Hide old submenu first.
            self.hide_submenu()
            
            # Update attributes of new submenu.
            self.submenu = submenu
            self.submenu.root_menu = self.get_root_menu()
            
            # Show new submenu.
            self.submenu.show(coordinate)
                
    def hide_submenu(self):
        '''Hide submenu.'''
        if self.submenu:
            self.submenu.hide()
            self.submenu = None
            
    def get_root_menu(self):
        '''Get root menu.'''
        if self.root_menu:
            return self.root_menu
        else:
            return self
            
class MenuItem(object):
    '''Menu item.'''
    
    def __init__(self, item, font_size, show_submenu_callback, hide_submenu_callback,
                 get_root_menu_callback,
                 have_icon, icon_width, icon_height, 
                 have_submenu, submenu_width, submenu_height,
                 item_padding_x, item_padding_y):
        '''Init menu item.'''
        # Init.
        self.item = item
        self.font_size = font_size
        self.item_padding_x = item_padding_x
        self.item_padding_y = item_padding_y
        self.show_submenu_callback = show_submenu_callback
        self.hide_submenu_callback = hide_submenu_callback
        self.get_root_menu_callback = get_root_menu_callback
        self.have_icon = have_icon
        self.icon_width = icon_width
        self.icon_height = icon_height
        self.have_submenu = have_submenu
        self.submenu_width = submenu_width
        self.submenu_height = submenu_height
        self.submenu_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")        

        # Create.
        if self.item:
            self.create_menu_item()
        else:
            self.create_separator_item()
        
    def create_separator_item(self):
        '''Create separator item.'''
        self.item_box = HSeparator(
            ui_theme.get_shadow_color("hSeparator").get_color_info(),
            self.item_padding_x, 
            self.item_padding_y)
        
    def create_menu_item(self):
        '''Create menu item.'''
        # Get item information.
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        
        # Calcuate content offset.
        self.content_offset = 0
        if item_dpixbuf == None and self.have_icon:
            self.content_offset = self.icon_width
            
        # Create button.
        self.item_box = gtk.Button()
        
        # Set button size.
        (width, height) = get_content_size(item_content, self.font_size)
        if self.have_submenu:
            self.item_box.set_size_request(
                self.item_padding_x * 4 + self.icon_width + self.submenu_width + int(width), 
                self.item_padding_y * 2 + max(int(height), self.icon_height))
        else:
            self.item_box.set_size_request(
                self.item_padding_x * 3 + self.icon_width + int(width), 
                self.item_padding_y * 2 + max(int(height), self.icon_height))
        
        # Expose button.
        widget_fix_cycle_destroy_bug(self.item_box)
        self.item_box.connect(
            "expose-event", 
            lambda w, e: self.expose_menu_item(
                w, e, item_dpixbuf, item_content))
        self.item_box.connect("enter-notify-event", self.enter_notify_menu_item)
        
        # Wrap menu aciton.
        self.item_box.connect("clicked", self.wrap_menu_clicked_action)        
        
    def wrap_menu_clicked_action(self, button):
        '''Wrap menu action.'''
        # (item_dpixbuf, item_content, item_node, item_data) = self.item
        item_node = self.item[2]
        if not isinstance(item_node, Menu):
            # Execute callback.
            if item_node:
                if len(self.item) > 3:
                    # print self.item[3:]
                    item_node(*self.item[3:])
                else:
                    item_node()
            
            # Hide menu.
            self.get_root_menu_callback().hide()    
            
    def expose_menu_item(self, widget, event, item_dpixbuf, item_content):
        '''Expose menu item.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        font_color = ui_theme.get_color("menuFont").get_color()
        
        # Draw select effect.
        if widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menuItemSelect").get_color_info(),
                         MENU_ITEM_RADIUS)
            
            # Set font color.
            font_color = ui_theme.get_color("menuSelectFont").get_color()
            
        # Draw item icon.
        pixbuf = None
        pixbuf_width = 0
        if item_dpixbuf:
            pixbuf = item_dpixbuf.get_pixbuf()
            pixbuf_width += pixbuf.get_width()
            draw_pixbuf(cr, pixbuf, rect.x + self.item_padding_x, rect.y + (rect.height - pixbuf.get_height()) / 2)
            
        # Draw item content.
        draw_font(cr, item_content, self.font_size, font_color,
                 rect.x + self.item_padding_x * 2 + pixbuf_width + self.content_offset,
                 rect.y,
                 rect.width - self.item_padding_x * 3 - pixbuf_width - self.content_offset,
                 rect.height,
                 ALIGN_START, ALIGN_MIDDLE
                 )
        
        # Draw submenu arrow.
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Menu):
            submenu_pixbuf = self.submenu_dpixbuf.get_pixbuf()
            draw_pixbuf(cr, submenu_pixbuf,
                        rect.x + rect.width - self.item_padding_x - submenu_pixbuf.get_width(),
                        rect.y + (rect.height - submenu_pixbuf.get_height()) / 2)
        
        # Propagate expose to children.
        propagate_expose(widget, event)
    
        return True

    def enter_notify_menu_item(self, widget, event):
        '''Callback for `enter-notify-event` signal.'''
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Menu):
            (item_x, item_y) = get_widget_root_coordinate(self.item_box)
            self.show_submenu_callback(
                item_node, 
                (item_x + widget.get_allocation().width / 2, item_y - widget.get_allocation().height))
        else:
            self.hide_submenu_callback()
