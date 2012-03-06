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

from constant import *
from draw import *
from button import *
from box import *
import gtk
import utils
import gobject

class Titlebar(object):
    '''Title bar.'''    
    
    def __init__(self, 
                 button_mask=["theme", "menu", "max", "min", "close"],
                 icon_dpixbuf=None,
                 app_name=None,
                 title=None,
                 ):
        '''Init titlebar.'''
        # Init.
        self.box = EventBox()
        self.layout_box = gtk.HBox()
        self.box.add(self.layout_box)
        
        # Add drag event box.
        self.drag_box = EventBox()
        self.layout_box.pack_start(self.drag_box, True, True)
        
        # Init left box to contain icon and title.
        self.left_box = gtk.HBox()
        self.drag_box.add(self.left_box)
        
        # Add icon.
        if icon_dpixbuf != None:
            self.icon_box = ImageBox(icon_dpixbuf)
            self.icon_align = gtk.Alignment()
            self.icon_align.set(0.5, 0.5, 0.0, 0.0)
            self.icon_align.set_padding(0, 0, 10, 10)
            self.icon_align.add(self.icon_box)
            self.left_box.pack_start(self.icon_align, False, False)
                    
        # Add app name.
        if app_name != None:
            self.app_name_box = TextBox(app_name, ui_theme.get_dynamic_color("titlebar"))
            self.app_name_align = gtk.Alignment()
            self.app_name_align.set(0.5, 0.5, 0.0, 0.0)
            self.app_name_align.set_padding(0, 0, 0, 0)
            self.app_name_align.add(self.app_name_box)
            self.left_box.pack_start(self.app_name_align, False, False)
        
        # Add title.
        if title != None:
            self.title_box = TextBox(title, ui_theme.get_dynamic_color("titlebar"))
            self.title_align = gtk.Alignment()
            self.title_align.set(0.5, 0.5, 0.0, 0.0)
            self.title_align.set_padding(0, 0, 0, 0)
            self.title_align.add(self.title_box)
            self.left_box.pack_start(self.title_align, True, True)
            
        # Add button box.
        self.button_box = gtk.HBox()
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.0, 0.0, 0.0)
        self.button_align.add(self.button_box)
        self.layout_box.pack_start(self.button_align, False, False)
        
        # Add theme button.
        if "theme" in button_mask:
            self.theme_button = ThemeButton()
            self.button_box.pack_start(self.theme_button, False, False)

        # Add menu button.
        if "menu" in button_mask:
            self.menu_button = MenuButton()
            self.button_box.pack_start(self.menu_button, False, False)
        
        # Add min button.
        if "min" in button_mask:
            self.min_button = MinButton()
            self.button_box.pack_start(self.min_button, False, False)
        
        # Add max button.
        if "max" in button_mask:
            self.max_button = MaxButton()
            self.button_box.pack_start(self.max_button, False, False)

        # Add close button.
        if "close" in button_mask:
            self.close_button = CloseButton()
            self.button_box.pack_start(self.close_button, False, False)
        
        # Show.
        self.box.show_all()
        
    def change_title(self, title):
        '''Change title.'''
        self.title_box.change_text(title)
        
if __name__ == "__main__":
    
    def max_signal(w):    
        if window_is_max(w):
            win.unmaximize()
            print "min"
        else:
            win.maximize()
            print "max"

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.connect("destroy", gtk.main_quit)
    tit = Titlebar()
    tit.max_button.connect("clicked", max_signal)
    win.add(tit.box)
    win.show_all()
    
    gtk.main()
