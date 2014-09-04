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

from cache_pixbuf import CachePixbuf
from constant import DEFAULT_FONT_SIZE
from draw import draw_vlinear, draw_pixbuf, draw_line, draw_text
from keymap import get_keyevent_name
from label import Label
from theme import ui_theme
from utils import is_in_rect
import gobject
import gtk
import pango
from deepin_utils.process import run_command
from utils import (get_content_size, color_hex_to_cairo, propagate_expose, set_clickable_cursor,
                   window_is_max, get_same_level_widgets, widget_fix_cycle_destroy_bug,
                   get_widget_root_coordinate, WIDGET_POS_BOTTOM_LEFT)

__all__ = ["Button", "ImageButton", "ThemeButton",
           "MenuButton", "MinButton", "CloseButton",
           "MaxButton", "ToggleButton", "ActionButton",
           "CheckButton", "RadioButton", "DisableButton",
           "LinkButton", "ComboButton", "SwitchButton"]

class Button(gtk.Button):
    '''
    Button with Deepin UI style.

    @undocumented: key_press_button
    @undocumented: expose_button
    '''

    def __init__(self,
                 label="",
                 font_size=DEFAULT_FONT_SIZE):
        '''
        Initialize Button class.

        @param label: Button label.
        @param font_size: Button label font size.
        '''
        gtk.Button.__init__(self)
        self.font_size = font_size
        self.min_width = 69
        self.min_height = 22
        self.padding_x = 15
        self.padding_y = 3

        self.set_label(label)

        self.connect("expose-event", self.expose_button)
        self.connect("key-press-event", self.key_press_button)

        self.keymap = {
            "Return" : self.clicked
            }

    def set_label(self, label, font_size=DEFAULT_FONT_SIZE):
        '''
        Set label of Button.

        @param label: Button label.
        @param font_size: Button label font size.
        '''
        self.label = label
        (self.label_width, self.label_height) = get_content_size(label, self.font_size)
        self.set_size_request(max(self.label_width + self.padding_x * 2, self.min_width),
                              max(self.label_height + self.padding_y * 2, self.min_height))

        self.queue_draw()

    def key_press_button(self, widget, event):
        '''
        Callback for `button-press-event` signal.

        @param widget: Button widget.
        @param event: Button press event.
        '''
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

    def expose_button(self, widget, event):
        '''
        Callback for `expose-event` signal.

        @param widget: Button widget.
        @param event: Button press event.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Get color info.
        if widget.state == gtk.STATE_NORMAL:
            text_color = ui_theme.get_color("button_font").get_color()
            border_color = ui_theme.get_color("button_border_normal").get_color()
            background_color = ui_theme.get_shadow_color("button_background_normal").get_color_info()
        elif widget.state == gtk.STATE_PRELIGHT:
            text_color = ui_theme.get_color("button_font").get_color()
            border_color = ui_theme.get_color("button_border_prelight").get_color()
            background_color = ui_theme.get_shadow_color("button_background_prelight").get_color_info()
        elif widget.state == gtk.STATE_ACTIVE:
            text_color = ui_theme.get_color("button_font").get_color()
            border_color = ui_theme.get_color("button_border_active").get_color()
            background_color = ui_theme.get_shadow_color("button_background_active").get_color_info()
        elif widget.state == gtk.STATE_INSENSITIVE:
            text_color = ui_theme.get_color("disable_text").get_color()
            border_color = ui_theme.get_color("disable_frame").get_color()
            disable_background_color = ui_theme.get_color("disable_background").get_color()
            background_color = [(0, (disable_background_color, 1.0)),
                                (1, (disable_background_color, 1.0))]

        # Draw background.
        draw_vlinear(
            cr,
            x + 1, y + 1, w - 2, h - 2,
            background_color)

        # Draw border.
        cr.set_source_rgb(*color_hex_to_cairo(border_color))
        draw_line(cr, x + 2, y + 1, x + w - 2, y + 1) # top
        draw_line(cr, x + 2, y + h, x + w - 2, y + h) # bottom
        draw_line(cr, x + 1, y + 2, x + 1, y + h - 2) # left
        draw_line(cr, x + w, y + 2, x + w, y + h - 2) # right

        # Draw four point.
        if widget.state == gtk.STATE_INSENSITIVE:
            top_left_point = ui_theme.get_pixbuf("button/disable_corner.png").get_pixbuf()
        else:
            top_left_point = ui_theme.get_pixbuf("button/corner.png").get_pixbuf()
        top_right_point = top_left_point.rotate_simple(270)
        bottom_right_point = top_left_point.rotate_simple(180)
        bottom_left_point = top_left_point.rotate_simple(90)

        draw_pixbuf(cr, top_left_point, x, y)
        draw_pixbuf(cr, top_right_point, x + w - top_left_point.get_width(), y)
        draw_pixbuf(cr, bottom_left_point, x, y + h - top_left_point.get_height())
        draw_pixbuf(cr, bottom_right_point, x + w - top_left_point.get_width(), y + h - top_left_point.get_height())

        # Draw font.
        draw_text(cr, self.label, x, y, w, h, self.font_size, text_color,
                    alignment=pango.ALIGN_CENTER)

        return True

gobject.type_register(Button)

class ImageButton(gtk.Button):
    '''
    ImageButton class.
    '''

    def __init__(self,
                 normal_dpixbuf,
                 hover_dpixbuf,
                 press_dpixbuf,
                 scale_x=False,
                 content=None,
                 insensitive_dpixbuf=None):
        '''
        Initialize ImageButton class.

        @param normal_dpixbuf: DynamicPixbuf for button normal status.
        @param hover_dpixbuf: DynamicPixbuf for button hover status.
        @param press_dpixbuf: DynamicPixbuf for button press status.
        @param scale_x: Whether scale horticulturally, default is False.
        @param content: Button label content.
        @param insensitive_dpixbuf: DyanmicPixbuf for button insensitive status, default is None.
        '''
        gtk.Button.__init__(self)
        cache_pixbuf = CachePixbuf()
        draw_button(self,
                    cache_pixbuf,
                    normal_dpixbuf,
                    hover_dpixbuf,
                    press_dpixbuf,
                    scale_x,
                    content,
                    insensitive_dpixbuf=insensitive_dpixbuf)

    def set_active(self, is_active):
        '''
        Set active status.

        @param is_active: Set as True to make ImageButton active.
        '''
        if is_active:
            self.set_state(gtk.STATE_PRELIGHT)
        else:
            self.set_state(gtk.STATE_NORMAL)

gobject.type_register(ImageButton)

class ThemeButton(gtk.Button):
    '''
    ThemeButton class.
    '''

    def __init__(self):
        '''
        Initialize ThemeButton class.
        '''
        gtk.Button.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        draw_button(
            self,
            self.cache_pixbuf,
            ui_theme.get_pixbuf("button/window_theme_normal.png"),
            ui_theme.get_pixbuf("button/window_theme_hover.png"),
            ui_theme.get_pixbuf("button/window_theme_press.png"))

gobject.type_register(ThemeButton)

class MenuButton(gtk.Button):
    '''
    MenuButton class.
    '''

    def __init__(self):
        '''
        Initialize MenuButton class.
        '''
        gtk.Button.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        draw_button(
            self,
            self.cache_pixbuf,
            ui_theme.get_pixbuf("button/window_menu_normal.png"),
            ui_theme.get_pixbuf("button/window_menu_hover.png"),
            ui_theme.get_pixbuf("button/window_menu_press.png"))

gobject.type_register(MenuButton)

class MinButton(gtk.Button):
    '''
    MinButton.
    '''

    def __init__(self):
        '''
        Initialize MinButton class.
        '''
        gtk.Button.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        draw_button(
            self,
            self.cache_pixbuf,
            ui_theme.get_pixbuf("button/window_min_normal.png"),
            ui_theme.get_pixbuf("button/window_min_hover.png"),
            ui_theme.get_pixbuf("button/window_min_press.png"))

gobject.type_register(MinButton)

class CloseButton(gtk.Button):
    '''
    CloseButton class.
    '''

    def __init__(self):
        '''
        Initialize CloseButton class.
        '''
        gtk.Button.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        draw_button(
            self,
            self.cache_pixbuf,
            ui_theme.get_pixbuf("button/window_close_normal.png"),
            ui_theme.get_pixbuf("button/window_close_hover.png"),
            ui_theme.get_pixbuf("button/window_close_press.png"))

gobject.type_register(CloseButton)

class MaxButton(gtk.Button):
    '''
    MaxButton class.
    '''

    def __init__(self,
                 sub_dir="button",
                 max_path_prefix="window_max",
                 unmax_path_prefix="window_unmax"):
        '''
        Initialize MaxButton class.

        @param sub_dir: Subdirectory of button images.
        @param max_path_prefix: Image path prefix for maximise status.
        @param unmax_path_prefix: Image path prefix for un-maximise status.
        '''
        gtk.Button.__init__(self)
        self.cache_pixbuf = CachePixbuf()
        draw_max_button(self, self.cache_pixbuf, sub_dir, max_path_prefix, unmax_path_prefix)

gobject.type_register(MaxButton)

def draw_button(widget,
                cache_pixbuf,
                normal_dpixbuf,
                hover_dpixbuf,
                press_dpixbuf,
                scale_x=False,
                button_label=None,
                font_size=DEFAULT_FONT_SIZE,
                label_dcolor=ui_theme.get_color("button_default_font"),
                insensitive_dpixbuf=None,
                ):
    '''
    Draw button.

    @param widget: Gtk.Widget instance.
    @param cache_pixbuf: CachePixbuf.
    @param normal_dpixbuf: DynamicPixbuf of normal status.
    @param hover_dpixbuf: DynamicPixbuf of hover status.
    @param press_dpixbuf: DynamicPixbuf of press status.
    @param scale_x: Whether button scale with content.
    @param button_label: Button label, default is None.
    @param font_size: Button label font size, default is DEFAULT_FONT_SIZE.
    @param label_dcolor: Button label color.
    @param insensitive_dpixbuf: DyanmicPixbuf of insensitive status, default is None.
    '''
    # Init request size.
    if scale_x:
        request_width = get_content_size(button_label, font_size)[0]
    else:
        request_width = normal_dpixbuf.get_pixbuf().get_width()
    request_height = normal_dpixbuf.get_pixbuf().get_height()
    widget.set_size_request(request_width, request_height)

    # Expose button.
    widget.connect("expose-event", lambda w, e: expose_button(
            w, e,
            cache_pixbuf,
            scale_x, False,
            normal_dpixbuf, hover_dpixbuf, press_dpixbuf,
            button_label, font_size, label_dcolor, insensitive_dpixbuf))

def expose_button(widget,
                  event,
                  cache_pixbuf,
                  scale_x,
                  scale_y,
                  normal_dpixbuf,
                  hover_dpixbuf,
                  press_dpixbuf,
                  button_label,
                  font_size,
                  label_dcolor,
                  insensitive_dpixbuf=None):
    '''
    Expose callback for L{ I{draw_button} <draw_button>}.

    @param widget: Gtk.Widget instance.
    @param cache_pixbuf: CachePixbuf.
    @param scale_x: Whether button scale width with content.
    @param scale_y: Whether button scale height with content.
    @param normal_dpixbuf: DynamicPixbuf of normal status.
    @param hover_dpixbuf: DynamicPixbuf of hover status.
    @param press_dpixbuf: DynamicPixbuf of press status.
    @param button_label: Button label, default is None.
    @param font_size: Button label font size, default is DEFAULT_FONT_SIZE.
    @param label_dcolor: Button label color.
    @param insensitive_dpixbuf: DynamicPixbuf of insensitive status.
    '''
    # Init.
    rect = widget.allocation

    image = None
    # Get pixbuf along with button's sate.
    if widget.state == gtk.STATE_NORMAL:
        image = normal_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_PRELIGHT:
        image = hover_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_ACTIVE:
        image = press_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_INSENSITIVE:
        if insensitive_dpixbuf == None:
            insensitive_dpixbuf = normal_dpixbuf
        image = insensitive_dpixbuf.get_pixbuf()

    # Init size.
    if scale_x:
        image_width = widget.allocation.width
    else:
        image_width = image.get_width()

    if scale_y:
        image_height = widget.allocation.height
    else:
        image_height = image.get_height()

    # Draw button.
    pixbuf = image
    if pixbuf.get_width() != image_width or pixbuf.get_height() != image_height:
        cache_pixbuf.scale(image, image_width, image_height)
        pixbuf = cache_pixbuf.get_cache()
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)

    # Draw font.
    if button_label:
        draw_text(cr, button_label,
                    rect.x, rect.y, rect.width, rect.height,
                    font_size,
                    label_dcolor.get_color(),
                    alignment=pango.ALIGN_CENTER
                    )

    # Propagate expose to children.
    propagate_expose(widget, event)

    return True

def draw_max_button(widget, cache_pixbuf, sub_dir, max_path_prefix, unmax_path_prefix):
    '''
    Draw maximum button.

    @param widget: Gtk.Widget instance.
    @param cache_pixbuf: CachePixbuf to avoid unnecessary pixbuf new operation.
    @param sub_dir: Subdirectory of button.
    @param max_path_prefix: Prefix of maximum image path.
    @param unmax_path_prefix: Prefix of un-maximum image path.
    '''
    # Init request size.
    pixbuf = ui_theme.get_pixbuf("%s/%s_normal.png" % (sub_dir, unmax_path_prefix)).get_pixbuf()
    widget.set_size_request(pixbuf.get_width(), pixbuf.get_height())

    # Redraw.
    widget.connect("expose-event", lambda w, e:
                   expose_max_button(w, e,
                                     cache_pixbuf,
                                     sub_dir, max_path_prefix, unmax_path_prefix))

def expose_max_button(widget, event, cache_pixbuf, sub_dir, max_path_prefix, unmax_path_prefix):
    '''
    Expose callback for L{ I{draw_max_button} <draw_max_button>}.

    @param widget: Gtk.Widget instance.
    @param event: Expose event.
    @param cache_pixbuf: CachePixbuf to avoid unnecessary new pixbuf operation.
    @param sub_dir: Subdirectory for image path.
    @param max_path_prefix: Prefix of maximum image path.
    @param unmax_path_prefix: Prefix of un-maximum image path.
    '''
    # Get dynamic pixbuf.
    if window_is_max(widget):
        normal_dpixbuf = ui_theme.get_pixbuf("%s/%s_normal.png" % (sub_dir, unmax_path_prefix))
        hover_dpixbuf = ui_theme.get_pixbuf("%s/%s_hover.png" % (sub_dir, unmax_path_prefix))
        press_dpixbuf = ui_theme.get_pixbuf("%s/%s_press.png" % (sub_dir, unmax_path_prefix))
    else:
        normal_dpixbuf = ui_theme.get_pixbuf("%s/%s_normal.png" % (sub_dir, max_path_prefix))
        hover_dpixbuf = ui_theme.get_pixbuf("%s/%s_hover.png" % (sub_dir, max_path_prefix))
        press_dpixbuf = ui_theme.get_pixbuf("%s/%s_press.png" % (sub_dir, max_path_prefix))

    # Get pixbuf along with button's sate.
    if widget.state == gtk.STATE_NORMAL:
        image = normal_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_PRELIGHT:
        image = hover_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_ACTIVE:
        image = press_dpixbuf.get_pixbuf()

    # Init size.
    image_width = image.get_width()
    image_height = image.get_height()

    # Draw button.
    pixbuf = image
    if pixbuf.get_width() != image_width or pixbuf.get_height() != image_height:
        cache_pixbuf.scale(image, image_width, image_height)
        pixbuf = cache_pixbuf.get_cache()
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)

    # Propagate expose to children.
    propagate_expose(widget, event)

    return True

class ToggleButton(gtk.ToggleButton):
    '''
    ToggleButton class.

    @undocumented: press_toggle_button
    @undocumented: release_toggle_button
    @undocumented: expose_toggle_button
    @undocumented: set_inactive_pixbuf_group
    @undocumented: set_active_pixbuf_group
    '''

    def __init__(self,
                 inactive_normal_dpixbuf,
                 active_normal_dpixbuf,
                 inactive_hover_dpixbuf=None,
                 active_hover_dpixbuf=None,
                 inactive_press_dpixbuf=None,
                 active_press_dpixbuf=None,
                 inactive_disable_dpixbuf=None,
                 active_disable_dpixbuf=None,
                 button_label=None,
                 padding_x=0,
                 font_size=DEFAULT_FONT_SIZE):
        '''
        Initialize ToggleButton class.

        @param inactive_normal_dpixbuf: DynamicPixbuf for inactive normal status.
        @param active_normal_dpixbuf: DynamicPixbuf for active normal status.
        @param inactive_hover_dpixbuf: DynamicPixbuf for inactive hover status, default is None.
        @param active_hover_dpixbuf: DynamicPixbuf for active hover status, default is None.
        @param inactive_press_dpixbuf: DynamicPixbuf for inactive press status, default is None.
        @param active_press_dpixbuf: DynamicPixbuf for active press status, default is None.
        @param inactive_disable_dpixbuf: DynamicPixbuf for inactive disable status, default is None.
        @param active_disable_dpixbuf: DynamicPixbuf for active disable status, default is None.
        @param button_label: Button label, default is None.
        @param padding_x: Padding x, default is 0.
        @param font_size: Font size, default is DEFAULT_FONT_SIZE.
        '''
        gtk.ToggleButton.__init__(self)
        self.font_size = font_size
        label_dcolor = ui_theme.get_color("button_default_font")
        self.button_press_flag = False

        self.inactive_pixbuf_group = (inactive_normal_dpixbuf,
                                      inactive_hover_dpixbuf,
                                      inactive_press_dpixbuf,
                                      inactive_disable_dpixbuf)

        self.active_pixbuf_group = (active_normal_dpixbuf,
                                    active_hover_dpixbuf,
                                    active_press_dpixbuf,
                                    active_disable_dpixbuf)

        # Init request size.
        label_width = 0
        button_width = inactive_normal_dpixbuf.get_pixbuf().get_width()
        button_height = inactive_normal_dpixbuf.get_pixbuf().get_height()
        if button_label:
            label_width = get_content_size(button_label, self.font_size)[0]
        self.set_size_request(button_width + label_width + padding_x * 2,
                              button_height)

        self.connect("button-press-event", self.press_toggle_button)
        self.connect("button-release-event", self.release_toggle_button)

        # Expose button.
        self.connect("expose-event", lambda w, e : self.expose_toggle_button(
                w, e,
                button_label, padding_x, self.font_size, label_dcolor))

    def press_toggle_button(self, widget, event):
        '''
        Callback for `button-press-event` signal.

        @param widget: ToggleButton widget.
        @param event: Button press event.
        '''
        self.button_press_flag = True
        self.queue_draw()

    def release_toggle_button(self, widget, event):
        '''
        Callback for `button-press-release` signal.

        @param widget: ToggleButton widget.
        @param event: Button release event.
        '''
        self.button_press_flag = False
        self.queue_draw()

    def expose_toggle_button(self, widget, event,
                             button_label, padding_x, font_size, label_dcolor):
        '''
        Callback for `expose-event` signal.

        @param widget: ToggleButton widget.
        @param event: Expose event.
        @param button_label: Button label string.
        @param padding_x: horticultural padding value.
        @param font_size: Font size.
        @param label_dcolor: Label DynamicColor.
        '''
        # Init.
        inactive_normal_dpixbuf, inactive_hover_dpixbuf, inactive_press_dpixbuf, inactive_disable_dpixbuf = self.inactive_pixbuf_group
        active_normal_dpixbuf, active_hover_dpixbuf, active_press_dpixbuf, active_disable_dpixbuf = self.active_pixbuf_group
        rect = widget.allocation
        image = inactive_normal_dpixbuf.get_pixbuf()

        # Get pixbuf along with button's sate.
        if widget.state == gtk.STATE_INSENSITIVE:
            if widget.get_active():
                image = active_disable_dpixbuf.get_pixbuf()
            else:
                image = inactive_disable_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_NORMAL:
            image = inactive_normal_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            if not inactive_hover_dpixbuf and not active_hover_dpixbuf:
                if widget.get_active():
                    image = active_normal_dpixbuf.get_pixbuf()
                else:
                    image = inactive_normal_dpixbuf.get_pixbuf()
            else:
                if inactive_hover_dpixbuf and active_hover_dpixbuf:
                    if widget.get_active():
                        image = active_hover_dpixbuf.get_pixbuf()
                    else:
                        image = inactive_hover_dpixbuf.get_pixbuf()
                elif inactive_hover_dpixbuf:
                    image = inactive_hover_dpixbuf.get_pixbuf()
                elif active_hover_dpixbuf:
                    image = active_hover_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            if inactive_press_dpixbuf and active_press_dpixbuf:
                if self.button_press_flag:
                    if widget.get_active():
                        image = active_press_dpixbuf.get_pixbuf()
                    else:
                        image = inactive_press_dpixbuf.get_pixbuf()
                else:
                    image = active_normal_dpixbuf.get_pixbuf()
            else:
                image = active_normal_dpixbuf.get_pixbuf()

        # Draw button.
        cr = widget.window.cairo_create()
        draw_pixbuf(cr, image, rect.x + padding_x, rect.y)

        # Draw font.
        if widget.state == gtk.STATE_INSENSITIVE:
            label_color = ui_theme.get_color("disable_text").get_color()
        else:
            label_color = label_dcolor.get_color()
        if button_label:
            draw_text(cr, button_label,
                        rect.x + image.get_width() + padding_x * 2,
                        rect.y,
                        rect.width - image.get_width() - padding_x * 2,
                        rect.height,
                        font_size,
                        label_color,
                        alignment=pango.ALIGN_LEFT
                        )

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

    def set_inactive_pixbuf_group(self, new_group):
        '''
        Set inactive pixbuf group.

        @param new_group: Inactive pixbuf group.
        '''
        self.inactive_pixbuf_group = new_group

    def set_active_pixbuf_group(self, new_group):
        '''
        Set inactive pixbuf group.

        @param new_group: Active pixbuf group.
        '''
        self.active_pixbuf_group = new_group

class ActionButton(gtk.Button):
    '''
    ActionButton class.

    @undocumented: expose_action_button
    '''

    def __init__(self, actions, index=0):
        '''
        Initialize for ActionButton class.

        @param actions: Actions for button.
        @param index: Action index, default is 0.
        '''
        gtk.Button.__init__(self)
        self.actions = actions
        self.index = index

        pixbuf = self.actions[self.index][0][0].get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())

        self.connect("expose-event", self.expose_action_button)
        self.connect("clicked", lambda w: self.update_action_index(w))

    def update_action_index(self, widget):
        '''
        Update action index of ActionButton.

        @param widget: ActionButton widget.
        '''
        # Call click callback.
        self.actions[self.index][1](widget)

        # Update index.
        self.index += 1
        if self.index >= len(self.actions):
            self.index = 0

        # Redraw.
        self.queue_draw()

    def expose_action_button(self, widget, event):
        '''
        Callback for `expose-event` signal.

        @param widget: ActionButton widget.
        @param event: Expose event.
        @return: Always return True.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        if widget.state == gtk.STATE_NORMAL:
            pixbuf = self.actions[self.index][0][0].get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            pixbuf = self.actions[self.index][0][1].get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            pixbuf = self.actions[self.index][0][2].get_pixbuf()

        draw_pixbuf(cr, pixbuf, rect.x, rect.y)

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

