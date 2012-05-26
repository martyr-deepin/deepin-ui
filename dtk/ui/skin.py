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

from dominant_color import get_dominant_color
from dialog import ConfirmDialog
import uuid
import os
import gtk
import gobject
from config import Config
from window import Window
from draw import draw_pixbuf, draw_vlinear, draw_hlinear
from mask import draw_mask
from utils import is_in_rect, set_cursor, color_hex_to_cairo, cairo_state, container_remove_all, cairo_disable_antialias, remove_directory, end_with_suffixs, create_directory, touch_file, scroll_to_bottom
from constant import SHADE_SIZE
from titlebar import Titlebar
from iconview import IconView
from scrolled_window import ScrolledWindow
from button import Button, ImageButton, ToggleButton, ActionButton
from theme import ui_theme
import math
from skin_config import skin_config
from label import Label
import urllib
import shutil

def draw_skin_mask(cr, x, y, w, h):
    '''Draw skin mask.'''
    draw_vlinear(cr, x, y, w, h,
                 ui_theme.get_shadow_color("skinWindowBackground").get_color_info())
    
class SkinWindow(Window):
    '''SkinWindow.'''
	
    def __init__(self, preview_width=450, preview_height=500):
        '''Init skin.'''
        Window.__init__(self)
        self.set_modal(True)                                # grab focus to avoid build too many skin window
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_skip_taskbar_hint(True)                    # skip taskbar
        self.set_position(gtk.WIN_POS_CENTER)
        self.draw_mask = lambda cr, x, y, w, h: draw_mask(self, x, y, w, h, draw_skin_mask)
        self.main_box = gtk.VBox()
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            "选择皮肤")
        
        self.window_frame.add(self.main_box)
        self.set_size_request(preview_width, preview_height)
        self.set_resizable(False)
        
        self.preview_page = SkinPreviewPage(
            "/home/andy/deepin-ui-private/skin",
            self.change_skin,
            self.switch_edit_page)
        
        self.main_box.pack_start(self.titlebar, False, False)
        self.body_box = gtk.VBox()
        self.main_box.pack_start(self.body_box, True, True)
        
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        
        self.add_move_event(self.titlebar)
        
        self.switch_preview_page()
        
    def change_skin(self, item):
        '''Change skin.'''
        # Load skin.
        if skin_config.load_skin(item.skin_dir):
            skin_config.apply_skin()
        
    def switch_preview_page(self):
        '''Switch preview page.'''
        container_remove_all(self.body_box)
        self.body_box.add(self.preview_page)
        self.preview_page.highlight_skin()
        
    def switch_edit_page(self):
        '''Switch edit page.'''
        # Switch to edit page.
        container_remove_all(self.body_box)
        edit_page = SkinEditPage()
        self.body_box.add(edit_page)
        
        edit_page.connect("click-save", lambda page: self.click_save_button())
        edit_page.connect("click-cancel", lambda page: self.click_cancel_button())
        
        self.show_all()
        
    def click_save_button(self):
        '''Click save button..'''
        # Save skin.
        skin_config.save_skin()
        
        # Switch to preview page.
        self.switch_preview_page()        
        
    def click_cancel_button(self):
        '''Click cancel button.'''
        # Reload skin from config file.
        if skin_config.load_skin(skin_config.skin_dir):
            skin_config.apply_skin()
        
        # Switch to preview page.
        self.switch_preview_page()        
        
gobject.type_register(SkinWindow)

