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
from draw import draw_vlinear, draw_pixbuf, draw_text, draw_hlinear
from line import HSeparator
from theme import ui_theme
from window import Window
import gobject
import gtk
from utils import (is_in_rect, get_content_size, propagate_expose,
                   get_widget_root_coordinate, get_screen_size, 
                   alpha_color_hex_to_cairo, get_window_shadow_size)

menu_grab_window = gtk.Window(gtk.WINDOW_POPUP)
menu_grab_window.move(0, 0)
menu_grab_window.set_default_size(0, 0)
menu_grab_window.show()
menu_active_item = None

root_menus = []

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
    
    if menu_active_item:
        menu_active_item.set_state(gtk.STATE_NORMAL)
        
def is_press_on_menu_grab_window(window):
    '''Is press on menu grab window.'''
    for toplevel in gtk.window_list_toplevels():
        if isinstance(window, gtk.Window):
            if window == toplevel:
                return True
        elif isinstance(window, gtk.gdk.Window):
            if window == toplevel.window:
                return True
            
    return False        
    
def menu_grab_window_button_press(widget, event):
    global menu_active_item
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if is_press_on_menu_grab_window(event.window):
            menu_grab_window_focus_out()
        elif isinstance(event_widget, Menu):
            menu_item = event_widget.get_menu_item_at_coordinate(event.get_root_coords())
            if menu_item:
                menu_item.item_box.event(event)
        else:
            event_widget.event(event)
            menu_grab_window_focus_out()
    
def menu_grab_window_motion_notify(widget, event):
    global menu_active_item
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, Menu):
            menu_item = event_widget.get_menu_item_at_coordinate(event.get_root_coords())
            if menu_item and isinstance(menu_item.item_box, gtk.Button):
                if menu_active_item:
                    menu_active_item.set_state(gtk.STATE_NORMAL)
                
                menu_item.item_box.set_state(gtk.STATE_PRELIGHT)
                menu_active_item = menu_item.item_box
                
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

menu_grab_window.connect("button-press-event", menu_grab_window_button_press)
menu_grab_window.connect("motion-notify-event", menu_grab_window_motion_notify)

