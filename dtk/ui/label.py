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

from constant import DEFAULT_FONT_SIZE, ALIGN_START, DEFAULT_FONT
from draw import draw_text, draw_hlinear
from keymap import get_keyevent_name
from theme import ui_theme
from utils import propagate_expose, get_content_size, is_double_click, is_left_button, set_clickable_cursor
import gtk
import pango
import pangocairo

class Label(gtk.EventBox):
    '''
    Label.

    @undocumented: button_press_label
    @undocumented: button_release_label
    @undocumented: motion_notify_label
    @undocumented: key_press_label
    @undocumented: focus_out_label
    @undocumented: get_index_at_event
    @undocumented: get_content_width
    @undocumented: expose_label
    @undocumented: draw_label_background
    @undocumented: draw_label_text
    @undocumented: update_size
    @undocumented: hover
    @undocumented: unhover
    '''

    def __init__(self,
                 text="",
                 text_color=None,
                 text_size=DEFAULT_FONT_SIZE,
                 text_x_align=ALIGN_START,
                 label_width=None,
                 enable_gaussian=False,
                 enable_select=True,
                 enable_double_click=True,
                 gaussian_radious=2,
                 border_radious=1,
                 wrap_width=None,
                 underline=False,
                 hover_color=None,
                 fixed_width=None
                 ):
        '''
        Initialize Label class.

        @param text: Label text.
        @param text_color: Label text color, default is None.
        @param text_size: Label text size, default is DEFAULT_FONT_SIZE.
        @param text_x_align: Horizontal align option, default is ALIGN_START.
        @param label_width: Label maximum width, default is None.
        @param enable_gaussian: Default is False, if it is True, color option no effect, default gaussian effect is white text and black shadow.
        @param enable_select: Default is True, label content can't select if it is False.
        @param gaussian_radious: Radious of gaussian.
        @param border_radious: Radious of border.
        @param wrap_width: Wrap width.
        @param underline: Whether display underline, default is False.
        @param hover_color: Hover color, default is None.
        @param fixed_width: Fixed width, default is None.
        '''
        # Init.
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)
        self.set_can_focus(True) # can focus to response key-press signal
        self.label_width = label_width
        self.enable_gaussian = enable_gaussian
        self.enable_select = enable_select
        self.enable_double_click = enable_double_click
        self.select_start_index = self.select_end_index = 0
        self.double_click_flag = False
        self.left_click_flag = False
        self.left_click_coordindate = None
        self.drag_start_index = 0
        self.drag_end_index = 0
        self.wrap_width = wrap_width
        self.underline = underline
        self.hover_color = hover_color
        self.is_hover = False
        self.ellipsize = pango.ELLIPSIZE_END
        self.update_size_hook = None
        self.fixed_width = fixed_width

        self.text = text
        self.text_size = text_size
        if text_color == None:
            self.text_color = ui_theme.get_color("label_text")
        else:
            self.text_color = text_color
        self.text_select_color = ui_theme.get_color("label_select_text")
        self.text_select_background = ui_theme.get_color("label_select_background")

        if self.enable_gaussian:
            self.gaussian_radious = gaussian_radious
            self.border_radious = border_radious
            self.gaussian_color="#000000"
            self.border_color="#000000"
        else:
            self.gaussian_radious=None
            self.border_radious=None
            self.gaussian_color=None
            self.border_color=None

        self.text_x_align = text_x_align

        self.update_size()

        self.connect("expose-event", self.expose_label)
        self.connect("button-press-event", self.button_press_label)
        self.connect("button-release-event", self.button_release_label)
        self.connect("motion-notify-event", self.motion_notify_label)
        self.connect("key-press-event", self.key_press_label)
        self.connect("focus-out-event", self.focus_out_label)

        # Add keymap.
        self.keymap = {
            "Ctrl + c" : self.copy_to_clipboard,
            }

    def set_ellipsize(self, ellipsize):
        '''
        Set ellipsize of label.

        @param ellipsize: Ellipsize style of text when text width longer than draw area, it can use below value:
         - pango.ELLIPSIZE_START
         - pango.ELLIPSIZE_CENTER
         - pango.ELLIPSIZE_END
        '''
        self.ellipsize = ellipsize

        self.queue_draw()

    def set_fixed_width(self, width):
        '''
        Set fixed width of label.

        @param width: The width of label.
        '''
        self.fixed_width = width
        self.set_size_request(width, -1)

    def copy_to_clipboard(self):
        '''
        Copy select text to clipboard.
        '''
        if self.select_start_index != self.select_end_index:
            cut_text = self.text[self.select_start_index:self.select_end_index]

            clipboard = gtk.Clipboard()
            clipboard.set_text(cut_text)

    def button_press_label(self, widget, event):
        '''
        Internal callback for `button-press-event` signal.

        @param widget: Label widget.
        @param event: Button press event.
        '''
        if not self.enable_gaussian:
            # Get input focus.
            self.grab_focus()

            # Select all when double click left button.
            if is_double_click(event) and self.enable_double_click:
                self.double_click_flag = True
                self.select_all()
            # Change cursor when click left button.
            elif is_left_button(event):
                self.left_click_flag = True
                self.left_click_coordindate = (event.x, event.y)

                self.drag_start_index = self.get_index_at_event(widget, event)

    def button_release_label(self, widget, event):
        '''
        Internal callback for `button-release-event` signal.

        @param widget: Label widget.
        @param event: Button release event.
        '''
        if not self.double_click_flag and self.left_click_coordindate == (event.x, event.y):
            self.select_start_index = self.select_end_index = 0
            self.queue_draw()

        self.double_click_flag = False
        self.left_click_flag = False

    def motion_notify_label(self, widget, event):
        '''
        Internal callback for `motion-notify-event` signal.

        @param widget: Label widget.
        @param event: Motion notify event.
        '''
        if not self.double_click_flag and self.left_click_flag and self.enable_select:
            self.drag_end_index = self.get_index_at_event(widget, event)

            self.select_start_index = min(self.drag_start_index, self.drag_end_index)
            self.select_end_index = max(self.drag_start_index, self.drag_end_index)

            self.queue_draw()

    def key_press_label(self, widget, event):
        '''
        Internal callback for `key-press-event` signal.

        @param widget: Label widget.
        @param event: Key press event.
        '''
        key_name = get_keyevent_name(event)

        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

        return False

    def focus_out_label(self, widget, event):
        '''
        Internal callback for `focus-out-event` signal.

        @param widget: Label widget.
        @param event: Focus out event.
        '''
        if self.select_start_index != self.select_end_index:
            self.select_start_index = self.select_end_index = 0

            self.queue_draw()

    def get_index_at_event(self, widget, event):
        '''
        Internal function to get index at event.

        @param widget: Label widget.
        @param event: gtk.gdk.Event.
        @return: Return the index at event.
        '''
        cr = widget.window.cairo_create()
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.text_size)))
        layout.set_text(self.text)
        (text_width, text_height) = layout.get_pixel_size()
        if int(event.x) > text_width:
            return len(self.text)
        else:
            (x_index, y_index) = layout.xy_to_index(int(event.x) * pango.SCALE, 0)
            return x_index

    def get_content_width(self, content):
        '''
        Internal fucntion to get content width.
        '''
        (content_width, content_height) = get_content_size(content, self.text_size, wrap_width=self.wrap_width)
        return content_width

    def select_all(self):
        '''
        Select all.
        '''
        self.select_start_index = 0
        self.select_end_index = len(self.text)

        self.queue_draw()

    def expose_label(self, widget, event):
        '''
        Internal callback for `expose-event` signal.

        @param widget: Label widget.
        @param event: Expose event.
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation

        self.draw_label_background(cr, rect)

        self.draw_label_text(cr, rect)

        propagate_expose(widget, event)

        return True

    def draw_label_background(self, cr, rect):
        '''
        Inernal function to draw label background.

        @param cr: Cairo context.
        @param rect: Draw area.
        @return: Always return True.
        '''
        if self.select_start_index != self.select_end_index:
            select_start_width = self.get_content_width(self.text[0:self.select_start_index])
            select_end_width = self.get_content_width(self.text[0:self.select_end_index])

            draw_hlinear(cr,
                         rect.x + select_start_width,
                         rect.y,
                         select_end_width - select_start_width,
                         rect.height,
                         [(0, (self.text_select_background.get_color(), 0)),
                          (0, (self.text_select_background.get_color(), 1))]
                         )

    def draw_label_text(self, cr, rect):
        '''
        Internal fucntion to draw label text.

        @param cr: Cairo context.
        @param rect: Draw area.
        '''
        if self.enable_gaussian:
            label_color = "#FFFFFF"
        elif self.is_hover and self.hover_color:
            label_color = self.hover_color.get_color()
        else:
            label_color = self.text_color.get_color()

        if not self.get_sensitive():
            draw_text(cr, self.text,
                      rect.x, rect.y, rect.width, rect.height,
                      self.text_size,
                      ui_theme.get_color("disable_text").get_color(),
                      alignment=self.text_x_align,
                      gaussian_radious=self.gaussian_radious,
                      gaussian_color=self.gaussian_color,
                      border_radious=self.border_radious,
                      border_color=self.border_color,
                      wrap_width=self.wrap_width,
                      underline=self.underline,
                      ellipsize=self.ellipsize,
                      )
        elif self.select_start_index == self.select_end_index:
            draw_text(cr, self.text,
                      rect.x, rect.y, rect.width, rect.height,
                      self.text_size,
                      label_color,
                      alignment=self.text_x_align,
                      gaussian_radious=self.gaussian_radious,
                      gaussian_color=self.gaussian_color,
                      border_radious=self.border_radious,
                      border_color=self.border_color,
                      wrap_width=self.wrap_width,
                      underline=self.underline,
                      ellipsize=self.ellipsize,
                      )
        else:
            select_start_width = self.get_content_width(self.text[0:self.select_start_index])
            select_end_width = self.get_content_width(self.text[0:self.select_end_index])

            # Draw left text.
            if self.text[0:self.select_start_index] != "":
                draw_text(cr, self.text[0:self.select_start_index],
                          rect.x, rect.y, rect.width, rect.height,
                          self.text_size,
                          label_color,
                          alignment=self.text_x_align,
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width,
                          underline=self.underline,
                          ellipsize=self.ellipsize,
                          )

            # Draw middle text.
            if self.text[self.select_start_index:self.select_end_index] != "":
                draw_text(cr, self.text[self.select_start_index:self.select_end_index],
                          rect.x + select_start_width, rect.y, rect.width, rect.height,
                          self.text_size,
                          self.text_select_color.get_color(),
                          alignment=self.text_x_align,
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width,
                          underline=self.underline,
                          ellipsize=self.ellipsize,
                          )

            # Draw right text.
            if self.text[self.select_end_index::] != "":
                draw_text(cr, self.text[self.select_end_index::],
                          rect.x + select_end_width, rect.y, rect.width, rect.height,
                          self.text_size,
                          label_color,
                          alignment=self.text_x_align,
                          gaussian_radious=self.gaussian_radious,
                          gaussian_color=self.gaussian_color,
                          border_radious=self.border_radious,
                          border_color=self.border_color,
                          wrap_width=self.wrap_width,
                          underline=self.underline,
                          ellipsize=self.ellipsize,
                          )

    def get_text(self):
        '''
        Get text of label.

        @return: Return the text of label.
        '''
        return self.text

    def set_text(self, text):
        '''
        Set text with given value.

        @param text: Label string.
        '''
        self.text = text
        self.update_size()
        self.queue_draw()

    def update_size(self):
        '''
        Internal function to update size.
        '''
        (label_width, label_height) = get_content_size(self.text, self.text_size, wrap_width=self.wrap_width)
        if self.label_width != None:
            if self.update_size_hook != None:
                self.update_size_hook(self, label_width, self.label_width)

            label_width = self.label_width

        if self.enable_gaussian:
            label_width += self.gaussian_radious * 2
            label_height += self.gaussian_radious * 2

        if self.fixed_width:
            label_width = self.fixed_width
        self.set_size_request(label_width, label_height)

    def set_clickable(self):
        '''
        Make label clickable.
        '''
        set_clickable_cursor(self)

        self.connect("enter-notify-event", lambda w, e: self.hover())
        self.connect("leave-notify-event", lambda w, e: self.unhover())

    def hover(self):
        self.is_hover = True

        self.queue_draw()

    def unhover(self):
        self.is_hover = False

        self.queue_draw()
