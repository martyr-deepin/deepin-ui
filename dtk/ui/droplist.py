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
from draw import draw_vlinear, draw_pixbuf, draw_font, draw_hlinear
from line import HSeparator
from theme import ui_theme
from utils import is_in_rect, get_content_size, propagate_expose, get_widget_root_coordinate, get_screen_size, remove_callback_id, alpha_color_hex_to_cairo, get_window_shadow_size
import gtk
import gobject

droplist_grab_window = gtk.Window(gtk.WINDOW_POPUP)
droplist_grab_window.move(0, 0)
droplist_grab_window.set_default_size(0, 0)
droplist_grab_window.show()
droplist_active_item = None

root_droplists = []
droplist_grab_window_press_id = None
droplist_grab_window_motion_id = None

def droplist_grab_window_focus_in():
    droplist_grab_window.grab_add()
    gtk.gdk.pointer_grab(
        droplist_grab_window.window, 
        True,
        gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK,
        None, None, gtk.gdk.CURRENT_TIME)
    
def droplist_grab_window_focus_out():
    global root_droplists
    
    for root_droplist in root_droplists:
        root_droplist.hide()
    
    root_droplists = []    
    
    gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
    droplist_grab_window.grab_remove()

def is_press_on_droplist_grab_window(window):
    '''Is press on droplist grab window.'''
    for toplevel in gtk.window_list_toplevels():
        if isinstance(window, gtk.Window):
            if window == toplevel:
                return True
        elif isinstance(window, gtk.gdk.Window):
            if window == toplevel.window:
                return True
            
    return False        
    
def droplist_grab_window_button_press(widget, event):
    global droplist_grab_window_press_id
    global droplist_grab_window_motion_id    
    global droplist_active_item
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if is_press_on_droplist_grab_window(event.window):
            droplist_grab_window_focus_out()
        elif isinstance(event_widget, Droplist):
            droplist_item = event_widget.get_droplist_item_at_coordinate(event.get_root_coords())
            if droplist_item:
                droplist_item.item_box.event(event)
        else:
            event_widget.event(event)
            droplist_grab_window_focus_out()
    
    remove_callback_id(droplist_grab_window_press_id)        
    remove_callback_id(droplist_grab_window_motion_id)        
        
    if droplist_active_item:
        droplist_active_item.set_state(gtk.STATE_NORMAL)
        
def droplist_grab_window_motion(widget, event):
    global droplist_active_item
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, Droplist):
            droplist_item = event_widget.get_droplist_item_at_coordinate(event.get_root_coords())
            if droplist_item and isinstance(droplist_item.item_box, gtk.Button):
                if droplist_active_item:
                    droplist_active_item.set_state(gtk.STATE_NORMAL)
                
                droplist_item.item_box.set_state(gtk.STATE_PRELIGHT)
                droplist_active_item = droplist_item.item_box
                
                enter_notify_event = gtk.gdk.Event(gtk.gdk.ENTER_NOTIFY)
                enter_notify_event.window = event.window
                enter_notify_event.time = event.time
                enter_notify_event.send_event = True
                enter_notify_event.x_root = event.x_root
                enter_notify_event.y_root = event.y_root
                enter_notify_event.x = event.x
                enter_notify_event.y = event.y
                enter_notify_event.state = event.state
                
                droplist_item.item_box.event(enter_notify_event)
                
                droplist_item.item_box.queue_draw()

