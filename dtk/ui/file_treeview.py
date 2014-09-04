#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from treeview import TreeItem
import collections
from gio_utils import (get_file_icon_pixbuf, is_directory, get_dir_child_files,
                       get_gfile_modification_time, get_gfile_size,
                       get_gfile_type,get_file_type_dict,
                       get_gfile_name, get_gfile_content_type, sort_file_by_name)
from draw import draw_pixbuf, draw_text, draw_vlinear
from threads import post_gui
from theme import ui_theme
import pango
import gobject
import gio
import threading as td
from deepin_utils.file import format_file_size
from utils import cairo_disable_antialias, get_content_size
import traceback
import sys

ICON_SIZE = 24
ICON_PADDING_LEFT = ICON_PADDING_RIGHT = 4
INDICATOR_PADDING_LEFT = INDICATOR_PADDING_RIGHT = 4
ITEM_PADDING_Y = 2
ITEM_HEIGHT = ICON_SIZE + ITEM_PADDING_Y * 2
COLUMN_OFFSET = 32
MODIFICATION_TIME_PADDING_LEFT = 20
CONTENT_TYPE_PADDING_LEFT = 12
SIZE_PADDING_LEFT = 12

def sort_by_key(items, sort_reverse, sort_key):
    if len(items) == 1 and (isinstance(items[0], EmptyItem) or isinstance(items[0], LoadingItem)):
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

def get_name_width(column_index, name):
    expand_indicator_pixbuf = ui_theme.get_pixbuf("treeview/arrow_down.png").get_pixbuf()
    return COLUMN_OFFSET * column_index + INDICATOR_PADDING_LEFT + expand_indicator_pixbuf.get_width() + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT + get_content_size(name)[0]

def get_modification_time_width(time):
    return get_content_size(time)[0] + MODIFICATION_TIME_PADDING_LEFT

def get_type_width(file_type):
    return get_content_size(file_type)[0] + CONTENT_TYPE_PADDING_LEFT

def get_size_width(size):
    return get_content_size(size)[0] + SIZE_PADDING_LEFT

def render_background(item, cr, rect):
    if item.is_select:
        draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                     ui_theme.get_shadow_color("listview_select").get_color_info())

class LoadingThread(td.Thread):

    def __init__(self, dir_item):
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit
        self.dir_item = dir_item

    def run(self):
        try:
            self.dir_item.load_status = self.dir_item.LOADING_START
            self.items = get_dir_items(self.dir_item.gfile.get_path(), self.dir_item.column_index + 1)
            if self.items == []:
                self.items = [EmptyItem(self.dir_item.column_index + 1)]

            for item in self.items:
                item.parent_item = self.dir_item

            self.dir_item.load_status = self.dir_item.LOADING_FINSIH

            self.render_items()
        except Exception, e:
            print "class LoadingThread got error: %s" % (e)
            traceback.print_exc(file=sys.stdout)

    @post_gui
    def render_items(self):
        self.dir_item.delete_chlid_item()
        self.dir_item.child_items = self.items
        self.dir_item.add_child_item()