class SkinPreviewPage(gtk.VBox):
    '''Skin preview.'''
	
    def __init__(self, skin_dir, change_skin_callback, switch_edit_page_callback):
        '''Init skin preview.'''
        gtk.VBox.__init__(self)
        self.skin_dir = skin_dir
        self.change_skin_callback = change_skin_callback
        self.switch_edit_page_callback = switch_edit_page_callback
        
        self.preview_align = gtk.Alignment()
        self.preview_align.set(0.5, 0.5, 1, 1)
        self.preview_align.set_padding(0, 0, 10, 5)
        self.preview_scrolled_window = ScrolledWindow()
        self.preview_scrolled_window.set_scroll_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.preview_scrolled_window.draw_mask = lambda cr, x, y, w, h: draw_mask(self.preview_scrolled_window, x, y, w, h, draw_skin_mask)
        self.preview_view = IconView()
        self.preview_view.draw_mask = lambda cr, x, y, w, h: draw_mask(self.preview_view, x, y, w, h, draw_skin_mask)
        
        self.preview_align.add(self.preview_scrolled_window)
        self.preview_scrolled_window.add_child(self.preview_view)
        self.pack_start(self.preview_align, True, True)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 0, 20)
        self.close_button = Button("关闭")
        self.close_button.connect("clicked", lambda w: w.get_toplevel().destroy())
        self.button_align.add(self.close_button)
        self.pack_start(self.button_align, False, False)
        
        for root, dirs, files in os.walk(skin_dir):
            dirs.sort()         # sort directory with alpha order
            for filename in files:
                if end_with_suffixs(filename, ["jpg", "png", "jpeg"]):
                    self.preview_view.add_items([SkinPreviewIcon(
                                root, 
                                filename, 
                                self.change_skin_callback, 
                                self.switch_edit_page_callback,
                                self.pop_delete_skin_dialog)])
                    
        self.preview_view.add_items([SkinAddIcon()])
        
        # Add drag image support.
        self.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_DROP,
            [("text/uri-list", 0, 1)],
            gtk.gdk.ACTION_COPY)

        self.connect("drag-data-received", self.drag_skin_file)
        
    def drag_skin_file(self, widget, drag_context, x, y, selection_data, info, timestamp):
        '''Drag skin file.'''
        skin_file = urllib.unquote(selection_data.get_uris()[0].split("file://")[1])                
        if end_with_suffixs(skin_file, ["jpg", "png", "jpeg"]):
            self.create_skin_from_image(skin_file)
        elif end_with_suffixs(skin_file, ["tar.gz"]):
            self.create_skin_from_package(skin_file)
        
    def create_skin_from_image(self, filepath):
        '''Create skin from image.'''
        # Init.
        skin_dir = os.path.join("/home/andy/deepin-ui-private/skin", str(uuid.uuid4()))
        skin_image_file = os.path.basename(filepath)
        config_file = os.path.join(skin_dir, "config.ini")
        dominant_color = get_dominant_color(filepath)
        default_config = {
            "name" : {"ui_theme_name" : "default",
                      "app_theme_name" : "default"},
            "application" : {"app_id" : "demo",
                             "app_version" : "0.1"},
            "background" : {"image" : skin_image_file,
                            "x" : "0",
                            "y" : "0",
                            "scale_x" : "1.0",
                            "scale_y" : "1.0",
                            "dominant_color" : dominant_color},
            "action" : {"deletable" : "True",
                        "editable" : "True",
                        "vertical_mirror" : "False",
                        "horizontal_mirror" : "False"}}
        
        # Create skin directory.
        create_directory(skin_dir, True)
        
        # Copy skin image file.
        shutil.copy(filepath, skin_dir)        
        
        # Touch skin config file.
        touch_file(config_file)
        
        # Write default skin config information.
        Config(config_file, default_config).write()
        
        # Apply new skin.
        self.preview_view.add_items([SkinPreviewIcon(
                    skin_dir,
                    skin_image_file,
                    self.change_skin_callback,
                    self.switch_edit_page_callback,
                    self.pop_delete_skin_dialog
                    )], -1)
        if skin_config.load_skin(skin_dir):
            skin_config.apply_skin()
            
        self.highlight_skin()    
        
        # Scroll scrollbar to bottom.
        scroll_to_bottom(self.preview_scrolled_window)            
        
    def create_skin_from_package(self, filepath):
        '''Create skin from package.'''
        pass
                    
    def highlight_skin(self):
        '''Highlight skin.'''
        # Highlight skin.
        for item in self.preview_view.items:
            if item.skin_dir == skin_config.skin_dir:
                self.preview_view.clear_highlight()
                self.preview_view.set_highlight(item)
                break
            
    def pop_delete_skin_dialog(self, item):
        '''Pop delete skin dialog.'''
        ConfirmDialog(
            "删除主题",
            "你确定要删除当前主题吗？",
            200, 
            100,
            lambda : self.remove_skin(item)).show_all()
            
    def remove_skin(self, item):
        '''Remove skin.'''
        if len(self.preview_view.items) > 1:
            # Change to first theme if delete current theme.
            if item.skin_dir == skin_config.skin_dir:
                print self.preview_view.items[0].skin_dir
                if skin_config.load_skin(self.preview_view.items[0].skin_dir):
                    skin_config.apply_skin()
                        
            # Remove skin directory.
            remove_directory(item.skin_dir)
            
            # Remove item from icon view.
            self.preview_view.delete_items([item])
        else:
            print "You can't delete last skin to make application can't use any skin! :)"
        
gobject.type_register(SkinPreviewPage)
        
