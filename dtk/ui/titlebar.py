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

from box import EventBox, ImageBox
from button import ThemeButton, MenuButton, MinButton, MaxButton, CloseButton
from draw import draw_line
from label import Label
from locales import _
import tooltip as Tooltip
from utils import window_is_max
import gobject
import gtk
import pango

class Titlebar(EventBox):
    '''Title bar.'''    
    
    def __init__(self, 
                 button_mask=["theme", "menu", "max", "min", "close"],
                 icon_dpixbuf=None,
                 app_name=None,
                 title=None,
                 add_separator=False,
                 height=26
                 ):
        '''Init titlebar.'''
        # Init.
        EventBox.__init__(self)
        self.set_size_request(-1, height)
        self.v_layout_box = gtk.VBox()
        self.h_layout_box = gtk.HBox()
        self.add(self.v_layout_box)
        self.v_layout_box.pack_start(self.h_layout_box, True, True)
        
        # Init separator.
        if add_separator:
            self.separator = gtk.HBox()
            self.separator.set_size_request(-1, 1)
            self.separator.connect("expose-event", self.expose_titlebar_separator)
            self.v_layout_box.pack_start(self.separator, True, True)
        
        # Add drag event box.
        self.drag_box = EventBox()
        self.h_layout_box.pack_start(self.drag_box, True, True)
        
        # Init left box to contain icon and title.
        self.left_box = gtk.HBox()
        self.drag_box.add(self.left_box)
        
        # Add icon.
        if icon_dpixbuf != None:
            self.icon_image_box = ImageBox(icon_dpixbuf)
            self.icon_align = gtk.Alignment()
            self.icon_align.set(0.5, 0.5, 0.0, 0.0)
            self.icon_align.set_padding(5, 5, 5, 0)
            self.icon_align.add(self.icon_image_box)
            self.left_box.pack_start(self.icon_align, False, False)
                    
        # Add app name.
        if app_name != None:
            self.app_name_box = Label(app_name, enable_gaussian=True)
            self.app_name_align = gtk.Alignment()
            self.app_name_align.set(0.5, 0.5, 0.0, 0.0)
            self.app_name_align.set_padding(2, 0, 5, 0)
            self.app_name_align.add(self.app_name_box)
            self.left_box.pack_start(self.app_name_align, False, False)
        
        # Add title.
        if title != None:
            self.title_box = Label(title, enable_gaussian=True, text_x_align=pango.ALIGN_CENTER)
            self.title_align = gtk.Alignment()
            self.title_align.set(0.5, 0.5, 0.0, 0.0)
            self.title_align.set_padding(2, 0, 30, 30)
            self.title_align.add(self.title_box)
            self.left_box.pack_start(self.title_align, True, True)
            
        # Add button box.
        self.button_box = gtk.HBox()
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.0, 0.0, 0.0)
        self.button_align.set_padding(0, 0, 0, 0)
        self.button_align.add(self.button_box)
        self.h_layout_box.pack_start(self.button_align, False, False)
        
        # Add theme button.
        if "theme" in button_mask:
            self.theme_button = ThemeButton()
            self.button_box.pack_start(self.theme_button, False, False, 1)
            Tooltip.text(self.theme_button, _("Change skin")).show_delay(self.theme_button, 2000)

        # Add menu button.
        if "menu" in button_mask:
            self.menu_button = MenuButton()
            self.button_box.pack_start(self.menu_button, False, False, 1)
            Tooltip.text(self.menu_button, _("Main menu")).show_delay(self.menu_button, 2000)
        
        # Add min button.
        if "min" in button_mask:
            self.min_button = MinButton()
            self.button_box.pack_start(self.min_button, False, False, 1)
            Tooltip.text(self.min_button, _("Minimum")).show_delay(self.min_button, 2000)        
            
        # Add max button.
        if "max" in button_mask:
            self.max_button = MaxButton()
            self.button_box.pack_start(self.max_button, False, False, 1)
            Tooltip.text(self.max_button, _("Maximize")).show_delay(self.max_button, 2000)        

        # Add close button.
        if "close" in button_mask:
            self.close_button = CloseButton()
            self.button_box.pack_start(self.close_button, False, False)
            Tooltip.text(self.close_button, _("Close")).show_delay(self.close_button, 2000)        
        
        # Show.
        self.show_all()
        
    def expose_titlebar_separator(self, widget, event):
        '''Expose nav separator.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
    
        # Draw separator.
        cr.set_source_rgba(1, 1, 1, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 2, rect.x + rect.width - 1, rect.y + 1)
    
        return True
    
    def change_title(self, title):
        '''Change title.'''
        self.title_box.change_text(title)
        
gobject.type_register(Titlebar)

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