class Droplist(gtk.Window):
    '''Droplist.'''
    
    def __init__(self, items, 
                 is_root_droplist=False,
                 select_scale=False,
                 x_align=ALIGN_START,
                 y_align=ALIGN_START,
                 font_size=DEFAULT_FONT_SIZE, 
                 opacity=1.0, 
                 padding_x=3, 
                 padding_y=3, 
                 item_padding_x=6, 
                 item_padding_y=3,
                 shadow_visible=True,
                 droplist_min_width=130):
        '''Init droplist, item format: (item_icon, itemName, item_node).'''
        # Init.
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_decorated(False)
        global root_droplists
        self.is_root_droplist = is_root_droplist
        self.select_scale = select_scale
        self.x_align = x_align
        self.y_align = y_align
        self.subdroplist_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")
        self.subdroplist = None
        self.root_droplist = None
        self.offset_x = 0       # use for handle extreme situaiton, such as, droplist show at side of screen
        self.offset_y = 0
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.item_padding_x = item_padding_x
        self.item_padding_y = item_padding_y
        self.droplist_min_width = droplist_min_width
        
        # Init droplist window.
        self.set_opacity(opacity)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.connect_after("show", self.init_droplist)
        
        # Add droplist item.
        self.item_box = gtk.VBox()
        self.item_align = gtk.Alignment()
        self.item_align.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_align.add(self.item_box)
        self.add(self.item_align)
        self.droplist_items = []
        
        if items:
            (have_icon, icon_width, icon_height, have_subdroplist, subdroplist_width, subdroplist_height) = self.get_droplist_icon_info(items)
            
            for item in items:
                droplist_item = DroplistItem(
                    item, font_size, self.select_scale, self.show_subdroplist, self.hide_subdroplist, self.get_root_droplist, self.get_droplist_items,
                    have_icon, icon_width, icon_height,
                    have_subdroplist, subdroplist_width, subdroplist_height,
                    padding_x, padding_y,
                    item_padding_x, item_padding_y, self.droplist_min_width)
                self.droplist_items.append(droplist_item)
                self.item_box.pack_start(droplist_item.item_box, False, False)
                
        self.connect_after("show", self.adjust_droplist_position)        
        self.connect("expose-event", self.expose_droplist)
                
    def expose_droplist(self, widget, event):
        '''Draw mask.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, h, w = rect.x, rect.y, rect.width, rect.height

        # Draw background.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(ui_theme.get_alpha_color("menuMask").get_color_info()))
        cr.rectangle(x, y, w, h)    
        cr.fill()
        
        # Draw left side.
        draw_hlinear(cr, x + 1, y + 1, 16 + self.padding_x + self.padding_x * 2, h - 2,
                     ui_theme.get_shadow_color("menuSide").get_color_info())
        
    def get_droplist_item_at_coordinate(self, (x, y)):
        '''Get droplist item at coordinate, return None if haven't any droplist item at given coordinate.'''
        match_droplist_item = None
        for droplist_item in self.droplist_items:                
            item_rect = droplist_item.item_box.get_allocation()
            (item_x, item_y) = get_widget_root_coordinate(droplist_item.item_box, WIDGET_POS_TOP_LEFT)
            if is_in_rect((x, y), (item_x, item_y, item_rect.width, item_rect.height)):
                match_droplist_item = droplist_item
                break    
            
        return match_droplist_item
                
    def get_droplist_items(self):
        '''Get droplist items.'''
        return self.droplist_items
    
    def init_droplist(self, widget):
        '''Realize droplist.'''
        global root_droplists
        global droplist_grab_window_press_id
        global droplist_grab_window_motion_id
        
        if self.is_root_droplist:
            droplist_grab_window_focus_out()
        
        if not gtk.gdk.pointer_is_grabbed():
            droplist_grab_window_focus_in()
            droplist_grab_window_press_id = droplist_grab_window.connect("button-press-event", droplist_grab_window_button_press)
            droplist_grab_window_motion_id = droplist_grab_window.connect("motion-notify-event", droplist_grab_window_motion)
            
        if self.is_root_droplist and not self in root_droplists:
            root_droplists.append(self)
                            
    def get_subdroplists(self):
        '''Get subdroplists.'''
        if self.subdroplist:
            return [self.subdroplist] + self.subdroplist.get_subdroplists()
        else:
            return []
                
    def get_droplist_icon_info(self, items):
        '''Get droplist icon information.'''
        have_icon = False
        icon_width = 16
        icon_height = 16
        have_subdroplist = False
        subdroplist_width = 0
        subdroplist_height = 0
        
        for item in items:
            if item:
                (item_dpixbuf, item_content, item_node) = item[0:3]
                if item_dpixbuf:
                    have_icon = True
                
                if isinstance(item_node, Droplist):
                    have_subdroplist = True
                    subdroplist_width = self.subdroplist_dpixbuf.get_pixbuf().get_width()
                    subdroplist_height = self.subdroplist_dpixbuf.get_pixbuf().get_height()
                    
                if have_icon and have_subdroplist:
                    break
                
        return (have_icon, icon_width, icon_height, have_subdroplist, subdroplist_width, subdroplist_height)
        
    def show(self, (x, y), (offset_x, offset_y)=(0, 0)):
        '''Show droplist.'''
        # Init offset.
        self.expect_x = x
        self.expect_y = y
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        # Show.
        self.show_all()
        
    def adjust_droplist_position(self, widget):
        '''Realize droplist.'''
        # Adjust coordinate.
        (screen_width, screen_height) = get_screen_size(self)
        
        droplist_width = droplist_height = 0
        for droplist_item in self.droplist_items:
            if droplist_width == 0 and isinstance(droplist_item.item_box, gtk.Button):
                droplist_width = droplist_item.item_box_width
            
            droplist_height += droplist_item.item_box_height    
        (shadow_x, shadow_y) = get_window_shadow_size(self)
        droplist_width += (self.padding_x + shadow_x) * 2    
        droplist_height += (self.padding_y + shadow_y) * 2
            
        if self.x_align == ALIGN_START:
            dx = self.expect_x
        elif self.x_align == ALIGN_MIDDLE:
            dx = self.expect_x - droplist_width / 2
        else:
            dx = self.expect_x - droplist_width
            
        if self.y_align == ALIGN_START:
            dy = self.expect_y
        elif self.y_align == ALIGN_MIDDLE:
            dy = self.expect_y - droplist_height / 2
        else:
            dy = self.expect_y - droplist_height

        if self.expect_x + droplist_width > screen_width:
            dx = self.expect_x - droplist_width + self.offset_x
        if self.expect_y + droplist_height > screen_height:
            dy = self.expect_y - droplist_height + self.offset_y
            
        self.move(dx, dy)
            
    def hide(self):
        '''Hide droplist.'''
        # Hide subdroplist.
        self.hide_subdroplist()
        
        # Hide current droplist window.
        self.hide_all()
        
        # Reset.
        self.subdroplist = None
        self.root_droplist = None
        
    def show_subdroplist(self, subdroplist, coordinate):
        '''Show subdroplist.'''
        if self.subdroplist != subdroplist:
            # Hide old subdroplist first.
            self.hide_subdroplist()
            
            # Update attributes of new subdroplist.
            self.subdroplist = subdroplist
            self.subdroplist.root_droplist = self.get_root_droplist()
            
            # Show new subdroplist.
            rect = self.get_allocation()
            self.subdroplist.show(coordinate, (-rect.width + self.shadow_radius * 2, 0))
                
    def hide_subdroplist(self):
        '''Hide subdroplist.'''
        if self.subdroplist:
            # Hide subdroplist.
            self.subdroplist.hide()
            self.subdroplist = None
            
            # Reset droplist items in subdroplist.
            for droplist_item in self.droplist_items:
                droplist_item.subdroplist_active = False
            
    def get_root_droplist(self):
        '''Get root droplist.'''
        if self.root_droplist:
            return self.root_droplist
        else:
            return self
            