class SkinPreviewIcon(gobject.GObject):
    '''Icon item.'''
    
    BUTTON_HIDE = 0
    BUTTON_NORMAL = 1
    BUTTON_HOVER = 2
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, 
                 skin_dir, 
                 background_file, 
                 change_skin_callback,
                 switch_edit_page_callback,
                 pop_delete_skin_dialog_callback):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.skin_dir = skin_dir
        self.background_file = background_file
        self.change_skin_callback = change_skin_callback
        self.switch_edit_page_callback = switch_edit_page_callback
        self.pop_delete_skin_dialog_callback = pop_delete_skin_dialog_callback
        self.background_path = os.path.join(skin_dir, background_file)
        self.width = 86
        self.height = 56
        self.icon_padding = 2
        self.padding_x = 7
        self.padding_y = 10
        self.hover_flag = False
        self.highlight_flag = False
        self.delete_button_status = self.BUTTON_HIDE
        self.edit_button_status = self.BUTTON_HIDE
        
        self.create_preview_pixbuf(self.background_path)
        
        # Load skin config information.
        self.config = Config(os.path.join(self.skin_dir, "config.ini"))
        self.config.load()
        
    def is_in_delete_button_area(self, x, y):
        '''Is cursor in delete button area.'''
        delete_pixbuf = ui_theme.get_pixbuf("skin/delete_normal.png").get_pixbuf()
        
        return is_in_rect((x, y), 
                          (self.get_width() - delete_pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3,
                           (self.icon_padding + self.padding_x) + 4, 
                           delete_pixbuf.get_width(),
                           delete_pixbuf.get_height()))
    
    def is_in_edit_button_area(self, x, y):
        '''Is cursor in edit button area.'''
        edit_pixbuf = ui_theme.get_pixbuf("skin/edit_normal.png").get_pixbuf()
        
        return is_in_rect((x, y), 
                          (self.get_width() - edit_pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3,
                           self.get_height() - edit_pixbuf.get_height() - (self.icon_padding + self.padding_x) - 4, 
                           edit_pixbuf.get_width(),
                           edit_pixbuf.get_height()))
    
    def is_deletable(self):
        '''Is deletable.'''
        return self.config.getboolean("action", "deletable")
    
    def is_editable(self):
        '''Is editable.'''
        return self.config.getboolean("action", "editable")    
        
    def create_preview_pixbuf(self, background_path):
        '''Create preview pixbuf.'''
        background_pixbuf = gtk.gdk.pixbuf_new_from_file(background_path)        
        background_width, background_height = background_pixbuf.get_width(), background_pixbuf.get_height()
        if background_width >= self.width and background_height >= self.height:
            if background_width / background_height == self.width / self.height:
                scale_width, scale_height = self.width, self.height
            elif background_width / background_height > self.width / self.height:
                scale_height = self.height
                scale_width = int(background_width * self.height / background_height)
            else:
                scale_width = self.width
                scale_height = int(background_height * self.width / background_width)
                
            self.pixbuf = background_pixbuf.scale_simple(
                scale_width, 
                scale_height, 
                gtk.gdk.INTERP_BILINEAR).subpixbuf(0, 0, self.width, self.height)
        else:
            self.pixbuf = background_pixbuf
            
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.width + (self.icon_padding + self.padding_x) * 2
        
    def get_height(self):
        '''Get height.'''
        return self.height + (self.icon_padding + self.padding_y) * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Draw frame.
        if self.hover_flag:
            pixbuf = ui_theme.get_pixbuf("skin/preview_hover.png").get_pixbuf()
        elif self.highlight_flag:
            pixbuf = ui_theme.get_pixbuf("skin/preview_highlight.png").get_pixbuf()
        else:
            pixbuf = ui_theme.get_pixbuf("skin/preview_normal.png").get_pixbuf()
        draw_pixbuf(
            cr,
            pixbuf,
            rect.x + self.padding_x,
            rect.y + self.padding_y)    
        
        # Draw background.
        with cairo_state(cr):
            # Mirror image if necessarily.
            preview_config = Config(os.path.join(self.skin_dir, "config.ini"))    
            preview_config.load()
            
            pixbuf = self.pixbuf.copy()
            if preview_config.getboolean("action", "vertical_mirror"):
                pixbuf = pixbuf.flip(True)
            
            if preview_config.getboolean("action", "horizontal_mirror"):
                pixbuf = pixbuf.flip(False)
                
            # Draw cover.
            draw_pixbuf(
                cr, 
                pixbuf,
                rect.x + (rect.width - self.pixbuf.get_width()) / 2,
                rect.y + (rect.height - self.pixbuf.get_height()) / 2
                )
            
        # Draw delete button.
        if self.delete_button_status != self.BUTTON_HIDE:
            if self.delete_button_status == self.BUTTON_NORMAL:
                pixbuf = ui_theme.get_pixbuf("skin/delete_normal.png").get_pixbuf()
            elif self.delete_button_status == self.BUTTON_HOVER:
                pixbuf = ui_theme.get_pixbuf("skin/delete_hover.png").get_pixbuf()
            
            delete_button_x = rect.x + rect.width - pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3
            delete_button_y = rect.y + (self.icon_padding + self.padding_x) + 4
            
            draw_pixbuf(cr, pixbuf, delete_button_x, delete_button_y)
            
        # Draw edit button.
        if self.edit_button_status != self.BUTTON_HIDE:
            if self.edit_button_status == self.BUTTON_NORMAL:
                pixbuf = ui_theme.get_pixbuf("skin/edit_normal.png").get_pixbuf()
            elif self.edit_button_status == self.BUTTON_HOVER:
                pixbuf = ui_theme.get_pixbuf("skin/edit_hover.png").get_pixbuf()
            
            edit_button_x = rect.x + rect.width - pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3
            edit_button_y = rect.y + rect.height - pixbuf.get_height() - (self.icon_padding + self.padding_x) - 4
            
            draw_pixbuf(cr, pixbuf, edit_button_x, edit_button_y)
            
    def icon_item_motion_notify(self, x, y):
        '''Handle `motion-notify-event` signal.'''
        self.hover_flag = True
        
        if self.is_deletable():
            if self.is_in_delete_button_area(x, y):
                self.delete_button_status = self.BUTTON_HOVER
            else:
                self.delete_button_status = self.BUTTON_NORMAL
        else:
            self.delete_button_status = self.BUTTON_HIDE
            
        if self.is_editable():
            if self.is_in_edit_button_area(x, y):
                self.edit_button_status = self.BUTTON_HOVER
            else:
                self.edit_button_status = self.BUTTON_NORMAL
        else:
            self.edit_button_status = self.BUTTON_HIDE
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''Lost focus.'''
        self.hover_flag = False
        self.delete_button_status = self.BUTTON_HIDE
        self.edit_button_status = self.BUTTON_HIDE
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''Highlight item.'''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''Set item with normal status.'''
        self.highlight_flag = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''Handle button-press event.'''
        if not self.is_deletable() and not self.is_editable():
            self.change_skin_callback(self)    
        else:
            if self.is_deletable() and self.is_in_delete_button_area(x, y):
                self.delete_button_status = self.BUTTON_HIDE
                
                # Pop delete dialog.
                self.pop_delete_skin_dialog_callback(self)
            elif self.is_editable() and self.is_in_edit_button_area(x, y):
                self.edit_button_status = self.BUTTON_HIDE
                
                self.change_skin_callback(self)
                self.switch_edit_page_callback()
            else:
                self.change_skin_callback(self)
            
        self.emit_redraw_request()    
    
    def icon_item_button_release(self, x, y):
        '''Handle button-release event.'''
        if self.is_deletable():
            if self.is_in_delete_button_area(x, y):
                self.delete_button_status = self.BUTTON_HOVER
            else:
                self.delete_button_status = self.BUTTON_NORMAL
                
        if self.is_editable():
            if self.is_in_edit_button_area(x, y):
                self.edit_button_status = self.BUTTON_HOVER
            else:
                self.edit_button_status = self.BUTTON_NORMAL
            
        self.emit_redraw_request()    
    
    def icon_item_single_click(self, x, y):
        '''Handle single click event.'''
        pass

    def icon_item_double_click(self, x, y):
        '''Handle double click event.'''
        pass
    
gobject.type_register(SkinPreviewIcon)

