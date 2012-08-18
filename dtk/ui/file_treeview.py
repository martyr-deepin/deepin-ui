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

from new_treeview import TreeItem
from gio_utils import get_file_icon_pixbuf, is_directory, get_dir_child_files, get_gfile_name
from draw import draw_pixbuf, draw_text
import gobject

ICON_SIZE = 24
ICON_PADDING_LEFT = ICON_PADDING_RIGHT = 4

class DirItem(TreeItem):
    '''
    Directory item.
    '''
	
    def __init__(self, gfile):
        '''
        Initialize DirItem class.
        '''
        # Init.
        TreeItem.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.directory_path = gfile.get_path()
        self.pixbuf = get_file_icon_pixbuf(self.directory_path, ICON_SIZE)
        
    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + ICON_PADDING_LEFT, 
                    rect.y)
        
        # Draw directory name.
        draw_text(cr, self.name, 
                  rect.x + ICON_SIZE + ICON_PADDING_LEFT + ICON_PADDING_RIGHT, 
                  rect.y, rect.width, rect.height)
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        return ICON_SIZE
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        return [self.render_name]
    
gobject.type_register(DirItem)

class FileItem(TreeItem):
    '''
    File item.
    '''
	
    def __init__(self, gfile):
        '''
        Initialize FileItem class.
        '''
        TreeItem.__init__(self)
        self.gfile = gfile
        self.name = get_gfile_name(self.gfile)
        self.file_path = gfile.get_path()
        self.pixbuf = get_file_icon_pixbuf(self.file_path, ICON_SIZE)
        
    def render_name(self, cr, rect):
        '''
        Render icon and name of DirItem.
        '''
        # Draw directory icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + ICON_PADDING_LEFT, 
                    rect.y)
        
        # Draw directory name.
        draw_text(cr, self.name, 
                  rect.x + ICON_SIZE + ICON_PADDING_LEFT + ICON_PADDING_RIGHT, 
                  rect.y, rect.width, rect.height)
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        return ICON_SIZE
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        return [self.render_name]
        
gobject.type_register(DirItem)

class LoadingItem(TreeItem):
    '''
    Loadding item.
    '''
	
    def __init__(self):
        '''
        Initialize LoadingItem class.
        '''
        TreeItem.__init__(self)
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        pass
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        pass
    
gobject.type_register(LoadingItem)

class EmptyItem(TreeItem):
    '''
    Loadding item.
    '''
	
    def __init__(self):
        '''
        Initialize EmptyItem class.
        '''
        TreeItem.__init__(self)
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        pass
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        pass
    
gobject.type_register(EmptyItem)

def get_dir_items(dir_path):
    '''
    Get children items with given directory path.
    '''
    items = []
    for gfile in get_dir_child_files(dir_path):
        if is_directory(gfile):
            items.append(DirItem(gfile))
        else:
            items.append(FileItem(gfile))
            
    return items