gobject.type_register(ActionButton)

class CheckButton(ToggleButton):
    '''
    CheckButton class.
    '''

    def __init__(self,
                 label_text=None,
                 padding_x=2,
                 font_size=DEFAULT_FONT_SIZE):
        '''
        Initialize CheckButton class.

        @param label_text: Label text.
        @param padding_x: Horticultural padding value, default is 8.
        @param font_size: Font size, default is DEFAULT_FONT_SIZE.
        '''
        ToggleButton.__init__(
            self,
            ui_theme.get_pixbuf("button/check_button_inactive_normal.png"),
            ui_theme.get_pixbuf("button/check_button_active_normal.png"),
            ui_theme.get_pixbuf("button/check_button_inactive_hover.png"),
            ui_theme.get_pixbuf("button/check_button_active_hover.png"),
            ui_theme.get_pixbuf("button/check_button_inactive_press.png"),
            ui_theme.get_pixbuf("button/check_button_active_press.png"),
            ui_theme.get_pixbuf("button/check_button_inactive_disable.png"),
            ui_theme.get_pixbuf("button/check_button_active_disable.png"),
            label_text, padding_x, font_size
            )

gobject.type_register(CheckButton)

class CheckAllButton(gtk.ToggleButton):
    '''
    CheckAllButton class.

    @undocumented: handle_click_event
    @undocumented: press_toggle_button
    @undocumented: release_toggle_button
    @undocumented: expose_toggle_button
    '''

    __gsignals__ = {
        "active-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self,
                 inactive_normal_dpixbuf=ui_theme.get_pixbuf("button/check_button_inactive_normal.png"),
                 active_normal_dpixbuf=ui_theme.get_pixbuf("button/check_button_active_normal.png"),
                 inactive_hover_dpixbuf=ui_theme.get_pixbuf("button/check_button_inactive_hover.png"),
                 active_hover_dpixbuf=ui_theme.get_pixbuf("button/check_button_active_hover.png"),
                 inactive_press_dpixbuf=ui_theme.get_pixbuf("button/check_button_inactive_press.png"),
                 active_press_dpixbuf=ui_theme.get_pixbuf("button/check_button_active_press.png"),
                 inactive_disable_dpixbuf=ui_theme.get_pixbuf("button/check_button_inactive_disable.png"),
                 active_disable_dpixbuf=ui_theme.get_pixbuf("button/check_button_active_disable.png"),
                 middle_disable_dpixbuf=ui_theme.get_pixbuf("button/check_button_middle_disable.png"),
                 middle_hover_dpixbuf=ui_theme.get_pixbuf("button/check_button_middle_hover.png"),
                 middle_normal_dpixbuf=ui_theme.get_pixbuf("button/check_button_middle_normal.png"),
                 middle_press_dpixbuf=ui_theme.get_pixbuf("button/check_button_middle_press.png"),
                 button_label=None,
                 padding_x=8,
                 font_size=DEFAULT_FONT_SIZE,
                 ):
        '''
        Initialize for CheckAllButton class.

        @param inactive_normal_dpixbuf: DyanmicPixbuf for button inactive normal status, default is None.
        @param active_normal_dpixbuf: DyanmicPixbuf for button active normal status, default is None.
        @param inactive_hover_dpixbuf: DyanmicPixbuf for button inactive hover status, default is None.
        @param active_hover_dpixbuf: DyanmicPixbuf for button active hover status, default is None.
        @param inactive_press_dpixbuf: DyanmicPixbuf for button inactive press status, default is None.
        @param active_press_dpixbuf: DyanmicPixbuf for button active press status, default is None.
        @param inactive_disable_dpixbuf: DyanmicPixbuf for button inactive disable status, default is None.
        @param active_disable_dpixbuf: DyanmicPixbuf for button active disable status, default is None.
        @param middle_disable_dpixbuf: DyanmicPixbuf for button middle disable status, default is None.
        @param middle_hover_dpixbuf: DyanmicPixbuf for button middle hover status, default is None.
        @param middle_normal_dpixbuf: DyanmicPixbuf for button middle normal status, default is None.
        @param middle_press_dpixbuf: DyanmicPixbuf for button middle press status, default is None.
        @param button_label: Button label, default is None.
        @param padding_x: Padding x, default is 0.
        @param font_size: Button label font size, default is DEFAULT_FONT_SIZE.
        '''
        gtk.ToggleButton.__init__(self)
        self.font_size = font_size
        label_dcolor = ui_theme.get_color("button_default_font")
        self.button_press_flag = False

        self.inactive_pixbuf_group = (inactive_normal_dpixbuf,
                                      inactive_hover_dpixbuf,
                                      inactive_press_dpixbuf,
                                      inactive_disable_dpixbuf)

        self.active_pixbuf_group = (active_normal_dpixbuf,
                                    active_hover_dpixbuf,
                                    active_press_dpixbuf,
                                    active_disable_dpixbuf)

        self.middle_pixbuf_group = (middle_normal_dpixbuf,
                                    middle_hover_dpixbuf,
                                    middle_press_dpixbuf,
                                    middle_disable_dpixbuf,
                                    )

        self.in_half_status = False

        # Init request size.
        label_width = 0
        button_width = inactive_normal_dpixbuf.get_pixbuf().get_width()
        button_height = inactive_normal_dpixbuf.get_pixbuf().get_height()
        if button_label:
            label_width = get_content_size(button_label, self.font_size)[0]
        self.set_size_request(button_width + label_width + padding_x * 2,
                              button_height)

        self.connect("button-press-event", self.press_toggle_button)
        self.connect("button-release-event", self.release_toggle_button)

        # Expose button.
        self.connect("expose-event", lambda w, e : self.expose_toggle_button(
                w, e,
                button_label, padding_x, self.font_size, label_dcolor))

        self.connect("clicked", self.handle_click_event)

    def update_status(self, actives):
        '''
        Update status of button.

        @param actives: This is boolean list that include all button's active status, CheckAllButton will change status in INACTIVE/ACTIVE/HALF-ACTIVE.
        '''
        if actives.count(True) == len(actives):
            self.set_half_status(False)
            self.set_active(True)
        elif actives.count(False) == len(actives):
            self.set_half_status(False)
            self.set_active(False)
        else:
            self.set_active(True)
            self.set_half_status(True)

        self.queue_draw()

    def set_half_status(self, half_status):
        '''
        Set half active status.
        '''
        self.in_half_status = half_status

    def handle_click_event(self, widget):
        '''
        Internal callback for `click` signal.

        @param widget: The CheckAllButton widget.
        '''
        if self.in_half_status:
            self.set_active(False)
            self.in_half_status = False

        self.emit("active-changed", self.get_active())

    def press_toggle_button(self, widget, event):
        '''
        Callback for `button-press-event` signal.

        @param widget: ToggleButton widget.
        @param event: Button press event.
        '''
        self.button_press_flag = True
        self.queue_draw()

    def release_toggle_button(self, widget, event):
        '''
        Callback for `button-press-release` signal.

        @param widget: ToggleButton widget.
        @param event: Button release event.
        '''
        self.button_press_flag = False
        self.queue_draw()

    def expose_toggle_button(self, widget, event,
                             button_label, padding_x, font_size, label_dcolor):
        '''
        Callback for `expose-event` signal.

        @param widget: ToggleButton widget.
        @param event: Expose event.
        @param button_label: Button label string.
        @param padding_x: horticultural padding value.
        @param font_size: Font size.
        @param label_dcolor: Label DynamicColor.
        '''
        # Init.
        inactive_normal_dpixbuf, inactive_hover_dpixbuf, inactive_press_dpixbuf, inactive_disable_dpixbuf = self.inactive_pixbuf_group
        active_normal_dpixbuf, active_hover_dpixbuf, active_press_dpixbuf, active_disable_dpixbuf = self.active_pixbuf_group
        middle_normal_dpixbuf, middle_hover_dpixbuf, middle_press_dpixbuf, middle_disable_dpixbuf = self.middle_pixbuf_group
        rect = widget.allocation
        image = inactive_normal_dpixbuf.get_pixbuf()

        # Get pixbuf along with button's sate.
        if widget.state == gtk.STATE_INSENSITIVE:
            if self.in_half_status:
                image = middle_disable_dpixbuf.get_pixbuf()
            else:
                if widget.get_active():
                    image = active_disable_dpixbuf.get_pixbuf()
                else:
                    image = inactive_disable_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_NORMAL:
            image = inactive_normal_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            if not inactive_hover_dpixbuf and not active_hover_dpixbuf:
                if self.in_half_status:
                    image = middle_normal_dpixbuf.get_pixbuf()
                else:
                    if widget.get_active():
                        image = active_normal_dpixbuf.get_pixbuf()
                    else:
                        image = inactive_normal_dpixbuf.get_pixbuf()
            else:
                if inactive_hover_dpixbuf and active_hover_dpixbuf:
                    if self.in_half_status:
                        image = middle_normal_dpixbuf.get_pixbuf()
                    else:
                        if widget.get_active():
                            image = active_hover_dpixbuf.get_pixbuf()
                        else:
                            image = inactive_hover_dpixbuf.get_pixbuf()
                elif inactive_hover_dpixbuf:
                    image = inactive_hover_dpixbuf.get_pixbuf()
                elif active_hover_dpixbuf:
                    if self.in_half_status:
                        image = middle_hover_dpixbuf.get_pixbuf()
                    else:
                        image = active_hover_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            if inactive_press_dpixbuf and active_press_dpixbuf:
                if self.button_press_flag:
                    if self.in_half_status:
                        image = middle_normal_dpixbuf.get_pixbuf()
                    else:
                        if widget.get_active():
                            image = active_press_dpixbuf.get_pixbuf()
                        else:
                            image = inactive_press_dpixbuf.get_pixbuf()
                else:
                    if self.in_half_status:
                        image = middle_normal_dpixbuf.get_pixbuf()
                    else:
                        image = active_normal_dpixbuf.get_pixbuf()
            else:
                if self.in_half_status:
                    image = middle_normal_dpixbuf.get_pixbuf()
                else:
                    image = active_normal_dpixbuf.get_pixbuf()

        # Draw button.
        cr = widget.window.cairo_create()
        draw_pixbuf(cr, image, rect.x + padding_x, rect.y)

        # Draw font.
        if widget.state == gtk.STATE_INSENSITIVE:
            label_color = ui_theme.get_color("disable_text").get_color()
        else:
            label_color = label_dcolor.get_color()
        if button_label:
            draw_text(cr, button_label,
                        rect.x + image.get_width() + padding_x * 2,
                        rect.y,
                        rect.width - image.get_width() - padding_x * 2,
                        rect.height,
                        font_size,
                        label_color,
                        alignment=pango.ALIGN_LEFT
                        )

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

