#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Xia Bin
#
# Author:     Xia Bin <xiabin@linuxdeepin.com>
#             Hou Shaohui houshao55@gmail.com
#
# Maintainer: Xia Bin <xiabin@linuxdeepin.com>
#             Hou Shaohui houshao55@gmail.com
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

import gtk
import gobject
from timeline import Timeline, CURVE_SINE
from draw import draw_pixbuf
from utils import set_cursor
from theme import ui_theme
from window import Window
from utils import is_in_rect

class HSlider(gtk.Viewport):
    '''
    HSlider class.

    @undocumented: slide_to_page
    @undocumented: set_to_page
    @undocumented: append_page
    '''

    __gsignals__ = {
            "start_slide" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            "completed_slide" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            }

    def __init__(self,
                 slide_time=200,
                 ):
        '''
        Initialize HSlider class.

        @param slide_time: The animation of slide time, default is 200ms.
        '''
        gtk.Viewport.__init__(self)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.fixed = gtk.Fixed()
        self.add(self.fixed)
        self.slide_time = slide_time
        self.pre_widget = None
        self.active_widget = None
        self.connect("realize", self._update_size)
        self.connect("size_allocate", self._update_size)
        self.page_width = 0
        self.page_height = 0
        self.in_sliding = False

    def _update_size(self, w=None, _w=None):
        self.page_width = self.allocation.width
        self.page_height = self.allocation.height
        if self.active_widget:
            self.active_widget.set_size_request(self.page_width, self.page_height)
        if self.pre_widget:
            self.pre_widget.set_size_request(self.page_width, self.page_height)
        self.show_all()

    def _to_right(self, percent):
        self.offset = int(round(percent * self.page_width))

        if self.pre_widget:
            self.fixed.move(self.pre_widget, - self.offset, 0)

        self.fixed.move(self.active_widget, self.page_width - self.offset, 0)

    def _to_left(self, percent):
        self.offset = int(round(percent * self.page_width))

        if self.pre_widget:
            self.fixed.move(self.pre_widget, self.offset, 0)

        self.fixed.move(self.active_widget, self.offset - self.page_width, 0)

    def _no_effect(self):
        self.offset = self.page_width

        if self.pre_widget:
            self.fixed.remove(self.pre_widget)
        self.fixed.move(self.active_widget, 0, 0)

    def to_page(self, w, direction):
        '''
        Slide to given page.

        @param w: gtk.Widget to slide.
        @param direction: The direction of slide animation, can use below value:
         - \"right\"    slide from right to left
         - \"left\"     slide from left to right
         - None         no animation effect, slide directly
        '''
        if self.in_sliding:
            return

        if w != self.active_widget:
            w.set_size_request(self.page_width, self.page_height)
            if w.parent != self.fixed:
                self.fixed.put(w, self.page_width, 0)
            self.active_widget = w

            self.timeline = Timeline(self.slide_time, CURVE_SINE)
            if direction == "right":
                self.timeline.connect('update', lambda source, status: self._to_right(status))
            elif direction == "left":
                self.timeline.connect('update', lambda source, status: self._to_left(status))
            else:
                self._no_effect()

            self.timeline.connect("start", lambda source: self._start())
            self.timeline.connect("completed", lambda source: self._completed())
            self.timeline.run()
            self.in_sliding = True

            self.show_all()

    def _start(self):
        self.emit("start_slide")

    def _completed(self):
        if self.pre_widget and self.pre_widget.parent == self.fixed:
            self.fixed.remove(self.pre_widget)
        self.pre_widget = self.active_widget
        #print "Pre: " +  str(self.pre_widget)  + "  act: " + str(self.active_widget) + "children: " + str(self.get_children())
        self.show_all()
        self.in_sliding = False
        self.emit("completed_slide")

    def to_page_now(self, w, d=None):
        '''
        Slide to given page immediately.

        @param w: gtk.Widget to slide.
        '''
        self.to_page(w, d)

    def slide_to_page(self, w, d):
        self.to_page(w, d)

    def set_to_page(self, w):
        self.to_page_now(w)

    def append_page(self, w):
        pass

gobject.type_register(HSlider)

