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

from mplayer_window import MplayerWindow
from skin import SkinWindow
from skin_config import skin_config
from threads import post_gui
from titlebar import Titlebar
from utils import container_remove_all, place_center
from window import Window
import gtk

class Application(object):
    """
    This is the base class of every program based on deepin-ui.
    Every program should realize it.
    """
    def __init__(self, app_support_colormap=True):
        """
        Initialize the Application class.
        @param app_support_colormap: Set False if you do not want the application to support colormap. By default it's True.
        """
        # Init.
        self.app_support_colormap = app_support_colormap
        self.close_callback = self.close_window

        # Start application.
        self.init()

    def init(self):
        """
        This do the remain initialize step.
        It Initializes the window and some important signal such as "destroy".
        """
        # Init gdk threads, the integrant method for multi-thread GUI application.
        gtk.gdk.threads_init()

        # Init status.
        self.menu_button_callback = None

        # Init window.
        if self.app_support_colormap:
            self.window = Window(True)
        else:
            self.window = MplayerWindow(True)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.connect("destroy", self.destroy)
        
        # Init main box.
        self.main_box = self.window.window_frame

        # Add titlebar box.
        self.titlebar = None
        self.titlebar_box = gtk.HBox()
        self.main_box.pack_start(self.titlebar_box, False)

    def add_titlebar(self,
                     button_mask=["theme", "menu", "max", "min", "close"],
                     icon_dpixbuf=None, app_name=None, title=None, add_separator=False, show_title=True):
        """
        Add titlebar to the application.
        Connect click signal of the standard button to default callback.
        @param button_mask: A list of string, each of which stands for a standard button on top right of the window. By default, it's ["theme", "menu", "max", "min", "close"].
        @param icon_dpixbuf: The icon pixbuf of type dtk.ui.theme.DynamicPixbuf. The icon pixbuf is dynamic and could be changed in other parts of the program. By default, it is None.
        @param app_name: The name string of the application, which will be displayed just next to the icon_dpixbuf. By default, it is None.
        @param title: The title string of the window, which will be displayed on the center of the titlebar. By default, it is None.
        @param add_separator: If True, add a line between the titlebar and the body of the window. By default, it's False.
        @param show_title: If False, do not display the icon_dpixbuf, app_name and the title. By default, it's True.
        """
        # Init titlebar.
        self.titlebar = Titlebar(button_mask, icon_dpixbuf, app_name, title, add_separator, show_title=show_title)
        if "theme" in button_mask:
            self.titlebar.theme_button.connect("clicked", self.theme_callback)
        if "menu" in button_mask:
            self.titlebar.menu_button.connect("clicked", self.menu_callback)
        if "min" in button_mask:
            self.titlebar.min_button.connect("clicked", lambda w: self.window.min_window())
        if "max" in button_mask:
            self.titlebar.max_button.connect("clicked", lambda w: self.window.toggle_max_window())
        if "close" in button_mask:
            self.titlebar.close_button.connect("clicked", self.close_callback)
        self.window.add_toggle_event(self.titlebar)
        self.window.add_move_event(self.titlebar)

        # Show titlebar.
        self.show_titlebar()
        
    def close_window(self, widget):
        """
        Close the window when the close button is clicked.
        @param widget: No used. Passed by gtk.
        """
        self.window.close_window()

    def show_titlebar(self):
        """
        Show title bar of the window. By default, it is invoked at the last step of add_titlebar.
        """
        if self.titlebar_box.get_children() == [] and self.titlebar != None:
            self.titlebar_box.add(self.titlebar)

    def hide_titlebar(self):
        """
        Hide the title bar.
        """
        container_remove_all(self.titlebar_box)

    @post_gui
    def raise_to_top(self):
        """
        Raise the window to the top of the window stack.
        """
        self.window.present()

    def set_title(self, title):
        """
        Set the application title.
        @param title: The title string of the application.
        """
        self.window.set_title(title)

    def set_default_size(self, default_width, default_height):
        """
        Set the default size of the window.
        @param default_width: Default width in pixels of the application.
        @param default_height: Default height in pixels of the application.
        """
        self.window.set_default_size(default_width, default_height)
        self.window.set_geometry_hints(
            None,
            default_width,       # minimum width
            default_height       # minimum height
            -1, -1, -1, -1, -1, -1, -1, -1
            )
        
        # Pass application size to skin config.
        skin_config.set_application_window_size(default_width, default_height)

    def set_icon(self, icon_dpixbuf):
        """
        Set the icon of the application. This icon is used by the window manager or the dock.
        @param icon_dpixbuf: The icon pixbuf of dtk.ui.theme.DynamicPixbuf.
        """
        gtk.window_set_default_icon(icon_dpixbuf.get_pixbuf())

    def destroy(self, widget, data=None):
        """
        Destroy the window and quit the program.
        @param widget: Not used.
        @param data: Not used.
        """
        gtk.main_quit()

    def run(self):
        """
        Show the window and start the mainloop.
        """
        # Show window.
        self.window.show_window()

        # Run main loop.
        gtk.main()

    def set_skin_preview(self, preview_pixbuf):
        """
        Set the skin preview of the application.
        @param preview_pixbuf: A pixbuf of type dtk.ui.theme.DynamicPixbuf.
        """
        '''Set skin preview pixbuf.'''
        self.skin_preview_pixbuf = preview_pixbuf
        
    def theme_callback(self, widget):
        """
        Invoked when the theme button is clicked.
        @param widget: Not used.
        @return: Always return False
        """
        skin_window = SkinWindow(self.skin_preview_pixbuf)
        skin_window.show_all()
        skin_window.connect("show", lambda w: place_center(self.window, w))

        return False

    def menu_callback(self, widget):
        """
        Invoked when the menu button is clicked.
        @param widget: Not used.
        @return: Always return False
        """
        if self.menu_button_callback:
            self.menu_button_callback(widget)

        return False

    def set_menu_callback(self, callback):
        """
        Set the menu_button_callback function.
        @param callback: A function which is invoked when the menu button is clicked.
        """
        '''Set menu callback.'''
        self.menu_button_callback = callback