gobject.type_register(CheckAllButton)

class CheckButtonBuffer(gobject.GObject):
    '''
    CheckButtonBuffer class.

    Use to render CheckButton in TreeView widget.

    @undocumented: render
    '''

    STATE_NORMAL = 1
    STATE_PRELIGHT = 2
    STATE_ACTIVE = 3

    def __init__(self,
                 active=False,
                 render_padding_x=0,
                 render_padding_y=0,
                 ):
        '''
        Initialize CheckButtonBuffer class.

        @param active: Set True to active buffer status, default is False.
        @param render_padding_x: Horizontal padding value, default is 0.
        @param render_padding_y: Vertical padding value, default is 0.
        '''
        gobject.GObject.__init__(self)
        self.inactive_normal_dpixbuf = ui_theme.get_pixbuf("button/check_button_inactive_normal.png")
        self.active_normal_dpixbuf = ui_theme.get_pixbuf("button/check_button_active_normal.png")
        self.inactive_hover_dpixbuf = ui_theme.get_pixbuf("button/check_button_inactive_hover.png")
        self.active_hover_dpixbuf = ui_theme.get_pixbuf("button/check_button_active_hover.png")
        self.inactive_press_dpixbuf = ui_theme.get_pixbuf("button/check_button_inactive_press.png")
        self.active_press_dpixbuf = ui_theme.get_pixbuf("button/check_button_active_press.png")

        self.render_padding_x = render_padding_x
        self.render_padding_y = render_padding_y
        pixbuf = self.inactive_normal_dpixbuf.get_pixbuf()
        self.render_width = pixbuf.get_width()
        self.render_height = pixbuf.get_height()

        self.active = active
        self.button_state = self.STATE_NORMAL

    def get_active(self):
        '''
        Get active status of check button buffer.

        @return: Return True if buffer is in active status.
        '''
        return self.active

    def is_in_button_area(self, x, y):
        '''
        Helper function to detect button event is in button area.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        return is_in_rect((x, y), (self.render_padding_x, self.render_padding_y, self.render_width, self.render_height))

    def press_button(self, x, y):
        '''
        Helper function to handle button-press-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = True

            self.active = not self.active

            return True
        else:
            return False

    def release_button(self, x, y):
        '''
        Helper function to handle button-release-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = False

            return True
        else:
            return False

    def motion_button(self, x, y):
        '''
        Helper function to handle motion-notify event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            if self.button_state != self.STATE_PRELIGHT:
                self.button_state = self.STATE_PRELIGHT

                return True
            else:
                return False
        else:
            if self.button_state != self.STATE_NORMAL:
                self.button_state = self.STATE_NORMAL

                return True
            else:
                return False

    def render(self, cr, rect):
        # Get pixbuf along with button's sate.
        if self.button_state == self.STATE_NORMAL:
            if self.active:
                image = self.active_normal_dpixbuf.get_pixbuf()
            else:
                image = self.inactive_normal_dpixbuf.get_pixbuf()
        elif self.button_state == self.STATE_PRELIGHT:
            if self.active:
                image = self.active_hover_dpixbuf.get_pixbuf()
            else:
                image = self.inactive_hover_dpixbuf.get_pixbuf()
        elif self.button_state == self.STATE_ACTIVE:
            if self.button_press_flag:
                if self.active:
                    image = self.inactive_press_dpixbuf.get_pixbuf()
                else:
                    image = self.active_press_dpixbuf.get_pixbuf()
            else:
                if self.active:
                    image = self.active_normal_dpixbuf.get_pixbuf()
                else:
                    image = self.inactive_normal_dpixbuf.get_pixbuf()

        # Draw button.
        draw_pixbuf(
            cr,
            image,
            rect.x + self.render_padding_x,
            rect.y + self.render_padding_y)

