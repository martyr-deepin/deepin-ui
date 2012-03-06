#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 QiuHailong
# 
# Author:     QiuHailong <qiuhailong@linuxdeepin>
# Maintainer: QiuHailong <qiuhailong@linuxdeepin>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that innt will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from utils import *
from draw import *
from scrolled_window import *
import glib
from window import *

class PreviewWindow(object):
    '''preview window.'''
	
    def __init__(self, image_arry):
        '''Init.'''        
        self.preview_window = Window()
        self.preview_window.set_position(gtk.WIN_POS_CENTER)
        self.preview_window.set_modal(True)
        self.preview_window.set_size_request(800, 500)

        self.scrolledWindow = ScrolledWindow(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        self.main_box = gtk.VBox()
        self.image_box = gtk.HBox()
        
        map(lambda path: self.image_box.pack_start(gtk.image_new_from_file(path)), image_arry)
        self.ticker = 0
        self.scrollnum = 0

        self.scrolledWindow.add_child(self.image_box)
        
        self.main_box.pack_start(self.scrolledWindow, True, True)
        
        self.preview_window.window_frame.add(self.main_box)
        
        self.scrolled_value = self.scrolledWindow.get_hadjustment()
        self.scrolled_timeID = glib.timeout_add(15, self.scrolled_image)
        self.preview_window.show_all()

    def scrolled_image(self):
        self.ticker += 1
        ticker = self.ticker % 100
        width = 800

        if 50 <= ticker <= 60:
            self.scrollnum += 10
        elif 60 <= ticker <= 90:
            self.scrollnum += 600 / 30
        elif 90 <= ticker <= 100:
            self.scrollnum += 10

        self.scrolled_value.set_value(self.scrollnum)
        
        if self.scrollnum + self.scrolled_value.get_page_size() >= self.scrolled_value.get_upper():
            self.preview_window.destroy()
            return False
        else:
            return True

            
if __name__ == "__main__":
    p = PreviewWindow(["/home/long/图片/a.jpg", 
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/b.jpg",
                       "/home/long/图片/c.jpg",
                       "/home/long/图片/d.jpg",
                       "/home/long/图片/e.jpg"])
    p.preview_window.connect("destroy", lambda w:gtk.main_quit())
    gtk.main()

