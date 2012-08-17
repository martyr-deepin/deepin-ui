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
import gtk

file_icon_pixbuf_dict = {}

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
        return icon_info.load_icon()
    
def get_dir_child_infos(dir_path):
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
                            
                    return file_infos        
            # Return empty list if got error when get enumerator of file.
            except Exception, e:
                print "get_dir_chlidren error: %s" % (e)
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

if __name__ == "__main__":
    print get_file_icon_pixbuf("/data/Picture/宝宝/ETB8227272-0003.JPG", 24)
    print get_dir_child_names("/")
    
