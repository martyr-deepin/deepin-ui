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

import os
import gobject
from locales import _
from theme import ui_theme
from paned import HPaned
from categorybar import Categorybar
from file_iconview import (FileIconView, iconview_get_dir_items)
from treeview import TreeView
from file_treeview import get_dir_items

class FileManager(HPaned):
    HOME_DIR = os.getenv("HOME", "") + "/"
    ICONVIEW = 0
    TREEVIEW = 1

    def __init__(self,
                 dir=HOME_DIR,
                 view_mode=ICONVIEW
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
        self.icon_size = 48
        self.iconview = FileIconView()
        self.iconview.add_items(iconview_get_dir_items(dir, self.icon_size))
        self.treeview = TreeView(get_dir_items(dir))
        self.add1(self.categorybar)
        if view_mode == self.ICONVIEW:
            self.add2(self.iconview)
        else:
            self.add2(self.treeview)

    def open_dir(self, dir):
        self.iconview.add_items(iconview_get_dir_items(dir), True)
        self.treeview.add_items(get_dir_items(dir), None, True)

gobject.type_register(FileManager)