class WizardBox(gtk.EventBox):
    '''
    WizardBox class.

    @undocumented: init_size
    @undocumented: on_expose_event
    @undocumented: handle_animation
    @undocumented: on_motion_notify
    @undocumented: on_enter_notify
    @undocumented: on_leave_notify
    @undocumented: on_button_press
    @undocumented: auto_animation
    @undocumented: start_animation
    @undocumented: update_animation
    @undocumented: completed_animation
    '''

    __gsignals__ = {
        'close': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

    def __init__(self,
                 slider_images=None,
                 pointer_images=None,
                 button_images=None,
                 show_button=True,
                 slide_delay=10000,
                 ):
        '''
        Initialize WizardBox class.

        @param slider_images: Slider images, default is None.
        @param pointer_images: Pointer images, default is None.
        @param pointer_images: Button images, default is None.
        @param show_button: Set as True to show button.
        @param slide_delay: The time of delay between slider image, default is 10000ms.
        '''
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK
                        )

        self.connect("expose-event", self.on_expose_event)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("button-press-event", self.on_button_press)

        # Init images.
        self.slider_pixbufs = map(gtk.gdk.pixbuf_new_from_file, slider_images)
        self.slider_numuber = len(slider_images)
        self.dot_normal_pixbuf, self.dot_active_pixbuf = map(gtk.gdk.pixbuf_new_from_file, pointer_images)
        self.button_normal_pixbuf, self.button_press_pixbuf = map(gtk.gdk.pixbuf_new_from_file, button_images)
        self.close_dpixbuf = ui_theme.get_pixbuf("button/window_close_normal.png")

        self.show_button = show_button

        # Init sizes.
        self.init_size()
        self.pointer_coords = {}

        # Move animation.
        self.active_index = 0
        self.target_index = None

        self.active_alpha = 1.0
        self.target_index = 0.0

        self.active_x = 0
        self.target_x = None
        self.slider_y = 0
        self.auto_animation_id = None
        self.auto_animation_timeout = slide_delay  # millisecond.
        self.slider_timeout = 1000 # millisecond.
        self.in_animation = False
        self.motion_index = None
        self.auto_animation()

    def init_size(self):
        slider_pixbuf = self.slider_pixbufs[0]
        self.slider_width = slider_pixbuf.get_width()
        self.slider_height = slider_pixbuf.get_height()
        self.set_size_request(self.slider_width, self.slider_height)

        self.dot_width = self.dot_normal_pixbuf.get_width()
        self.dot_height = self.dot_normal_pixbuf.get_height()

        dot_spacing = 10
        self.dot_width_offset = self.dot_width + dot_spacing
        dot_area_width = self.dot_width * self.slider_numuber + dot_spacing * (self.slider_numuber - 1)
        dot_offset_y = 40
        self.dot_start_x =  (self.slider_width - dot_area_width) / 2
        self.dot_y = self.slider_height - dot_offset_y

        close_spacing = 0
        close_x = self.slider_width - self.close_dpixbuf.get_pixbuf().get_width() - close_spacing
        close_y = close_spacing
        self.close_rect = gtk.gdk.Rectangle(close_x, close_y,
                                            self.close_dpixbuf.get_pixbuf().get_width(),
                                            self.close_dpixbuf.get_pixbuf().get_height())

        button_bottom_size = 55
        button_width = self.button_normal_pixbuf.get_width()
        button_height = self.button_normal_pixbuf.get_height()
        button_x = (self.slider_width - button_width) / 2
        button_y = self.slider_height - button_height - button_bottom_size
        self.button_rect = gtk.gdk.Rectangle(button_x,  button_y, button_width, button_height)

    def on_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        cr.save()
        draw_pixbuf(cr, self.slider_pixbufs[self.active_index], rect.x + self.active_x,
                    rect.x + self.slider_y, self.active_alpha)

        if self.target_index != None and self.target_x != None:
            draw_pixbuf(cr, self.slider_pixbufs[self.target_index], rect.x + self.target_x,
                        rect.y + self.slider_y, self.target_alpha)
        cr.restore()

        # Draw select pointer.
        dot_start_x = rect.x + self.dot_start_x

        for index in range(self.slider_numuber):
            if self.target_index == None:
                if self.active_index == index:
                    dot_pixbuf = self.dot_active_pixbuf
                else:
                    dot_pixbuf = self.dot_normal_pixbuf
            else:
                if self.target_index == index:
                    dot_pixbuf = self.dot_active_pixbuf
                else:
                    dot_pixbuf = self.dot_normal_pixbuf

            pointer_rect = gtk.gdk.Rectangle(
                dot_start_x, rect.y + self.dot_y,
                self.dot_width, self.dot_height)
            self.pointer_coords[index] = pointer_rect
            draw_pixbuf(cr, dot_pixbuf, dot_start_x, rect.y + self.dot_y)
            dot_start_x += self.dot_width_offset

        # Draw close pixbuf.
        draw_pixbuf(cr, self.close_dpixbuf.get_pixbuf(),
                    rect.x + self.close_rect.x, rect.y + self.close_rect.y)

        if self.show_button and self.target_index == self.slider_numuber - 1:
            if self.button_hover_flag:
                pixbuf = self.button_press_pixbuf
            else:
                pixbuf = self.button_normal_pixbuf
            draw_pixbuf(cr, pixbuf, rect.x + self.button_rect.x, rect.y + self.button_rect.y)
        return True

    def handle_animation(self, widget, event):
        self.motion_index = None
        for index, rect in self.pointer_coords.items():
            if rect.x <= event.x <= rect.x + rect.width and rect.y <= event.y <= rect.y + rect.height:
                set_cursor(widget, gtk.gdk.HAND2)
                self.motion_index = index
                break
        else:
            self.motion_index = None
            set_cursor(widget, None)

    def on_motion_notify(self, widget, event):
        self.handle_animation(widget, event)
        if is_in_rect((event.x, event.y), self.button_rect):
            self.button_hover_flag = True
        else:
            self.button_hover_flag = False
        self.queue_draw()

    def on_enter_notify(self, widget, event):
        if self.auto_animation_id is not None:
            gobject.source_remove(self.auto_animation_id)
            self.auto_animation_id = None

    def on_leave_notify(self, widget, event):
        self.auto_animation()
        set_cursor(widget, None)

    def on_button_press(self, widget, event):
        if self.motion_index != None:
            self.start_animation(self.slider_timeout, self.motion_index)

        if is_in_rect((event.x, event.y), self.close_rect):
            self.emit("close")

        if is_in_rect((event.x, event.y), self.button_rect):
            self.emit("close")


    def auto_animation(self):
        self.auto_animation_id = gobject.timeout_add(self.auto_animation_timeout,
                                                 lambda : self.start_animation(self.slider_timeout))

    def start_animation(self, animation_time, target_index=None, direction="left"):
        if target_index is None:
            if self.active_index >= self.slider_numuber - 1:
                return False
                target_index = 0
            else:
                target_index = self.active_index + 1
        else:
            if target_index < self.active_index:
                direction = "right"

        if not self.in_animation:
            self.in_animation = True
            self.target_index = target_index

            self.timeline = Timeline(animation_time, CURVE_SINE)
            self.timeline.connect("update", lambda source, status: self.update_animation(source, status, direction))
            self.timeline.connect("completed", lambda source: self.completed_animation(source, target_index))
            self.timeline.run()
        return True

    def update_animation(self, source, status, direction):
        self.active_alpha = 1.0 - status
        self.target_alpha = status

        if direction == "right":
            self._to_right(status)
        else:
            self._to_left(status)

        self.queue_draw()

    def completed_animation(self, source, index):
        self.active_index = index
        self.active_alpha = 1.0
        # self.target_index = None
        self.target_alpha = 0.0
        self.in_animation = False
        self.active_x = 0
        self.target_x = None
        self.queue_draw()

    def _to_right(self, status):
        self.active_x = self.slider_width * status
        self.target_x = 0

    def _to_left(self, status):
        self.active_x = 0 - (self.slider_width * status)
        self.target_x = 0

