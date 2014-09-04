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

from button import Button, ImageButton, ToggleButton, ActionButton
from cache_pixbuf import CachePixbuf
from deepin_utils.config import Config
from constant import SHADOW_SIZE, COLOR_SEQUENCE
from dialog import ConfirmDialog, OpenFileDialog, SaveFileDialog
from dialog import DialogBox, DIALOG_MASK_SINGLE_PAGE
from draw import draw_pixbuf, draw_vlinear, draw_hlinear
from iconview import IconView
from label import Label
from locales import _, LANGUAGE
from scrolled_window import ScrolledWindow
from skin_config import skin_config
from theme import ui_theme
import tooltip as Tooltip
import gobject
import gtk
import math
import os
import threading as td
import urllib
from deepin_utils.file import remove_directory, end_with_suffixs
from utils import (is_in_rect, set_cursor, remove_timeout_id,
                   color_hex_to_cairo, cairo_state, container_remove_all,
                   cairo_disable_antialias,
                   scroll_to_bottom,
                   place_center, file_is_image,
                   get_optimum_pixbuf_from_file)


__all__ = ["SkinWindow"]

class LoadSkinThread(td.Thread):
    '''
    Thread to load skin.
    '''

    def __init__(self,
                 skin_dirs,
                 add_skin_icons,
                 add_add_icon,
                 ):
        '''
        Initialize LoadSkinThread class.

        @param skin_dirs: Skin directories.
        @param add_skin_icons: Callback to add skin icon.
        @param add_add_icon: Callback to add add icon.
        '''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit

        self.skin_dirs = skin_dirs
        self.add_skin_icons = add_skin_icons
        self.add_add_icon = add_add_icon

        self.skin_icon_list = []

        self.in_loading = True

    def render_skin_icons(self):
        if len(self.skin_icon_list) > 0:
            self.add_skin_icons(self.skin_icon_list)
            self.skin_icon_list = []

        if not self.in_loading:
            self.add_add_icon()
        return self.in_loading

    def run(self):
        '''
        Run.
        '''
        gtk.timeout_add(100, self.render_skin_icons)
        for skin_dir in self.skin_dirs:
            for root, dirs, files in os.walk(skin_dir):
                dirs.sort()         # sort directory with alpha order
                for filename in files:
                    if file_is_image(os.path.join(root, filename)):
                        self.skin_icon_list.append((root, filename))
        self.in_loading = False

class SkinWindow(DialogBox):
    '''
    SkinWindow.

    @undocumented: change_skin
    @undocumented: switch_preview_page
    @undocumented: switch_edit_page
    '''

    def __init__(self,
                 app_frame_pixbuf,
                 preview_width=450,
                 preview_height=500,
                 ):
        '''
        Initialize SkinWindow class.

        @param app_frame_pixbuf: Application's pixbuf for frame.
        @param preview_width: Preview width, default is 450 pixels.
        @param preview_height: Preview height, default is 500 pixels.
        '''
        DialogBox.__init__(self, _("Select Skin"), preview_width, preview_height, mask_type=DIALOG_MASK_SINGLE_PAGE)
        self.app_frame_pixbuf = app_frame_pixbuf

        self.preview_page = SkinPreviewPage(self, self.change_skin, self.switch_edit_page)

        self.close_button = Button(_("Close"))
        self.close_button.connect("clicked", lambda w: w.get_toplevel().destroy())
        self.right_button_box.set_buttons([self.close_button])

        self.switch_preview_page()

    def change_skin(self, item):
        '''
        Internal function to change skin with given item.
        '''
        # Load skin.
        if skin_config.reload_skin(os.path.basename(item.skin_dir)):
            skin_config.apply_skin()

    def switch_preview_page(self):
        '''
        Internal function to switch preview page.
        '''
        container_remove_all(self.body_box)
        self.body_box.add(self.preview_page)
        self.preview_page.highlight_skin()

        self.close_button = Button(_("Close"))
        self.close_button.connect("clicked", lambda w: w.get_toplevel().destroy())
        self.right_button_box.set_buttons([self.close_button])

        self.show_all()

    def switch_edit_page(self):
        '''
        Internal function to switch edit page.
        '''
        if self.app_frame_pixbuf != None:
            # Switch to edit page.
            container_remove_all(self.body_box)
            edit_page = SkinEditPage(self, self.app_frame_pixbuf, self.switch_preview_page)
            self.body_box.add(edit_page)

            self.show_all()

