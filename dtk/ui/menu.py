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
from keymap import get_keyevent_name
import gobject
import gtk
from utils import (is_in_rect, get_content_size, propagate_expose,
                   get_widget_root_coordinate, get_screen_size, invisible_window,
                   alpha_color_hex_to_cairo, get_window_shadow_size)

__all__ = ["Menu", "MenuItem"]

menu_grab_window = gtk.Window(gtk.WINDOW_POPUP)
invisible_window(menu_grab_window)
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
                if menu_item.item_box.state != gtk.STATE_INSENSITIVE:
                    menu_item.item_box.event(event)
        else:
            if event_widget.state != gtk.STATE_INSENSITIVE:
                event_widget.event(event)
                menu_grab_window_focus_out()

def menu_grab_window_key_press(widget, event):
    if get_keyevent_name(event) == "Escape":
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
menu_grab_window.connect("key-press-event", menu_grab_window_key_press)
menu_grab_window.connect("motion-notify-event", menu_grab_window_motion_notify)

class Menu(Window):
    '''
    Menu.

    @undocumented: realize_menu
    @undocumented: hide_menu
    @undocumented: get_menu_item_at_coordinate
    @undocumented: get_menu_items
    @undocumented: init_menu
    @undocumented: get_submenus
    @undocumented: get_menu_icon_info
    @undocumented: adjust_menu_position
    @undocumented: show_submenu
    @undocumented: hide_submenu
    @undocumented: get_root_menu
    '''

    def __init__(self,
                 items,
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
                 menu_min_width=130,
                 menu_item_select_color=None):
        '''
        Initialize Menu class.

        @param items: A list of item, item format: ((item_normal_dpixbuf, item_hover_dpixbuf, item_disable_dpixbuf), item_name, item_node).
        @param is_root_menu: Default is False for submenu, you should set it as True if you build root menu.
        @param select_scale: Default is False, it will use parant's width if it set True.
        @param x_align: Horizontal alignment value.
        @param y_align: Vertical alignment value.
        @param font_size: Menu font size, default is DEFAULT_FONT_SIZE
        @param padding_x: Horizontal padding value, default is 3 pixel.
        @param padding_y: Vertical padding value, default is 3 pixel.
        @param item_padding_x: Horizontal item padding value, default is 6 pixel.
        @param item_padding_y: Vertical item padding value, default is 3 pixel.
        @param shadow_visible: Whether show window shadow, default is True.
        @param menu_min_width: Minimum width of menu.
        '''
        global root_menus

        # Init.
        Window.__init__(self,
                        shadow_visible=shadow_visible,
                        window_type=gtk.WINDOW_POPUP,
                        shadow_radius=6)
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
        self.menu_item_select_color = menu_item_select_color

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
        self.font_size = font_size

        if items:
            self.add_menu_items(items)

        self.connect("show", self.init_menu)
        self.connect("hide", self.hide_menu)
        self.connect("realize", self.realize_menu)

    def set_mutual_icons(self, index, icons):
        # deepin-media-player useing.
        # other no use.
        for item in self.menu_items:
            item.set_item_icons(None)
        #
        self.menu_items[index].set_item_icons(icons)

    def add_menu_items(self, items):
        (icon_width, icon_height, have_submenu, submenu_width, submenu_height) = self.get_menu_icon_info(items)

        for item in items:
            menu_item = MenuItem(
                item,
                self.font_size,
                self.select_scale,
                self.show_submenu,
                self.hide_submenu,
                self.get_root_menu,
                self.get_menu_items,
                icon_width,
                icon_height,
                have_submenu,
                submenu_width,
                submenu_height,
                self.padding_x,
                self.padding_y,
                self.item_padding_x,
                self.item_padding_y,
                self.menu_min_width,
                self.menu_item_select_color)
            self.menu_items.append(menu_item)
            self.item_box.pack_start(menu_item.item_box, False, False)

    def clear_menus(self):
        self.menu_items = []
        self.item_align.remove(self.item_box)
        self.item_box = gtk.VBox()
        self.item_align.add(self.item_box)
        self.resize(1, 1)

    def hide_menu(self, widget):
        '''
        Internal callback for `hide` signal.
        '''
        # Avoid menu (popup window) show at (0, 0) when next show.
        self.move(-1000000, -1000000)

    def realize_menu(self, widget):
        '''
        Internal callback for `realize` signal.
        '''
        # Avoid menu (popup window) show at (0, 0) first.
        self.move(-1000000, -1000000)

        # Never draw background.
        self.window.set_back_pixmap(None, False)

    def draw_menu_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.

        @param cr: Cairo context.
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        # Draw background.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("menu_mask").get_color_info()))
        cr.rectangle(x, y, w, h)
        cr.fill()

        # Draw left side.
        draw_hlinear(cr, x + 1, y + 1, 16 + self.padding_x + self.padding_x * 2, h - 2,
                     ui_theme.get_shadow_color("menu_side").get_color_info())

    def get_menu_item_at_coordinate(self, (x, y)):
        '''
        Internal function to get menu item at coordinate, return None if haven't any menu item at given coordinate.
        '''
        match_menu_item = None
        for menu_item in self.menu_items:
            item_rect = menu_item.item_box.get_allocation()
            (item_x, item_y) = get_widget_root_coordinate(menu_item.item_box, WIDGET_POS_TOP_LEFT)
            if is_in_rect((x, y), (item_x, item_y, item_rect.width, item_rect.height)):
                match_menu_item = menu_item
                break

        return match_menu_item

    def get_menu_items(self):
        '''
        Internal function to get menu items.
        '''
        return self.menu_items

    def init_menu(self, widget):
        '''
        Internal callback for `show` signal.
        '''
        global root_menus

        if self.is_root_menu:
            menu_grab_window_focus_out()

        if not gtk.gdk.pointer_is_grabbed():
            menu_grab_window_focus_in()

        if self.is_root_menu and not self in root_menus:
            root_menus.append(self)

        self.adjust_menu_position()

    def get_submenus(self):
        '''
        Internal function to get submenus.
        '''
        if self.submenu:
            return [self.submenu] + self.submenu.get_submenus()
        else:
            return []

    def get_menu_icon_info(self, items):
        '''
        Internal function to get menu icon information.
        '''
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
        '''
        Show menu with given position.

        @param x: X coordinate of menu.
        @param y: Y coordinate of menu.
        @param offset_x: Offset x when haven't enough space to show menu, default is 0.
        @param offset_y: Offset y when haven't enough space to show menu, default is 0.
        '''
        # Init offset.
        self.expect_x = x
        self.expect_y = y
        self.offset_x = offset_x
        self.offset_y = offset_y

        # Show.
        self.show_all()

    def adjust_menu_position(self):
        '''
        Internal function to realize menu position.
        '''
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
        '''
        Hide menu.
        '''
        # Hide submenu.
        self.hide_submenu()

        # Hide current menu window.
        self.hide_all()

        # Reset.
        self.submenu = None
        self.root_menu = None

    def show_submenu(self, submenu, coordinate, offset_y):
        '''
        Internal function to show submenu.
        '''
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
        '''
        Internal function to hide submenu.
        '''
        if self.submenu:
            # Hide submenu.
            self.submenu.hide()
            self.submenu = None

            # Reset menu items in submenu.
            for menu_item in self.menu_items:
                menu_item.submenu_active = False

    def get_root_menu(self):
        '''
        Internal to get root menu.
        '''
        if self.root_menu:
            return self.root_menu
        else:
            return self

    def set_menu_item_sensitive_by_index(self, index, sensitive):
        '''
        Set sensitive state of menu item with given index.

        @param index: Menu item index.
        @return: Return True if set success, else return False, index out of bound will cause return False.
        '''
        if 0 <= index < len(self.menu_items):
            self.menu_items[index].item_box.set_sensitive(sensitive)

            return True
        else:
            return False

