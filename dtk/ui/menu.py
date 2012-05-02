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

from constant import DEFAULT_FONT_SIZE, MENU_ITEM_RADIUS, ALIGN_START, ALIGN_MIDDLE, WIDGET_POS_RIGHT_CENTER, WIDGET_POS_TOP_LEFT
from draw import draw_vlinear, draw_pixbuf, draw_font
from line import HSeparator
from theme import ui_theme
from utils import is_in_rect, get_content_size, widget_fix_cycle_destroy_bug, propagate_expose, get_widget_root_coordinate, get_screen_size
from window import Window
import gtk
import gobject

menu_grab_window = gtk.Window(gtk.WINDOW_POPUP)
menu_grab_window.move(0, 0)
menu_grab_window.set_default_size(0, 0)
menu_grab_window.show()

root_menus = []
menu_grab_window_press_id = None
menu_grab_window_motion_id = None

def menu_grab_window_focus_in():
    menu_grab_window.grab_add()
    gtk.gdk.pointer_grab(
        menu_grab_window.window, 
        True,
        gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK,
        None, None, gtk.gdk.CURRENT_TIME)
    
def menu_grab_window_focus_out():
    global root_menus
    
    for root_menu in root_menus:
        root_menu.hide()
    
    root_menus = []    
    
    gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
    menu_grab_window.grab_remove()

def menu_grab_window_button_press(widget, event):
    global menu_grab_window_press_id
    global menu_grab_window_motion_id    
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, Menu):
            menu_item = event_widget.get_menu_item_at_coordinate(event.get_root_coords())
            if menu_item:
                menu_item.item_box.event(event)
        else:
            menu_grab_window_focus_out()
    
    if menu_grab_window_press_id:
        gobject.source_remove(menu_grab_window_press_id)
        menu_grab_window_press_id = None
        
    if menu_grab_window_motion_id:
        gobject.source_remove(menu_grab_window_motion_id)
        menu_grab_window_motion_id = None
        
def menu_grab_window_motion(widget, event):
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, Menu):
            menu_item = event_widget.get_menu_item_at_coordinate(event.get_root_coords())
            if menu_item and isinstance(menu_item.item_box, gtk.Button):
                # menu_item.enter_notify_menu_item(menu_item.item_box)
                
                enter_notify_event = gtk.gdk.Event(gtk.gdk.ENTER_NOTIFY)
                enter_notify_event.window = event.window
                enter_notify_event.time = event.time
                enter_notify_event.send_event = True
                enter_notify_event.x_root = event.x_root
                enter_notify_event.y_root = event.y_root
                enter_notify_event.x = event.x
                enter_notify_event.y = event.y
                enter_notify_event.state = event.state
                
                menu_item.item_box.event(enter_notify_event)
                
                menu_item.item_box.queue_draw()

class Menu(Window):
    '''Menu.'''
	
    def __init__(self, items, 
                 is_root_menu=False,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 font_size=DEFAULT_FONT_SIZE, 
                 opacity=1.0, 
                 padding_x=4, 
                 padding_y=4, 
                 item_padding_x=6, 
                 item_padding_y=4):
        '''Init menu, item format: (item_icon, itemName, item_node).'''
        # Init.
        Window.__init__(self, False, "menuMask")
        global root_menus
        self.is_root_menu = is_root_menu
        self.x_align = x_align
        self.y_align = y_align
        self.submenu_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")
        self.submenu = None
        self.root_menu = None
        self.offset_x = 0       # use for handle extreme situaiton, such as, menu show at side of screen
        self.offset_y = 0
        
        # Init menu window.
        self.set_opacity(opacity)
        self.set_skip_taskbar_hint(True)
        self.connect_after("show", self.init_menu)
        
        # Add menu item.
        self.item_box = gtk.VBox()
        self.item_align = gtk.Alignment()
        self.item_align.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_align.add(self.item_box)
        self.window_frame.add(self.item_align)
        self.menu_items = []
        
        if items:
            (have_icon, icon_width, icon_height, have_submenu, submenu_width, submenu_height) = self.get_menu_icon_info(items)
            
            for item in items:
                menu_item = MenuItem(
                    item, font_size, self.show_submenu, self.hide_submenu, self.get_root_menu, self.get_menu_items,
                    have_icon, icon_width, icon_height,
                    have_submenu, submenu_width, submenu_height,
                    item_padding_x, item_padding_y)
                self.menu_items.append(menu_item)
                self.item_box.pack_start(menu_item.item_box, False, False)
                
    def get_menu_item_at_coordinate(self, (x, y)):
        '''Get menu item at coordinate, return None if haven't any menu item at given coordinate.'''
        match_menu_item = None
        for menu_item in self.menu_items:                
            item_rect = menu_item.item_box.get_allocation()
            (item_x, item_y) = get_widget_root_coordinate(menu_item.item_box, WIDGET_POS_TOP_LEFT)
            if is_in_rect((x, y), (item_x, item_y, item_rect.width, item_rect.height)):
                match_menu_item = menu_item
                break    
            
        return match_menu_item
                
    def get_menu_items(self):
        '''Get menu items.'''
        return self.menu_items
    
    def init_menu(self, widget):
        '''Realize menu.'''
        global root_menus
        global menu_grab_window_press_id
        global menu_grab_window_motion_id
        
        if not gtk.gdk.pointer_is_grabbed():
            menu_grab_window_focus_in()
            menu_grab_window_press_id = menu_grab_window.connect("button-press-event", menu_grab_window_button_press)
            menu_grab_window_motion_id = menu_grab_window.connect("motion-notify-event", menu_grab_window_motion)
            
        if self.is_root_menu and not self in root_menus:
            root_menus.append(self)
                            
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
        
    def show(self, (x, y), (offset_x, offset_y)=(0, 0)):
        '''Show menu.'''
        # Init offset.
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        # Show.
        self.show_all()
        
        # Adjust coordinate.
        rect = self.get_allocation()
        (screen_width, screen_height) = get_screen_size(self)
        
        if self.x_align == ALIGN_START:
            dx = x
        elif self.x_align == ALIGN_MIDDLE:
            dx = x - rect.width / 2
        else:
            dx = x - rect.width
            
        if self.y_align == ALIGN_START:
            dy = y
        elif self.y_align == ALIGN_MIDDLE:
            dy = y - rect.height / 2
        else:
            dy = y - rect.height

        if x + rect.width > screen_width:
            dx = x - rect.width + offset_x
        if y + rect.height > screen_height:
            dy = y - rect.height + offset_y
            
        self.move(dx, dy)
            
    def hide(self):
        '''Hide menu.'''
        # Hide submenu.
        self.hide_submenu()
        
        # Hide current menu window.
        self.hide_all()
        
        # Reset.
        self.submenu = None
        self.root_menu = None
        
    def show_submenu(self, submenu, coordinate):
        '''Show submenu.'''
        if self.submenu != submenu:
            # Hide old submenu first.
            self.hide_submenu()
            
            # Update attributes of new submenu.
            self.submenu = submenu
            self.submenu.root_menu = self.get_root_menu()
            
            # Show new submenu.
            rect = self.get_allocation()
            self.submenu.show(coordinate, (-rect.width + self.shadow_radius * 2, 0))
                
    def hide_submenu(self):
        '''Hide submenu.'''
        if self.submenu:
            # Hide submenu.
            self.submenu.hide()
            self.submenu = None
            
            # Reset menu items in submenu.
            for menu_item in self.menu_items:
                menu_item.submenu_active = False
            
    def get_root_menu(self):
        '''Get root menu.'''
        if self.root_menu:
            return self.root_menu
        else:
            return self
            
