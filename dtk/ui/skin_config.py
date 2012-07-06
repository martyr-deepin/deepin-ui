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

from cache_pixbuf import CachePixbuf
from config import Config
from constant import SHADE_SIZE, COLOR_SEQUENCE
from draw import draw_pixbuf, draw_vlinear, draw_hlinear
from utils import color_hex_to_cairo, remove_file, touch_file, create_directory
import gobject
import gtk
import os
import tarfile
import uuid

class SkinConfig(gobject.GObject):
    '''SkinConfig.'''
	
    def __init__(self):
        '''Init skin.'''
        # Init.
        gobject.GObject.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        
        self.theme_list = []
        self.window_list = []
        
    def set_application_window_size(self, app_window_width, app_window_height):
        '''Set application window size.'''
        self.app_window_width = app_window_width
        self.app_window_height = app_window_height
        
    def update_image_size(self, x, y, scale_x, scale_y):
        '''Update image size.'''
        self.x = x
        self.y = y
        self.scale_x = scale_x
        self.scale_y = scale_y
        
    def get_skin_file_path(self, filename):
        '''Get skin file path.'''
        skin_file_dir = None
        for skin_dir in [self.system_skin_dir, self.user_skin_dir]:
            if os.path.exists(skin_dir):
                if self.skin_name in os.listdir(os.path.expanduser(skin_dir)):
                    skin_file_dir = skin_dir
                    break
            
        if skin_file_dir:
            return os.path.join(skin_file_dir, self.skin_name, filename)
        else:
            return None
        
    def is_skin_exist(self, skin_name, system_skin_dir, user_skin_dir):
        '''Is skin exist in skin directories.'''
        for skin_dir in [system_skin_dir, user_skin_dir]:
            if os.path.exists(skin_dir):
                if skin_name in os.listdir(os.path.expanduser(skin_dir)):
                    return True
                
        return False        
    
    def get_default_skin(self, system_skin_dir, user_skin_dir):
        '''Get default skin.'''
        for skin_dir in [system_skin_dir, user_skin_dir]:
            if os.path.exists(skin_dir):
                skin_list = os.listdir(os.path.expanduser(skin_dir))
                if len(skin_list) > 0:
                    return skin_list[0]
                
        return None        
        
    def get_skin_dir(self):
        '''Get skin dir.'''
        for skin_dir in [self.system_skin_dir, self.user_skin_dir]:
            if os.path.exists(skin_dir):
                if self.skin_name in os.listdir(os.path.expanduser(skin_dir)):
                    return os.path.join(skin_dir, self.skin_name)                
                
        return None       
        
    def init_skin(self, skin_name, system_skin_dir, user_skin_dir, skin_config_file,
                  app_given_id, app_given_version):
        '''Init skin.'''
        self.skin_config_file = skin_config_file
        if os.path.exists(skin_config_file):
            # Read skin name from config file.
            skin_config = Config(skin_config_file)
            skin_config.load()
            
            # Load skin.
            init_skin_name = skin_config.get("skin", "skin_name")
        else:
            # Create skin config if it not exists.
            touch_file(self.skin_config_file)
            
            init_skin_name = skin_name
            
        if self.is_skin_exist(init_skin_name, system_skin_dir, user_skin_dir):
            self.load_skin(init_skin_name, system_skin_dir, user_skin_dir)
        else:
            # Try load default skin if user's select skin not exists.
            default_skin_name = self.get_default_skin(system_skin_dir, user_skin_dir)
            assert(default_skin_name != None)
            self.load_skin(default_skin_name, system_skin_dir, user_skin_dir)
            
        self.app_given_id = app_given_id
        self.app_given_version = app_given_version
        
    def save_skin_name(self):
        '''Save skin name.'''
        skin_config = Config(self.skin_config_file)
        skin_config.load()
        if skin_config.get("skin", "skin_name") != self.skin_name:
            skin_config.set("skin", "skin_name", self.skin_name)
            skin_config.write(self.skin_config_file)
            
    def reload_skin(self, skin_name=None):
        '''Reload skin.'''
        if skin_name:
            return self.load_skin(skin_name)
        else:
            return self.load_skin(self.skin_name)
        
    def load_skin(self, skin_name, system_skin_dir=None, user_skin_dir=None):
        '''Load skin, return True if load finish, otherwise return False.'''
        try:
            # Save skin dir.
            self.skin_name = skin_name
            
            if system_skin_dir:
                self.system_skin_dir = system_skin_dir
                create_directory(self.system_skin_dir)
                
            if user_skin_dir:
                self.user_skin_dir = user_skin_dir
                create_directory(self.user_skin_dir)
                
            self.skin_dir = self.get_skin_dir()
            
            # Load config file.
            self.config = Config(self.get_skin_file_path("config.ini"))
            self.config.load()
            
            # Get theme config.
            self.theme_name = self.config.get("theme", "theme_name")
            
            # Get application config.
            self.app_id = self.config.get("application", "app_id")
            self.app_version = self.config.getfloat("application", "app_version")
            
            # Get background config.
            self.image = self.config.get("background", "image")
            self.x = self.config.getfloat("background", "x")
            self.y = self.config.getfloat("background", "y")
            self.scale_x = self.config.getfloat("background", "scale_x")
            self.scale_y = self.config.getfloat("background", "scale_y")
            self.dominant_color = self.config.get("background", "dominant_color")
            
            # Get action config.
            self.deletable = self.config.getboolean("action", "deletable")
            self.editable = self.config.getboolean("action", "editable")
            self.vertical_mirror = self.config.getboolean("action", "vertical_mirror")
            self.horizontal_mirror = self.config.getboolean("action", "horizontal_mirror")
            
            # Generate background pixbuf.
            self.background_pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_skin_file_path(self.image))
            
            # Save skin name.
            self.save_skin_name()

            return True
        except Exception, e:
            print "load_skin error: %s" % (e)
            return False
    
    def save_skin(self, given_filepath=None):
        '''Save skin.'''
        self.config.set("theme", "theme_name", self.theme_name)
        
        self.config.set("background", "x", self.x)
        self.config.set("background", "y", self.y)
        self.config.set("background", "scale_x", self.scale_x)
        self.config.set("background", "scale_y", self.scale_y)
        
        self.config.set("action", "vertical_mirror", self.vertical_mirror)
        self.config.set("action", "horizontal_mirror", self.horizontal_mirror)
        
        self.config.write(given_filepath)
    
    def change_theme(self, theme_name):
        '''Change theme.'''
        self.theme_name = theme_name        
        
        self.apply_skin()
        
    def apply_skin(self):
        '''Apply skin.'''
        # Change theme.
        for theme in self.theme_list:
            if theme.theme_name != self.theme_name:
                theme.change_theme(self.theme_name)
            
        # Redraw application.
        for window in self.window_list:
            window.queue_draw()
    
    def add_theme(self, theme):
        '''Add theme.'''
        if not theme in self.theme_list:
            self.theme_list.append(theme)
            
    def remove_theme(self, theme):
        '''Remove theme.'''
        if theme in self.theme_list:
            self.theme_list.remove(theme)
    
    def wrap_skin_window(self, window):
        '''Wrap skin window.'''
        self.add_skin_window(window)    
        window.connect("destroy", lambda w: self.remove_skin_window(w))
    
    def add_skin_window(self, window):
        '''Add skin window.'''
        if not window in self.window_list:
            self.window_list.append(window)
            
    def remove_skin_window(self, window):
        '''Remove skin window.'''
        if window in self.window_list:
            self.window_list.remove(window)
            
    def reset(self):
        '''Reset.'''
        self.x = 0
        self.y = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        self.vertical_mirror = False
        self.horizontal_mirror = False
        
    def auto_resize(self):
        '''Auto resize.'''
        self.x = 0
        self.y = 0
        
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_skin_file_path(self.image))
        if self.app_window_width > self.app_window_height:
            self.scale_x = self.scale_y =  float(self.app_window_height) / pixbuf.get_height()
        else:
            self.scale_x = self.scale_y = float(self.app_window_width) / pixbuf.get_width()
        
        self.vertical_mirror = False
        self.horizontal_mirror = False
        
    def vertical_mirror_background(self):
        '''Vertical mirror background.'''
        self.vertical_mirror = not self.vertical_mirror
        
        self.apply_skin()
        
    def horizontal_mirror_background(self):
        '''Horizontal mirror background.'''
        self.horizontal_mirror = not self.horizontal_mirror
        
        self.apply_skin()
    
    def render_background(self, cr, widget, x, y, 
                          translate_width=0,
                          translate_height=0):
        '''Render background.'''
        # Init.
        toplevel_rect = widget.get_toplevel().allocation
        render_width = toplevel_rect.width + translate_width
        render_height = toplevel_rect.height + translate_height
        
        # Draw background.
        background_x = int(self.x * self.scale_x)
        background_y = int(self.y * self.scale_y)
        background_width = int(self.background_pixbuf.get_width() * self.scale_x)
        background_height = int(self.background_pixbuf.get_height() * self.scale_y)
        self.cache_pixbuf.scale(self.background_pixbuf, background_width, background_height,
                                self.vertical_mirror, self.horizontal_mirror)
                
        draw_pixbuf(
            cr,
            self.cache_pixbuf.get_cache(),
            x + background_x,
            y + background_y)
        
        # Draw dominant color if necessarily.
        if ((background_width + background_x) < render_width 
            and (background_height + background_y) < render_height):
            cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))
            cr.rectangle(
                x + background_x + background_width,
                y + background_y + background_height,
                render_width - (background_width + background_x),
                render_height - (background_height + background_y))
            cr.fill()
        
        if (background_width + background_x) < render_width:
            draw_hlinear(
                cr,
                x + (background_width + background_x) - SHADE_SIZE,
                y,
                SHADE_SIZE,
                (background_height + background_y),
                [(0, (self.dominant_color, 0)),
                 (1, (self.dominant_color, 1))])
            
            cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))
            cr.rectangle(
                x + (background_width + background_x),
                y,
                render_width - (background_width + background_x),
                (background_height + background_y))
            cr.fill()
            
        if (background_height + background_y) < render_height:
            draw_vlinear(
                cr,
                x,
                y + (background_height + background_y) - SHADE_SIZE,
                (background_width + background_x),
                SHADE_SIZE,
                [(0, (self.dominant_color, 0)),
                 (1, (self.dominant_color, 1))])
            
            cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))
            cr.rectangle(
                x,
                y + (background_height + background_y),
                (background_width + background_x),
                render_height - (background_height + background_y))
            cr.fill()
            
    def export_skin(self, filepath):
        '''Export skin.'''
        # Build temp config file.
        config_filepath = os.path.join("/tmp/%s", str(uuid.uuid4()))
        touch_file(config_filepath)
        self.save_skin(config_filepath)
        
        # Build skin package.
        with tarfile.open("%s.tar.gz" % filepath, "w:gz") as tar:
            # Add config file.
            tar.add(config_filepath, "config.ini", False)
            
            # Add background image file.
            tar.add(self.get_skin_file_path(self.image), self.image, False)
            
            # Copy theme files is theme is not standard theme.
            if not self.theme_name in COLOR_SEQUENCE:
                tar.add(os.path.join(self.ui_theme_dir, self.theme_name), os.path.join("ui_theme", self.theme_name))
                tar.add(os.path.join(self.app_theme_dir, self.theme_name), os.path.join("app_theme", self.theme_name))
        
        # Remove temp config file.
        remove_file(config_filepath)    
        
    def load_themes(self, ui_theme, app_theme):
        '''Set theme directories.'''
        # Load theme.
        ui_theme.load_theme()
        app_theme.load_theme()
        
        # Init theme directories.
        self.ui_theme_dir = ui_theme.user_theme_dir
        self.app_theme_dir = app_theme.user_theme_dir
            
gobject.type_register(SkinConfig)

skin_config = SkinConfig()
