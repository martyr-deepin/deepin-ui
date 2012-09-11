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

from dtk.ui.init_skin import init_skin
from dtk.ui.utils import get_parent_dir
import os

app_theme = init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )

# from dtk.ui.window import EmbedWindow
from dtk.ui.window import Window, PlugWindow
from dtk.ui.application import Application
from dtk.ui.new_treeview import TreeView
from dtk.ui.constant import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from dtk.ui.file_treeview import (get_dir_items, sort_by_name, sort_by_size,
                                  sort_by_type, sort_by_mtime)
import gtk

if __name__ == "__main__":
    gtk.gdk.threads_init()
    
    # window = EmbedWindow()
    # window = Window(is_embed=True)
    window = PlugWindow()
    window.set_default_size(200, 100)
    
    # window.window_frame.add(gtk.Button("Test Builder"))
    
    window.show_all()
    
    gtk.main()
