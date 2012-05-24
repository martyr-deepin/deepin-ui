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
import gobject
import os
from utils import color_hex_to_cairo
from draw import draw_pixbuf, draw_vlinear, draw_hlinear
from config import Config
from constant import SHADE_SIZE

class SkinConfig(gobject.GObject):
    '''SkinConfig.'''
	
    def __init__(self):
        '''Init skin.'''
        # Init.
        gobject.GObject.__init__(self)
        
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
        
    def load_skin(self, skin_dir):
        '''Load skin, return True if load finish, otherwise return False.'''
        try:
            # Save skin dir.
            self.skin_dir = skin_dir
            
            # Load config file.
            self.config = Config(os.path.join(self.skin_dir, "config.ini"))
            self.config.load()
            
            # Get name config.
            self.ui_theme_name = self.config.get("name", "ui_theme_name")
            self.app_theme_name = self.config.get("name", "app_theme_name")
            
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
            self.background_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.skin_dir, self.image))
            
            return True
        except Exception, e:
            print "load_skin error: %s" % (e)
            return False
    
    def save_skin(self):
        '''Save skin.'''
        self.config.set("background", "x", self.x)
        self.config.set("background", "y", self.y)
        self.config.set("background", "scale_x", self.scale_x)
        self.config.set("background", "scale_y", self.scale_y)
        
        self.config.set("action", "vertical_mirror", self.vertical_mirror)
        self.config.set("action", "horizontal_mirror", self.horizontal_mirror)
        
        self.config.write()
    
    def apply_skin(self):
        '''Apply skin.'''
        for window in self.window_list:
            window.queue_draw()
    
    def import_skin(self):
        '''Import skin.'''
        pass
        
    def export_skin(self):
        '''Export skin.'''
        pass
    
    def build_skin_package(self):
        '''Build skin package.'''
        pass
    
    def extract_skin_package(self):
        '''Extract skin package.'''
        pass
    
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
        
    def vertical_mirror_background(self):
        '''Vertical mirror background.'''
        self.vertical_mirror = not self.vertical_mirror
        
        self.apply_skin()
        
    def horizontal_mirror_background(self):
        '''Horizontal mirror background.'''
        self.horizontal_mirror = not self.horizontal_mirror
        
        self.apply_skin()
    
    def render_background(self, cr, widget, x, y):
        '''Render background.'''
        # Get toplevel size.
        toplevel_rect = widget.get_toplevel().allocation
        
        # Draw background.
        background_x = int(self.x * self.scale_x)
        background_y = int(self.y * self.scale_y)
        background_width = int(self.background_pixbuf.get_width() * self.scale_x)
        background_height = int(self.background_pixbuf.get_height() * self.scale_y)
        pixbuf = self.background_pixbuf.scale_simple(
                background_width,
                background_height,
                gtk.gdk.INTERP_BILINEAR
                )
        
        if self.vertical_mirror:
            pixbuf = pixbuf.flip(True)
            
        if self.horizontal_mirror:
            pixbuf = pixbuf.flip(False)
            
        draw_pixbuf(
            cr,
            pixbuf,
            x + background_x,
            y + background_y)
        
        # Draw dominant color if necessarily.
        if (background_width + background_x) < toplevel_rect.width and (background_height + background_y) < toplevel_rect.height:
            cr.set_source_rgb(*color_hex_to_cairo(self.dominant_color))
            cr.rectangle(
                x + background_x + background_width,
                y + background_y + background_height,
                toplevel_rect.width - (background_width + background_x),
                toplevel_rect.height - (background_height + background_y))
            cr.fill()
        
        if (background_width + background_x) < toplevel_rect.width:
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
                toplevel_rect.width - (background_width + background_x),
                (background_height + background_y))
            cr.fill()
            
        if (background_height + background_y) < toplevel_rect.height:
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
                toplevel_rect.height - (background_height + background_y))
            cr.fill()
            
gobject.type_register(SkinConfig)

skin_config = SkinConfig()
skin_config.load_skin("/home/andy/deepin-ui-private/skin/01")
