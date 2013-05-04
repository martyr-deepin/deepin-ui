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

from dtk.ui.init_skin import init_skin
from deepin_utils.file import get_parent_dir, get_current_dir
import os

init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    )

from dtk.ui.application import Application
from dtk.ui.treeview import TreeView, TextItem
from dtk.ui.constant import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
import gtk

if __name__ == "__main__":
    # Init application.
    application = Application()

    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    # Set application preview pixbuf.
    application.set_skin_preview(os.path.join(get_current_dir(__file__), "frame.png"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "max", "min", "close"], 
        )
    
    # Add TreeView.
    treeview = TreeView()
    treeview.add_items(map(TextItem, ["Node1", "Node2", "Node3"]))
    treeview.visible_items[0].add_items(map(TextItem, ["Node1 - SubNode1", "Node1 - SubNode2", "Node1 - SubNode3"]))
    treeview.visible_items[1].add_items(map(TextItem, ["Node2 - SubNode1", "Node2 - SubNode2", "Node2 - SubNode3"]))
    treeview.visible_items[2].add_items(map(TextItem, ["Node3 - SubNode1", "Node3 - SubNode2", "Node3 - SubNode3"]))
    
    treeview_align = gtk.Alignment()
    treeview_align.set(0.5, 0.5, 1, 1)
    treeview_align.set_padding(0, 2, 2, 2)
    treeview_align.add(treeview)
    
    application.main_box.pack_start(treeview_align)
    application.window.connect("show", lambda w: treeview.visible_highlight())

    application.run()
