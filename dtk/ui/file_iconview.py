#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Zhai Xiang
#
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
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

import collections
from gio_utils import (get_file_icon_pixbuf, is_directory, get_dir_child_files,
                       get_file_type_dict,
                       get_gfile_name, sort_file_by_name)
from draw import draw_pixbuf, draw_text, draw_vlinear
from theme import ui_theme
import pango
import gobject
import gio
from scrolled_window import ScrolledWindow
from iconview import IconView
from constant import DEFAULT_FONT_SIZE

ITEM_PADDING_Y = 10
ITEM_HEIGHT = 22
COLUMN_OFFSET = 10

def sort_by_key(items, sort_reverse, sort_key):
    if len(items) == 1 and (isinstance(items[0], EmptyItem)):
        return items
    else:
        # Init.
        item_oreder_dict = collections.OrderedDict(get_file_type_dict())

        # Split item with different file type.
        for item in items:
            item_oreder_dict[item.type].append(item)

        # Get sorted item list.
        item_list = []
        for (file_type, type_items) in item_oreder_dict.items():
            item_list += sorted(type_items, key=sort_key, reverse=sort_reverse)

        return item_list

def sort_by_name(items, sort_reverse):
    return sort_by_key(items, sort_reverse, lambda i: i.name)

def sort_by_size(items, sort_reverse):
    return sort_by_key(items, sort_reverse, lambda i: i.size)

def sort_by_type(items, sort_reverse):
    return sort_by_key(items, sort_reverse, lambda i: i.content_type)

def sort_by_mtime(items, sort_reverse):
    return sort_by_key(items, sort_reverse, lambda i: i.modification_time)

class FileIconView(ScrolledWindow):
    def __init__(self, items=None):
        ScrolledWindow.__init__(self, 0, 0)
        self.file_iconview = IconView()
        self.file_iconview.draw_mask = self.draw_mask
        if items != None:
            self.file_iconview.add_items(items)
        self.file_scrolledwindow = ScrolledWindow()
        self.file_scrolledwindow.add_child(self.file_iconview)
        self.add_child(self.file_scrolledwindow)

    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.

        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def add_items(self, items, clear=False):
        self.file_iconview.clear()
        self.file_iconview.add_items(items)

gobject.type_register(FileIconView)

class DirItem(gobject.GObject):
    '''
    Directory item.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    LOADING_INIT = 0
    LOADING_START = 1
    LOADING_FINSIH = 2

    def __init__(self, gfile, icon_size):
        '''
        Initialize DirItem class.
        '''
        # Init.
        gobject.GObject.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.directory_path = gfile.get_path()
        self.icon_size = icon_size
        self.pixbuf = get_file_icon_pixbuf(self.directory_path, self.icon_size)
        self.is_button_press = False;

    def render(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw select background.
        if self.is_button_press == True:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf,
                    rect.x + self.icon_size / 2,
                    rect.y + (rect.height - self.icon_size) / 2,
                    )

        # Draw directory name.
        draw_text(cr,
                  self.name,
                  rect.x,
                  rect.y + self.icon_size + ITEM_PADDING_Y * 2,
                  rect.width,
                  DEFAULT_FONT_SIZE,
                  DEFAULT_FONT_SIZE,
                  alignment=pango.ALIGN_CENTER)

    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.

        This is IconView interface, you should implement it.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get item width.

        This is IconView interface, you should implement it.
        '''
        return self.icon_size * 2

    def get_height(self):
        '''
        Get item height.

        This is IconView interface, you should implement it.
        '''
        return self.icon_size + DEFAULT_FONT_SIZE + ITEM_PADDING_Y * 3

    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True

        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = False

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = False
        self.is_button_press = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.

        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.

        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True

    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.

        Here is slider rule
        '''
        pass

    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.

        @return: Return True if do release work, otherwise return False.

        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        del self.pixbuf
        self.pixbuf = None

        # Return True to tell IconView call gc.collect() to release memory resource.
        return True

gobject.type_register(DirItem)

class FileItem(gobject.GObject):
    '''
    File item.
    '''

    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    LOADING_INIT = 0
    LOADING_START = 1
    LOADING_FINSIH = 2

    def __init__(self, gfile, icon_size):
        '''
        Initialize DirItem class.
        '''
        # Init.
        gobject.GObject.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.directory_path = gfile.get_path()
        self.icon_size = icon_size
        self.pixbuf = get_file_icon_pixbuf(self.directory_path, self.icon_size)
        self.is_button_press = False;

    def render(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw select background.
        if self.is_button_press == True:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf,
                    rect.x + self.icon_size / 2,
                    rect.y + (rect.height - self.icon_size) / 2,
                    )

        # Draw directory name.
        draw_text(cr,
                  self.name,
                  rect.x,
                  rect.y + self.icon_size + ITEM_PADDING_Y * 2,
                  rect.width,
                  DEFAULT_FONT_SIZE,
                  DEFAULT_FONT_SIZE,
                  alignment=pango.ALIGN_CENTER)

    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.

        This is IconView interface, you should implement it.
        '''
        self.emit("redraw-request")

    def get_width(self):
        '''
        Get item width.

        This is IconView interface, you should implement it.
        '''
        return self.icon_size * 2

    def get_height(self):
        '''
        Get item height.

        This is IconView interface, you should implement it.
        '''
        return self.icon_size + DEFAULT_FONT_SIZE + ITEM_PADDING_Y * 3

    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True

        self.emit_redraw_request()

    def icon_item_lost_focus(self):
        '''
        Lost focus.

        This is IconView interface, you should implement it.
        '''
        self.hover_flag = False

        self.emit_redraw_request()

    def icon_item_highlight(self):
        '''
        Highlight item.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()

    def icon_item_normal(self):
        '''
        Set item with normal status.

        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = False
        self.is_button_press = False

        self.emit_redraw_request()

    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.

        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True

    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.

        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True

    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.

        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.

        '''
        app_info = gio.app_info_get_default_for_type(self.gfile.query_info("standard::content-type").get_content_type(), False)
        if app_info:
            app_info.launch([self.gfile], None)
        else:
            print "Don't know how to open file: %s" % (self.name)


    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.

        @return: Return True if do release work, otherwise return False.

        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        del self.pixbuf
        self.pixbuf = None

        # Return True to tell IconView call gc.collect() to release memory resource.
        return True

gobject.type_register(FileItem)

class EmptyItem(gobject.GObject):
    '''
    Loadding item.
    '''

    def __init__(self):
        '''
        Initialize EmptyItem class.
        '''
        gobject.GObject.__init__(self)

    def get_height(self):
        return ITEM_HEIGHT

    def render(self, cr, rect):
        # Draw select background.
        if self.is_select:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw loading text.
        draw_text(cr, "(空)",
                  rect.x + COLUMN_OFFSET * self.column_index,
                  rect.y,
                  rect.width, rect.height)

    def unselect(self):
        self.is_select = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def select(self):
        self.is_select = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(EmptyItem)

def iconview_get_dir_items(dir_path, icon_size=48, show_hidden=False):
    '''
    Get children items with given directory path.
    '''
    items = []
    for gfile in get_dir_child_files(dir_path, sort_file_by_name, False, show_hidden):
        if is_directory(gfile):
            items.append(DirItem(gfile, icon_size))
        else:
            items.append(FileItem(gfile, icon_size))
    return items
