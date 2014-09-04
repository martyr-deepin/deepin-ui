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
from deepin_utils.file import touch_file_dir
from gtk import gdk
import gtk

class WebView(webkit.WebView):
    '''
    WebView wrap that support cookie.

    @undocumented: save_adjustment
    @undocumented: do_scroll
    '''

    def __init__(self, cookie_filepath=None):
        '''
        Init for WebView.

        @param cookie_filepath: Filepath to save cookie.
        '''
        webkit.WebView.__init__(self)
        self.cookie_filepath = cookie_filepath
        if self.cookie_filepath != None:
            touch_file_dir(cookie_filepath)
            dtk_webkit_cookie.add_cookie(cookie_filepath)
        settings = self.get_settings()
        settings.set_property("enable-default-context-menu", False)
        self.connect("set-scroll-adjustments", self.save_adjustment)
        self.connect("scroll-event", self.do_scroll)

    def enable_inspector(self):
        '''
        Enable inspector feature of webview.
        '''
        class Inspector (gtk.Window):
            def __init__ (self, inspector):
                '''initialize the WebInspector class'''
                gtk.Window.__init__(self)
                self.set_default_size(600, 480)

                self._web_inspector = inspector

                self._web_inspector.connect("inspect-web-view",
                                            self._inspect_web_view_cb)
                self._web_inspector.connect("show-window",
                                            self._show_window_cb)
                self._web_inspector.connect("attach-window",
                                            self._attach_window_cb)
                self._web_inspector.connect("detach-window",
                                            self._detach_window_cb)
                self._web_inspector.connect("close-window",
                                            self._close_window_cb)
                self._web_inspector.connect("finished",
                                            self._finished_cb)

                self.connect("delete-event", self._close_window_cb)

            def _inspect_web_view_cb (self, inspector, web_view):
                '''Called when the 'inspect' menu item is activated'''
                scrolled_window = gtk.ScrolledWindow()
                webview = webkit.WebView()
                scrolled_window.add(webview)
                scrolled_window.show_all()

                self.add(scrolled_window)
                return webview

            def _show_window_cb (self, inspector):
                '''Called when the inspector window should be displayed'''
                self.present()
                return True

            def _attach_window_cb (self, inspector):
                '''Called when the inspector should displayed in the same
                window as the WebView being inspected
                '''
                return False

            def _detach_window_cb (self, inspector):
                '''Called when the inspector should appear in a separate window'''
                return False

            def _close_window_cb (self, inspector, view):
                '''Called when the inspector window should be closed'''
                self.hide()
                return True

            def _finished_cb (self, inspector):
                '''Called when inspection is done'''
                self._web_inspector = 0
                self.destroy()
                return False

        settings = self.get_settings()
        settings.set_property("enable-default-context-menu", True)
        settings.set_property("enable-developer-extras", True)
        Inspector(self.get_web_inspector())

    def save_adjustment(self, webview, hadj, vadj):
        '''
        Internal callback of "set-scroll-adjustmens" signal.
        '''
        self.vadjustment = vadj
        self.hadjustment = hadj

    def do_scroll(self, w, e):
        if hasattr(self, "vadjustment"):
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