class Menu(Window):
    '''Menu.'''
    
    def __init__(self, items, 
                 is_root_menu=False,
                 select_scale=False,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 font_size=DEFAULT_FONT_SIZE, 
                 padding_x=3, 
                 padding_y=3, 
                 item_padding_x=6, 
                 item_padding_y=3,
                 shadow_visible=True,
                 menu_min_width=130):
        '''Init menu, item format: (item_icon, itemName, item_node).'''
        global root_menus
        
        # Init.
        Window.__init__(self, shadow_visible=shadow_visible, window_type=gtk.WINDOW_POPUP)
        self.set_can_focus(True) # can focus to response key-press signal
        self.draw_mask = self.draw_menu_mask
        self.is_root_menu = is_root_menu
        self.select_scale = select_scale
        self.x_align = x_align
        self.y_align = y_align
        self.submenu = None
        self.root_menu = None
        self.offset_x = 0       # use for handle extreme situaiton, such as, menu show at side of screen
        self.offset_y = 0
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.item_padding_x = item_padding_x
        self.item_padding_y = item_padding_y
        self.menu_min_width = menu_min_width
        
        # Init menu window.
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        
        # Add menu item.
        self.item_box = gtk.VBox()
        self.item_align = gtk.Alignment()
        self.item_align.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_align.add(self.item_box)
        self.window_frame.add(self.item_align)
        self.menu_items = []
        
        if items:
            (icon_width, icon_height, have_submenu, submenu_width, submenu_height) = self.get_menu_icon_info(items)
            
            for item in items:
                menu_item = MenuItem(
                    item, font_size, self.select_scale, self.show_submenu, self.hide_submenu, 
                    self.get_root_menu, self.get_menu_items,
                    icon_width, icon_height,
                    have_submenu, submenu_width, submenu_height,
                    padding_x, padding_y,
                    item_padding_x, item_padding_y, self.menu_min_width)
                self.menu_items.append(menu_item)
                self.item_box.pack_start(menu_item.item_box, False, False)
                
        self.connect("show", self.init_menu)
        self.connect("hide", self.hide_menu)
        self.connect("realize", self.realize_menu)
        
    def hide_menu(self, widget):
        '''Hide menu.'''
        # Avoid menu (popup window) show at (0, 0) when next show. 
        self.move(-1000000, -1000000)
        
    def realize_menu(self, widget):
        '''Realize menu.'''
        # Avoid menu (popup window) show at (0, 0) first. 
        self.move(-1000000, -1000000)
        
        # Never draw background.
        self.window.set_back_pixmap(None, False)
                
    def draw_menu_mask(self, cr, x, y, w, h):
        '''Draw mask.'''
        # Draw background.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("menu_mask").get_color_info()))
        cr.rectangle(x, y, w, h)    
        cr.fill()
        
        # Draw left side.
        draw_hlinear(cr, x + 1, y + 1, 16 + self.padding_x + self.padding_x * 2, h - 2,
                     ui_theme.get_shadow_color("menu_side").get_color_info())
        
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
        
        if self.is_root_menu:
            menu_grab_window_focus_out()
        
        if not gtk.gdk.pointer_is_grabbed():
            menu_grab_window_focus_in()
            
        if self.is_root_menu and not self in root_menus:
            root_menus.append(self)
            
        self.adjust_menu_position()    
            
    def get_submenus(self):
        '''Get submenus.'''
        if self.submenu:
            return [self.submenu] + self.submenu.get_submenus()
        else:
            return []
                
    def get_menu_icon_info(self, items):
        '''Get menu icon information.'''
        have_submenu = False
        icon_width = 16
        icon_height = 16
        submenu_width = 16
        submenu_height = 15
        
        for item in items:
            if item:
                (item_icons, item_content, item_node) = item[0:3]
                if isinstance(item_node, Menu):
                    have_submenu = True
                    
                if have_submenu:
                    break
                
        return (icon_width, icon_height, have_submenu, submenu_width, submenu_height)
        
    def show(self, (x, y), (offset_x, offset_y)=(0, 0)):
        '''Show menu.'''
        # Init offset.
        self.expect_x = x
        self.expect_y = y
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        # Show.
        self.show_all()
        
    def adjust_menu_position(self):
        '''Realize menu.'''
        # Adjust coordinate.
        (screen_width, screen_height) = get_screen_size(self)
        
        menu_width = menu_height = 0
        for menu_item in self.menu_items:
            if isinstance(menu_item.item_box, gtk.Button):
                item_box_width = menu_item.item_box_width
                if item_box_width > menu_width:
                    menu_width = item_box_width
            
            menu_height += menu_item.item_box_height    
        (shadow_x, shadow_y) = get_window_shadow_size(self)
        menu_width += (self.padding_x + shadow_x) * 2    
        menu_height += (self.padding_y + shadow_y) * 2
            
        if self.x_align == ALIGN_START:
            dx = self.expect_x
        elif self.x_align == ALIGN_MIDDLE:
            dx = self.expect_x - menu_width / 2
        else:
            dx = self.expect_x - menu_width
            
        if self.y_align == ALIGN_START:
            dy = self.expect_y
        elif self.y_align == ALIGN_MIDDLE:
            dy = self.expect_y - menu_height / 2
        else:
            dy = self.expect_y - menu_height

        if self.expect_x + menu_width > screen_width:
            dx = self.expect_x - menu_width + self.offset_x
        if self.expect_y + menu_height > screen_height:
            dy = self.expect_y - menu_height + self.offset_y
            
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
        
    def show_submenu(self, submenu, coordinate, offset_y):
        '''Show submenu.'''
        if self.submenu != submenu:
            # Hide old submenu first.
            self.hide_submenu()
            
            # Update attributes of new submenu.
            self.submenu = submenu
            self.submenu.root_menu = self.get_root_menu()
            
            # Show new submenu.
            rect = self.get_allocation()
            self.submenu.show(coordinate, (-rect.width + self.shadow_radius * 2, offset_y))
                
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
                 select_scale,
                 show_submenu_callback, 
                 hide_submenu_callback,
                 get_root_menu_callback,
                 get_menu_items_callback,
                 icon_width, icon_height, 
                 have_submenu, submenu_width, submenu_height,
                 menu_padding_x, menu_padding_y,
                 item_padding_x, item_padding_y, min_width):
        '''Init menu item.'''
        # Init.
        self.item = item
        self.font_size = font_size
        self.select_scale = select_scale
        self.menu_padding_x = menu_padding_x
        self.menu_padding_y = menu_padding_y
        self.item_padding_x = item_padding_x
        self.item_padding_y = item_padding_y
        self.show_submenu_callback = show_submenu_callback
        self.hide_submenu_callback = hide_submenu_callback
        self.get_root_menu_callback = get_root_menu_callback
        self.get_menu_items_callback = get_menu_items_callback
        self.icon_width = icon_width
        self.icon_height = icon_height
        self.have_submenu = have_submenu
        self.submenu_width = submenu_width
        self.submenu_height = submenu_height
        self.submenu_active = False
        self.min_width = min_width
        self.arrow_padding_x = 5

        # Create.
        if self.item:
            self.create_menu_item()
        else:
            self.create_separator_item()
        
    def create_separator_item(self):
        '''Create separator item.'''
        self.item_box = HSeparator(
            ui_theme.get_shadow_color("h_separator").get_color_info(),
            self.item_padding_x, 
            self.item_padding_y)
        self.item_box_height = self.item_padding_y * 2 + 1
        
    def create_menu_item(self):
        '''Create menu item.'''
        # Get item information.
        (item_icons, item_content, item_node) = self.item[0:3]
        
        # Create button.
        self.item_box = gtk.Button()
        
        # Expose button.
        self.item_box.connect("expose-event", self.expose_menu_item)
        self.item_box.connect("enter-notify-event", lambda w, e: self.enter_notify_menu_item(w))
        
        # Wrap menu aciton.
        self.item_box.connect("button-press-event", self.wrap_menu_clicked_action)        
        
        self.item_box.connect("realize", lambda w: self.realize_item_box(w, item_content))
        
    def realize_item_box(self, widget, item_content):
        '''Realize item box.'''
        # Set button size.
        (width, height) = get_content_size(item_content, self.font_size)
        self.item_box_height = self.item_padding_y * 2 + max(int(height), self.icon_height)
        if self.select_scale:
            self.item_box_width = widget.get_parent().get_parent().allocation.width
        else:
            self.item_box_width = self.item_padding_x * 3 + self.icon_width + int(width)

            if self.have_submenu:
                self.item_box_width += self.item_padding_x + self.submenu_width + self.arrow_padding_x * 2
                
        self.item_box_width = max(self.item_box_width, self.min_width)        
                
        self.item_box.set_size_request(self.item_box_width, self.item_box_height)        
        
    def wrap_menu_clicked_action(self, button, event):
        '''Wrap menu action.'''
        item_node = self.item[2]
        if not isinstance(item_node, Menu):
            # Hide menu.
            menu_grab_window_focus_out()
            
            # Execute callback.
            if item_node:
                if len(self.item) > 3:
                    item_node(*self.item[3:])
                else:
                    item_node()
            
    def expose_menu_item(self, widget, event):
        '''Expose menu item.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        font_color = ui_theme.get_color("menu_font").get_color()
        (item_icons, item_content, item_node) = self.item[0:3]
        
        # Draw select effect.
        if self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menu_item_select").get_color_info(),
                         MENU_ITEM_RADIUS)
            
            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()
            
        # Draw item icon.
        pixbuf = None
        pixbuf_width = 0
        if item_icons:
            (item_normal_dpixbuf, item_hover_dpixbuf) = item_icons
            if self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
                if item_hover_dpixbuf == None:
                    pixbuf = item_normal_dpixbuf.get_pixbuf()
                else:
                    pixbuf = item_hover_dpixbuf.get_pixbuf()
            else:
                pixbuf = item_normal_dpixbuf.get_pixbuf()
            pixbuf_width += pixbuf.get_width()
            draw_pixbuf(cr, pixbuf, rect.x + self.item_padding_x, rect.y + (rect.height - pixbuf.get_height()) / 2)
            
        # Draw item content.
        draw_text(cr, item_content, 
                    rect.x + self.item_padding_x * 2 + self.icon_width,
                    rect.y,
                    rect.width,
                    rect.height,
                    self.font_size, font_color,
                    )
        
        # Draw submenu arrow.
        if isinstance(item_node, Menu):
            if self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
                submenu_pixbuf = ui_theme.get_pixbuf("menu/arrow_hover.png").get_pixbuf()
            else:
                submenu_pixbuf = ui_theme.get_pixbuf("menu/arrow_normal.png").get_pixbuf()
            draw_pixbuf(cr, submenu_pixbuf,
                        rect.x + rect.width - self.item_padding_x - submenu_pixbuf.get_width() - self.arrow_padding_x,
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
        
        (item_icons, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Menu):
            menu_window = self.item_box.get_toplevel()
            (menu_window_x, menu_window_y) = get_widget_root_coordinate(menu_window, WIDGET_POS_RIGHT_CENTER)
            (item_x, item_y) = get_widget_root_coordinate(self.item_box)
            self.show_submenu_callback(
                item_node, 
                (menu_window_x - menu_window.shadow_radius, 
                 item_y - widget.get_allocation().height - menu_window.shadow_radius),
                self.item_box.allocation.height + menu_window.shadow_radius)
            
            self.submenu_active = True
        else:
            self.hide_submenu_callback()
