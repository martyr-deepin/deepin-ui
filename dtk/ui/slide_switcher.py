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
from draw import draw_pixbuf
from timeline import Timeline, CURVE_SINE
from utils import remove_timeout_id, is_in_rect
from utils import set_cursor
from constant import ALIGN_START, ALIGN_MIDDLE
from theme import ui_theme
import gobject
import gtk

class SlideSwitcher(EventBox):
    '''
    SlideSwitcher class.

    @undocumented: expose_slide_switcher
    @undocumented: enter_notify_slide_switcher
    @undocumented: leave_notify_slide_switcher
    @undocumented: update_animation
    @undocumented: completed_animation
    @undocumented: motion_notify_slide_switcher
    @undocumented: handle_animation
    @undocumented: start_animation
    @undocumented: to_left_animation
    @undocumented: to_right_animation
    @undocumented: start_auto_slide
    @undocumented: stop_auto_slide
    '''

    __gsignals__ = {
        "motion-notify-index" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
        "button-press-index" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
        "leave-notify-index" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,)),
    }

    def __init__(self,
                 images,
                 pointer_offset_x=-130,
                 pointer_offset_y=-20,
                 pointer_padding=20,
                 hover_animation_time=500,
                 auto_animation_time=2000,
                 auto_slide_timeout=5000,
                 horizontal_align=ALIGN_START,
                 vertical_align=ALIGN_START,
                 height_offset=0,
                 hover_switch=True,
                 auto_switch=True,
                 navigate_switch=False,
                 active_dpixbuf=ui_theme.get_pixbuf("slide_switcher/active.png"),
                 inactive_dpixbuf=ui_theme.get_pixbuf("slide_switcher/inactive.png"),
                 ):
        '''
        Initialize SlideSwitcher class.

        @param images: The image list of sliders.
        @param pointer_offset_x: The offset x of pointer relative to right edge of slider image, default is -130 pixels.
        @param pointer_offset_y: The offset y of pointer relative to bottom edge of slider image, default is -20 pixels.
        @param pointer_padding: The padding between pointers, default is 20 pixels.
        @param hover_animation_time: The animation time of hover operation, default is 500 milliseconds.
        @param auto_animation_time: The animation time of automatic play, default is 2000 milliseconds.
        @param auto_slide_timeout: The slide timeout of automatic play, default is 2000 milliseconds.
        @param horizontal_align: The horizontal alignment, default is ALIGN_START.
        @param vertical_align: The vertical alignment, default is ALIGN_START.
        @param height_offset: The height offset, default is 0 pixels.
        @param hover_switch: Set as True to make slider switch when hover operation active.
        @param auto_switch: Set as True to make slider play automatically.
        @param navigate_switch: Set as True to make slider switch navigate.
        @param active_dpixbuf: The dynamic pixbuf of active status.
        @param inactive_dpixbuf: The dynamic pixbuf of inactive status.
        '''
        EventBox.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.slide_images = images
        self.image_number = len(self.slide_images)
        self.active_index = 0
        self.motion_index = None
        self.target_index = None
        self.active_alpha = 1.0
        self.target_alpha = 0.0
        self.in_animiation = False
        self.hover_animation_time = hover_animation_time # animiation time of hover, in milliseconds
        self.auto_animation_time = auto_animation_time # animiation time automatically, in milliseconds
        self.auto_slide_timeout = auto_slide_timeout # slide timeout, in milliseconds
        self.auto_slide_timeout_id = None
        self.horizontal_align = horizontal_align
        self.vertical_align = vertical_align
        self.hover_switch = hover_switch
        self.auto_switch = auto_switch
        self.navigate_switch = navigate_switch
        self.in_right_nav = False
        self.in_left_nav = False
        self.active_dpixbuf = active_dpixbuf
        self.inactive_dpixbuf = inactive_dpixbuf
        size_pixbuf = self.slide_images[0]

        self.pointer_offset_x = pointer_offset_x
        self.pointer_offset_y = pointer_offset_y
        self.pointer_radious = self.active_dpixbuf.get_pixbuf().get_width() / 2
        self.pointer_padding = pointer_padding
        self.set_size_request(-1, size_pixbuf.get_height() + height_offset)

        self.connect("expose-event", self.expose_slide_switcher)
        self.connect("motion-notify-event", self.motion_notify_slide_switcher)
        self.connect("leave-notify-event", self.leave_notify_slide_switcher)
        self.connect("enter-notify-event", self.enter_notify_slide_switcher)
        self.connect("button-press-event", lambda w, e: self.handle_animation(w, e, True))

        self.start_auto_slide()

    def expose_slide_switcher(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw background.
        if self.active_alpha > 0.0:
            active_pixbuf = self.slide_images[self.active_index]
            if self.horizontal_align == ALIGN_START:
                render_x = rect.x
            elif self.horizontal_align == ALIGN_MIDDLE:
                render_x = rect.x + (rect.width - active_pixbuf.get_width()) / 2
            else:
                render_x = rect.x + rect.width - active_pixbuf.get_width()

            if self.vertical_align == ALIGN_START:
                render_y = rect.y
            elif self.vertical_align == ALIGN_MIDDLE:
                render_y = rect.y + (rect.height - active_pixbuf.get_height()) / 2
            else:
                render_y = rect.y + rect.height - active_pixbuf.get_height()
            draw_pixbuf(cr,
                        active_pixbuf,
                        render_x,
                        render_y,
                        self.active_alpha)

        if self.target_index != None and self.target_alpha > 0.0:
            target_pixbuf = self.slide_images[self.target_index]
            if self.horizontal_align == ALIGN_START:
                render_x = rect.x
            elif self.horizontal_align == ALIGN_MIDDLE:
                render_x = rect.x + (rect.width - target_pixbuf.get_width()) / 2
            else:
                render_x = rect.x + rect.width - target_pixbuf.get_width()

            if self.vertical_align == ALIGN_START:
                render_y = rect.y
            elif self.vertical_align == ALIGN_MIDDLE:
                render_y = rect.y + (rect.height - target_pixbuf.get_height()) / 2
            else:
                render_y = rect.y + rect.height - target_pixbuf.get_height()
            draw_pixbuf(cr,
                        target_pixbuf,
                        render_x,
                        render_y,
                        self.target_alpha)

        # Draw select pointer.
        if self.image_number > 1:
            for index in range(0, self.image_number):
                if self.target_index == None:
                    if self.active_index == index:
                        pixbuf = self.active_dpixbuf.get_pixbuf()
                    else:
                        pixbuf = self.inactive_dpixbuf.get_pixbuf()
                else:
                    if self.target_index == index:
                        pixbuf = self.active_dpixbuf.get_pixbuf()
                    else:
                        pixbuf = self.inactive_dpixbuf.get_pixbuf()

                draw_pixbuf(cr,
                            pixbuf,
                            rect.x + rect.width + self.pointer_offset_x + index * self.pointer_padding,
                            rect.y + rect.height + self.pointer_offset_y
                            )

        return True

    def enter_notify_slide_switcher(self, widget, event):
        self.stop_auto_slide()

    def leave_notify_slide_switcher(self, widget, event):
        rect = widget.allocation
        if is_in_rect((event.x, event.y), (0, 0, rect.width, rect.height)):
            self.handle_animation(widget, event)
        else:
            self.start_auto_slide()

        set_cursor(widget, None)

        self.emit("leave-notify-index", self.active_index)

    def update_animation(self, source, status):
        self.active_alpha = 1.0 - status
        self.target_alpha = status

        self.queue_draw()

    def completed_animation(self, source, index):
        self.active_index = index
        self.active_alpha = 1.0
        self.target_index = None
        self.target_alpha = 0.0
        self.in_animiation = False

        self.queue_draw()

        # Start new animiation when cursor at new index when animiation completed.
        if self.motion_index:
            if self.active_index != self.motion_index:
                self.start_animation(self.hover_animation_time, self.motion_index)

    def motion_notify_slide_switcher(self, widget, event):
        self.handle_animation(widget, event)

    def handle_animation(self, widget, event, button_press=False):
        # Init.
        rect = widget.allocation

        start_x = rect.width + self.pointer_offset_x - self.pointer_radious
        start_y = rect.height + self.pointer_offset_y
        self.left_retangle = (0, 0, rect.width/3, rect.height - self.pointer_offset_y)
        self.right_retangle = (0 + 2*rect.width/3, 0, rect.width/3, rect.height - self.pointer_offset_y)

        if self.image_number > 1 and (start_y - 4 * self.pointer_radious < event.y < start_y + self.pointer_radious * 6
            and start_x - 2 * self.pointer_radious < event.x < start_x + 4 * self.pointer_padding + 4 * self.pointer_radious):

            set_cursor(widget, gtk.gdk.HAND2)

            if self.hover_switch or button_press:
                self.motion_index = None
                for index in range(0, self.image_number):
                    if start_x + index * self.pointer_padding < event.x < start_x + (index + 1) * self.pointer_padding:
                        self.motion_index = index
                        if self.active_index != index:
                            self.start_animation(self.hover_animation_time, index)
                        break
        elif self.image_number > 1 and is_in_rect((event.x, event.y), self.left_retangle) and self.navigate_switch:
            if not self.in_left_nav:
                self.in_left_nav = True
                self.queue_draw()
            set_cursor(widget, gtk.gdk.SB_LEFT_ARROW)
            if button_press:
                self.to_left_animation()
        elif self.image_number > 1 and is_in_rect((event.x, event.y), self.right_retangle) and self.navigate_switch:
            if not self.in_right_nav:
                self.in_right_nav = True
                self.queue_draw()
            set_cursor(widget, gtk.gdk.SB_RIGHT_ARROW)
            if button_press:
                self.to_right_animation()
        else:
            if self.in_left_nav or self.in_right_nav:
                self.in_left_nav = False
                self.in_right_nav = False
                self.queue_draw()
            set_cursor(widget, None)

            if button_press:
                self.emit("button-press-index", self.active_index)
            else:
                self.emit("motion-notify-index", self.active_index)

    def start_animation(self, animation_time, index=None):
        # Update ticker with active index if option index is None.
        if index == None:
            if self.active_index >= self.image_number - 1:
                index = 0
            else:
                index = self.active_index + 1

        if not self.in_animiation:
            self.in_animiation = True
            self.target_index = index

            timeline = Timeline(animation_time, CURVE_SINE)
            timeline.connect('update', self.update_animation)
            timeline.connect("completed", lambda source: self.completed_animation(source, index))
            timeline.run()

        return True

    def to_left_animation(self, animation_time=500):
        if self.active_index == 0:
            index = self.image_number - 1
        else:
            index = self.active_index - 1
        self.start_animation(animation_time, index)

    def to_right_animation(self, animation_time=500):
        self.start_animation(animation_time)

    def start_auto_slide(self):
        if self.auto_switch:
            self.auto_slide_timeout_id = gtk.timeout_add(self.auto_slide_timeout, lambda : self.start_animation(self.auto_animation_time))

    def stop_auto_slide(self):
        if self.auto_slide_timeout_id:
            remove_timeout_id(self.auto_slide_timeout_id)

gobject.type_register(SlideSwitcher)

