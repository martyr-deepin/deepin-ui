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

from utils import *
import gobject, gtk
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

class DynamicPixbufAnimation(object):
    '''Dynamic pixbuf animation.'''
    
    def __init__(self, filepath):
        '''Init.'''
        self.update(filepath)
        
    def update(self, filepath):
        '''Update path.'''
        self.pixbuf_animation = gtk.gdk.PixbufAnimation(filepath)

    def get_pixbuf_animation(self):
        '''Get pixbuf animation.'''
        return self.pixbuf_animation
    
class DynamicImage(object):
    '''Dynamic image.'''
	
    def __init__(self, get_theme_ticker, parent, dpixbuf_animation):
        '''Init dynamic image.'''
        self.get_theme_ticker = get_theme_ticker
        self.dpixbuf_animation = dpixbuf_animation
        self.image = gtk.Image()
        self.ticker = 0

        self.update_animation()
        self.image.connect("expose-event", self.expose_callback)
        
        parent.connect("size-allocate", lambda w, e: self.image.realize())
        
    def update_animation(self):
        '''Update animation.'''
        self.image.set_from_animation(self.dpixbuf_animation.get_pixbuf_animation())    
        
    def expose_callback(self, widget, event):
        '''Expose callback.'''
        if self.ticker != self.get_theme_ticker():
            self.ticker = self.get_theme_ticker()
            self.update_animation()
            
        return False
    
class Theme(object):
    '''Ui_Theme.'''
    
    def __init__(self, theme_dir):
        '''Init ui_theme.'''
        # Init.
        self.theme_dir = theme_dir
        themes = os.listdir(self.theme_dir)
        theme_name = read_file("./defaultTheme", True)
        if theme_name == "" or not theme_name in themes:
            if "default" in themes:
                self.theme_name = "default"
            else:
                self.theme_name = themes[0]
        else:
            self.theme_name = theme_name
        self.color_path = "colors.txt"
        self.ticker = 0
        self.pixbuf_dict = {}
        self.color_dict = {}
        self.alpha_color_dict = {}
        self.shadow_color_dict = {}
        self.animation_dict = {}
        
        # Scan theme files.
        image_dir = self.get_image_dir()
        for root, dirs, files in os.walk(image_dir):
            for filepath in files:
                path = (os.path.join(root, filepath)).split(image_dir)[1]
                self.pixbuf_dict[path] = DynamicPixbuf(self.get_image_path(path))
                
        # Scan dynamic colors file.
        colors = eval_file(self.get_color_path(self.color_path))
        
        # Init dynamic colors.
        for (color_name, color) in colors["colors"].items():
            self.color_dict[color_name] = DynamicColor(color)

        # Init dynamic alpha colors.
        for (color_name, color_info) in colors["alphaColors"].items():
            self.alpha_color_dict[color_name] = DynamicAlphaColor(color_info)
        
        # Init dynamic shadow colors.
        for (color_name, color_info) in colors["shadowColors"].items():
            self.shadow_color_dict[color_name] = DynamicShadowColor(color_info)
            
        # Scan animation.
        animation_dir = self.get_animation_dir()
        for root, dirs, files in os.walk(animation_dir):
            for filepath in files:
                path = (os.path.join(root, filepath)).split(animation_dir)[1]
                self.animation_dict[path] = DynamicPixbufAnimation(self.get_animation_path(path))
                
    def get_image_dir(self):
        '''Get theme directory.'''
        return os.path.join(self.theme_dir, "%s/image/" % (self.theme_name))

    def get_image_path(self, path):
        '''Get pixbuf path.'''
        return os.path.join(self.get_image_dir(), path)

    def get_animation_dir(self):
        '''Get theme directory.'''
        return os.path.join(self.theme_dir, "%s/animation/" % (self.theme_name))
    
    def get_animation_path(self, path):
        '''Get pixbuf path.'''
        return os.path.join(self.get_animation_dir(), path)
    
    def get_theme_dir(self):
        '''Get theme directory.'''
        return os.path.join(self.theme_dir, "%s/" % (self.theme_name))                
    
    def get_color_path(self, path):
        '''Get pixbuf path.'''
        return os.path.join(self.get_theme_dir(), path)
            
    def get_dynamic_pixbuf(self, path):
        '''Get dynamic pixbuf.'''
        return self.pixbuf_dict[path]

    def get_dynamic_pixbuf_animation(self, path):
        '''Get dynamic pixbuf animation.'''
        return self.animation_dict[path]
    
    def get_dynamic_color(self, color_name):
        '''Get dynamic color.'''
        return self.color_dict[color_name]
    
    def get_dynamic_alpha_color(self, color_name):
        '''Get dynamic alpha color.'''
        return self.alpha_color_dict[color_name]
    
    def get_dynamic_shadow_color(self, color_name):
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
            pixbuf.update(self.get_image_path(path))
            
        # Update dynamic colors.
        colors = eval_file(self.get_color_path(self.color_path))
            
        for (color_name, color) in colors["colors"].items():
            self.color_dict[color_name].update(color)
            
        # Update dynamic alpha colors.
        for (color_name, color_info) in colors["alphaColors"].items():
            self.alpha_color_dict[color_name].update(color_info)
            
        # Update shadow colors.
        for (color_name, color_info) in colors["shadowColors"].items():
            self.shadow_color_dict[color_name].update(color_info)
            
        # Update animation.
        for (path, animation) in self.animation_dict.items():
            animation.update(self.get_animation_path(path))
            
        # Remeber ui_theme.
        write_file("./defaultTheme", new_theme_name)
            
# Init.
ui_theme = Theme(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "theme"))            