gobject.type_register(Menu)

class MenuItem(object):
    '''Menu item.'''
    
    def __init__(self, item, font_size, 
                 show_submenu_callback, 
                 hide_submenu_callback,
                 get_root_menu_callback,
                 get_menu_items_callback,
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
        self.get_menu_items_callback = get_menu_items_callback
        self.have_icon = have_icon
        self.icon_width = icon_width
        self.icon_height = icon_height
        self.have_submenu = have_submenu
        self.submenu_width = submenu_width
        self.submenu_height = submenu_height
        self.submenu_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")        
        self.submenu_active = False

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
            
        # Set adjust offset x.
        self.adjust_offset = 0    
        if not self.have_icon:
            self.adjust_offset = -self.item_padding_x
            
        # Create button.
        self.item_box = gtk.Button()
        
        # Set button size.
        (width, height) = get_content_size(item_content, self.font_size)
        if self.have_submenu:
            self.item_box.set_size_request(
                self.item_padding_x * 4 + self.icon_width + self.submenu_width + int(width) + self.adjust_offset, 
                self.item_padding_y * 2 + max(int(height), self.icon_height))
        else:
            self.item_box.set_size_request(
                self.item_padding_x * 3 + self.icon_width + int(width) + self.adjust_offset, 
                self.item_padding_y * 2 + max(int(height), self.icon_height))
        
        # Expose button.
        widget_fix_cycle_destroy_bug(self.item_box)
        self.item_box.connect(
            "expose-event", 
            lambda w, e: self.expose_menu_item(
                w, e, item_dpixbuf, item_content))
        self.item_box.connect("enter-notify-event", lambda w, e: self.enter_notify_menu_item(w))
        
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
                    item_node(*self.item[3:])
                else:
                    item_node()
            
            # Hide menu.
            # self.get_root_menu_callback().hide()    
            menu_grab_window_focus_out()
            
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
        elif self.submenu_active:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menuItemActiveSubmenu").get_color_info(),
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
                 rect.x + self.item_padding_x * 2 + pixbuf_width + self.content_offset + self.adjust_offset,
                 rect.y,
                 rect.width - self.item_padding_x * 3 - pixbuf_width - self.content_offset - self.adjust_offset,
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

    def enter_notify_menu_item(self, widget):
        '''Callback for `enter-notify-event` signal.'''
        # Reset all items in same menu.
        for menu_item in self.get_menu_items_callback():
            if menu_item != self and menu_item.submenu_active:
                menu_item.submenu_active = False
                menu_item.item_box.queue_draw()
        
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Menu):
            menu_window = self.item_box.get_toplevel()
            (menu_window_x, menu_window_y) = get_widget_root_coordinate(menu_window, WIDGET_POS_RIGHT_CENTER)
            (item_x, item_y) = get_widget_root_coordinate(self.item_box)
            self.show_submenu_callback(
                item_node, 
                (menu_window_x - menu_window.shadow_radius, item_y - widget.get_allocation().height))
            
            self.submenu_active = True
        else:
            self.hide_submenu_callback()
