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
from utils import eval_file, get_parent_dir, create_directory
import gtk
import os

class DynamicTreeView(object):
    '''Dynamic tree view.'''
	
    def __init__(self, get_theme_ticker, parent, liststore, background_dcolor, select_dcolor):
        '''Init dynamic tree view.'''
        self.get_theme_ticker = get_theme_ticker
        self.tree_view = gtk.TreeView(liststore)
        self.background_dcolor = background_dcolor
        self.select_dcolor = select_dcolor
        self.ticker = 0
        
        self.update_color()
        self.tree_view.connect("expose-event", self.expose_callback)
        
        parent.connect("size-allocate", lambda w, e: self.tree_view.realize())
        
    def update_color(self):
        '''Update color.'''
        self.tree_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.background_dcolor.get_color()))
        self.tree_view.modify_base(gtk.STATE_ACTIVE, gtk.gdk.color_parse(self.select_dcolor.get_color()))
        
    def expose_callback(self, widget, event):
        '''Expose callback.'''
        if self.ticker != self.get_theme_ticker():
            self.ticker = self.get_theme_ticker()
            self.update_color()
            
        return False

class DynamicTextView(object):
    '''Dynamic text view.'''
	
    def __init__(self, get_theme_ticker, parent, background_dcolor, foreground_dcolor, background_dpixbuf=None):
        '''Init dynamic text view.'''
        self.get_theme_ticker = get_theme_ticker
        self.text_view = gtk.TextView()
        self.background_dcolor = background_dcolor
        self.foreground_dcolor = foreground_dcolor
        self.background_dpixbuf = background_dpixbuf
        self.ticker = 0

        self.update_color()
        self.text_view.connect("expose-event", self.expose_callback)
        self.text_view.connect("realize", lambda w: self.update_background())
        
        parent.connect("size-allocate", lambda w, e: self.text_view.realize())
        
    def update_color(self):
        '''Update color.'''
        self.text_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.background_dcolor.get_color()))
        self.text_view.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.foreground_dcolor.get_color()))
        self.update_background()
        
    def update_background(self):
        '''Update background.'''
        if self.background_dpixbuf != None and self.text_view.get_realized():
            (pixmap, _) = self.background_dpixbuf.get_pixbuf().render_pixmap_and_mask(127)
            self.text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_back_pixmap(pixmap, False)
        
    def expose_callback(self, widget, event):
        '''Expose callback.'''
        if self.ticker != self.get_theme_ticker():
            self.ticker = self.get_theme_ticker()
            self.update_color()
            
        return False
    
class DynamicColor(object):
    '''Dynamic color.'''
    
    def __init__(self, color):
        '''Init.'''
        self.update(color)
        
    def update(self, color):
        '''Update path.'''
        self.color = color

    def get_color(self):
        '''Get color.'''
        return self.color

class DynamicAlphaColor(object):
    '''Dynamic alpha color.'''
    
    def __init__(self, color_info):
        '''Init.'''
        self.update(color_info)
        
    def update(self, color_info):
        '''Update path.'''
        (self.color, self.alpha) = color_info
        
    def get_color_info(self):
        '''Get color info.'''
        return (self.color, self.alpha)

    def get_color(self):
        '''Get color info.'''
        return self.color
    
    def get_alpha(self):
        '''Get alpha.'''
        return self.alpha
    
class DynamicShadowColor(object):
    '''Dynamic shadow color.'''
	
    def __init__(self, color_info):
        '''Init.'''
        self.update(color_info)
        
    def update(self, color_info):
        '''Update path.'''
        self.color_info = color_info
        
    def get_color_info(self):
        '''Get color info.'''
        return self.color_info

class DynamicPixbuf(object):
    '''Dynamic pixbuf.'''
    
    def __init__(self, filepath):
        '''Init.'''
        self.update(filepath)
        
    def update(self, filepath):
        '''Update path.'''
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filepath)

    def get_pixbuf(self):
        '''Get pixbuf.'''
        return self.pixbuf

class Theme(object):
    '''Theme.'''
    
    def __init__(self, system_theme_dir, user_theme_dir):
        '''Init theme.'''
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
        '''Load.'''
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
        '''Get theme file path.'''
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
        '''Get dynamic pixbuf.'''
        # Just init pixbuf_dict when first load some pixbuf.
        if not self.pixbuf_dict.has_key(path):
            self.pixbuf_dict[path] = DynamicPixbuf(self.get_theme_file_path("image/%s" % (path)))
            
        return self.pixbuf_dict[path]

    def get_color(self, color_name):
        '''Get dynamic color.'''
        return self.color_dict[color_name]
    
    def get_alpha_color(self, color_name):
        '''Get dynamic alpha color.'''
        return self.alpha_color_dict[color_name]
    
    def get_shadow_color(self, color_name):
        '''Get dynamic shadow color.'''
        return self.shadow_color_dict[color_name]    
    
    def get_ticker(self):
        '''Get ticker.'''
        return self.ticker    
    
    def change_theme(self, new_theme_name):
        '''Change ui_theme.'''
        # Update ticker.
        self.ticker += 1
        
        # Change theme name.
        self.theme_name = new_theme_name

        # Update dynmaic pixbuf.
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