gobject.type_register(SkinWindow)

class SkinPreviewPage(gtk.VBox):
    '''
    Skin preview.
    '''

    def __init__(self,
                 dialog,
                 change_skin_callback,
                 switch_edit_page_callback,
                 ):
        '''
        Init skin preview.
        '''
        gtk.VBox.__init__(self)
        self.dialog = dialog
        self.change_skin_callback = change_skin_callback
        self.switch_edit_page_callback = switch_edit_page_callback

        self.preview_align = gtk.Alignment()
        self.preview_align.set(0.5, 0.5, 1, 1)
        self.preview_align.set_padding(0, 0, 10, 2)
        self.preview_scrolled_window = ScrolledWindow()
        self.preview_scrolled_window.draw_mask = self.dialog.get_mask_func(self.preview_scrolled_window)
        self.preview_view = IconView()
        self.preview_view.draw_mask = self.dialog.get_mask_func(self.preview_view)

        self.preview_align.add(self.preview_scrolled_window)
        self.preview_scrolled_window.add_child(self.preview_view)
        self.pack_start(self.preview_align, True, True)

        LoadSkinThread([skin_config.system_skin_dir, skin_config.user_skin_dir],
                       self.add_skin_icons,
                       self.add_add_icon).start()

        # Add drag image support.
        self.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_DROP,
            [("text/uri-list", 0, 1)],
            gtk.gdk.ACTION_COPY)

        self.connect("drag-data-received", self.drag_skin_file)

    def add_skin_icons(self, skin_infos):
        '''
        Add skin icon.
        '''
        items = []
        for (root, filename) in skin_infos:
            items.append(
                SkinPreviewIcon(
                    root,
                    filename,
                    self.change_skin_callback,
                    self.switch_edit_page_callback,
                    self.pop_delete_skin_dialog))
        self.preview_view.add_items(items)

    def add_add_icon(self):
        '''
        Add add icon.
        '''
        self.preview_view.add_items([SkinAddIcon(self.create_skin_from_file)])

    def drag_skin_file(self, widget, drag_context, x, y, selection_data, info, timestamp):
        '''
        Drag skin file.
        '''
        self.create_skin_from_file(urllib.unquote(selection_data.get_uris()[0].split("file://")[1]))

    def create_skin_from_file(self, skin_file):
        '''
        Create skin from file.
        '''
        if file_is_image(skin_file):
            self.create_skin_from_image(skin_file)
        elif end_with_suffixs(skin_file, ["tar.gz"]):
            self.create_skin_from_package(skin_file)

    def create_skin_from_image(self, filepath):
        '''
        Create skin from image.
        '''
        (load_skin_status, skin_dir, skin_image_file) = skin_config.load_skin_from_image(filepath)

        if load_skin_status:
            self.add_skin_preview_icon(skin_dir, skin_image_file)

    def create_skin_from_package(self, filepath):
        '''
        Create skin from package.
        '''
        (load_skin_status, skin_dir, skin_image_file) = skin_config.load_skin_from_package(filepath)

        if load_skin_status:
            self.add_skin_preview_icon(skin_dir, skin_image_file)
        else:
            ConfirmDialog(_("Skin Version Mismatch"),
                          _("Imported skin version mismatches with current one!")).show_all()

    def add_skin_preview_icon(self, skin_dir, skin_image_file):
        self.preview_view.add_items([SkinPreviewIcon(
                    skin_dir,
                    skin_image_file,
                    self.change_skin_callback,
                    self.switch_edit_page_callback,
                    self.pop_delete_skin_dialog
                    )], -1)

        self.highlight_skin()

        # Scroll scrollbar to bottom.
        scroll_to_bottom(self.preview_scrolled_window)

    def highlight_skin(self):
        '''
        Highlight skin.
        '''
        # Highlight skin.
        for item in self.preview_view.items:
            if isinstance(item, SkinPreviewIcon) and item.skin_dir == skin_config.skin_dir:
                self.preview_view.clear_highlight()
                self.preview_view.set_highlight(item)
                break

    def pop_delete_skin_dialog(self, item):
        '''
        Pop delete skin dialog.
        '''
        if LANGUAGE == 'en_US':
            message_text_size=10
        else:
            message_text_size=11

        dialog = ConfirmDialog(
            _("Delete skin"),
            _("Are you sure you want to delete this skin?"),
            confirm_callback = lambda : self.remove_skin(item),
            message_text_size=message_text_size,
            )
        dialog.show_all()
        place_center(self.get_toplevel(), dialog)

    def remove_skin(self, item):
        '''
        Remove skin.
        '''
        if len(self.preview_view.items) > 1:
            # Change to first theme if delete current theme.
            if item.skin_dir == skin_config.skin_dir:
                item_index = max(self.preview_view.items.index(item) - 1, 0)
                if skin_config.reload_skin(os.path.basename(self.preview_view.items[item_index].skin_dir)):
                    skin_config.apply_skin()
                    self.highlight_skin()

            # Remove skin directory.
            remove_directory(item.skin_dir)

            # Remove item from icon view.
            self.preview_view.delete_items([item])
        else:
            print "You can't delete last skin to make application can't use any skin! :)"

