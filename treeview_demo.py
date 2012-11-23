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
from dtk.ui.utils import get_parent_dir
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

def m_single_click_item(widget, event, argv1, argv2, argv3):
    pass
    #print widget, event, argv1, argv2, argv3

def m_delete_select_items(widget, items):
    print widget, items

def m_button_press_item(widget, event, argv1, argv2, argv3):
    pass
    #print widget, event, argv1, argv2, argv3

def m_double_click_item(widget, event, argv1, argv2, argv3):
    pass
    #print widget, event, argv1, argv2, argv3

def m_right_press_items(widget, event, argv1, argv2, argv3):
    print widget, event, argv1, argv2, argv3

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
    print os.path.expanduser("~")
    treeview = TreeView(get_dir_items(os.path.expanduser("~")))
    treeview.set_highlight_item(treeview.get_items()[1])
    treeview.connect("delete-select-items", m_delete_select_items)
    treeview.connect("button-press-item", m_button_press_item)
    treeview.connect("double-click-item", m_double_click_item)
    treeview.connect("right-press-items", m_right_press_items)
    treeview.connect("single-click-item", m_single_click_item)
    # treeview = TreeView(get_dir_items("/"))
    treeview_align = gtk.Alignment()
    treeview_align.set(0.5, 0.5, 1, 1)
    treeview_align.set_padding(0, 2, 2, 2)
    
    treeview.set_column_titles(["文件名", "大小", "类型", "修改时间"],
                               [sort_by_name, sort_by_size, sort_by_type, sort_by_mtime])
    
    treeview_align.add(treeview)
    application.main_box.pack_start(treeview_align)

    application.run()
