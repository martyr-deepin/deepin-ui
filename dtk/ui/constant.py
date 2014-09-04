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
import pango

MENU_ITEM_RADIUS = 2            # menu item radius
DEFAULT_WINDOW_WIDTH = 890      # default window width
DEFAULT_WINDOW_HEIGHT = 629     # default window height

# Edge dictionary to use in deepin-ui unitive.
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
WIDGET_POS_CENTER = 8

def get_system_font():
    '''
    Helper function to get system font when deepin-ui load.

    This function will create invisible gtk window to get system font, window destroy after detect.

    @return: Return font string in current system.
    '''
    font_test_window = gtk.Window(gtk.WINDOW_POPUP)
    font_test_window.set_default_size(0, 0)
    font_test_window.move(-1000000, -1000000)
    font_name = ' '.join(str(font_test_window.get_pango_context().get_font_description()).split(" ")[0:-1])
    font_test_window.destroy()

    return font_name

DEFAULT_FONT = get_system_font() # get system font

# Align alias.
ALIGN_START = pango.ALIGN_LEFT
ALIGN_MIDDLE = pango.ALIGN_CENTER
ALIGN_END = pango.ALIGN_RIGHT

# Button status.
BUTTON_NORMAL = 0
BUTTON_PRESS = 1
BUTTON_HOVER = 2

# Default font size of deepin-ui.
DEFAULT_FONT_SIZE = 9

# Shadow size.
SHADOW_SIZE = 200

# Color name dictionary.
COLOR_NAME_DICT = {
        "dark_grey" : "#333333",
        "red" : "#FF0000",
        "orange" : "#FF6C00",
        "gold" : "#FFC600",
        "yellow" : "#FCFF00",
        "green_yellow" : "#C0FF00",
        "chartreuse" : "#00FF00",
        "cyan" : "#00FDFF",
        "dodger_blue" : "#00A8FF",
        "blue" : "#006AFF",
        "dark_purple" : "#6A00FF",
        "purple" : "#BA00FF",
        "deep_pink" : "#FF00B4"
        }
BLACK_COLOR_MAPPED = "dark_grey" # when detect `black` use `dark grey` instead
WHITE_COLOR_MAPPED = "dodger_blue" # when detect `white` use `dodger blue` instead
COLOR_SEQUENCE = ["red", "orange", "gold", "yellow", "green_yellow", "chartreuse", "dark_grey",
                  "deep_pink", "purple", "dark_purple", "blue", "dodger_blue", "cyan"]
SIMILAR_COLOR_SEQUENCE = ["red", "orange", "gold", "yellow", "green_yellow", "chartreuse",
                          "deep_pink", "purple", "dark_purple", "blue", "dodger_blue", "cyan"]

# Version.
VERSION = "1.0.3"

# Size of paned handle in deepin-ui.
PANED_HANDLE_SIZE = 11