gobject.type_register(SkinPreviewPage)

class SkinPreviewIcon(gobject.GObject):
    '''
    Icon item.
    '''

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
        '''
        Init item icon.
        '''
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

        self.pixbuf = get_optimum_pixbuf_from_file(self.background_path, self.width, self.height, False)

        self.show_delete_button_id = None
        self.show_edit_button_id = None
        self.show_delay = 500  # milliseconds

        # Load skin config information.
        self.config = Config(os.path.join(self.skin_dir, "config.ini"))
        self.config.load()

    def is_in_delete_button_area(self, x, y):
        '''
        Is cursor in delete button area.
        '''
        delete_pixbuf = ui_theme.get_pixbuf("skin/delete_normal.png").get_pixbuf()

        return is_in_rect((x, y),
                          (self.get_width() - delete_pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3,
                           (self.icon_padding + self.padding_x) + 4,
                           delete_pixbuf.get_width(),
                           delete_pixbuf.get_height()))

    def is_in_edit_button_area(self, x, y):
        '''
        Is cursor in edit button area.
        '''
        edit_pixbuf = ui_theme.get_pixbuf("skin/edit_normal.png").get_pixbuf()

        return is_in_rect((x, y),
                          (self.get_width() - edit_pixbuf.get_width() - (self.icon_padding + self.padding_x) - 3,
                           self.get_height() - edit_pixbuf.get_height() - (self.icon_padding + self.padding_x) - 4,
                           edit_pixbuf.get_width(),
                           edit_pixbuf.get_height()))

    def is_deletable(self):
        '''
        Is deletable.
        '''
        return self.config.getboolean("action", "deletable")

    def is_editable(self):
        '''
        Is editable.
        '''
        return self.config.getboolean("action", "editable")

    def emit_redraw_request(self):
        '''
        Emit redraw-request signal.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get width.
        '''
        return self.width + (self.icon_padding + self.padding_x) * 2

    def get_height(self):
        '''
        Get height.
        '''
        return self.height + (self.icon_padding + self.padding_y) * 2

    def render(self, cr, rect):
        '''
        Render item.
        '''
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
        '''
        Handle `motion-notify-event` signal.
        '''
        self.hover_flag = True

        remove_timeout_id(self.show_delete_button_id)
        remove_timeout_id(self.show_edit_button_id)

        if self.is_deletable():
            if self.is_in_delete_button_area(x, y):
                if self.delete_button_status == self.BUTTON_HIDE:
                    self.show_delete_button_id = gtk.timeout_add(self.show_delay, lambda : self.show_delete_button(self.BUTTON_HOVER))
                else:
                    self.delete_button_status = self.BUTTON_HOVER
            else:
                if self.delete_button_status == self.BUTTON_HOVER:
                    self.delete_button_status = self.BUTTON_NORMAL
                else:
                    self.show_delete_button_id = gtk.timeout_add(self.show_delay, lambda : self.show_delete_button(self.BUTTON_NORMAL))
        else:
            self.delete_button_status = self.BUTTON_HIDE

        if self.is_editable():
            if self.is_in_edit_button_area(x, y):
                if self.edit_button_status == self.BUTTON_HIDE:
                    self.show_edit_button_id = gtk.timeout_add(self.show_delay, lambda : self.show_edit_button(self.BUTTON_HOVER))
                else:
                    self.edit_button_status = self.BUTTON_HOVER
            else:
                if self.edit_button_status == self.BUTTON_HOVER:
                    self.edit_button_status = self.BUTTON_NORMAL
                else:
                    self.show_edit_button_id = gtk.timeout_add(self.show_delay, lambda : self.show_edit_button(self.BUTTON_NORMAL))
        else:
            self.edit_button_status = self.BUTTON_HIDE

        self.emit_redraw_request()

    def show_delete_button(self, status):
        '''
        Show delete button.
        '''
        self.delete_button_status = status
        self.emit_redraw_request()

    def show_edit_button(self, status):
        '''
        Show edit button.
        '''
        self.edit_button_status = status
        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.
        '''
        self.hover_flag = False
        self.delete_button_status = self.BUTTON_HIDE
        self.edit_button_status = self.BUTTON_HIDE

        remove_timeout_id(self.show_delete_button_id)
        remove_timeout_id(self.show_edit_button_id)

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.
        '''
        self.highlight_flag = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        '''
        if not self.is_deletable() and not self.is_editable():
            self.change_skin_callback(self)
        else:
            if self.is_deletable() and self.is_in_delete_button_area(x, y):
                if self.delete_button_status != self.BUTTON_HIDE:
                    self.delete_button_status = self.BUTTON_HIDE
                    self.edit_button_status = self.BUTTON_HIDE

                    self.pop_delete_skin_dialog_callback(self)
            elif self.is_editable() and self.is_in_edit_button_area(x, y):
                if self.edit_button_status != self.BUTTON_HIDE:
                    self.delete_button_status = self.BUTTON_HIDE
                    self.edit_button_status = self.BUTTON_HIDE

                    self.change_skin_callback(self)
                    self.switch_edit_page_callback()
            else:
                self.change_skin_callback(self)

        self.emit_redraw_request()

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        '''
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
        '''
        Handle single click event.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        '''
        pass

