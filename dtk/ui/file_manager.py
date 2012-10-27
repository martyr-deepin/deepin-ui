#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Zhai Xiang
# 
# Author:     Zhai Xiang <xiangzhai83@gmail.com>
# Maintainer: Zhai Xiang <xiangzhai83@gmail.com>
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

import gtk
import os
from locales import _
from theme import ui_theme
from dtk.ui.paned import HPaned
from dtk.ui.categorybar import Categorybar
from new_treeview import TreeView
from dtk.ui.file_treeview import (get_dir_items, sort_by_name, sort_by_size,
                                  sort_by_type, sort_by_mtime)

class FileManager(HPaned):
    HOME_DIR = os.getenv("HOME", "") + "/"

    def __init__(self, 
                 dir=HOME_DIR
                ):
        HPaned.__init__(self)
        self.categorybar = Categorybar([
            (ui_theme.get_pixbuf("filemanager/computer.png"), _("Computer"), None), 
            (ui_theme.get_pixbuf("filemanager/user-home.png"), _("Home"), lambda : self.open_dir(self.HOME_DIR)),
            (ui_theme.get_pixbuf("filemanager/user-desktop.png"), _("Desktop"), lambda : self.open_dir(self.HOME_DIR + "Desktop/")),
            (ui_theme.get_pixbuf("filemanager/folder-documents.png"), _("Documents"), lambda : self.open_dir(self.HOME_DIR + "Documents/")),
            (ui_theme.get_pixbuf("filemanager/folder-download.png"), _("Downloads"), lambda : self.open_dir(self.HOME_DIR + "Downloads/")),
            (ui_theme.get_pixbuf("filemanager/folder-music.png"), _("Music"), lambda : self.open_dir(self.HOME_DIR + "Music/")),
            (ui_theme.get_pixbuf("filemanager/folder-pictures.png"), _("Pictures"), lambda : self.open_dir(self.HOME_DIR + "Pictures/")),
            (ui_theme.get_pixbuf("filemanager/folder-videos.png"), _("Videos"), lambda : self.open_dir(self.HOME_DIR + "Videos/")),
            (ui_theme.get_pixbuf("filemanager/user-trash.png"), _("Trash"), lambda : self.open_dir("trash:///"))
            ])
        self.treeview = TreeView(get_dir_items(dir))
        '''
        FIXME: add set_column_titles then blocked
        self.treeview.set_column_titles([_("Name"), _("Size"), _("Type"), _("Edit Time")],
                                        [sort_by_name, sort_by_size, sort_by_type, sort_by_mtime])
        '''
        self.add1(self.categorybar)
        self.add2(self.treeview)

    def open_dir(self, dir):
        self.treeview.add_items(get_dir_items(dir), None, True)
