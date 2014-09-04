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

# This module *just* use for test module under dtk.ui

from skin_config import skin_config
from theme import Theme, ui_theme
from deepin_utils.file import get_parent_dir
import os

# Init skin config.
skin_config.init_skin(
    "01",
    os.path.join(get_parent_dir(__file__, 3), "skin"),
    os.path.expanduser("~/.config/deepin-demo/skin"),
    os.path.expanduser("~/.config/deepin-demo/skin_config.ini"),
    "deepin-media-player",
    "1.0"
    )

# Create application theme.
app_theme = Theme(
    os.path.join(get_parent_dir(__file__, 3), "app_theme"),
    os.path.expanduser("~/.config/deepin-demo/theme")
    )

# Set theme.
skin_config.load_themes(ui_theme, app_theme)
