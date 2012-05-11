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

import gtk
from dtk.ui.application import Application
from dtk.ui.constant import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH
from dtk.ui.theme import ui_theme
from dtk.ui.utils import run_command
from dtk.ui.frame import HorizontalFrame, VerticalFrame
from dtk.ui.mplayer_view import MplayerView
from dtk.ui.statusbar import Statusbar
from dtk.ui.dragbar import Dragbar

def show_video(widget, xid):
    '''Show video.'''
    run_command("mplayer -fs -wid %s %s" % (xid, "/data/Video/Manatee.avi"))
    
if __name__ == "__main__":
    # Init application.
    application = Application("demo", False)

    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    
    # Set application icon.
    application.set_icon(ui_theme.get_pixbuf("icon.ico"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "menu", "max", "min", "close"], 
        ui_theme.get_pixbuf("title.png"), 
        "电影播放器",
        "深度Linux视频演示")
    
    # Add mplayer view.
    mplayer_view = MplayerView()
    mplayer_view.connect("get-xid", show_video)
    mplayer_frame = HorizontalFrame()
    mplayer_frame.add(mplayer_view)
    
    main_box = gtk.VBox()
    main_box.pack_start(mplayer_frame)
    
    main_frame = VerticalFrame()
    main_frame.add(main_box)
    application.main_box.pack_start(main_frame)
    
    # Add statusbar.
    statusbar = Statusbar(36)
    main_box.pack_start(statusbar, False)
    application.window.add_move_event(statusbar)
    application.window.add_toggle_event(statusbar)
    
    # Add drag bar.
    Dragbar(application.window, statusbar)
    
    # Run.
    application.run()
