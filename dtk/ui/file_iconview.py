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

from iconview import IconItem
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
from utils import cairo_disable_antialias, get_content_size, format_file_size
import traceback
import sys

ICON_SIZE = 32
ICON_PADDING_LEFT = ICON_PADDING_RIGHT = 4
INDICATOR_PADDING_LEFT = INDICATOR_PADDING_RIGHT = 4
ITEM_PADDING_Y = 2
ITEM_HEIGHT = ICON_SIZE + ITEM_PADDING_Y * 2
COLUMN_OFFSET = 32
MODIFICATION_TIME_PADDING_LEFT = 12
CONTENT_TYPE_PADDING_LEFT = 12
SIZE_PADDING_LEFT = 12

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

def get_name_width(column_index, name):
    return COLUMN_OFFSET * column_index + INDICATOR_PADDING_LEFT + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT + get_content_size(name)[0]

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
	
class DirItem(IconItem):
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
        IconItem.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.directory_path = gfile.get_path()
        self.pixbuf = get_file_icon_pixbuf(self.directory_path, ICON_SIZE)
        self.load_status = self.LOADING_INIT
        self.name_width = get_name_width(self.column_index, self.name)
        
    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw select background.
        if self.is_select:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())
        
        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT,
                    rect.y + (rect.height - ICON_SIZE) / 2,
                    )
        
        # Draw directory name.
        draw_text(cr, self.name, 
                  rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT,
                  rect.y,
                  rect.width, rect.height)
    
    def add_child_item(self):
        self.add_items_callback(self.child_items, self.row_index + 1)
        
    def delete_chlid_item(self):
        for child_item in self.child_items:
            if isinstance(child_item, DirItem) and child_item.is_expand:
                child_item.unexpand()

        self.delete_items_callback(self.child_items)
    
    def get_height(self):
        return ITEM_HEIGHT
    
    def unselect(self):
        self.is_select = False
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def select(self):
        self.is_select = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def double_click(self, column, offset_x, offset_y):
        pass

    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        self.drag_line = drag_line
        self.drag_line_at_bottom = drag_line_at_bottom

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
gobject.type_register(DirItem)

class FileItem(IconItem):
    '''
    File item.
    '''
	
    def __init__(self, gfile, column_index=0):
        '''
        Initialize FileItem class.
        '''
        IconItem.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.file_path = gfile.get_path()
        self.pixbuf = get_file_icon_pixbuf(self.file_path, ICON_SIZE)
        self.name_width = get_name_width(self.column_index, self.name)
        
    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw select background.
        if self.is_select:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                         ui_theme.get_shadow_color("listview_select").get_color_info())
        
        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT,
                    rect.y + (rect.height - ICON_SIZE) / 2,
                    )
        
        # Draw directory name.
        draw_text(cr, self.name, 
                  rect.x + COLUMN_OFFSET * self.column_index + INDICATOR_PADDING_LEFT + INDICATOR_PADDING_RIGHT + ICON_PADDING_LEFT + ICON_SIZE + ICON_PADDING_RIGHT,
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
    
    def get_height(self):
        return ITEM_HEIGHT
        
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
            
gobject.type_register(DirItem)

class EmptyItem(IconItem):
    '''
    Loadding item.
    '''
	
    def __init__(self, column_index=0):
        '''
        Initialize EmptyItem class.
        '''
        IconItem.__init__(self)
        self.column_index = column_index
        
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

class FileIconView(ScrolledWindow):

    def __init__(self):
        ScrolledWindow.__init__(self, 0, 0)

gobject.type_register(FileIconView)

def get_dir_items(dir_path, column_index=0, show_hidden=False):
    '''
    Get children items with given directory path.
    '''
    items = []
    for gfile in get_dir_child_files(dir_path, sort_file_by_name):
        if is_directory(gfile):
            items.append(DirItem(gfile, column_index))
        else:
            items.append(FileItem(gfile, column_index))
            
    return items
