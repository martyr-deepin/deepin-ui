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
from deepin_utils.file import get_parent_dir, get_current_dir
import os

app_theme = init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )

from dtk.ui.application import Application
from dtk.ui.dragable_tab import TabBox
from dtk.ui.constant import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
import gtk

if __name__ == "__main__":
    # Init application.
    application = Application()

    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    # Set application icon.
    application.set_icon(app_theme.get_pixbuf("icon.ico"))
    
    # Set application preview pixbuf.
    application.set_skin_preview(os.path.join(get_current_dir(__file__), "frame.png"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "max", "min", "close"], 
        app_theme.get_pixbuf("logo.png"), 
        "Tab demo",
        "Tab demo",
        )
    
    tabbox = TabBox()
    align = gtk.Alignment()
    align.set(0.5, 0.5, 1, 1)
    align.set_padding(2, 2, 2, 2)
    align.add(tabbox)
    
    
    application.main_box.pack_start(align)

    application.run()
