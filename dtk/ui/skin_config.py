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

import gobject
import os
from config import Config

class SkinConfig(gobject.GObject):
    '''SkinConfig.'''
	
    def __init__(self):
        '''Init skin.'''
        # Init.
        gobject.GObject.__init__(self)
        
        self.window_list = []
        
    def load_skin(self, skin_dir):
        '''Load skin, return True if load finish, otherwise return False.'''
        try:
            # Load config file.
            self.config = Config(os.path.join(skin_dir, "config.ini"))
            self.config.load()
            
            # Get name config.
            self.ui_theme_name = self.config.get("name", "ui_theme_name")
            self.app_theme_name = self.config.get("name", "app_theme_name")
            
            # Get application config.
            self.app_id = self.config.get("application", "app_id")
            self.app_version = self.config.getfloat("application", "app_version")
            
            # Get background config.
            self.image = self.config.get("background", "image")
            self.x = self.config.getint("background", "x")
            self.y = self.config.getint("background", "y")
            self.scale = self.config.getfloat("background", "scale")
            self.dominant_color = self.config.get("background", "dominant_color")
            
            # Get editable config.
            self.editable = self.config.getboolean("editable", "editable")
            
            return True
        except Exception, e:
            print "load_skin error: %s" % (e)
            return False
    
    def save_skin(self):
        '''Save skin.'''
        pass
    
    def apply_skin(self):
        '''Apply skin.'''
        for window in self.window_list:
            window.queue_draw()
            print "Draw: %s" % (window)
    
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
    
gobject.type_register(SkinConfig)

skin_config = SkinConfig()
