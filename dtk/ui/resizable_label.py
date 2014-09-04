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

from box import EventBox
from utils import get_content_size, cairo_state, is_in_rect
from constant import DEFAULT_FONT_SIZE
from draw import draw_text
import gobject
import gtk
from timeline import Timeline, CURVE_SINE
from locales import _

class ResizableLabelBuffer(gobject.GObject):
    '''
    ResizableLabelBuffer class.

    @undocumented: get_max_size
    @undocumented: get_expand_size
    @undocumented: get_init_size
    @undocumented: render
    @undocumented: handle_button_press
    @undocumented: update
    @undocumented: completed
    '''

    __gsignals__ = {
        'update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        }

    def __init__(self,
                 label_content,
                 label_wrap_width,
                 label_init_height,
                 label_init_line,
                 label_font_size,
                 label_font_color,
                 animation_time=200, # milliseconds
                 ):
        '''
        Initialize ResizableLabelBuffer class.

        @param label_content: The content of label.
        @param label_wrap_width: The wrap width of label.
        @param label_init_height: The initialize height of label.
        @param label_init_line: The initialize line number of label.
        @param label_font_size: The font size.
        @param label_font_color: The font color.
        @param animation_time: The time of animation, default is 200 milliseconds.
        '''
        gobject.GObject.__init__(self)

        self.label_content = label_content
        self.label_init_height = label_init_height
        self.label_init_line = label_init_line
        self.label_font_size = label_font_size
        self.label_font_color = label_font_color
        self.label_wrap_width = label_wrap_width

        self.animation_time = animation_time
        self.in_animation = False
        self.label_line_height = int(float(self.label_init_height / self.label_init_line))
        self.label_expand_height = self.label_line_height * 2
        (self.max_width, self.max_height) = self.get_max_size()
        self.is_expandable = not (self.max_height <= self.label_init_height)
        (self.init_width, self.init_height) = self.get_init_size()
        self.has_expand = False
        (self.expand_width, self.expand_height) = self.get_expand_size()
        self.expand_button_content = _("Expand")
        self.shrink_button_content = _("Shrink")
        (self.expand_button_width, self.expand_button_height) = get_content_size(self.expand_button_content, self.label_font_size)
        (self.shrink_button_width, self.shrink_button_height) = get_content_size(self.shrink_button_content, self.label_font_size)

    def get_max_size(self):
        return get_content_size(
            self.label_content,
            self.label_font_size,
            wrap_width=self.label_wrap_width)

    def get_expand_size(self):
        if self.is_expandable:
            return (self.label_wrap_width,
                    self.max_height + self.label_expand_height)
        else:
            return (self.label_wrap_width,
                    self.max_height)

    def get_init_size(self):
        if self.is_expandable:
            return (self.label_wrap_width,
                    self.label_init_height + self.label_expand_height)
        else:
            return (self.label_wrap_width,
                    self.label_init_height)

    def render(self, cr, rect):
        # Draw label content.
        with cairo_state(cr):
            if self.is_expandable:
                content_height = int(rect.height - self.label_expand_height) / self.label_line_height * self.label_line_height
                cr.rectangle(rect.x, rect.y, rect.width, content_height)
            else:
                content_height = rect.height
                cr.rectangle(rect.x, rect.y, rect.width, content_height)
            cr.clip()

            draw_text(
                cr,
                self.label_content,
                rect.x + (rect.width - self.label_wrap_width) / 2,
                rect.y,
                rect.width,
                content_height,
                text_size=self.label_font_size,
                text_color=self.label_font_color,
                wrap_width=self.label_wrap_width
                )

        # Draw expand button.
        if self.is_expandable:
            if self.has_expand:
                text = self.shrink_button_content
                text_width, text_height = self.shrink_button_width, self.shrink_button_height
            else:
                text = self.expand_button_content
                text_width, text_height = self.expand_button_width, self.expand_button_height
            draw_text(
                cr,
                text,
                rect.x + rect.width - (rect.width - self.label_wrap_width) / 2 - text_width,
                rect.y + rect.height - text_height,
                text_width,
                text_height,
                )

    def handle_button_press(self, cr, rect, event_x, event_y):
        if self.is_expandable:
            if not self.in_animation:
                if self.has_expand:
                    text_width, text_height = self.shrink_button_width, self.shrink_button_height
                else:
                    text_width, text_height = self.expand_button_width, self.expand_button_height
                if is_in_rect((event_x, event_y),
                              (rect.width - (rect.width - self.label_wrap_width) / 2 - text_width,
                               rect.height - text_height,
                               text_width,
                               text_height)):

                    if self.has_expand:
                        start_position = self.expand_height
                        animation_distance = self.init_height - self.expand_height
                    else:
                        start_position = self.init_height
                        animation_distance = self.expand_height - self.init_height

                    self.in_animation = True

                    timeline = Timeline(self.animation_time, CURVE_SINE)
                    timeline.connect('update', lambda source, status:
                                     self.update(source,
                                                 status,
                                                 start_position,
                                                 animation_distance))
                    timeline.connect("completed", self.completed)
                    timeline.run()
        else:
            print "no expand button"

    def update(self, source, status, start_position, pos):
        self.emit("update", int(start_position + status * pos))

    def completed(self, source):
        self.in_animation = False
        self.has_expand = not self.has_expand

gobject.type_register(ResizableLabelBuffer)

class ResizableLabel(EventBox):
    '''
    ResizableLabel class.

    @undocumented: update_size
    @undocumented: expose_resizable_label
    @undocumented: button_press_resizable_label
    '''

    def __init__(self,
                 label_content,
                 label_wrap_width,
                 label_init_height,
                 label_init_line,
                 label_font_size=DEFAULT_FONT_SIZE,
                 label_font_color="#000000",
                 ):
        '''
        Initialize ResizableLabel class.

        @param label_content: The content of label.
        @param label_wrap_width: The wrap width of label.
        @param label_init_height: The initialize height of label.
        @param label_init_line: The initialize line number of label.
        @param label_font_size: The font size.
        @param label_font_color: The font color.
        '''
        EventBox.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.buffer = ResizableLabelBuffer(
            label_content,
            label_wrap_width,
            label_init_height,
            label_init_line,
            label_font_size,
            label_font_color,
            )

        self.set_size_request(self.buffer.init_width, self.buffer.init_height)

        self.buffer.connect("update", self.update_size)
        self.connect("expose-event", self.expose_resizable_label)
        self.connect("button-press-event", self.button_press_resizable_label)

    def update_size(self, label_buffer, label_height):
        self.set_size_request(-1, label_height)

    def expose_resizable_label(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        self.buffer.render(cr, rect)

    def button_press_resizable_label(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        self.buffer.handle_button_press(cr, rect, event.x, event.y)

gobject.type_register(ResizableLabel)
