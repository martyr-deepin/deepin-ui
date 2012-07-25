#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
#
# Author:     Xia Bin <xiabin@linuxdeepin.com>
# Maintainer: Xia Bin <xiabin@linuxdeepin.com>
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

import webkit
import dtk_webkit_cookie
#import gobject
from gtk import gdk


class WebView(webkit.WebView):

    def __init__(self, cookie_filepath=None):
        #self = gobject.new(webkit.WebView, "self-scrolling", False)
        webkit.WebView.__init__(self)
        #self.set_property("self-scrolling", False)
        self.cookie_filepath = cookie_filepath
        if self.cookie_filepath != None:
            dtk_webkit_cookie.add_cookie(cookie_filepath)
        settings = self.get_settings()
        settings.set_property("enable-default-context-menu", False)
        self.connect("set-scroll-adjustments", self.save_adjustment)
        self.connect("scroll-event", self.do_scroll)

    def save_adjustment(self, web, hadj, vadj):
        self.vadjustment = vadj
        self.hadjustment = hadj

    def do_scroll(self, w, e):
        value = self.vadjustment.value
        step = self.vadjustment.step_increment
        page_size = self.vadjustment.page_size
        upper = self.vadjustment.upper

        if e.direction == gdk.SCROLL_DOWN:
            self.vadjustment.set_value(min(upper-page_size-1, value+step))
            return True
        elif e.direction == gdk.SCROLL_UP:
            self.vadjustment.set_value(max(0, value-step))
            return True
        else:
            return False