gobject.type_register(CheckButtonBuffer)

class RadioButton(ToggleButton):
    '''
    RadioButton class.

    @undocumented: click_radio_button
    '''

    def __init__(self,
                 label_text=None,
                 padding_x=2,
                 font_size=DEFAULT_FONT_SIZE,
                 ):
        '''
        Initialize RadioButton class.

        @param label_text: Label text.
        @param padding_x: Horticultural padding value, default is 8.
        @param font_size: Font size, default is DEFAULT_FONT_SIZE.
        '''
        ToggleButton.__init__(
            self,
            ui_theme.get_pixbuf("button/radio_button_inactive_normal.png"),
            ui_theme.get_pixbuf("button/radio_button_active_normal.png"),
            ui_theme.get_pixbuf("button/radio_button_inactive_hover.png"),
            ui_theme.get_pixbuf("button/radio_button_active_hover.png"),
            ui_theme.get_pixbuf("button/radio_button_inactive_press.png"),
            ui_theme.get_pixbuf("button/radio_button_active_press.png"),
            ui_theme.get_pixbuf("button/radio_button_inactive_disable.png"),
            ui_theme.get_pixbuf("button/radio_button_active_disable.png"),
            label_text,
            padding_x,
            font_size
            )

        self.switch_lock = False
        self.connect("clicked", self.click_radio_button)

    def click_radio_button(self, widget):
        '''
        Callback for `clicked` signal.

        @param widget: RadioButton widget.
        '''
        if not self.switch_lock:
            for w in get_same_level_widgets(self):
                w.switch_lock = True
                w.set_active(w == self)
                w.switch_lock = False