gobject.type_register(Menu)

class MenuItem(object):
    '''
    Menu item for L{ I{Menu} <Menu>}.

    @undocumented: create_separator_item
    @undocumented: create_menu_item
    @undocumented: realize_item_box
    @undocumented: wrap_menu_clicked_action
    @undocumented: expose_menu_item
    @undocumented: enter_notify_menu_item
    '''

    def __init__(self,
                 item,
                 font_size,
                 select_scale,
                 show_submenu_callback,
                 hide_submenu_callback,
                 get_root_menu_callback,
                 get_menu_items_callback,
                 icon_width,
                 icon_height,
                 have_submenu,
                 submenu_width,
                 submenu_height,
                 menu_padding_x, menu_padding_y,
                 item_padding_x, item_padding_y, min_width,
                 menu_item_select_color=None):
        '''
        Initialize MenuItem class.

        @param item: item format: ((item_normal_dpixbuf, item_hover_dpixbuf, item_disable_dpixbuf), item_name, item_node).
        @param font_size: Menu font size.
        @param select_scale: Default is False, it will use parant's width if it set True.
        @param show_submenu_callback: Callback when show submenus.
        @param hide_submenu_callback: Callback when hide submenus.
        @param get_root_menu_callback: Callback to get root menu.
        @param get_menu_items_callback: Callback to get menu items.
        @param icon_width: Icon width.
        @param icon_height: Icon height.
        @param have_submenu: Whether have submenu.
        @param submenu_width: Width of submenu.
        @param submenu_height: Height of submenu.
        @param menu_padding_x: Horizontal padding of menu.
        @param menu_padding_y: Vertical padding of menu.
        @param item_padding_x: Horizontal padding of item.
        @param item_padding_y: Vertical padding of item.
        @param min_width: Minimum width.
        '''
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
        self.menu_item_select_color = menu_item_select_color

        # Create.
        if self.item:
            self.create_menu_item()
        else:
            self.create_separator_item()

    def set_item_icons(self, icons):
        # deepin media player modify icons.
        if self.item:
            (item_icons, item_content, item_node) = self.item[0:3]
            item_icons = icons
            if len(self.item) > 3:
                self.item = (item_icons, item_content, item_node, self.item[-1])
            else:
                self.item = (item_icons, item_content, item_node)

    def create_separator_item(self):
        '''
        Internal function to create separator item.
        '''
        self.item_box = HSeparator(
            ui_theme.get_shadow_color("h_separator").get_color_info(),
            self.item_padding_x,
            self.item_padding_y)
        self.item_box_height = self.item_padding_y * 2 + 1

    def create_menu_item(self):
        '''
        Internal function to create menu item.
        '''
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
        '''
        Internal callback for `realize` signal.
        '''
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
        '''
        Internal function to wrap clicked menu action.
        '''
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
        '''
        Internal callback for `expose` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        font_color = ui_theme.get_color("menu_font").get_color()
        (item_icons, item_content, item_node) = self.item[0:3]

        # Draw select effect.
        if widget.state == gtk.STATE_INSENSITIVE:
            # Set font color.
            font_color = ui_theme.get_color("menu_disable_font").get_color()
        elif self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            # Draw background.
            if self.menu_item_select_color:
                item_select_color = self.menu_item_select_color
            else:
                item_select_color = ui_theme.get_shadow_color("menu_item_select").get_color_info()
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height,
                         item_select_color,
                         MENU_ITEM_RADIUS)

            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()

        # Draw item icon.
        pixbuf = None
        pixbuf_width = 0
        if item_icons:
            (item_normal_dpixbuf, item_hover_dpixbuf, item_disable_dpixbuf) = item_icons
            if widget.state == gtk.STATE_INSENSITIVE:
                pixbuf = item_disable_dpixbuf.get_pixbuf()
            elif self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
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
            if widget.state == gtk.STATE_INSENSITIVE:
                submenu_pixbuf = ui_theme.get_pixbuf("menu/arrow_disable.png").get_pixbuf()
            elif self.submenu_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
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
        '''
        Internal callback for `enter-notify-event` signal.
        '''
        # Reset all items in same menu.
        for menu_item in self.get_menu_items_callback():
            if menu_item != self and menu_item.submenu_active:
                menu_item.submenu_active = False
                menu_item.item_box.queue_draw()

        (item_icons, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Menu):
            if widget.state != gtk.STATE_INSENSITIVE:
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
