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

from skin_config import skin_config
from deepin_utils.file import create_directory, eval_file, get_parent_dir
import gtk
import os

class DynamicColor(object):
    '''
    Dynamic color.
    '''

    def __init__(self, color):
        '''
        Initialize DynamicColor.

        @param color: Initialize color.
        '''
        self.update(color)

    def update(self, color):
        '''
        Update color.

        @param color: Color value.
        '''
        self.color = color

    def get_color(self):
        '''
        Get color.

        @return: Return current color value.
        '''
        return self.color

class DynamicAlphaColor(object):
    '''
    Dynamic alpha color.
    '''

    def __init__(self, color_info):
        '''
        Initialize DynamicAlphaColor class.

        @param color_info: Color information, format as (hex_color, alpha)
        '''
        self.update(color_info)

    def update(self, color_info):
        '''
        Update color_info with given value.
        '''
        (self.color, self.alpha) = color_info

    def get_color_info(self):
        '''
        Get color info.

        @return: Return color information, format as (hex_color, alpha)
        '''
        return (self.color, self.alpha)

    def get_color(self):
        '''
        Get color.

        @return: Return hex color string.
        '''
        return self.color

    def get_alpha(self):
        '''
        Get alpha value.

        @return: Return alpha value.
        '''
        return self.alpha

class DynamicShadowColor(object):
    '''
    Dynamic shadow color.
    '''

    def __init__(self, color_info):
        '''
        Initialize DynamicShadowColor class.

        @param color_info: Color information, format as:

        >>> [(color_position_1, (hex_color_1, color_alpha_1),
        >>>  (color_position_2, (hex_color_2, color_alpha_2),
        >>>  (color_position_3, (hex_color_3, color_alpha_3)]
        '''
        self.update(color_info)

    def update(self, color_info):
        '''
        Update color with given value.

        @param color_info: Color information, format as:

        >>> [(color_position_1, (hex_color_1, color_alpha_1),
        >>>  (color_position_2, (hex_color_2, color_alpha_2),
        >>>  (color_position_3, (hex_color_3, color_alpha_3)]
        '''
        self.color_info = color_info

    def get_color_info(self):
        '''
        Get color information.

        @return: Return color information, format as:

        >>> [(color_position_1, (hex_color_1, color_alpha_1),
        >>>  (color_position_2, (hex_color_2, color_alpha_2),
        >>>  (color_position_3, (hex_color_3, color_alpha_3)]
        '''
        return self.color_info

class DynamicPixbuf(object):
    '''
    Dynamic pixbuf.
    '''

    def __init__(self, filepath):
        '''
        Initialize DynamicPixbuf class.

        @param filepath: Dynamic pixbuf filepath.
        '''
        self.update(filepath)

    def update(self, filepath):
        '''
        Update filepath with given value.

        @param filepath: Dynamic pixbuf filepath.
        '''
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filepath)

    def get_pixbuf(self):
        '''
        Get pixbuf.
        '''
        return self.pixbuf

class Theme(object):
    '''
    Theme.

    @undocumented: get_ticker
    '''

    def __init__(self,
                 system_theme_dir,
                 user_theme_dir):
        '''
        Initialize Theme class.

        @param system_theme_dir: Default theme directory.
        @param user_theme_dir: User's theme save directory, generic is ~/.config/project-name/theme
        '''
        # Init.
        self.system_theme_dir = system_theme_dir
        self.user_theme_dir = user_theme_dir
        self.theme_info_file = "theme.txt"
        self.ticker = 0
        self.pixbuf_dict = {}
        self.color_dict = {}
        self.alpha_color_dict = {}
        self.shadow_color_dict = {}

        # Create directory if necessarily.
        for theme_dir in [self.system_theme_dir, self.user_theme_dir]:
            create_directory(theme_dir)

    def load_theme(self):
        '''
        Load theme.
        '''
        self.theme_name = skin_config.theme_name

        # Scan dynamic theme_info file.
        theme_info = eval_file(self.get_theme_file_path(self.theme_info_file))

        # Init dynamic colors.
        for (color_name, color) in theme_info["colors"].items():
            self.color_dict[color_name] = DynamicColor(color)

        # Init dynamic alpha colors.
        for (color_name, color_info) in theme_info["alpha_colors"].items():
            self.alpha_color_dict[color_name] = DynamicAlphaColor(color_info)

        # Init dynamic shadow colors.
        for (color_name, color_info) in theme_info["shadow_colors"].items():
            self.shadow_color_dict[color_name] = DynamicShadowColor(color_info)

        # Add in theme list of skin_config.
        skin_config.add_theme(self)

    def get_theme_file_path(self, filename):
        '''
        Get theme file path with given theme name.

        @return: Return filepath of theme.
        '''
        theme_file_dir = None
        for theme_dir in [self.system_theme_dir, self.user_theme_dir]:
            if os.path.exists(theme_dir):
                if self.theme_name in os.listdir(os.path.expanduser(theme_dir)):
                    theme_file_dir = theme_dir
                    break

        if theme_file_dir:
            return os.path.join(theme_file_dir, self.theme_name, filename)
        else:
            return None

    def get_pixbuf(self, path):
        '''
        Get pixbuf with given relative path.

        @param path: Image relative filepath to theme.

        @return: Return pixbuf with given relative path.
        '''
        # Just init pixbuf_dict when first load some pixbuf.
        if not self.pixbuf_dict.has_key(path):
            self.pixbuf_dict[path] = DynamicPixbuf(self.get_theme_file_path("image/%s" % (path)))

        return self.pixbuf_dict[path]

    def get_color(self, color_name):
        '''
        Get color with given dynamic color.

        @param color_name: DynamicColor name from theme.txt.

        @return: Return color with given dynamic color.
        '''
        return self.color_dict[color_name]

    def get_alpha_color(self, color_name):
        '''
        Get color with given dynamic alpha color.

        @param color_name: DynamicAlphaColor name from theme.txt.

        @return: Return color with given dynamic alpha color.
        '''
        return self.alpha_color_dict[color_name]

    def get_shadow_color(self, color_name):
        '''
        Get color with given dynamic shadow color.

        @param color_name: DynamicShadowColor name from theme.txt.

        @return: Return color with given dynamic shadow color.
        '''
        return self.shadow_color_dict[color_name]

    def get_ticker(self):
        '''
        Internal function to get ticker.
        '''
        return self.ticker

    def change_theme(self, new_theme_name):
        '''
        Change theme with given new theme name.

        @param new_theme_name: New theme name.
        '''
        # Update ticker.
        self.ticker += 1

        # Change theme name.
        self.theme_name = new_theme_name

        # Update dynamic pixbuf.
        for (path, pixbuf) in self.pixbuf_dict.items():
            pixbuf.update(self.get_theme_file_path("image/%s" % (path)))

        # Update dynamic colors.
        theme_info = eval_file(self.get_theme_file_path(self.theme_info_file))

        for (color_name, color) in theme_info["colors"].items():
            self.color_dict[color_name].update(color)

        # Update dynamic alpha colors.
        for (color_name, color_info) in theme_info["alpha_colors"].items():
            self.alpha_color_dict[color_name].update(color_info)

        # Update shadow colors.
        for (color_name, color_info) in theme_info["shadow_colors"].items():
            self.shadow_color_dict[color_name].update(color_info)

# Init.
ui_theme = Theme(os.path.join(get_parent_dir(__file__, 2), "theme"),
                 os.path.expanduser("~/.config/deepin-ui/theme"))
