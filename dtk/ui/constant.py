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

MENU_ITEM_RADIUS = 2            # menu item radius
DEFAULT_WINDOW_WIDTH = 890      # default window width
DEFAULT_WINDOW_HEIGHT = 631     # default window height

EDGE_DICT = {
    gtk.gdk.TOP_LEFT_CORNER : gtk.gdk.WINDOW_EDGE_NORTH_WEST,
    gtk.gdk.TOP_SIDE : gtk.gdk.WINDOW_EDGE_NORTH,
    gtk.gdk.TOP_RIGHT_CORNER : gtk.gdk.WINDOW_EDGE_NORTH_EAST,
    gtk.gdk.LEFT_SIDE : gtk.gdk.WINDOW_EDGE_WEST,
    gtk.gdk.RIGHT_SIDE : gtk.gdk.WINDOW_EDGE_EAST,      
    gtk.gdk.BOTTOM_LEFT_CORNER : gtk.gdk.WINDOW_EDGE_SOUTH_WEST,
    gtk.gdk.BOTTOM_SIDE : gtk.gdk.WINDOW_EDGE_SOUTH,
    gtk.gdk.BOTTOM_RIGHT_CORNER : gtk.gdk.WINDOW_EDGE_SOUTH_EAST,
    }

WIDGET_POS_TOP_LEFT = 0
WIDGET_POS_TOP_RIGHT = 1
WIDGET_POS_TOP_CENTER = 2
WIDGET_POS_BOTTOM_LEFT = 3
WIDGET_POS_BOTTOM_RIGHT = 4
WIDGET_POS_BOTTOM_CENTER = 5
WIDGET_POS_LEFT_CENTER = 6
WIDGET_POS_RIGHT_CENTER = 7

DEFAULT_FONT = "文泉驿微米黑"

ALIGN_START = 0
ALIGN_END = 1
ALIGN_MIDDLE = 2

BACKGROUND_IMAGE = "background9.jpg"

BUTTON_NORMAL = 0
BUTTON_PRESS = 1
BUTTON_HOVER = 2

DEFAULT_FONT_SIZE = 11