class DirItem(TreeItem):
    '''
    Directory item.
    '''

    LOADING_INIT = 0
    LOADING_START = 1
    LOADING_FINSIH = 2

    def __init__(self, gfile, column_index=0):
        '''
        Initialize DirItem class.
        '''
        # Init.
        TreeItem.__init__(self)
        self.gfile = gfile
        self.type = get_gfile_type(self.gfile)
        self.name = get_gfile_name(self.gfile)
        self.modification_time = get_gfile_modification_time(self.gfile)
        self.content_type = get_gfile_content_type(self.gfile)
        self.size = get_gfile_size(self.gfile)
        self.size_name = "%s 项" % (self.size)
        self.directory_path = gfile.get_path()
        self.pixbuf = None
        self.column_index = column_index
        self.is_expand = False
        self.load_status = self.LOADING_INIT
        self.name_width = get_name_width(self.column_index, self.name)
        self.modification_time_width = get_modification_time_width(self.modification_time)
        self.content_type_width = get_type_width(self.content_type)
        self.size_width = get_size_width(self.size_name)

    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        if self.pixbuf == None:
            self.pixbuf = get_file_icon_pixbuf(self.directory_path, ICON_SIZE)

        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory arrow icon.
        if self.is_expand:
            expand_indicator_pixbuf = ui_theme.get_pixbuf("treeview/arrow_down.png").get_pixbuf()
        else:
            expand_indicator_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png").get_pixbuf()
        draw_pixbuf(cr, expand_indicator_pixbuf,
                    rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT,
                    rect.y + (rect.height - expand_indicator_pixbuf.get_height()) / 2,
                    )

        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf,
                    rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + expand_indicator_pixbuf.get_width() + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT,
                    rect.y + (rect.height - ICON_SIZE) / 2,
                    )

        # Draw directory name.
        draw_text(cr, self.name,
                  rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + expand_indicator_pixbuf.get_width() + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_modification_time(self, cr, rect):
        '''
        Render type of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory type.
        draw_text(cr, self.modification_time,
                  rect.x + MODIFICATION_TIME_PADDING_LEFT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_type(self, cr, rect):
        '''
        Render type of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory type.
        draw_text(cr, self.content_type,
                  rect.x + CONTENT_TYPE_PADDING_LEFT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_size(self, cr, rect):
        '''
        Render size of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory size.
        draw_text(cr, self.size_name,
                  rect.x,
                  rect.y,
                  rect.width, rect.height,
                  alignment=pango.ALIGN_RIGHT
                  )

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def expand(self):
        self.is_expand = True

        if self.load_status == self.LOADING_INIT:
            self.add_loading_item()
        elif self.load_status == self.LOADING_FINSIH:
            self.add_child_item()

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unexpand(self):
        self.is_expand = False

        self.delete_chlid_item()

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def add_loading_item(self):
        loading_item = LoadingItem(self.column_index + 1)
        loading_item.parent_item = self
        self.child_items = [loading_item]

        self.add_child_item()

        LoadingThread(self).start()

    def add_child_item(self):
        self.add_items_callback(self.child_items, self.row_index + 1)

    def delete_chlid_item(self):
        for child_item in self.child_items:
            if isinstance(child_item, DirItem) and child_item.is_expand:
                child_item.unexpand()

        self.delete_items_callback(self.child_items)

    def get_height(self):
        return ITEM_HEIGHT

    def get_column_widths(self):
        return [self.name_width, self.size_width, self.content_type_width, self.modification_time_width]

    def get_column_renders(self):
        return [self.render_name,
                self.render_size,
                self.render_type,
                self.render_modification_time,
                ]

    def unselect(self):
        self.is_select = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def select(self):
        self.is_select = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def double_click(self, column, offset_x, offset_y):
        if self.is_expand:
            self.unexpand()
        else:
            self.expand()

    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        self.drag_line = drag_line
        self.drag_line_at_bottom = drag_line_at_bottom

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def release_resource(self):
        '''
        '''
        # print "release dir: %s" % self.directory_path
        if self.pixbuf:
            del self.pixbuf
            self.pixbuf = None

        return True

    def highlight(self):
        self.is_highlight = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhighlight(self):
        self.is_highlight = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(DirItem)

class FileItem(TreeItem):
    '''
    File item.
    '''

    def __init__(self, gfile, column_index=0):
        '''
        Initialize FileItem class.
        '''
        TreeItem.__init__(self)
        self.gfile = gfile
        self.type = get_gfile_type(self.gfile)
        self.name = get_gfile_name(self.gfile)
        self.modification_time = get_gfile_modification_time(self.gfile)
        self.content_type = get_gfile_content_type(self.gfile)
        self.size = get_gfile_size(self.gfile)
        self.size_name = format_file_size(self.size)
        self.file_path = gfile.get_path()
        self.pixbuf = None
        self.column_index = column_index
        self.name_width = get_name_width(self.column_index, self.name)
        self.modification_time_width = get_modification_time_width(self.modification_time)
        self.content_type_width = get_type_width(self.content_type)
        self.size_width = get_size_width(self.size_name)

    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        if self.pixbuf == None:
            self.pixbuf = get_file_icon_pixbuf(self.file_path, ICON_SIZE)

        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Init.
        expand_indicator_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png").get_pixbuf()

        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf,
                    rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + expand_indicator_pixbuf.get_width() + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT,
                    rect.y + (rect.height - ICON_SIZE) / 2,
                    )

        # Draw directory name.
        draw_text(cr, self.name,
                  rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + expand_indicator_pixbuf.get_width() + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_modification_time(self, cr, rect):
        '''
        Render type of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory type.
        draw_text(cr, self.modification_time,
                  rect.x + MODIFICATION_TIME_PADDING_LEFT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_type(self, cr, rect):
        '''
        Render type of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory type.
        draw_text(cr, self.content_type,
                  rect.x + CONTENT_TYPE_PADDING_LEFT,
                  rect.y,
                  rect.width, rect.height)

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def render_size(self, cr, rect):
        '''
        Render size of DirItem.
        '''
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw directory size.
        draw_text(cr, self.size_name,
                  rect.x,
                  rect.y,
                  rect.width,
                  rect.height,
                  alignment=pango.ALIGN_RIGHT,
                  )

        # Draw drag line.
        if self.drag_line:
            with cairo_disable_antialias(cr):
                cr.set_line_width(1)
                if self.drag_line_at_bottom:
                    cr.rectangle(rect.x, rect.y + rect.height - 1, rect.width, 1)
                else:
                    cr.rectangle(rect.x, rect.y, rect.width, 1)
                cr.fill()

    def expand(self):
        pass

    def unexpand(self):
        pass

    def get_height(self):
        return ITEM_HEIGHT

    def get_column_widths(self):
        return [self.name_width, self.size_width, self.content_type_width, self.modification_time_width]

    def get_column_renders(self):
        return [self.render_name,
                self.render_size,
                self.render_type,
                self.render_modification_time,
                ]

    def unselect(self):
        self.is_select = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def select(self):
        self.is_select = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def double_click(self, column, offset_x, offset_y):
        app_info = gio.app_info_get_default_for_type(self.gfile.query_info("standard::content-type").get_content_type(), False)
        if app_info:
            app_info.launch([self.gfile], None)
        else:
            print "Don't know how to open file: %s" % (self.name)

    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        self.drag_line = drag_line
        self.drag_line_at_bottom = drag_line_at_bottom

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def release_resource(self):
        '''
        '''
        # print "release file: %s" % self.file_path
        if self.pixbuf:
            del self.pixbuf
            self.pixbuf = None

        return True

    def highlight(self):
        self.is_highlight = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhighlight(self):
        self.is_highlight = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(DirItem)

class LoadingItem(TreeItem):
    '''
    Loadding item.
    '''

    def __init__(self, column_index=0):
        '''
        Initialize LoadingItem class.
        '''
        TreeItem.__init__(self)
        self.column_index = column_index

    def get_height(self):
        return ITEM_HEIGHT

    def get_column_widths(self):
        return [200, 1, 1]

    def get_column_renders(self):
        return [self.render,
                lambda cr, rect: render_background(self, cr, rect),
                lambda cr, rect: render_background(self, cr, rect),
                lambda cr, rect: render_background(self, cr, rect),
                ]

    def render(self, cr, rect):
        # Draw select background.
        if self.is_select or self.is_highlight:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw loading text.
        draw_text(cr, "正在加载...",
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


    def highlight(self):
        self.is_highlight = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhighlight(self):
        self.is_highlight = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(LoadingItem)

class EmptyItem(TreeItem):
    '''
    Loadding item.
    '''

    def __init__(self, column_index=0):
        '''
        Initialize EmptyItem class.
        '''
        TreeItem.__init__(self)
        self.column_index = column_index

    def get_height(self):
        return ITEM_HEIGHT

    def get_column_widths(self):
        return [200, 1, 1]

    def get_column_renders(self):
        return [self.render,
                lambda cr, rect: render_background(self, cr, rect),
                lambda cr, rect: render_background(self, cr, rect),
                lambda cr, rect: render_background(self, cr, rect)
                ]

    def render(self, cr, rect):
        # Draw select background.
        if self.is_select or self.is_highlight:
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

    def release_resource(self):
        '''
        '''
        return False

    def highlight(self):
        self.is_highlight = True

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhighlight(self):
        self.is_highlight = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

gobject.type_register(EmptyItem)

def get_dir_items(dir_path, column_index=0, show_hidden=False):
    '''
    Get children items with given directory path.
    '''
    items = []
    for gfile in get_dir_child_files(dir_path, sort_file_by_name, False, show_hidden):
        if is_directory(gfile):
            items.append(DirItem(gfile, column_index))
        else:
            items.append(FileItem(gfile, column_index))

    return items
