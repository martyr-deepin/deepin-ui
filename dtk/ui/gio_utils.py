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
import os
import collections
import sys
import traceback
import time
from locales import _

file_icon_pixbuf_dict = {}

def get_file_type_dict():
    '''
    @return: Return dictionary include file type.
    '''
    return ([(gio.FILE_TYPE_DIRECTORY, []),
             (gio.FILE_TYPE_SYMBOLIC_LINK, []),
             (gio.FILE_TYPE_MOUNTABLE, []),
             (gio.FILE_TYPE_REGULAR, []),
             (gio.FILE_TYPE_SHORTCUT, []),
             (gio.FILE_TYPE_SPECIAL, []),
             (gio.FILE_TYPE_UNKNOWN, []),
             ])

def get_file_icon_pixbuf(filepath, icon_size):
    '''
    Get icon pixbuf with given filepath.

    @param filepath: File path.
    @return: Return icon pixbuf with given filepath.
    '''
    gfile = gio.File(filepath)
    mime_type = gfile.query_info("standard::content-type").get_content_type()
    if file_icon_pixbuf_dict.has_key(mime_type):
        return file_icon_pixbuf_dict[mime_type]
    else:
        icon_theme = gtk.icon_theme_get_default()
        icon_info = icon_theme.lookup_by_gicon(
            gfile.query_info("standard::icon").get_icon(),
            icon_size,
            gtk.ICON_LOOKUP_USE_BUILTIN)
        if icon_info:
            return icon_info.load_icon()
        # Return unknown icon when icon_info is None.
        else:
            return icon_theme.load_icon("unknown", icon_size, gtk.ICON_LOOKUP_USE_BUILTIN)

def get_dir_child_num(gfile):
    '''
    Get child number with given directory.

    @param gfile: The directory GFile.
    @return: Return number of child files with given directory.
    '''
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

def get_dir_child_infos(dir_path, sort=None, reverse=False, show_hidden=False):
    '''
    Get children FileInfos with given directory path.

    @param dir_path: Directory path.
    @param sort: The function to sort files, this function have two arguments:
     - file_infos: File info list.
     - reverse: Whether sort files reverse.
    @param show_hidden: Show hidden file or not
    @return: Return a list of gio.Fileinfo.
    '''
    # Get gio file.
    gfile = gio.File(dir_path)

    # Return empty list if file not exists.
    if not gfile.query_exists():
        return []
    else:
        gfile_info = gfile.query_info("standard::type")
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
                            if show_hidden == False and file_info.get_name()[0] == '.':
                                continue
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

def get_dir_child_files(dir_path, sort_files=None, reverse=False, show_hidden=False):
    '''
    Get children gio.File with given directory path.

    @param dir_path: Directory path.
    @param sort_files: Whether sort files, default is None.
    @param reverse: Whether sort files reverse, default is False.
    @param show_hidden: Show hidden file or not
    @return: Return a list of gio.File.
    '''
    gfiles = []
    file_infos = get_dir_child_infos(dir_path, sort_files, reverse, show_hidden)
    for (index, file_info) in enumerate(file_infos):
        gfile = gio.File(os.path.join(dir_path, file_infos[index].get_name()))
        gfiles.append(gfile)

    return gfiles

def sort_file_by_name(file_infos, reverse):
    '''
    Sort file info by name.

    @param file_infos: The file info list.
    @param reverse: Whether sort files reverse, default is False.
    '''
    # Init.
    file_info_oreder_dict = collections.OrderedDict(get_file_type_dict())

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

    @param gfile: The GFile.
    @return: Return the name with given gfile, use \"standard::name\" to query info from gfile.
    '''
    return gfile.query_info("standard::name").get_name()

def get_gfile_content_type(gfile):
    '''
    Get type of gfile.

    @param gfile: The GFile.
    @return: Return content type with given gfile, use \"standard::content-type\" to query info from gfile.
    '''
    return gio.content_type_get_description(gfile.query_info("standard::content-type").get_content_type())

def get_gfile_modification_time(gfile):
    '''
    Get modification time.

    @param gfile: The GFile.
    @return: Return modified time with given gfile, use \"time::modified\" to query info from gfile.
    '''
    return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(gfile.query_info("time::modified").get_modification_time()))

def get_gfile_size(gfile):
    '''
    Get size of gfile.

    @param gfile: The GFile.
    @return: Return size of gfile, return number if gfile is directory.
    '''
    if gfile.query_info("standard::type").get_file_type() == gio.FILE_TYPE_DIRECTORY:
        return get_dir_child_num(gfile)
    else:
        return gfile.query_info("standard::size").get_size()

def get_gfile_type(gfile):
    '''
    Get type of gfile.

    @param gfile: The GFile.
    @return: Return type of gfile.
    '''
    return gfile.query_info("standard::type").get_file_type()

def is_directory(gfile):
    '''
    Whether gfile is directory.

    @param gfile: gio.File.
    @return: Return True if gfile is directory, else return False.
    '''
    return gfile.query_info("standard::type").get_file_type() == gio.FILE_TYPE_DIRECTORY

def start_desktop_file(desktop_path):
    '''
    Start application with given desktop path.

    @param desktop_path: The path of desktop file.
    @return: Return True if launch application successfully, otherwise return error string.
    '''
    if not os.path.exists(desktop_path):
        return _("The desktop file doesn't exist: %s") % desktop_path
    else:
        app_info = gio.unix.desktop_app_info_new_from_filename(desktop_path)
        if app_info == None:
            return _("The desktop file is not valid: %s") % desktop_path
        else:
            try:
                app_info.launch()

                return True
            except Exception, e:
                traceback.print_exc(file=sys.stdout)

                return str(e)

if __name__ == "__main__":
    print get_file_icon_pixbuf("/data/Picture/宝宝/ETB8227272-0003.JPG", 24)
    print get_dir_child_files("/")
    print get_dir_child_names("/home/andy")

