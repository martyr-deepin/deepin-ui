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

import gio
from utils import format_file_size
import gtk
import os
import collections
import sys
import traceback
import time

file_icon_pixbuf_dict = {}
FILE_TYPE_COMPARE_WEIGHTS = {
    gio.FILE_TYPE_DIRECTORY : 0,
    gio.FILE_TYPE_SYMBOLIC_LINK : 1,
    gio.FILE_TYPE_MOUNTABLE : 2,
    gio.FILE_TYPE_REGULAR : 3,
    gio.FILE_TYPE_SHORTCUT : 4,
    gio.FILE_TYPE_SPECIAL : 5,
    gio.FILE_TYPE_UNKNOWN : 6
    }

def get_file_icon_pixbuf(filepath, icon_size):
    '''
    Get icon pixbuf with given filepath.

    @param filepath: File path.
    @return: Return icon pixbuf with given filepath.
    '''
    gfile = gio.File(filepath)
    gfile_info = gfile.query_info("standard::*")
    mime_type = gfile_info.get_content_type()
    if file_icon_pixbuf_dict.has_key(mime_type):
        return file_icon_pixbuf_dict[mime_type] 
    else:
        gfile_icon = gfile_info.get_icon()
        icon_theme = gtk.icon_theme_get_default()
        icon_info = icon_theme.lookup_by_gicon(gfile_icon, icon_size, gtk.ICON_LOOKUP_USE_BUILTIN)
        if icon_info:
            return icon_info.load_icon()
        # Return unknown icon when icon_info is None.
        else:
            return icon_theme.load_icon("unknown", icon_size, gtk.ICON_LOOKUP_USE_BUILTIN)
    
def get_dir_child_num(gfile):
    gfile_enumerator = gfile.enumerate_children("standard::*")
    
    # Return empty list if enumerator is None.
    if gfile_enumerator == None:
        return 0
    else:
        child_num = 0
        while True:
            if gfile_enumerator.next_file() == None:
                break
            else:
                child_num += 1
                
        return child_num            
        
def get_dir_child_infos(dir_path, sort=None, reverse=False):
    '''
    Get children FileInfos with given directory path.
    
    @param dir_path: Directory path.
    @return: Return a list of gio.Fileinfo.
    '''
    # Get gio file.
    gfile = gio.File(dir_path)
    
    # Return empty list if file not exists.
    if not gfile.query_exists():    
        return [] 
    else:
        gfile_info = gfile.query_info("standard::*")
        if gfile_info.get_file_type() == gio.FILE_TYPE_DIRECTORY:
            try:
                gfile_enumerator = gfile.enumerate_children("standard::*")
                
                # Return empty list if enumerator is None.
                if gfile_enumerator == None:
                    return []
                else:
                    file_infos = []
                    while True:
                        file_info = gfile_enumerator.next_file()
                        if file_info == None:
                            break
                        else:
                            file_infos.append(file_info)
                            
                    if sort:
                        return sort(file_infos, reverse)
                    else:
                        return file_infos        
            # Return empty list if got error when get enumerator of file.
            except Exception, e:
                print "function get_dir_children got error: %s" % (e)
                traceback.print_exc(file=sys.stdout)
                
                return []
        # Return empty list if file is not directory.
        else:
            return []
        
def get_dir_child_names(dir_path):
    '''
    Get children names with given directory path.
    
    @param dir_path: Directory path.
    @return: Return a list of filepath.
    '''
    return map(lambda info: info.get_name(), get_dir_child_infos(dir_path))

def get_dir_child_files(dir_path, sort_files=None, reverse=False):
    '''
    Get children gio.File with given directory path.

    @param dir_path: Directory path.
    @return: Return a list of gio.File.
    '''
    gfiles = []
    for file_info in get_dir_child_infos(dir_path, sort_files, reverse):
        gfiles.append(gio.File(os.path.join(dir_path, file_info.get_name())))

    return gfiles    
    
def sort_file_by_name(file_infos, reverse):
    '''
    Sort file info by name.
    '''
    # Init.
    file_info_oreder_dict = collections.OrderedDict(
        [(gio.FILE_TYPE_DIRECTORY, []),
         (gio.FILE_TYPE_SYMBOLIC_LINK, []),
         (gio.FILE_TYPE_MOUNTABLE, []),
         (gio.FILE_TYPE_REGULAR, []),
         (gio.FILE_TYPE_SHORTCUT, []),
         (gio.FILE_TYPE_SPECIAL, []),
         (gio.FILE_TYPE_UNKNOWN, []),
         ]
        )
    
    # Split info with different file type.
    for file_info in file_infos:
        file_info_oreder_dict[file_info.get_file_type()].append(file_info)
    
    # Get sorted info list.
    infos = []    
    for (file_type, file_type_infos) in file_info_oreder_dict.items():
        infos += sorted(file_type_infos, key=lambda info: info.get_name())
        
    return infos    

def get_gfile_name(gfile):
    '''
    Get name of gfile.
    '''
    return gfile.query_info("standard::*").get_name()

def get_gfile_type(gfile):
    '''
    Get type of gfile.
    '''
    return gio.content_type_get_description(gfile.query_info("standard::*").get_content_type())

def get_gfile_modification_time(gfile):
    return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(gfile.query_info("time::modified").get_modification_time()))

def get_gfile_size(gfile):
    if gfile.query_info("standard::type").get_file_type() == gio.FILE_TYPE_DIRECTORY:
        return "%s 项" % (get_dir_child_num(gfile))
    else:
        return format_file_size(gfile.query_info("standard::size").get_size())

def is_directory(gfile):
    '''
    Whether gfile is directory.
    
    @param gfile: gio.File.
    @return: Return True if gfile is directory, else return False.
    '''
    return gfile.query_info("standard::*").get_file_type() == gio.FILE_TYPE_DIRECTORY

if __name__ == "__main__":
    print get_file_icon_pixbuf("/data/Picture/宝宝/ETB8227272-0003.JPG", 24)
    print get_dir_child_files("/")
    print get_dir_child_names("/home/andy")
    