gobject.type_register(RadioButton)

class RadioButtonBuffer(gobject.GObject):
    '''
    RaidoButtonBuffer class.

    Use to render RaidoButton in TreeView widget.

    @undocumented: render
    '''

    STATE_NORMAL = 1
    STATE_PRELIGHT = 2
    STATE_ACTIVE = 3

    def __init__(self,
                 active=False,
                 render_padding_x=0,
                 render_padding_y=0,
                 ):
        '''
        Initialize RadioButtonBuffer class.

        @param active: Set True to active buffer status, default is False.
        @param render_padding_x: Horizontal padding value, default is 0.
        @param render_padding_y: Vertical padding value, default is 0.
        '''
        gobject.GObject.__init__(self)
        self.inactive_normal_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_normal.png")
        self.active_normal_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_normal.png")
        self.inactive_hover_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_hover.png")
        self.active_hover_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_hover.png")
        self.inactive_press_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_press.png")
        self.active_press_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_press.png")

        self.render_padding_x = render_padding_x
        self.render_padding_y = render_padding_y
        pixbuf = self.inactive_normal_dpixbuf.get_pixbuf()
        self.render_width = pixbuf.get_width()
        self.render_height = pixbuf.get_height()

        self.active = active
        self.button_state = self.STATE_NORMAL

    def get_active(self):
        '''
        Get active status of raido button buffer.

        @return: Return True if buffer is in active status.
        '''
        return self.active

    def set_active(self):
        self.button_state = self.STATE_ACTIVE
        self.button_press_flag = False
        self.active = True
        #self.queue_draw()

    def is_in_button_area(self, x, y):
        '''
        Helper function to detect button event is in button area.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        return is_in_rect((x, y), (self.render_padding_x, self.render_padding_y, self.render_width, self.render_height))

    def press_button(self, x, y):
        '''
        Helper function to handle button-press-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y) and self.active == False:
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = True

            self.active = True

            return True
        else:
            return False

    def release_button(self, x, y):
        '''
        Helper function to handle button-release-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = False

            return True
        else:
            return False

    def motion_button(self, x, y):
        '''
        Helper function to handle motion-notify event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            if self.button_state != self.STATE_PRELIGHT:
                self.button_state = self.STATE_PRELIGHT

                return True
            else:
                return False
        else:
            if self.button_state != self.STATE_NORMAL:
                self.button_state = self.STATE_NORMAL

                return True
            else:
                return False

    def render(self, cr, rect):
        # Get pixbuf along with button's sate.
        if self.button_state == self.STATE_NORMAL:
            if self.active:
                image = self.active_normal_dpixbuf.get_pixbuf()
            else:
                image = self.inactive_normal_dpixbuf.get_pixbuf()
        elif self.button_state == self.STATE_PRELIGHT:
            if self.active:
                image = self.active_hover_dpixbuf.get_pixbuf()
            else:
                image = self.inactive_hover_dpixbuf.get_pixbuf()
        elif self.button_state == self.STATE_ACTIVE:
            if self.button_press_flag:
                if self.active:
                    image = self.inactive_press_dpixbuf.get_pixbuf()
                else:
                    image = self.active_press_dpixbuf.get_pixbuf()
            else:
                if self.active:
                    image = self.active_normal_dpixbuf.get_pixbuf()
                else:
                    image = self.inactive_normal_dpixbuf.get_pixbuf()

        # Draw button.
        draw_pixbuf(
            cr,
            image,
            rect.x + self.render_padding_x,
            rect.y + self.render_padding_y)

