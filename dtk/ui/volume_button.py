#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
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

from cache_pixbuf import CachePixbuf
from draw import draw_pixbuf
from theme import ui_theme
from utils import set_clickable_cursor
import tooltip as Tooltip
import gobject
import gtk

'''
100 / 500 = 0.2
x = 100 -> 100 * 0.2 = 20
x = 500 -> 500 * 0.2 = 100
x = 100 -> 100 * 0.2 = 20
'''

ZERO_STATE = 0
MIN_STATE = 1
MID_STATE = 2
MAX_STATE = 3
MUTE_STATE = -1

MOUSE_VOLUME_STATE_PRESS  = 1
MOUSE_VOLUME_STATE_HOVER  = 2
MOUSE_VOLUME_STATE_NORMAL = -1

VOLUME_RIGHT = "right"
VOLUME_LEFT   = "left"

class VolumeButton(gtk.Button):
    '''
    Volume button.
    '''

    __gsignals__ = {
        "volume-state-changed":(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_INT,gobject.TYPE_INT,))
        }

    def __init__(self,
                 volume_max_value = 100,
                 volume_width = 52,
                 volume_x = 0,
                 volume_y = 15,
                 line_height = 3,
                 volume_padding_x = 5,
                 volume_level_values = [(1, 33),(34, 66),(67, 100)],
                 scroll_bool = False,
                 press_emit_bool = False,
                 inc_value=5,
                 bg_pixbuf = ui_theme.get_pixbuf("volumebutton/bg.png"),
                 fg_pixbuf = ui_theme.get_pixbuf("volumebutton/fg.png"),
                 zero_volume_normal_pixbuf = ui_theme.get_pixbuf("volumebutton/zero_normal.png"),
                 zero_volume_hover_pixbuf = ui_theme.get_pixbuf("volumebutton/zero_hover.png"),
                 zero_volume_press_pixbuf = ui_theme.get_pixbuf("volumebutton/zero_press.png"),
                 min_volume_normal_pixbuf = ui_theme.get_pixbuf("volumebutton/lower_normal.png"),
                 min_volume_hover_pixbuf = ui_theme.get_pixbuf("volumebutton/lower_hover.png"),
                 min_volume_press_pixbuf = ui_theme.get_pixbuf("volumebutton/lower_press.png"),
                 mid_volume_normal_pixbuf = ui_theme.get_pixbuf("volumebutton/middle_normal.png"),
                 mid_volume_hover_pixbuf = ui_theme.get_pixbuf("volumebutton/middle_hover.png"),
                 mid_volume_press_pixbuf = ui_theme.get_pixbuf("volumebutton/middle_press.png"),
                 max_volume_normal_pixbuf = ui_theme.get_pixbuf("volumebutton/high_normal.png"),
                 max_volume_hover_pixbuf = ui_theme.get_pixbuf("volumebutton/high_hover.png"),
                 max_volume_press_pixbuf = ui_theme.get_pixbuf("volumebutton/high_press.png"),
                 mute_volume_normal_pixbuf = ui_theme.get_pixbuf("volumebutton/mute_normal.png"),
                 mute_volume_hover_pixbuf = ui_theme.get_pixbuf("volumebutton/mute_hover.png"),
                 mute_volume_press_pixbuf = ui_theme.get_pixbuf("volumebutton/mute_press.png"),
                 point_volume_pixbuf = ui_theme.get_pixbuf("volumebutton/point_normal.png"),
                 ):
        '''
        Initialize VolumeButton class.

        @param volume_max_value: Maximum value of volume, default is 100.
        @param volume_width: Width of volume button widget, default is 52 pixel.
        @param volume_x: X padding of volume button widget.
        @param volume_y: Y padding of volume button widget.
        @param line_height: Height of volume progressbar, default is 3 pixel.
        @param volume_padding_x: X padding value around volume progressbar.
        @param volume_level_values: The values of volume level.
        @param scroll_bool: True allowed scroll to change value, default is False.
        @param press_emit_bool: True to emit `volume-state-changed` signal when press, default is False.
        @param inc_value: The increase value of volume change, default is 5.
        '''
        gtk.Button.__init__(self)
        ###########################
        if volume_x < max_volume_normal_pixbuf.get_pixbuf().get_width():
            volume_x = max_volume_normal_pixbuf.get_pixbuf().get_width()
        '''Init pixbuf.'''
        self.__bg_pixbuf = bg_pixbuf
        self.__fg_pixbuf = fg_pixbuf
        self.__bg_cache_pixbuf = CachePixbuf()
        self.__fg_cache_pixbuf = CachePixbuf()
        # zero volume pixbuf.
        self.__zero_volume_normal_pixbuf  = zero_volume_normal_pixbuf
        self.__zero_volume_hover_pixbuf   = zero_volume_hover_pixbuf
        self.__zero_volume_press_pixbuf   = zero_volume_press_pixbuf
        # min volume pixbuf.
        self.__min_volume_normal_pixbuf  = min_volume_normal_pixbuf
        self.__min_volume_hover_pixbuf   = min_volume_hover_pixbuf
        self.__min_volume_press_pixbuf   = min_volume_press_pixbuf
        # mid volume pixbuf:
        self.__mid_volume_normal_pixbuf     = mid_volume_normal_pixbuf
        self.__mid_volume_hover_pixbuf      = mid_volume_hover_pixbuf
        self.__mid_volume_press_pixbuf        = mid_volume_press_pixbuf
        # max volume pixbuf[normal, hover, press].
        self.__max_volume_normal_pixbuf  = max_volume_normal_pixbuf
        self.__max_volume_hover_pixbuf   = max_volume_hover_pixbuf
        self.__max_volume_press_pixbuf   = max_volume_press_pixbuf
        # mute volume pixbuf[normal, hover, press].
        self.__mute_volume_normal_pixbuf    = mute_volume_normal_pixbuf
        self.__mute_volume_hover_pixbuf     = mute_volume_hover_pixbuf
        self.__mute_volume_press_pixbuf     = mute_volume_press_pixbuf
        # point volume pixbuf.
        self.__point_volume_pixbuf    = point_volume_pixbuf
        '''Init Set VolumeButton attr.'''
        '''Init value.'''
        self.__press_emit_bool  = press_emit_bool
        self.__line_height       = line_height
        self.__current_value    = 0
        self.__mute_bool        = False
        self.temp_mute_bool     = False
        self.__drag             = False
        self.__volume_max_value = volume_max_value
        self.__volume_width     = volume_width

        self.__volume_left_x    = volume_x - self.__max_volume_normal_pixbuf.get_pixbuf().get_width() - volume_padding_x
        self.__volume_left_y    = volume_y - self.__max_volume_normal_pixbuf.get_pixbuf().get_height()/2 + self.__point_volume_pixbuf.get_pixbuf().get_height()/2
        self.__volume_right_x   = volume_x
        self.__volume_right_y   = volume_y
        '''Left'''
        self.volume_level_values = volume_level_values
        self.__volume_state = MIN_STATE
        self.__mouse_state  = MOUSE_VOLUME_STATE_NORMAL
        '''Right'''
        # bg value.
        self.__bg_x         = 0
        self.__bg_y         = self.__volume_right_y
        self.__bg_padding_x = self.__volume_right_x
        # fg value.
        self.__fg_x         = 0
        self.__fg_y         = self.__volume_right_y
        self.__fg_padding_x = self.__volume_right_x
        # point value.
        self.__point_y         = self.__volume_right_y
        self.__point_padding_x = self.__volume_right_x
        self.inc_value = inc_value

        '''Init VolumeButton event.'''
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("expose-event",         self.__expose_draw_volume)
        self.connect("motion-notify-event",  self.__motion_mouse_set_point)
        self.connect("button-press-event",   self.__press_mouse_set_point)
        self.connect("button-release-event", self.__release_mouse_set_point)
        '''Event value'''
        self.press_bool = False
        # scroll event.
        if scroll_bool:
            self.connect("scroll-event",     self.__scroll_mouse_set_point)

        self.set_size_request(volume_width + self.__volume_left_x + self.__volume_right_x + self.__mute_volume_normal_pixbuf.get_pixbuf().get_width(), 30)

        set_clickable_cursor(self)

    def set_press_emit_bool(self, emit_bool):
        self.__press_emit_bool = emit_bool

    def __set_point_padding_x(self, event):
        self.__mute_bool = False
        self.__point_padding_x = int(event.x)
        self.queue_draw()

    def __press_mouse_set_point(self, widget, event):
        temp_x = int(event.x)

        temp_min_x = self.__bg_x + self.__bg_padding_x - self.__point_volume_pixbuf.get_pixbuf().get_width()/2
        temp_max_x = self.__bg_x + self.__bg_padding_x + self.__volume_width + self.__point_volume_pixbuf.get_pixbuf().get_width()/2
        self.queue_draw()
        if temp_min_x < temp_x < temp_max_x:
            self.__set_point_padding_x(event)
            self.__drag = True
        else:
            if self.__volume_left_x <= temp_x <= temp_min_x:
                # Set mouse state press.
                self.__mouse_state = MOUSE_VOLUME_STATE_PRESS
                self.temp_mute_bool = True
                self.press_bool = True

    def __release_mouse_set_point(self, widget, event):
        # Set mouse state normal.
        self.__mouse_state = MOUSE_VOLUME_STATE_NORMAL
        self.__drag = False
        self.press_bool = False

        temp_x = int(event.x)
        temp_y = int(event.y)

        temp_min_x = self.__bg_x + self.__bg_padding_x - self.__point_volume_pixbuf.get_pixbuf().get_width()/2
        if self.__volume_left_x <= temp_x <= temp_min_x  and ( self.__volume_left_y <=temp_y < (self.__volume_left_y + self.__mute_volume_hover_pixbuf.get_pixbuf().get_height())):
            if self.temp_mute_bool and not self.__mute_bool:
                # Set mute state.
                self.__mute_bool = not self.__mute_bool
                self.__volume_state = MUTE_STATE
                self.temp_mute_bool = False
            else: # modify state.
                self.__mute_bool = False
                self.temp_mute_bool = False
                self.__set_volume_value_to_state(self.__current_value)
                self.queue_draw()

        if self.__press_emit_bool:
            self.emit("volume-state-changed", self.__current_value, self.__volume_state)

        self.queue_draw()

    def __motion_mouse_set_point(self, widget, event):
        temp_x = int(event.x)
        temp_y = int(event.y)
        temp_min_x = self.__bg_x + self.__bg_padding_x - self.__point_volume_pixbuf.get_pixbuf().get_width()/2

        if (self.__volume_left_x <= temp_x <= temp_min_x) and ( self.__volume_left_y <=temp_y < (self.__volume_left_y + self.__mute_volume_hover_pixbuf.get_pixbuf().get_height())):
            self.__mouse_state = MOUSE_VOLUME_STATE_HOVER
        else:
            self.__mouse_state = MOUSE_VOLUME_STATE_NORMAL
        if not self.press_bool:
            self.queue_draw()

        if self.__drag:
            self.__set_point_padding_x(event)

    def __scroll_mouse_set_point(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.volume_other_set_value(VOLUME_RIGHT)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.volume_other_set_value(VOLUME_LEFT)

    def volume_other_set_value(self, volume_type):
        point_width_average      = self.__point_volume_pixbuf.get_pixbuf().get_width() / 2
        temp_min = (self.__point_padding_x - point_width_average)
        temp_max = (self.__point_padding_x + self.__volume_width - point_width_average)

        self.__mute_bool = False

        if volume_type == VOLUME_RIGHT:
            if self.__point_padding_x >= temp_max:
                self.__point_padding_x = temp_max
            else:
                self.__point_padding_x += self.inc_value
        elif volume_type == VOLUME_LEFT:
            if self.__point_padding_x <= temp_min:
                self.__point_padding_x = temp_min
            else:
                self.__point_padding_x -= self.inc_value

        self.queue_draw()

    def __expose_draw_volume(self, widget, event):
        self.__draw_volume_right(widget, event)              # 1: get current value.
        self.__set_volume_value_to_state(self.__current_value) # 2: value to state.
        self.__draw_volume_left(widget, event)               # 3: draw state pixbuf.

        if not self.__press_emit_bool:
            self.emit("volume-state-changed", self.__current_value, self.__volume_state)
        # propagate_expose(widget, event)
        return True


    '''Left function'''
    @property
    def volume_state(self):
        return self.__volume_state

    @volume_state.setter
    def volume_state(self, state):
        if state == MIN_STATE:
            self.__volume_state = MIN_STATE
        elif state == ZERO_STATE:
            self.__volume_state = ZERO_STATE
        elif state == MID_STATE:
            self.__volume_state = MID_STATE
        elif state == MAX_STATE:
            self.__volume_state = MAX_STATE
        elif state == MUTE_STATE:
            self.__volume_state = MUTE_STATE


    @volume_state.getter
    def volume_state(self):
        return self.__volume_state

    @volume_state.deleter
    def volume_state(self):
        del self.__volume_state

    def set_volume_level_values(self, show_value):
        try:
            show_value[0][0] - show_value[0][1]
            show_value[1][0] - show_value[1][1]
            show_value[2][0] - show_value[2][1]

            self.volume_level_values = show_value
        except:
            print "Error show value!!"

    def __set_volume_value_to_state(self, value):
        if not self.__mute_bool:
            temp_show_value = self.volume_level_values
            if temp_show_value[0][0] <= value <= temp_show_value[0][1]:
                self.__volume_state = MIN_STATE
            elif temp_show_value[1][0] <= value <= temp_show_value[1][1]:
                self.__volume_state = MID_STATE
            elif temp_show_value[2][0] <= value <= temp_show_value[2][1]:
                self.__volume_state = MAX_STATE
            elif 0 == value:
                self.__volume_state = ZERO_STATE
        else:
            self.__volume_state = MUTE_STATE

    def set_volume_mute(self, mute_flag=True):
        if mute_flag:
            self.temp_mute_bool = False
            self.__mute_bool = True
            self.__volume_state = MUTE_STATE
        else:
            self.temp_mute_bool = False
            self.__mute_bool = False
            self.__set_volume_value_to_state(self.value)

        self.queue_draw()

    def __draw_volume_left(self, widget, event):
        cr = widget.window.cairo_create()
        x, y, w, h = widget.allocation

        if self.__volume_state == MUTE_STATE: # mute state.
            if self.__mouse_state == MOUSE_VOLUME_STATE_NORMAL:
                pixbuf = self.__mute_volume_normal_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_HOVER:
                pixbuf = self.__mute_volume_hover_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_PRESS:
                pixbuf = self.__mute_volume_press_pixbuf
        elif self.__volume_state == ZERO_STATE: # zero state.
            if self.__mouse_state == MOUSE_VOLUME_STATE_NORMAL:
                pixbuf = self.__zero_volume_normal_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_HOVER:
                pixbuf = self.__zero_volume_hover_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_PRESS:
                pixbuf = self.__zero_volume_press_pixbuf
        elif self.__volume_state == MIN_STATE: # min state.
            if self.__mouse_state == MOUSE_VOLUME_STATE_NORMAL:
                pixbuf = self.__min_volume_normal_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_HOVER:
                pixbuf = self.__min_volume_hover_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_PRESS:
                pixbuf = self.__min_volume_press_pixbuf
        elif self.__volume_state == MID_STATE: # mid state.
            if self.__mouse_state == MOUSE_VOLUME_STATE_NORMAL:
                pixbuf = self.__mid_volume_normal_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_HOVER:
                pixbuf = self.__mid_volume_hover_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_PRESS:
                pixbuf = self.__mid_volume_press_pixbuf
        elif self.__volume_state == MAX_STATE: # max state.
            if self.__mouse_state == MOUSE_VOLUME_STATE_NORMAL:
                pixbuf = self.__max_volume_normal_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_HOVER:
                pixbuf = self.__max_volume_hover_pixbuf
            elif self.__mouse_state == MOUSE_VOLUME_STATE_PRESS:
                pixbuf = self.__max_volume_press_pixbuf


        draw_pixbuf(cr,
                    pixbuf.get_pixbuf(),
                    x + self.__volume_left_x,
                    y + self.__volume_left_y,
                    )

    '''Right function'''
    @property
    def line_height(self):
        return self.__line_height

    @line_height.setter
    def line_height(self, width):
        self.__line_height = width
        self.queue_draw()

    @line_height.getter
    def line_height(self):
        return self.__line_height

    @line_height.deleter
    def line_height(self):
        del self.__line_height

    @property
    def value(self):
        return self.__current_value

    @value.setter
    def value(self, value):
        if 0 <= value <= self.__volume_max_value:
            Tooltip.text(self, str(value))
            temp_padding = (float(self.__volume_max_value) / self.__volume_width)
            temp_padding_x = float(value) / temp_padding
            self.__point_padding_x = temp_padding_x + ((self.__fg_padding_x))
            self.queue_draw()

    @value.getter
    def value(self):
        return self.__current_value


    def set_volume_position(self, x, y):
        self.__volume_right_x = x
        self.__volume_right_y = y
        # Set x.
        self.__bg_padding_x    = self.__volume_right_x
        self.__fg_padding_x    = self.__volume_right_x
        self.__point_padding_x = self.__volume_right_x
        # Set y.
        self.__bg_y    = self.__volume_right_y
        self.__fg_y    = self.__volume_right_y
        self.__point_y = self.__volume_right_y

    @property
    def max_value(self):
        self.__volume_max_value

    @max_value.setter
    def max_value(self, max_value):
        self.__volume_max_value = max_value

    @max_value.getter
    def max_value(self):
        return self.__volume_max_value

    @max_value.deleter
    def max_value(self):
        del self.__volume_max_value

    def __draw_volume_right(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_line_width(self.__line_height)
        x, y, w, h = widget.allocation

        fg_height_average = (self.__point_volume_pixbuf.get_pixbuf().get_height() - self.__fg_pixbuf.get_pixbuf().get_height()) / 2
        bg_height_average = (self.__point_volume_pixbuf.get_pixbuf().get_height() - self.__bg_pixbuf.get_pixbuf().get_height()) / 2
        point_width_average      = self.__point_volume_pixbuf.get_pixbuf().get_width() / 2
        ##################################################
        # Draw bg.
        if self.__volume_width > 0:
            self.__bg_cache_pixbuf.scale(self.__bg_pixbuf.get_pixbuf(),
                                         self.__volume_width,
                                         self.__bg_pixbuf.get_pixbuf().get_height(),
                                         )
            draw_pixbuf(
                cr,
                self.__bg_cache_pixbuf.get_cache(),
                x + self.__bg_x + self.__bg_padding_x,
                y + self.__bg_y + bg_height_average)

        temp_fg_padding_x = self.__point_padding_x - (self.__fg_x + self.__fg_padding_x)

        if temp_fg_padding_x < 0:
            temp_fg_padding_x = 0
        if temp_fg_padding_x > self.__volume_width:
            temp_fg_padding_x = self.__volume_width
        # Get current value.
        self.__current_value = temp_fg_padding_x * (float(self.__volume_max_value) / self.__volume_width)

        # Draw fg.
        if temp_fg_padding_x > 0:
            self.__fg_cache_pixbuf.scale(self.__fg_pixbuf.get_pixbuf(),
                                         int(temp_fg_padding_x),
                                         self.__fg_pixbuf.get_pixbuf().get_height(),
                                         )
            draw_pixbuf(
                cr,
                self.__fg_cache_pixbuf.get_cache(),
                x + self.__fg_x + self.__fg_padding_x,
                y + self.__fg_y + fg_height_average)
        #################################################
        # Draw point.
        temp_point_padding_x     = (self.__point_padding_x - point_width_average)

        temp_min = (self.__volume_right_x - point_width_average)
        temp_max = (self.__volume_right_x + self.__volume_width - point_width_average)
        if temp_point_padding_x < temp_min:
            temp_point_padding_x = temp_min
        if temp_point_padding_x > temp_max:
            temp_point_padding_x = temp_max

        draw_pixbuf(cr,
                    self.__point_volume_pixbuf.get_pixbuf(),
                    x + temp_point_padding_x,
                    y + self.__point_y)

gobject.type_register(VolumeButton)

if __name__ == "__main__":
    import random
    from dtk.ui.window import Window
    def set_time_position():
        volume_button.value = (random.randint(0, 100))
        return True

    def get_volume_value(volume_button, value, volume_state):
        print "[get_volume_value:]"
        print "volume_button:%s" % volume_button
        print "value:%s" % value
        print "volume_state:%s" % volume_state

    def set_value_button_clicked(widget):
        print volume_button.volume_state
        volume_button.max_value = 200
        volume_button.value = 100
        volume_button.line_height = 4    # Set draw line width.
        # volume_button.set_volume_level_values([(0,10),(11,80),(81,100)])

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    # win = Window()
    win.set_size_request(200, 120)
    win.set_title("测试音量按钮")
    main_vbox = gtk.VBox()
    volume_button = VolumeButton(100,220)
    volume_button.value = 100
    # volume_button = VolumeButton()
    volume_button.connect("volume-state-changed", get_volume_value)
    set_value_button = gtk.Button("设置音量的值")
    set_value_button.connect("clicked", set_value_button_clicked)
    main_vbox.pack_start(volume_button, True, True)
    main_vbox.pack_start(set_value_button, True, True)
    # win.add(volume_button)
    win.add(main_vbox)
    # win.window_frame.add(main_vbox)
    # gtk.timeout_add(500, set_time_position)
    win.show_all()
    gtk.main()

