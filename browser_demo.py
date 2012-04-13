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

from dtk.ui.application import Application
from dtk.ui.constant import *
from dtk.ui.menu import *
from dtk.ui.navigatebar import *
from dtk.ui.statusbar import *
from dtk.ui.categorybar import *
from dtk.ui.scrolled_window import *
from dtk.ui.box import *
from dtk.ui.button import *
from dtk.ui.listview import *
from dtk.ui.tooltip import *
from dtk.ui.popup_window import *
from dtk.ui.frame import *
from dtk.ui.dragbar import *
from dtk.ui.scalebar import *
from dtk.ui.volume_button import *
from dtk.ui.entry import *
from dtk.ui.paned import *
from dtk.ui.label import *
from dtk.ui.browser import *

if __name__ == "__main__":
    # Init application.
    application = Application("demo")
    
    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    
    # Set application icon.
    application.set_icon(ui_theme.get_pixbuf("icon.ico"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "menu", "max", "min", "close"], 
        ui_theme.get_pixbuf("title.png"), 
        "深度图形库",
        "/home/andy/deepin-ui/demo.py")
    
    # Add browser.
    horizontal_frame = HorizontalFrame()
    browser_client = BrowserClient("http://www.linuxdeepin.com/forum", "/home/andy/cookie.txt")
    horizontal_frame.add(browser_client)
    application.main_box.pack_start(horizontal_frame)
    
    # Run.
    application.run()
