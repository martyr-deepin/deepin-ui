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

from dtk.ui.init_skin import init_skin
from deepin_utils.file import get_parent_dir
import os

app_theme = init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )

from dtk.ui.application import Application
from dtk.ui.new_treeview import TreeView
from dtk.ui.constant import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from dtk.ui.file_treeview import (get_dir_items, sort_by_name, sort_by_size,
                                  sort_by_type, sort_by_mtime)
import gtk

try:
    import deepin_tzmap
except ImportError:
    print "-----------------------Please Install Python cc-timzone-map Widget Binding----------------------"
    print "https://github.com/linuxdeepin/deepin-system-settings/tree/master/modules/date_time/src/examples"
    print "------------------------------------------------------------------------------------------------"

if __name__ == "__main__":
    # Init application.
    application = Application()

    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    # Set application icon.
    application.set_icon(app_theme.get_pixbuf("icon.ico"))
    
    # Set application preview pixbuf.
    application.set_skin_preview(app_theme.get_pixbuf("frame.png"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "max", "min", "close"], 
        app_theme.get_pixbuf("logo.png"), 
        "TreeView demo",
        "TreeView demo",
        )
    
    # Add TreeView.
    deepin_tzmap1 = deepin_tzmap.new()
    align = gtk.Alignment()
    align.set(0.5, 0.5, 1, 1)
    align.set_padding(0, 2, 2, 2)
    align.add(deepin_tzmap1)
    
    application.main_box.pack_start(align)

    application.run()
