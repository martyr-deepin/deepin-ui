#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Deepin, Inc.
#               2013 Zhai Xiang
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
from dtk.ui.address_entry import IpAddressEntry, MacAddressEntry
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
    application.set_skin_preview(app_theme.get_pixbuf("frame.png"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "max", "min", "close"], 
        app_theme.get_pixbuf("logo.png"), 
        "IpAddressEntry demo",
        "IpAddressEntry demo",
        )
    
    align1 = gtk.Alignment()                                             
    align1.set(0, 0, 0, 0)                                           
    align1.set_padding(10, 10, 10, 10)
    ip_address_entry = IpAddressEntry("192.168.1.16")
    print "DEBUG", ip_address_entry.get_address()
    align1.add(ip_address_entry)
    align2 = gtk.Alignment()
    align2.set(0, 0, 0, 0)
    align2.set_padding(10, 10, 10, 10)
    mac_address_entry = MacAddressEntry("60:eb:69:5c:3f:2b")
    align2.add(mac_address_entry)
    application.main_box.pack_start(align1)
    application.main_box.pack_start(align2)

    application.run()