gobject.type_register(SkinPreviewIcon)

class SkinAddIcon(gobject.GObject):
    '''
    Icon item.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, ok_callback=None, cancel_callback=None):
        '''
        Init item icon.
        '''
        gobject.GObject.__init__(self)
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback
        self.width = 86
        self.height = 56
        self.icon_padding = 2
        self.padding_x = 7
        self.padding_y = 10
        self.hover_flag = False
        self.highlight_flag = False

    def emit_redraw_request(self):
        '''
        Emit redraw-request signal.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get width.
        '''
        return self.width + (self.icon_padding + self.padding_x) * 2

    def get_height(self):
        '''
        Get height.
        '''
        return self.height + (self.icon_padding + self.padding_y) * 2

    def render(self, cr, rect):
        '''
        Render item.
        '''
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
        '''
        Handle `motion-notify-event` signal.
        '''
        self.hover_flag = True

        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.
        '''
        self.hover_flag = False

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.
        '''
        self.highlight_flag = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        '''
        OpenFileDialog(_("Add Skin File"), None, self.ok_callback, self.cancel_callback)

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        '''
        pass

    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        '''
        pass

gobject.type_register(SkinAddIcon)

class SkinEditPage(gtk.VBox):
    '''
    Init skin edit page.
    '''

    def __init__(self,
                 dialog,
                 app_frame_pixbuf,
                 switch_preview_page):
        '''
        Init skin edit page.
        '''
        gtk.VBox.__init__(self)
        self.dialog = dialog
        self.switch_preview_page = switch_preview_page
        self.edit_area_align = gtk.Alignment()
        self.edit_area_align.set(0.5, 0.5, 1, 1)
        self.edit_area_align.set_padding(5, 0, 28, 28)
        self.edit_area = SkinEditArea(app_frame_pixbuf)
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

        self.export_button.connect("clicked", self.export_skin)
        self.v_split_button.connect("clicked", lambda w: self.click_vertical_mirror_button())
        self.h_split_button.connect("clicked", lambda w: self.click_horizontal_mirror_button())

        Tooltip.text(self.resize_button, _("Zoom automatically"))
        Tooltip.text(self.v_split_button, _("Flip vertically"))
        Tooltip.text(self.h_split_button, _("Flip horizontally"))
        Tooltip.text(self.lock_button, _("Lock scaling"))
        Tooltip.text(self.export_button, _("Export"))

        self.color_label_align = gtk.Alignment()
        self.color_label_align.set(0.0, 0.5, 0, 0)
        self.color_label_align.set_padding(0, 0, 20, 0)
        self.color_label = Label(_("Select color"), ui_theme.get_color("skin_title"))
        self.color_label.set_size_request(100, 30)
        self.color_label_align.add(self.color_label)

        self.color_select_align = gtk.Alignment()
        self.color_select_align.set(0.5, 0.5, 1, 1)
        self.color_select_align.set_padding(0, 0, 30, 30)
        self.color_select_view = IconView()
        self.color_select_view.draw_mask = self.dialog.get_mask_func(self.color_select_view)
        self.color_select_scrolled_window = ScrolledWindow()
        self.color_select_scrolled_window.add_child(self.color_select_view)
        self.color_select_align.add(self.color_select_scrolled_window)

        for color in COLOR_SEQUENCE:
            self.color_select_view.add_items([ColorIconItem(color)])

        self.back_button = Button(_("Back"))
        self.back_button.connect("clicked", lambda w: self.switch_preview_page())
        self.dialog.right_button_box.set_buttons([self.back_button])

        self.pack_start(self.edit_area_align, False, False)
        self.pack_start(self.action_align, False, False)
        self.pack_start(self.color_label_align, True, True)
        self.pack_start(self.color_select_align, True, True)

        self.highlight_color_icon(skin_config.theme_name)

        self.color_select_view.connect("button-press-item", self.change_skin_theme)

    def click_vertical_mirror_button(self):
        '''
        Click vertical mirror button.
        '''
        skin_config.vertical_mirror_background()
        skin_config.save_skin()

    def click_horizontal_mirror_button(self):
        '''
        Click horizontal mirror button.
        '''
        skin_config.horizontal_mirror_background()
        skin_config.save_skin()

    def change_skin_theme(self, view, item, x, y):
        '''
        Change skin theme.
        '''
        # Highlight theme icon.
        self.highlight_color_icon(item.color)

        # Change and save theme.
        skin_config.change_theme(item.color)
        skin_config.save_skin()

    def highlight_color_icon(self, color):
        '''
        Highlight color icon.
        '''
        for item in self.color_select_view.items:
            if item.color == color:
                self.color_select_view.clear_highlight()
                self.color_select_view.set_highlight(item)
                break

    def export_skin(self, button):
        '''
        Export skin.
        '''
        SaveFileDialog(_("Export"), None, skin_config.export_skin)