gobject.type_register(RadioButtonBuffer)

class DisableButton(gtk.Button):
    '''
    DisableButton class.

    @undocumented: expose_disable_button
    '''

    def __init__(self, dpixbufs):
        '''
        Initialize DisableButton class.

        @param dpixbufs: DyanmicPixbuf.
        '''
        gtk.Button.__init__(self)
        pixbuf = dpixbufs[0].get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())

        widget_fix_cycle_destroy_bug(self)
        self.connect("expose-event", lambda w, e: self.expose_disable_button(w, e, dpixbufs))

    def expose_disable_button(self, widget, event, dpixbufs):
        '''
        Callback for `expose-event` signal.

        @param widget: DisableButton widget.
        @param event: Expose event.
        @param dpixbufs: DynamicPixbufs.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        (normal_dpixbuf, hover_dpixbuf, press_dpixbuf, disable_dpixbuf) = dpixbufs

        # Draw.
        if widget.state == gtk.STATE_INSENSITIVE:
            pixbuf = disable_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_NORMAL:
            pixbuf = normal_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            pixbuf = hover_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            pixbuf = press_dpixbuf.get_pixbuf()

        draw_pixbuf(cr, pixbuf, rect.x, rect.y)

        # Propagate expose to children.
        propagate_expose(widget, event)

        return True

gobject.type_register(DisableButton)

class LinkButton(Label):
    '''
    LinkButton click to open browser.
    '''

    def __init__(self,
                 text,
                 link,
                 enable_gaussian=True,
                 text_color=ui_theme.get_color("link_text"),
                 ):
        '''
        Initialize LinkButton class.

        @param text: Link content.
        @param link: Link address.
        @param enable_gaussian: To enable gaussian effect on link, default is True.
        @param text_color: Link color, just use when option enable_gaussian is False.
        '''
        Label.__init__(self, text, text_color, enable_gaussian=enable_gaussian, text_size=9,
                       gaussian_radious=1, border_radious=0)

        self.connect("button-press-event", lambda w, e: run_command("xdg-open %s" % link))

        set_clickable_cursor(self)

gobject.type_register(LinkButton)

class ComboButton(gtk.Button):
    '''
    ComboButton class.

    @undocumented: expose_combo_button
    @undocumented: button_press_combo_button
    @undocumented: click_combo_button
    '''

    __gsignals__ = {
        "button-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "arrow-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int, int, int, int)),
    }

    def __init__(self,
                 button_normal_dpixbuf,
                 button_hover_dpixbuf,
                 button_press_dpixbuf,
                 button_disable_dpixbuf,
                 arrow_normal_dpixbuf,
                 arrow_hover_dpixbuf,
                 arrow_press_dpixbuf,
                 arrow_disable_dpixbuf,
                 ):
        '''
        Initialize ComboButton class.

        @param button_normal_dpixbuf: DyanmicPixbuf of button normal status.
        @param button_hover_dpixbuf: DyanmicPixbuf of button hover status.
        @param button_press_dpixbuf: DyanmicPixbuf of button press status.
        @param button_disable_dpixbuf: DyanmicPixbuf of button disable status.
        @param arrow_normal_dpixbuf: DyanmicPixbuf of arrow normal status.
        @param arrow_hover_dpixbuf: DyanmicPixbuf of arrow hover status.
        @param arrow_press_dpixbuf: DyanmicPixbuf of arrow press status.
        @param arrow_disable_dpixbuf: DyanmicPixbuf of arrow disable status.
        '''
        # Init.
        gtk.Button.__init__(self)
        self.button_normal_dpixbuf = button_normal_dpixbuf
        self.button_hover_dpixbuf = button_hover_dpixbuf
        self.button_press_dpixbuf = button_press_dpixbuf
        self.button_disable_dpixbuf = button_disable_dpixbuf
        self.arrow_normal_dpixbuf = arrow_normal_dpixbuf
        self.arrow_hover_dpixbuf = arrow_hover_dpixbuf
        self.arrow_press_dpixbuf = arrow_press_dpixbuf
        self.arrow_disable_dpixbuf = arrow_disable_dpixbuf
        button_pixbuf = button_normal_dpixbuf.get_pixbuf()
        arrow_pixbuf = arrow_normal_dpixbuf.get_pixbuf()
        self.button_width = button_pixbuf.get_width()
        self.arrow_width = arrow_pixbuf.get_width()
        self.height = button_pixbuf.get_height()
        self.set_size_request(self.button_width + self.arrow_width, self.height)
        self.in_button = True

        self.connect("expose-event", self.expose_combo_button)
        self.connect("button-press-event", self.button_press_combo_button)
        self.connect("clicked", self.click_combo_button)

    def expose_combo_button(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Get pixbuf info.
        if widget.state == gtk.STATE_NORMAL:
            button_pixbuf = self.button_normal_dpixbuf.get_pixbuf()
            arrow_pixbuf = self.arrow_normal_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            button_pixbuf = self.button_hover_dpixbuf.get_pixbuf()
            arrow_pixbuf = self.arrow_hover_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            if self.in_button:
                button_pixbuf = self.button_press_dpixbuf.get_pixbuf()
                arrow_pixbuf = self.arrow_hover_dpixbuf.get_pixbuf()
            else:
                button_pixbuf = self.button_hover_dpixbuf.get_pixbuf()
                arrow_pixbuf = self.arrow_press_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_INSENSITIVE:
            button_pixbuf = self.button_disable_dpixbuf.get_pixbuf()
            arrow_pixbuf = self.arrow_disable_dpixbuf.get_pixbuf()

        # Draw.
        draw_pixbuf(cr, button_pixbuf, rect.x, rect.y)
        draw_pixbuf(cr, arrow_pixbuf, rect.x + self.button_width, rect.y)

        return True

    def button_press_combo_button(self, widget, event):
        self.in_button = event.x < self.button_width

    def click_combo_button(self, widget):
        if self.in_button:
            self.emit("button-clicked")
        else:
            (button_x, button_y) = get_widget_root_coordinate(self, WIDGET_POS_BOTTOM_LEFT)
            self.emit("arrow-clicked",
                      button_x + self.button_width,
                      button_y,
                      self.arrow_width,
                      self.height)

gobject.type_register(ComboButton)

class SwitchButton(ToggleButton):
    '''
    SwitchButton class.
    '''

    def __init__(self, active=False, inactive_disable_dpixbuf=None, active_disable_dpixbuf=None):
        '''
        Initialize SwitchButton class.

        @param active: Button active status, default is False.
        '''
        if inactive_disable_dpixbuf and active_disable_dpixbuf:
            ToggleButton.__init__(self,
                                  ui_theme.get_pixbuf("switchbutton/off.png"),
                                  ui_theme.get_pixbuf("switchbutton/on.png"),
                                  inactive_disable_dpixbuf = inactive_disable_dpixbuf,
                                  active_disable_dpixbuf = active_disable_dpixbuf)
        else:
            ToggleButton.__init__(self,
                                  ui_theme.get_pixbuf("switchbutton/off.png"),
                                  ui_theme.get_pixbuf("switchbutton/on.png"))
        self.set_active(active)

gobject.type_register(SwitchButton)
