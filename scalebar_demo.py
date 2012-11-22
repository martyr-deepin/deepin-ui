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
from dtk.ui.scalebar import HScalebar
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
        "Scalebar demo",
        "Scalebar demo",
        )
    
    # Add Scalebar.
    hscale1 = HScalebar(
        app_theme.get_pixbuf("scalebar/l_fg.png"), 
        app_theme.get_pixbuf("scalebar/l_bg.png"), 
        app_theme.get_pixbuf("scalebar/m_fg.png"), 
        app_theme.get_pixbuf("scalebar/m_bg.png"), 
        app_theme.get_pixbuf("scalebar/r_fg.png"), 
        app_theme.get_pixbuf("scalebar/r_bg.png"), 
        app_theme.get_pixbuf("scalebar/point.png"))
    adjust1 = gtk.Adjustment(0, -1.0, 1.0)
    hscale1.set_adjustment(adjust1)
    hscale1.add_mark(0, HScalebar.POS_TOP, "0")
    hscale1.add_mark(adjust1.get_lower(), HScalebar.POS_BOTTOM, "左")
    hscale1.add_mark(adjust1.get_upper(), HScalebar.POS_BOTTOM, "右")
    hscale1_align = gtk.Alignment()
    hscale1_align.set(0.5, 0.5, 1, 1)
    hscale1_align.set_padding(0, 2, 2, 2)
    hscale1_align.add(hscale1)
    
    hscale2 = HScalebar(
        app_theme.get_pixbuf("scalebar/l_fg.png"), 
        app_theme.get_pixbuf("scalebar/l_bg.png"), 
        app_theme.get_pixbuf("scalebar/m_fg.png"), 
        app_theme.get_pixbuf("scalebar/m_bg.png"), 
        app_theme.get_pixbuf("scalebar/r_fg.png"), 
        app_theme.get_pixbuf("scalebar/r_bg.png"), 
        app_theme.get_pixbuf("scalebar/point.png"), 
        True, 
        " %")
    adjust2 = gtk.Adjustment(0, 0, 150)
    hscale2.set_adjustment(adjust2)
    #hscale2.set_size_request(100, 0)
    hscale2_align = gtk.Alignment()
    hscale2_align.set(0.5, 0.5, 1, 1)
    hscale2_align.set_padding(0, 2, 2, 2)
    hscale2_align.add(hscale2)
    
    application.main_box.pack_start(hscale1_align)
    application.main_box.pack_start(hscale2_align)

    application.run()