gobject.type_register(SkinEditPage)

class ColorIconItem(gobject.GObject):
    '''
    Icon item.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, color):
        '''
        Init item icon.
        '''
        gobject.GObject.__init__(self)
        self.color = color
        self.width = 42
        self.height = 27
        self.padding_x = 6
        self.padding_y = 6
        self.hover_flag = False
        self.highlight_flag = False

    def emit_redraw_request(self):
        '''
        Emit redraw-request signal.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get width.
        '''
        return self.width + self.padding_x * 2

    def get_height(self):
        '''
        Get height.
        '''
        return self.height + self.padding_y * 2

    def render(self, cr, rect):
        '''
        Render item.
        '''
        # Init.
        draw_x = rect.x + self.padding_x
        draw_y = rect.y + self.padding_y

        # Draw color area.
        draw_pixbuf(
            cr,
            ui_theme.get_pixbuf("skin/color_%s.png" % (self.color)).get_pixbuf(),
            draw_x,
            draw_y)

        # Draw select effect.
        if self.hover_flag:
            draw_pixbuf(
                cr,
                ui_theme.get_pixbuf("skin/color_frame_hover.png").get_pixbuf(),
                draw_x - 2,
                draw_y - 2)
        elif self.highlight_flag:
            draw_pixbuf(
                cr,
                ui_theme.get_pixbuf("skin/color_frame_highlight.png").get_pixbuf(),
                draw_x - 2,
                draw_y - 2)

    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.
        '''
        self.hover_flag = True

        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.
        '''
        self.hover_flag = False

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.
        '''
        self.highlight_flag = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        '''
        pass

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        '''
        pass

    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        '''
        pass

gobject.type_register(ColorIconItem)

class SkinEditArea(gtk.EventBox):
    '''
    Skin edit area.
    '''

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

    def __init__(self, app_frame_pixbuf):
        '''
        Init skin edit area.
        '''
        gtk.EventBox.__init__(self)
        self.set_has_window(False)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal

        self.preview_frame_width = 390
        self.preview_frame_height = 270
        self.app_window_width = skin_config.app_window_width
        self.app_window_height = skin_config.app_window_height
        self.preview_pixbuf = app_frame_pixbuf
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
        self.shadow_size = int(self.eval_scale(SHADOW_SIZE))
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

        self.cache_pixbuf = CachePixbuf()

        self.connect("expose-event", self.expose_skin_edit_area)
        self.connect("button-press-event", self.button_press_skin_edit_area)
        self.connect("button-release-event", self.button_release_skin_edit_area)
        self.connect("motion-notify-event", self.motion_skin_edit_area)
        self.connect("leave-notify-event", self.leave_notify_skin_edit_area)

    def eval_scale(self, value):
        '''
        Eval scale.
        '''
        return value * self.preview_pixbuf_width / self.app_window_width

    def expose_skin_edit_area(self, widget, event):
        '''
        Expose edit area.
        '''
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
            self.cache_pixbuf.scale(self.background_pixbuf, self.resize_width, self.resize_height,
                                    skin_config.vertical_mirror, skin_config.horizontal_mirror)

            draw_pixbuf(
                cr,
                self.cache_pixbuf.get_cache(),
                x + self.padding_x + resize_x,
                y + self.padding_y + resize_y)

            # Draw dominant shadow color.
            if self.button_release_flag:
                offset_x = x + self.padding_x
                offset_y = y + self.padding_y
                background_area_width = self.resize_width + resize_x
                background_area_height = self.resize_height + resize_y

                with cairo_state(cr):
                    cr.rectangle(
                        x + self.padding_x + resize_x,
                        y + self.padding_y + resize_y,
                        w,
                        h
                        )
                    cr.clip()

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
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("skin_edit_area_preview").get_color()))
                cr.rectangle(x, y, w, h)
                cr.stroke()

    def button_press_skin_edit_area(self, widget, event):
        '''
        Callback for `button-press-event`
        '''
        self.button_press_flag = True
        self.button_release_flag = False
        self.action_type = self.skin_edit_area_get_action_type(event)
        self.skin_edit_area_set_cursor(self.action_type)

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.drag_background_x = self.resize_x
        self.drag_background_y = self.resize_y

    def button_release_skin_edit_area(self, widget, event):
        '''
        Callback for `button-release-event`.
        '''
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
        skin_config.save_skin()

    def leave_notify_skin_edit_area(self, widget, event):
        '''
        Callback for `leave-notify-event` signal.
        '''
        if not self.button_press_flag:
            self.in_resize_area_flag = False

            set_cursor(self, None)

            self.queue_draw()

    def motion_skin_edit_area(self, widget, event):
        '''
        Callback for `motion-notify-event`.
        '''
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
        '''
        Set cursor.
        '''
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
        '''
        Get action type.
        '''
        ex, ey = event.x, event.y
        resize_x = self.padding_x + self.shadow_padding + self.resize_x
        resize_y = self.padding_y + self.shadow_padding + self.resize_y
        edit_area_rect = self.get_allocation()

        if not is_in_rect((ex, ey), (0, 0, edit_area_rect.width, edit_area_rect.height)):
            return self.POSITION_OUTSIDE
        elif is_in_rect((ex, ey),
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
        '''
        Is at resize area.
        '''
        offset_x = self.padding_x + self.shadow_padding
        offset_y = self.padding_y + self.shadow_padding
        return is_in_rect(
            (event.x, event.y),
            (self.resize_x + offset_x - self.resize_pointer_size / 2,
             self.resize_y + offset_y - self.resize_pointer_size / 2,
             self.resize_width + self.resize_pointer_size,
             self.resize_height + self.resize_pointer_size))

    def skin_edit_area_resize(self, action_type, event):
        '''
        Resize.
        '''
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
        '''
        Adjust left.
        '''
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
        '''
        Adjust top.
        '''
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
        '''
        Adjust right.
        '''
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
        '''
        Adjust bottom.
        '''
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
        '''
        Drag background.
        '''
        new_resize_x = int(event.x) - self.drag_start_x + self.drag_background_x
        new_resize_y = int(event.y) - self.drag_start_y + self.drag_background_y
        self.resize_x = min(max(new_resize_x, self.min_resize_width - self.resize_width), 0)
        self.resize_y = min(max(new_resize_y, self.min_resize_height - self.resize_height), 0)

        self.queue_draw()

    def update_skin_config(self):
        '''
        Update skin config.
        '''
        self.resize_scale_x = skin_config.scale_x
        self.resize_scale_y = skin_config.scale_y
        self.resize_x = self.eval_scale(skin_config.x * self.resize_scale_x)
        self.resize_y = self.eval_scale(skin_config.y * self.resize_scale_y)
        self.resize_width = int(self.eval_scale(self.background_pixbuf.get_width() * self.resize_scale_x))
        self.resize_height = int(self.eval_scale(self.background_pixbuf.get_height() * self.resize_scale_y))

    def click_reset_button(self):
        '''
        Click reset button.
        '''
        # Reset skin config.
        skin_config.reset()

        # Update skin config.
        self.update_skin_config()

        # Apply and save skin.
        skin_config.apply_skin()
        skin_config.save_skin()

    def click_auto_resize_button(self):
        '''
        Click auto resize button.
        '''
        # Auto resize skin config.
        skin_config.auto_resize()

        # Update skin config.
        self.update_skin_config()

        # Apply and save skin.
        skin_config.apply_skin()
        skin_config.save_skin()

    def update_lock_status(self, toggle_button):
        '''
        Update lock status.
        '''
        self.lock_flag = toggle_button.get_active()

gobject.type_register(SkinEditArea)

if __name__ == '__main__':
    skin_window = SkinWindow()

    skin_window.show_all()

    gtk.main()