class SkinAddIcon(gobject.GObject):
    '''Icon item.'''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.width = 86
        self.height = 56
        self.icon_padding = 2
        self.padding_x = 7
        self.padding_y = 10
        self.hover_flag = False
        self.highlight_flag = False
        
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.width + (self.icon_padding + self.padding_x) * 2
        
    def get_height(self):
        '''Get height.'''
        return self.height + (self.icon_padding + self.padding_y) * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Draw frame.
        if self.hover_flag:
            pixbuf = ui_theme.get_pixbuf("skin/preview_hover.png").get_pixbuf()
        elif self.highlight_flag:
            pixbuf = ui_theme.get_pixbuf("skin/preview_highlight.png").get_pixbuf()
        else:
            pixbuf = ui_theme.get_pixbuf("skin/preview_normal.png").get_pixbuf()
        draw_pixbuf(
            cr,
            pixbuf,
            rect.x + self.padding_x,
            rect.y + self.padding_y)    
        
        # Draw background.
        with cairo_state(cr):
            pixbuf = ui_theme.get_pixbuf("skin/add.png").get_pixbuf()
            # Draw cover.
            draw_pixbuf(
                cr, 
                pixbuf,
                rect.x + (rect.width - pixbuf.get_width()) / 2,
                rect.y + (rect.height - pixbuf.get_height()) / 2
                )
        
    def icon_item_motion_notify(self, x, y):
        '''Handle `motion-notify-event` signal.'''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''Lost focus.'''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''Highlight item.'''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''Set item with normal status.'''
        self.highlight_flag = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''Handle button-press event.'''
        pass        
    
    def icon_item_button_release(self, x, y):
        '''Handle button-release event.'''
        pass
    
    def icon_item_single_click(self, x, y):
        '''Handle single click event.'''
        pass

    def icon_item_double_click(self, x, y):
        '''Handle double click event.'''
        pass
        
gobject.type_register(SkinAddIcon)

class SkinEditPage(gtk.VBox):
    '''Init skin edit page.'''
	
    __gsignals__ = {
        "click-save" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "click-cancel" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self):
        '''Init skin edit page.'''
        gtk.VBox.__init__(self)
        self.edit_area_align = gtk.Alignment()
        self.edit_area_align.set(0.5, 0.5, 1, 1)
        self.edit_area_align.set_padding(5, 0, 30, 30)
        self.edit_area = SkinEditArea()        
        self.edit_area_align.add(self.edit_area)
        
        self.action_align = gtk.Alignment()
        self.action_align.set(0.5, 0.5, 1, 1)
        self.action_align.set_padding(5, 5, 30, 30)
        self.action_box = gtk.HBox()
        self.action_left_align = gtk.Alignment()
        self.action_left_align.set(0.0, 0.5, 0, 0)
        self.action_right_align = gtk.Alignment()
        self.action_right_align.set(1.0, 0.5, 0, 0)
        self.action_left_box = gtk.HBox()
        self.action_left_box.set_size_request(-1, 20)
        self.action_right_box = gtk.HBox()
        self.action_right_box.set_size_request(-1, 20)
        self.action_align.add(self.action_box)
        self.action_box.pack_start(self.action_left_align, True, True)
        self.action_box.pack_start(self.action_right_align, False, False)
        self.action_left_align.add(self.action_left_box)
        self.action_right_align.add(self.action_right_box)
        
        # Default display auto resize status when image is 1:1 status.
        if skin_config.scale_x == 1.0 and skin_config.scale_y == 1.0:
            action_index = 1
        # Otherwise default display 1:1 status.
        else:
            action_index = 0
        self.resize_button = ActionButton(
            [((ui_theme.get_pixbuf("skin/reset_normal.png"),
                        ui_theme.get_pixbuf("skin/reset_hover.png"),
                        ui_theme.get_pixbuf("skin/reset_press.png")),
              lambda w: self.edit_area.click_reset_button()),
             ((ui_theme.get_pixbuf("skin/auto_resize_normal.png"),
                        ui_theme.get_pixbuf("skin/auto_resize_hover.png"),
                        ui_theme.get_pixbuf("skin/auto_resize_press.png")),
              lambda w: self.edit_area.click_auto_resize_button())],
            action_index
            )
        self.v_split_button = ImageButton(
            ui_theme.get_pixbuf("skin/v_split_normal.png"),
            ui_theme.get_pixbuf("skin/v_split_hover.png"),
            ui_theme.get_pixbuf("skin/v_split_press.png"),
            )
        self.h_split_button = ImageButton(
            ui_theme.get_pixbuf("skin/h_split_normal.png"),
            ui_theme.get_pixbuf("skin/h_split_hover.png"),
            ui_theme.get_pixbuf("skin/h_split_press.png"),
            )
        self.lock_button = ToggleButton(
            ui_theme.get_pixbuf("skin/lock_normal.png"),
            ui_theme.get_pixbuf("skin/lock_press.png"),
            ui_theme.get_pixbuf("skin/lock_hover.png"),
            ui_theme.get_pixbuf("skin/lock_press.png"),
            )
        self.lock_button.connect("toggled", self.edit_area.update_lock_status)
        self.lock_button.set_active(True)
        self.action_left_box.pack_start(self.resize_button)
        self.action_left_box.pack_start(self.v_split_button)
        self.action_left_box.pack_start(self.h_split_button)
        self.action_left_box.pack_start(self.lock_button)
        
        self.export_button = ImageButton(
            ui_theme.get_pixbuf("skin/export_normal.png"),
            ui_theme.get_pixbuf("skin/export_hover.png"),
            ui_theme.get_pixbuf("skin/export_press.png"),
            )
        self.action_right_box.pack_start(self.export_button)
        
        self.v_split_button.connect("clicked", lambda w: skin_config.vertical_mirror_background())
        self.h_split_button.connect("clicked", lambda w: skin_config.horizontal_mirror_background())
        
        self.color_label_align = gtk.Alignment()
        self.color_label_align.set(0.0, 0.5, 0, 0)
        self.color_label_align.set_padding(0, 0, 20, 0)
        self.color_label = Label("配色选择", ui_theme.get_color("skinTitle"), 11)
        self.color_label.set_size_request(100, 30)
        self.color_label_align.add(self.color_label)
        
        self.color_select_align = gtk.Alignment()
        self.color_select_align.set(0.5, 0.5, 1, 1)
        self.color_select_align.set_padding(0, 0, 32, 32)
        self.color_select_view = IconView()
        self.color_select_view.draw_mask = lambda cr, x, y, w, h: draw_mask(self.color_select_view, x, y, w, h, draw_skin_mask)
        self.color_select_scrolled_window = ScrolledWindow()
        self.color_select_scrolled_window.set_scroll_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        self.color_select_scrolled_window.add_child(self.color_select_view)
        self.color_select_align.add(self.color_select_scrolled_window)
        
        for color in [
            "#FF0000",
            "#FF6C00",
            "#FFC600",
            "#FCFF00",
            "#C0FF00",
            "#00FF60",
            "#333333",
            "#FF00B4",
            "#BA00FF",
            "#8400FF",
            "#0006FF",
            "#00A8FF",
            "#00FDFF",
            ]:
            self.color_select_view.add_items([ColorIconItem(color)])
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 0, 20)
        self.button_box = gtk.HBox()
        self.save_button = Button("保存")
        self.cancel_button = Button("取消")
        self.button_align.add(self.button_box)
        self.button_box.pack_start(self.save_button, False, False, 10)
        self.button_box.pack_start(self.cancel_button)
        
        self.pack_start(self.edit_area_align, False, False)
        self.pack_start(self.action_align, False, False)
        self.pack_start(self.color_label_align, True, True)
        self.pack_start(self.color_select_align, True, True)
        self.pack_start(self.button_align, False, False)
        
        self.save_button.connect("clicked", lambda w: self.emit("click-save"))
        self.cancel_button.connect("clicked", lambda w: self.emit("click-cancel"))
        