class Wizard(Window):
    '''
    Wizard class.

    @undocumented: destroy_wizard
    '''

    def __init__(self,
                 slider_files,
                 pointer_files,
                 button_files,
                 show_button=True,
                 finish_callback=None,
                 slide_delay=8000,
                 ):
        '''
        Initialize Wizard class.

        @param slider_files: The slider image files.
        @param pointer_files: The pointer image files.
        @param button_files: The button image files.
        @param show_button: if True will at last page show start button.
        @param finish_callback: The callback call when slider finish, this callback don't need input argument, default is None.
        @param slide_delay: The delay between slider images, default is 8000ms.
        '''
        Window.__init__(self)
        self.finish_callback = finish_callback

        self.set_position(gtk.WIN_POS_CENTER)
        self.set_resizable(False)
        self.wizard_box = WizardBox(slider_files, pointer_files, button_files, show_button, slide_delay)
        self.wizard_box.connect("close", lambda widget: self.destroy())
        self.connect("destroy", self.destroy_wizard)
        self.window_frame.add(self.wizard_box)
        self.add_move_event(self.wizard_box)

    def destroy_wizard(self, widget):
        if self.finish_callback:
            self.finish_callback()

if __name__ == "__main__":
    s = HSlider()

    w = gtk.Window()
    w.set_size_request(300, 300)
    h = gtk.HBox()
    w1 = gtk.Button("Widget 1")
    w2 = gtk.Button("Widget 2")

    s.to_page_now(w1)

    b = gtk.Button("to1")
    b.connect("clicked", lambda w: s.to_page(w1, "right" ))
    h.add(b)

    b = gtk.Button("to2")
    b.connect("clicked", lambda w: s.to_page(w2, "left"))
    h.add(b)

    v = gtk.VBox()
    v.add(h)
    v.add(s)

    w.add(v)
    w.show_all()

    w.connect("destroy", gtk.main_quit)

    gtk.main()
