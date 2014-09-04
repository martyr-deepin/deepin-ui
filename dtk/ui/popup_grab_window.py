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

from utils import invisible_window
from scrolled_window import ScrolledWindow
import gtk
import gobject

class PopupGrabWindow(gtk.Window):
    '''
    PopupGrabWindow class.

    @undocumented: input_method_commit
    @undocumented: popup_grab_window_focus_in
    @undocumented: popup_grab_window_focus_out
    @undocumented: is_press_on_popup_grab_window
    @undocumented: popup_grab_window_button_press
    @undocumented: popup_grab_window_enter_notify
    @undocumented: popup_grab_window_leave_notify
    @undocumented: popup_grab_window_scroll_event
    @undocumented: popup_grab_window_key_press
    @undocumented: popup_grab_window_key_release
    @undocumented: popup_grab_window_button_press
    @undocumented: popup_grab_window_button_release
    @undocumented: popup_grab_window_motion_notify
    '''

    __gsignals__ = {
        "input-method-focus-in" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "input-method-commit" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        }

    def __init__(self,
                 wrap_window_type,
                 focus_out_callback=None,
                 handle_input_method=False,
                 ):
        '''
        Initialize PopupGrabWindow class.

        @param wrap_window_type: The type of wrap window to response event.
        @param wrap_window_type: The callback for focus-out signal, default is None.
        @param handle_input_method: Whether handle input method, default is False.
        '''
        # Init.
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.wrap_window_type = wrap_window_type
        self.focus_out_callback = focus_out_callback
        self.handle_input_method = handle_input_method
        self.in_focus_out_callbacking = False
        self.popup_windows = []
        self.press_flag = False

        if self.handle_input_method:
            self.im = gtk.IMMulticontext()
            self.im.connect("commit", self.input_method_commit)

        invisible_window(self)

        self.connect("button-press-event", self.popup_grab_window_button_press)
        self.connect("button-release-event", self.popup_grab_window_button_release)
        self.connect("motion-notify-event", self.popup_grab_window_motion_notify)
        self.connect("enter-notify-event", self.popup_grab_window_enter_notify)
        self.connect("leave-notify-event", self.popup_grab_window_leave_notify)
        self.connect("scroll-event", self.popup_grab_window_scroll_event)
        self.connect("key-press-event", self.popup_grab_window_key_press)
        self.connect("key-release-event", self.popup_grab_window_key_release)

        self.show()

    def input_method_commit(self, im, input_text):
        self.emit("input-method-commit", im, input_text)

    def popup_grab_window_focus_in(self):
        '''
        Handle `focus-in` signal of popup_grab_window.
        '''
        self.grab_add()
        gtk.gdk.pointer_grab(
            self.window,
            True,
            gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK,
            None, None, gtk.gdk.CURRENT_TIME)

        if self.handle_input_method:
            self.im.set_client_window(self.window)
            self.im.focus_in()

            self.emit("input-method-focus-in", self.im)

    def popup_grab_window_focus_out(self):
        '''
        Handle `focus-out` signal of popup_grab_window.
        '''
        for root_popup_window in self.popup_windows:
            root_popup_window.hide()

        self.popup_windows = []

        gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
        self.grab_remove()

        self.press_flag = False

        if self.focus_out_callback and not self.in_focus_out_callbacking:
            self.in_focus_out_callbacking = True
            self.focus_out_callback()
            self.in_focus_out_callbacking = False

        if self.handle_input_method:
            self.im.focus_out()

    def is_press_on_popup_grab_window(self, window):
        '''
        Whether press on popup_window of popup_grab_window.

        @param window: gtk.Window or gtk.gdk.Window
        '''
        for toplevel in gtk.window_list_toplevels():
            if isinstance(window, gtk.Window):
                if window == toplevel:
                    return True
            elif isinstance(window, gtk.gdk.Window):
                if window == toplevel.window:
                    return True

        return False

    def popup_grab_window_button_press(self, widget, event):
        '''
        Handle `button-press-event` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Button press event.
        '''
        self.press_flag = True

        if event and event.window:
            event_widget = event.window.get_user_data()
            if self.is_press_on_popup_grab_window(event.window):
                self.popup_grab_window_focus_out()
            elif isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "tag_by_popup_grab_window"):
                event_widget.event(event)
            elif isinstance(event_widget, self.wrap_window_type):
                event_widget.event(event)
            else:
                event_widget.event(event)
                self.popup_grab_window_focus_out()

    def popup_grab_window_enter_notify(self, widget, event):
        '''
        Handle `enter-notify` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Enter notify event.
        '''
        if event and event.window:
            event_widget = event.window.get_user_data()
            if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "tag_by_popup_grab_window"):
                event_widget.event(event)

    def popup_grab_window_leave_notify(self, widget, event):
        '''
        Handle `leave-notify` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Leave notify event.
        '''
        if event and event.window:
            event_widget = event.window.get_user_data()
            if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "tag_by_popup_grab_window"):
                event_widget.event(event)

    def popup_grab_window_scroll_event(self, widget, event):
        '''
        Handle `scroll` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Scroll event.
        '''
        if event and event.window:
            for popup_window in self.popup_windows:
                if hasattr(popup_window, "get_scrolledwindow"):
                    popup_window.get_scrolledwindow().event(event)

    def popup_grab_window_key_press(self, widget, event):
        '''
        Handle `key-press-event` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Key press event.
        '''
        if event and event.window:
            for popup_window in self.popup_windows:
                popup_window.event(event)

    def popup_grab_window_key_release(self, widget, event):
        '''
        Handle `key-release-event` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Key release event.
        '''
        if event and event.window:
            for popup_window in self.popup_windows:
                popup_window.event(event)

    def popup_grab_window_button_release(self, widget, event):
        '''
        Handle `button-release-event` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Button release event.
        '''
        self.press_flag = False

        if event and event.window:
            event_widget = event.window.get_user_data()
            if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "tag_by_popup_grab_window"):
                event_widget.event(event)
            else:
                # Make scrolledbar smaller if release out of scrolled_window area.
                for popup_window in self.popup_windows:
                    if hasattr(popup_window, "get_scrolledwindow"):
                        scrolled_window = popup_window.get_scrolledwindow()
                        scrolled_window.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
                        scrolled_window.make_bar_smaller(gtk.ORIENTATION_VERTICAL)

    def popup_grab_window_motion_notify(self, widget, event):
        '''
        Handle `motion-notify` signal of popup_grab_window.

        @param widget: Popup_Window widget.
        @param event: Motion notify signal.
        '''
        if event and event.window:
            event_widget = event.window.get_user_data()
            if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "tag_by_popup_grab_window"):
                event_widget.event(event)
            else:
                if self.press_flag:
                    for popup_window in self.popup_windows:
                        if hasattr(popup_window, "get_scrolledwindow"):
                            scrolled_window = popup_window.get_scrolledwindow()
                            motion_notify_event = gtk.gdk.Event(gtk.gdk.MOTION_NOTIFY)
                            motion_notify_event.window = scrolled_window.vwindow
                            motion_notify_event.send_event = True
                            motion_notify_event.time = event.time
                            motion_notify_event.x = event.x
                            motion_notify_event.y = event.y
                            motion_notify_event.x_root = event.x_root
                            motion_notify_event.y_root = event.y_root
                            motion_notify_event.state = event.state

                            scrolled_window.event(motion_notify_event)
                else:
                    if isinstance(event_widget.get_toplevel(), self.wrap_window_type):
                        event_widget.event(event)

gobject.type_register(PopupGrabWindow)

def handle_grab_window(grab_window, wrap_window):
    grab_window.popup_grab_window_focus_out()

    if not gtk.gdk.pointer_is_grabbed():
        grab_window.popup_grab_window_focus_in()

    if not wrap_window in grab_window.popup_windows:
        grab_window.popup_windows.append(wrap_window)

        if hasattr(wrap_window, "get_scrolledwindow"):
            wrap_window.get_scrolledwindow().tag_by_popup_grab_window = True

def wrap_grab_window(grab_window, wrap_window):
    wrap_window.connect_after("show", lambda w: handle_grab_window(grab_window, w))