gobject.type_register(Droplist)

class DroplistItem(object):
    '''Droplist item.'''
    
    def __init__(self, item, font_size, 
                 select_scale,
                 show_subdroplist_callback, 
                 hide_subdroplist_callback,
                 get_root_droplist_callback,
                 get_droplist_items_callback,
                 have_icon, icon_width, icon_height, 
                 have_subdroplist, subdroplist_width, subdroplist_height,
                 droplist_padding_x, droplist_padding_y,
                 item_padding_x, item_padding_y, min_width):
        '''Init droplist item.'''
        # Init.
        self.item = item
        self.font_size = font_size
        self.select_scale = select_scale
        self.droplist_padding_x = droplist_padding_x
        self.droplist_padding_y = droplist_padding_y
        self.item_padding_x = item_padding_x
        self.item_padding_y = item_padding_y
        self.show_subdroplist_callback = show_subdroplist_callback
        self.hide_subdroplist_callback = hide_subdroplist_callback
        self.get_root_droplist_callback = get_root_droplist_callback
        self.get_droplist_items_callback = get_droplist_items_callback
        self.have_icon = have_icon
        self.icon_width = icon_width
        self.icon_height = icon_height
        self.have_subdroplist = have_subdroplist
        self.subdroplist_width = subdroplist_width
        self.subdroplist_height = subdroplist_height
        self.subdroplist_dpixbuf = ui_theme.get_pixbuf("menu/subMenu.png")        
        self.subdroplist_active = False
        self.min_width = min_width
        self.arrow_padding_x = 5

        # Create.
        if self.item:
            self.create_droplist_item()
        else:
            self.create_separator_item()
        
    def create_separator_item(self):
        '''Create separator item.'''
        self.item_box = HSeparator(
            ui_theme.get_shadow_color("hSeparator").get_color_info(),
            self.item_padding_x, 
            self.item_padding_y)
        self.item_box_height = self.item_padding_y * 2 + 1
        
    def create_droplist_item(self):
        '''Create droplist item.'''
        # Get item information.
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        
        # Create button.
        self.item_box = gtk.Button()
        
        # Expose button.
        self.item_box.connect(
            "expose-event", 
            lambda w, e: self.expose_droplist_item(
                w, e, item_dpixbuf, item_content))
        self.item_box.connect("enter-notify-event", lambda w, e: self.enter_notify_droplist_item(w))
        
        # Wrap droplist aciton.
        self.item_box.connect("button-press-event", self.wrap_droplist_clicked_action)        
        
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

            if self.have_subdroplist:
                self.item_box_width += self.item_padding_x + self.subdroplist_width + self.arrow_padding_x * 2
                
        self.item_box_width = max(self.item_box_width, self.min_width)        
                
        self.item_box.set_size_request(self.item_box_width, self.item_box_height)        
        
    def wrap_droplist_clicked_action(self, button, event):
        '''Wrap droplist action.'''
        item_node = self.item[2]
        if not isinstance(item_node, Droplist):
            # Hide droplist.
            droplist_grab_window_focus_out()
            
            # Execute callback.
            if item_node:
                if len(self.item) > 3:
                    item_node(*self.item[3:])
                else:
                    item_node()
            
    def expose_droplist_item(self, widget, event, item_dpixbuf, item_content):
        '''Expose droplist item.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        font_color = ui_theme.get_color("menuFont").get_color()
        
        # Draw select effect.
        if self.subdroplist_active or widget.state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
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
                 rect.x + self.item_padding_x * 2 + self.icon_width,
                 rect.y,
                 rect.width,
                 rect.height,
                 ALIGN_START, ALIGN_MIDDLE
                 )
        
        # Draw subdroplist arrow.
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Droplist):
            subdroplist_pixbuf = self.subdroplist_dpixbuf.get_pixbuf()
            draw_pixbuf(cr, subdroplist_pixbuf,
                        rect.x + rect.width - self.item_padding_x - subdroplist_pixbuf.get_width() - self.arrow_padding_x,
                        rect.y + (rect.height - subdroplist_pixbuf.get_height()) / 2)
        
        # Propagate expose to children.
        propagate_expose(widget, event)
    
        return True

    def enter_notify_droplist_item(self, widget):
        '''Callback for `enter-notify-event` signal.'''
        # Reset all items in same droplist.
        for droplist_item in self.get_droplist_items_callback():
            if droplist_item != self and droplist_item.subdroplist_active:
                droplist_item.subdroplist_active = False
                droplist_item.item_box.queue_draw()
        
        (item_dpixbuf, item_content, item_node) = self.item[0:3]
        if isinstance(item_node, Droplist):
            droplist_window = self.item_box.get_toplevel()
            (droplist_window_x, droplist_window_y) = get_widget_root_coordinate(droplist_window, WIDGET_POS_RIGHT_CENTER)
            (item_x, item_y) = get_widget_root_coordinate(self.item_box)
            self.show_subdroplist_callback(
                item_node, 
                (droplist_window_x - droplist_window.shadow_radius, 
                 item_y - widget.get_allocation().height - droplist_window.shadow_radius))
            
            self.subdroplist_active = True
        else:
            self.hide_subdroplist_callback()