gobject.type_register(SkinEditPage)

class ColorIconItem(gobject.GObject):
    '''Icon item.'''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, color):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.color = color
        self.width = 42
        self.height = 27
        self.padding_x = 6
        self.padding_y = 6
        self.hover_flag = False
        self.highlight_flag = False
        
    def emit_redraw_request(self):
        '''Emit redraw-request signal.'''
        self.emit("redraw-request")
        
    def get_width(self):
        '''Get width.'''
        return self.width + self.padding_x * 2
        
    def get_height(self):
        '''Get height.'''
        return self.height + self.padding_y * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        # Init.
        draw_x = rect.x + self.padding_x
        draw_y = rect.y + self.padding_y
        
        # Draw color area.
        draw_pixbuf(
            cr,
            ui_theme.get_pixbuf("skin/%s.png" % (self.color)).get_pixbuf(),
            draw_x,
            draw_y)
        
        # Draw select effect.
        if self.hover_flag:
            draw_pixbuf(
                cr,
                ui_theme.get_pixbuf("skin/color_frame_hover.png").get_pixbuf(),
                draw_x,
                draw_y)
        elif self.highlight_flag:
            draw_pixbuf(
                cr,
                ui_theme.get_pixbuf("skin/color_frame_highlight.png").get_pixbuf(),
                draw_x,
                draw_y)
            
        # draw_font(cr, self.color, 6, "#000000", draw_x, draw_y, rect.width, rect.height)
        
    def icon_item_motion_notify(self, x, y):
        '''Handle `motion-notify-event` signal.'''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''Lost focus.'''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''Highlight item.'''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''Set item with normal status.'''
        self.highlight_flag = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''Handle button-press event.'''
        pass        
    
    def icon_item_button_release(self, x, y):
        '''Handle button-release event.'''
        pass
    
    def icon_item_single_click(self, x, y):
        '''Handle single click event.'''
        pass

    def icon_item_double_click(self, x, y):
        '''Handle double click event.'''
        pass
    
gobject.type_register(ColorIconItem)

