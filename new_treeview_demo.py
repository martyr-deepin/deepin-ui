#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygtk
import gtk,sys

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

from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.new_treeview import TreeView, TreeItem

win = gtk.Window()

items = [TreeItem()]
new_tree_view = TreeView(items)

win.connect("destroy", lambda w: gtk.main_quit())

win.add(new_tree_view)
win.show_all()

gtk.main()