class SkinEditArea(gtk.EventBox):
    '''Skin edit area.'''
	
    POSITION_LEFT_SIDE = 0
    POSITION_RIGHT_SIDE = 1
    POSITION_TOP_SIDE = 2
    POSITION_BOTTOM_SIDE = 3
    POSITION_TOP_LEFT_CORNER = 4
    POSITION_TOP_RIGHT_CORNER = 5
    POSITION_BOTTOM_LEFT_CORNER = 6
    POSITION_BOTTOM_RIGHT_CORNER = 7
    POSITION_INSIDE = 8
    POSITION_OUTSIDE = 9
    
    def __init__(self):
        '''Init skin edit area.'''
        gtk.EventBox.__init__(self)
        self.set_has_window(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        
        self.preview_pixbuf = ui_theme.get_pixbuf("frame.png").get_pixbuf()
        self.preview_frame_width = 390
        self.preview_frame_height = 270
        self.app_window_width = skin_config.app_window_width
        self.app_window_height = skin_config.app_window_height
        self.preview_pixbuf_width = self.preview_pixbuf.get_width()
        self.preview_pixbuf_height = self.preview_pixbuf.get_height()
        self.padding_x = (self.preview_frame_width - self.preview_pixbuf_width) / 2
        self.padding_y = (self.preview_frame_height - self.preview_pixbuf_height) / 2
        self.set_size_request(self.preview_frame_width, self.preview_frame_height)
        
        # Load config from skin_config.
        self.background_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(skin_config.skin_dir, skin_config.image))
        self.background_preview_width = int(self.eval_scale(self.background_pixbuf.get_width()))
        self.background_preview_height = int(self.eval_scale(self.background_pixbuf.get_height()))
        self.dominant_color = skin_config.dominant_color
        
        # Update skin config.
        self.update_skin_config()
        
        self.resize_pointer_size = 8
        self.resize_frame_size = 2
        self.shadow_radius = 6
        self.frame_radius = 2
        self.shadow_padding = self.shadow_radius - self.frame_radius
        self.shadow_size = int(self.eval_scale(SHADE_SIZE))
        self.min_resize_width = self.min_resize_height = self.shadow_size
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_background_x = 0
        self.drag_background_y = 0
        
        self.action_type = None
        self.button_press_flag = False
        self.button_release_flag = True
        self.resize_frame_flag = False
        self.in_resize_area_flag = False
        self.lock_flag = True
        
        self.connect("expose-event", self.expose_skin_edit_area)
        self.connect("button-press-event", self.button_press_skin_edit_area)
        self.connect("button-release-event", self.button_release_skin_edit_area)
        self.connect("motion-notify-event", self.motion_skin_edit_area)
        self.connect("leave-notify-event", self.leave_notify_skin_edit_area)
        
    def eval_scale(self, value):
        '''Eval scale.'''
        return value * self.preview_pixbuf_width / self.app_window_width
        
    def expose_skin_edit_area(self, widget, event):
        '''Expose edit area.'''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        resize_x = int(self.resize_x)
        resize_y = int(self.resize_y)
        
        with cairo_state(cr):
            cr.rectangle(x, y, w, h)
            cr.clip()
            
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(x, y, w, h)
            cr.fill()

            if self.button_release_flag:
                offset_x = x + self.padding_x
                offset_y = y + self.padding_y
                
                # Draw dominant color.
                cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))        
                cr.rectangle(
                    offset_x + resize_x,
                    offset_y + resize_y,
                    w - self.padding_x - resize_x,
                    h - self.padding_y - resize_y)
                cr.fill()
                
            # Draw background.
            pixbuf = self.background_pixbuf.scale_simple(
                self.resize_width,
                self.resize_height,
                gtk.gdk.INTERP_BILINEAR)
            
            if skin_config.vertical_mirror:
                pixbuf = pixbuf.flip(True)
                
            if skin_config.horizontal_mirror:
                pixbuf = pixbuf.flip(False)
            
            draw_pixbuf(
                cr, 
                pixbuf,
                x + self.padding_x + resize_x,
                y + self.padding_y + resize_y)
            
            # Draw dominant shadow color.
            if self.button_release_flag:
                offset_x = x + self.padding_x
                offset_y = y + self.padding_y
                background_area_width = self.resize_width + resize_x
                background_area_height = self.resize_height + resize_y
                draw_hlinear(
                    cr, 
                    offset_x + background_area_width - self.shadow_size,
                    offset_y + resize_y,
                    self.shadow_size,
                    background_area_height - resize_y,
                    [(0, (self.dominant_color, 0)),
                     (1, (self.dominant_color, 1))])
                
                draw_vlinear(
                    cr, 
                    offset_x + resize_x,
                    offset_y + background_area_height - self.shadow_size,
                    background_area_width - resize_x,
                    self.shadow_size,
                    [(0, (self.dominant_color, 0)),
                     (1, (self.dominant_color, 1))]
                    )
                
            # Draw window.
            draw_pixbuf(
                cr,
                self.preview_pixbuf,
                x + self.padding_x,
                y + self.padding_y)    
            
            if self.in_resize_area_flag:
                resize_x = x + self.padding_x + resize_x
                resize_y = y + self.padding_y + resize_y
                
                # Draw resize frame.
                cr.set_source_rgb(0, 1, 1)
                
                # Resize frame.
                cr.rectangle(           # top
                    resize_x, 
                    resize_y - self.resize_frame_size / 2,
                    self.resize_width,
                    self.resize_frame_size)
                cr.rectangle(           # bottom
                    resize_x,
                    resize_y + self.resize_height - self.resize_frame_size / 2,
                    self.resize_width,
                    self.resize_frame_size)
                cr.rectangle(           # left
                    resize_x - self.resize_frame_size / 2,
                    resize_y,
                    self.resize_frame_size,
                    self.resize_height)
                cr.rectangle(           # right
                    resize_x + self.resize_width - self.resize_frame_size / 2,
                    resize_y,
                    self.resize_frame_size,
                    self.resize_height)
                
                # Resize pointer.
                cr.arc(           # top-left
                    resize_x,
                    resize_y,
                    self.resize_pointer_size / 2,
                    0,
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # top-center
                    resize_x + self.resize_width / 2,
                    resize_y,
                    self.resize_pointer_size / 2,
                    0,
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # top-right
                    resize_x + self.resize_width,
                    resize_y,
                    self.resize_pointer_size / 2,
                    0,
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # bottom-left
                    resize_x,
                    resize_y + self.resize_height,
                    self.resize_pointer_size / 2,
                    0, 
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # bottom-center
                    resize_x + self.resize_width / 2,
                    resize_y + self.resize_height,
                    self.resize_pointer_size / 2,
                    0,
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # bottom-right
                    resize_x + self.resize_width,
                    resize_y + self.resize_height,
                    self.resize_pointer_size / 2,
                    0, 
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # left-center
                    resize_x,
                    resize_y + self.resize_height / 2,
                    self.resize_pointer_size / 2,
                    0,
                    2 * math.pi)
                cr.fill()
                
                cr.arc(           # right-center
                    resize_x + self.resize_width,
                    resize_y + self.resize_height / 2,
                    self.resize_pointer_size / 2,
                    0, 
                    2 * math.pi)
                cr.fill()
            
            # Draw preview frame.
            with cairo_disable_antialias(cr):
                cr.set_source_rgb(*color_hex_to_cairo("#CCCCCC"))
                cr.rectangle(x, y, w, h)
                cr.stroke()
            
    def button_press_skin_edit_area(self, widget, event):
        '''Callback for `button-press-event`'''
        self.button_press_flag = True
        self.button_release_flag = False
        self.action_type = self.skin_edit_area_get_action_type(event)
        self.skin_edit_area_set_cursor(self.action_type)
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.drag_background_x = self.resize_x
        self.drag_background_y = self.resize_y
    
    def button_release_skin_edit_area(self, widget, event):
        '''Callback for `button-release-event`.'''
        # Init.
        rect = widget.allocation
        
        # Update status.
        self.button_press_flag = False
        self.button_release_flag = True
        self.action_type = None
        
        # Update cursor.
        if is_in_rect((event.x, event.y), (0, 0, rect.width, rect.height)):
            self.skin_edit_area_set_cursor(self.skin_edit_area_get_action_type(event))
        else:
            self.skin_edit_area_set_cursor(None)
    
        # Change skin.
        skin_config.update_image_size(
            self.resize_x * self.background_preview_width * self.app_window_width / self.preview_pixbuf_width / self.resize_width,
            self.resize_y * self.background_preview_height * self.app_window_width / self.preview_pixbuf_width / self.resize_height,
            self.resize_width / float(self.background_preview_width),
            self.resize_height / float(self.background_preview_height)
            )
        
        # Update in_resize_area_flag.
        self.in_resize_area_flag = self.is_in_resize_area(event)
        
        # Apply skin.
        skin_config.apply_skin()
    
    def leave_notify_skin_edit_area(self, widget, event):
        '''Callback for `leave-notify-event` signal.'''
        if not self.button_press_flag:
            self.in_resize_area_flag = False        
        
            self.queue_draw()
        
    def motion_skin_edit_area(self, widget, event):
        '''Callback for `motion-notify-event`.'''
        if self.button_press_flag:
            if self.action_type != None:
                if self.action_type == self.POSITION_INSIDE:
                    self.skin_edit_area_drag_background(event)
                elif self.action_type == self.POSITION_TOP_LEFT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_TOP_RIGHT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_LEFT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_TOP_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_BOTTOM_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_LEFT_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
                elif self.action_type == self.POSITION_RIGHT_SIDE:
                    self.skin_edit_area_resize(self.action_type, event)
        else:
            self.skin_edit_area_set_cursor(self.skin_edit_area_get_action_type(event))

            if not self.button_press_flag:
                old_flag = self.in_resize_area_flag
                self.in_resize_area_flag = self.is_in_resize_area(event)
                if old_flag != self.in_resize_area_flag:
                    self.queue_draw()
    
    def skin_edit_area_set_cursor(self, action_type):
        '''Set cursor.'''
        if action_type == self.POSITION_INSIDE:
            set_cursor(self, gtk.gdk.FLEUR)
        elif action_type == self.POSITION_TOP_LEFT_CORNER:
            set_cursor(self, gtk.gdk.TOP_LEFT_CORNER)
        elif action_type == self.POSITION_TOP_RIGHT_CORNER:
            set_cursor(self, gtk.gdk.TOP_RIGHT_CORNER)
        elif action_type == self.POSITION_BOTTOM_LEFT_CORNER:
            set_cursor(self, gtk.gdk.BOTTOM_LEFT_CORNER)
        elif action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
            set_cursor(self, gtk.gdk.BOTTOM_RIGHT_CORNER)
        elif action_type == self.POSITION_TOP_SIDE:
            set_cursor(self, gtk.gdk.TOP_SIDE)
        elif action_type == self.POSITION_BOTTOM_SIDE:
            set_cursor(self, gtk.gdk.BOTTOM_SIDE)
        elif action_type == self.POSITION_LEFT_SIDE:
            set_cursor(self, gtk.gdk.LEFT_SIDE)
        elif action_type == self.POSITION_RIGHT_SIDE:
            set_cursor(self, gtk.gdk.RIGHT_SIDE)
        else:
            set_cursor(self, None)
            
    def skin_edit_area_get_action_type(self, event):
        '''Get action type.'''
        ex, ey = event.x, event.y
        resize_x = self.padding_x + self.shadow_padding + self.resize_x
        resize_y = self.padding_y + self.shadow_padding + self.resize_y
        
        if is_in_rect((ex, ey), 
                      (resize_x - self.resize_pointer_size / 2,
                       resize_y - self.resize_pointer_size / 2,
                       self.resize_pointer_size,
                       self.resize_pointer_size)):
            return self.POSITION_TOP_LEFT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y - self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_TOP_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_TOP_RIGHT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x - self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_LEFT_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_RIGHT_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x - self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_LEFT_CORNER
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_SIDE
        elif is_in_rect((ex, ey), 
                        (resize_x + self.resize_width - self.resize_pointer_size / 2,
                         resize_y + self.resize_height - self.resize_pointer_size / 2,
                         self.resize_pointer_size,
                         self.resize_pointer_size)):
            return self.POSITION_BOTTOM_RIGHT_CORNER
        elif is_in_rect((ex, ey),
                        (resize_x + self.resize_pointer_size / 2,
                         resize_y + self.resize_pointer_size / 2,
                         self.resize_width - self.resize_pointer_size,
                         self.resize_height - self.resize_pointer_size)):
            return self.POSITION_INSIDE
        else:
            return self.POSITION_OUTSIDE
        
    def is_in_resize_area(self, event):
        '''Is at resize area.'''
        offset_x = self.padding_x + self.shadow_padding
        offset_y = self.padding_y + self.shadow_padding
        return is_in_rect(
            (event.x, event.y),
            (self.resize_x + offset_x - self.resize_pointer_size / 2,
             self.resize_y + offset_y - self.resize_pointer_size / 2, 
             self.resize_width + self.resize_pointer_size, 
             self.resize_height + self.resize_pointer_size))        
        
    def skin_edit_area_resize(self, action_type, event):
        '''Resize.'''
        if action_type == self.POSITION_LEFT_SIDE:
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_SIDE:
            self.skin_edit_area_adjust_top(event)
            self.queue_draw()
        elif action_type == self.POSITION_RIGHT_SIDE:
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_SIDE:
            self.skin_edit_area_adjust_bottom(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_LEFT_CORNER:
            self.skin_edit_area_adjust_top(event)
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_TOP_RIGHT_CORNER:
            self.skin_edit_area_adjust_top(event)
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_LEFT_CORNER:
            self.skin_edit_area_adjust_bottom(event)
            self.skin_edit_area_adjust_left(event)
            self.queue_draw()
        elif action_type == self.POSITION_BOTTOM_RIGHT_CORNER:
            self.skin_edit_area_adjust_bottom(event)
            self.skin_edit_area_adjust_right(event)
            self.queue_draw()
            
    def skin_edit_area_adjust_left(self, event):
        '''Adjust left.'''
        offset_x = self.padding_x + self.shadow_padding
        if self.lock_flag:
            new_resize_x = min(int(event.x) - offset_x, 0)
            new_resize_width = int(self.resize_width + self.resize_x - new_resize_x)
            new_resize_height = int(new_resize_width * self.background_pixbuf.get_height() / self.background_pixbuf.get_width())
            
            if self.resize_height + self.resize_y - new_resize_height > 0:
                self.resize_height += int(self.resize_y)
                self.resize_y = 0
                new_resize_width = int(self.resize_height * self.background_pixbuf.get_width() / self.background_pixbuf.get_height())
                self.resize_x = int(self.resize_width + self.resize_x - new_resize_width)
                self.resize_width = int(new_resize_width)
            else:
                self.resize_width = int(new_resize_width)
                self.resize_x = int(new_resize_x)
                self.resize_y = int(self.resize_height + self.resize_y - new_resize_height)
                self.resize_height = int(new_resize_height)
        else:
            new_resize_x = min(int(event.x) - offset_x, 0)
            self.resize_width = int(self.resize_width + self.resize_x - new_resize_x)
            self.resize_x = int(new_resize_x)
        
    def skin_edit_area_adjust_top(self, event):
        '''Adjust top.'''
        offset_y = self.padding_y + self.shadow_padding
        if self.lock_flag:
            new_resize_y = min(int(event.y) - offset_y, 0)
            new_resize_height = int(self.resize_height + self.resize_y - new_resize_y)
            new_resize_width = int(new_resize_height * self.background_pixbuf.get_width() / self.background_pixbuf.get_height())
            
            if self.resize_width + self.resize_x - new_resize_width > 0:
                self.resize_width += int(self.resize_x)                
                self.resize_x = 0
                new_resize_height = int(self.resize_width * self.background_pixbuf.get_height() / self.background_pixbuf.get_width())
                self.resize_y = int(self.resize_height + self.resize_y - new_resize_height)
                self.resize_height = int(new_resize_height)
            else:
                self.resize_height = int(new_resize_height)
                self.resize_y = int(new_resize_y)
                self.resize_x = int(self.resize_width + self.resize_x - new_resize_width)
                self.resize_width = int(new_resize_width)
        else:
            new_resize_y = min(int(event.y) - offset_y, 0)
            self.resize_height = int(self.resize_height + self.resize_y - new_resize_y)
            self.resize_y = int(new_resize_y)
        
    def skin_edit_area_adjust_right(self, event):
        '''Adjust right.'''
        offset_x = self.padding_x + self.shadow_padding
        if self.lock_flag:
            new_resize_width = max(int(event.x) - self.resize_x - offset_x, self.min_resize_width - self.resize_x)
            new_resize_height = int(new_resize_width * self.background_pixbuf.get_height() / self.background_pixbuf.get_width())
            
            if new_resize_height + self.resize_y < self.min_resize_height:
                self.resize_height = int(self.min_resize_height - self.resize_y)
                self.resize_width = int(self.resize_height * self.background_pixbuf.get_width() / self.background_pixbuf.get_height())
            else:
                self.resize_width = int(new_resize_width)
                self.resize_height = int(new_resize_height)
        else:
            new_resize_x = max(offset_x + self.min_resize_width, int(event.x))
            self.resize_width = int(new_resize_x - self.resize_x - offset_x)
        
    def skin_edit_area_adjust_bottom(self, event):
        '''Adjust bottom.'''
        offset_y = self.padding_y + self.shadow_padding
        if self.lock_flag:
            new_resize_height = max(int(event.y) - self.resize_y - offset_y, self.min_resize_height - self.resize_y)
            new_resize_width = int(new_resize_height * self.background_pixbuf.get_width() / self.background_pixbuf.get_height())
            
            if new_resize_width + self.resize_x < self.min_resize_width:
                self.resize_width = int(self.min_resize_width - self.resize_x)
                self.resize_height = int(self.resize_width * self.background_pixbuf.get_height() / self.background_pixbuf.get_width())
            else:
                self.resize_height = int(new_resize_height)
                self.resize_width = int(new_resize_width)
        else:
            new_resize_y = max(offset_y + self.min_resize_height, int(event.y))
            self.resize_height = int(new_resize_y - self.resize_y - offset_y)
    
    def skin_edit_area_drag_background(self, event):
        '''Drag background.'''
        new_resize_x = int(event.x) - self.drag_start_x + self.drag_background_x
        new_resize_y = int(event.y) - self.drag_start_y + self.drag_background_y
        self.resize_x = min(max(new_resize_x, self.min_resize_width - self.resize_width), 0)
        self.resize_y = min(max(new_resize_y, self.min_resize_height - self.resize_height), 0)
        
        self.queue_draw()
        
    def update_skin_config(self):
        '''Update skin config.'''
        self.resize_scale_x = skin_config.scale_x
        self.resize_scale_y = skin_config.scale_y
        self.resize_x = self.eval_scale(skin_config.x * self.resize_scale_x)
        self.resize_y = self.eval_scale(skin_config.y * self.resize_scale_y)
        self.resize_width = int(self.eval_scale(self.background_pixbuf.get_width() * self.resize_scale_x))
        self.resize_height = int(self.eval_scale(self.background_pixbuf.get_height() * self.resize_scale_y))
        
    def click_reset_button(self):
        '''Click reset button.'''
        # Reset skin config.
        skin_config.reset()
        
        # Update skin config.
        self.update_skin_config()
        
        # Apply skin.
        skin_config.apply_skin()
        
    def click_auto_resize_button(self):
        '''Click auto resize button.'''
        # Auto resize skin config.
        skin_config.auto_resize()
        
        # Update skin config.
        self.update_skin_config()
        
        # Apply skin.
        skin_config.apply_skin()
        
    def update_lock_status(self, toggle_button):
        '''Update lock status.'''
        self.lock_flag = toggle_button.get_active()
        
gobject.type_register(SkinEditArea)

if __name__ == '__main__':
    skin_window = SkinWindow()
    
    skin_window.show_all()
    
    gtk.main()
    
