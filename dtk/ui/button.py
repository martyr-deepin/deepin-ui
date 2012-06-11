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

from utils import get_content_size, color_hex_to_cairo, propagate_expose, window_is_max, get_same_level_widgets
from theme import ui_theme
from draw import draw_vlinear, draw_pixbuf, draw_line, draw_font
from constant import DEFAULT_FONT_SIZE, ALIGN_START
import gtk
import gobject

class Button(gtk.Button):
    '''Button.'''
	
    def __init__(self, label, font_size=DEFAULT_FONT_SIZE):
        '''Init button.'''
        gtk.Button.__init__(self)
        self.font_size = font_size
        self.min_width = 69
        self.min_height = 22
        self.padding_x = 15
        self.padding_y = 3
        self.clickable = True
        
        self.set_label(label)
        
        self.connect("expose-event", self.expose_button)
        
    def set_label(self, label, font_size=DEFAULT_FONT_SIZE):
        '''Set label.'''
        self.label = label
        (self.label_width, self.label_height) = get_content_size(label, self.font_size)
        self.set_size_request(max(self.label_width + self.padding_x * 2, self.min_width),
                              max(self.label_height + self.padding_y * 2, self.min_height))
        
        self.queue_draw()
        
    def set_clickable(self, clickable):
        '''Set clickable.'''
        self.clickable = clickable
        
        self.queue_draw()
        
    def expose_button(self, widget, event):
        '''Expose button.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Get color info.
        if not self.clickable:
            border_color = ui_theme.get_color("buttonBorderDisable").get_color()
            background_color = ui_theme.get_shadow_color("buttonBackgroundDisable").get_color_info()
            button_color = ui_theme.get_color("buttonDisableFont").get_color()
        else:
            button_color = ui_theme.get_color("buttonFont").get_color()
            
            if widget.state == gtk.STATE_NORMAL:
                border_color = ui_theme.get_color("buttonBorderNormal").get_color()
                background_color = ui_theme.get_shadow_color("buttonBackgroundNormal").get_color_info()
            elif widget.state == gtk.STATE_PRELIGHT:
                border_color = ui_theme.get_color("buttonBorderPrelight").get_color()
                background_color = ui_theme.get_shadow_color("buttonBackgroundPrelight").get_color_info()
            elif widget.state == gtk.STATE_ACTIVE:
                border_color = ui_theme.get_color("buttonBorderActive").get_color()
                background_color = ui_theme.get_shadow_color("buttonBackgroundActive").get_color_info()
            
        # Draw background.
        draw_vlinear(
            cr,
            x + 1, y + 1, w - 2, h - 2,
            background_color)
        
        # Draw border.
        cr.set_source_rgb(*color_hex_to_cairo(border_color))
        draw_line(cr, x + 2, y + 1, x + w - 1, y + 1) # top
        draw_line(cr, x + 2, y + h, x + w - 1, y + h) # bottom
        draw_line(cr, x + 1, y + 2, x + 1, y + h - 1) # left
        draw_line(cr, x + w, y + 2, x + w, y + h - 1) # right
        
        # Draw four point.
        top_left_point = ui_theme.get_pixbuf("button.png").get_pixbuf()
        top_right_point = top_left_point.rotate_simple(270)
        bottom_right_point = top_left_point.rotate_simple(180)
        bottom_left_point = top_left_point.rotate_simple(90)
        
        draw_pixbuf(cr, top_left_point, x, y)
        draw_pixbuf(cr, top_right_point, x + w - top_left_point.get_width(), y)
        draw_pixbuf(cr, bottom_left_point, x, y + h - top_left_point.get_height())
        draw_pixbuf(cr, bottom_right_point, x + w - top_left_point.get_width(), y + h - top_left_point.get_height())
        
        # Draw font.
        draw_font(cr, self.label, self.font_size, button_color, x, y, w, h)
        
        return True
        
gobject.type_register(Button)

class ImageButton(gtk.Button):
    '''Image button.'''
	
    def __init__(self, normal_dpixbuf, hover_dpixbuf, press_dpixbuf, scale_x=False, content=None):
        '''Init font button.'''
        gtk.Button.__init__(self)
        draw_button(self, normal_dpixbuf, hover_dpixbuf, press_dpixbuf, scale_x, content)
        
gobject.type_register(ImageButton)

class ThemeButton(gtk.Button):
    '''Theme button.'''
	
    def __init__(self):
        '''Init theme button.'''
        gtk.Button.__init__(self)
        draw_button(
            self, 
            ui_theme.get_pixbuf("button/window_theme_normal.png"),
            ui_theme.get_pixbuf("button/window_theme_hover.png"),
            ui_theme.get_pixbuf("button/window_theme_press.png"))
        
gobject.type_register(ThemeButton)

class MenuButton(gtk.Button):
    '''Menu button.'''
	
    def __init__(self):
        '''Init menu button.'''
        gtk.Button.__init__(self)
        draw_button(
            self, 
            ui_theme.get_pixbuf("button/window_menu_normal.png"),
            ui_theme.get_pixbuf("button/window_menu_hover.png"),
            ui_theme.get_pixbuf("button/window_menu_press.png"))
        
gobject.type_register(MenuButton)

class MinButton(gtk.Button):
    '''Min button.'''
	
    def __init__(self):
        '''Init min button.'''
        gtk.Button.__init__(self)
        draw_button(
            self, 
            ui_theme.get_pixbuf("button/window_min_normal.png"),
            ui_theme.get_pixbuf("button/window_min_hover.png"),
            ui_theme.get_pixbuf("button/window_min_press.png"))
        
gobject.type_register(MinButton)

class CloseButton(gtk.Button):
    '''Close button.'''
	
    def __init__(self):
        '''Init close button.'''
        gtk.Button.__init__(self)
        draw_button(
            self, 
            ui_theme.get_pixbuf("button/window_close_normal.png"),
            ui_theme.get_pixbuf("button/window_close_hover.png"),
            ui_theme.get_pixbuf("button/window_close_press.png"))
        
gobject.type_register(CloseButton)

class MaxButton(gtk.Button):
    '''Max button.'''
	
    def __init__(self,sub_dir="button", max_path_prefix="window_max", unmax_path_prefix="window_unmax"):
        '''Init max button.'''
        gtk.Button.__init__(self)
        draw_max_button(self, sub_dir, max_path_prefix, unmax_path_prefix)
        
gobject.type_register(MaxButton)

def draw_button(widget, normal_dpixbuf, hover_dpixbuf, press_dpixbuf,
                scale_x=False, button_label=None, font_size=DEFAULT_FONT_SIZE, 
                label_dcolor=ui_theme.get_color("buttonDefaultFont")):
    '''Create button.'''
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
            scale_x, False,
            normal_dpixbuf, hover_dpixbuf, press_dpixbuf,
            button_label, font_size, label_dcolor))
        
def expose_button(widget, event, 
                  scale_x, scaleY,
                  normal_dpixbuf, hover_dpixbuf, press_dpixbuf,
                  button_label, font_size, label_dcolor):
    '''Expose function to replace event box's image.'''
    # Init.
    rect = widget.allocation
    
    # Get pixbuf along with button's sate.
    if widget.state == gtk.STATE_NORMAL:
        image = normal_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_PRELIGHT:
        image = hover_dpixbuf.get_pixbuf()
    elif widget.state == gtk.STATE_ACTIVE:
        image = press_dpixbuf.get_pixbuf()
    
    # Init size.
    if scale_x:
        image_width = widget.allocation.width
    else:
        image_width = image.get_width()
        
    if scaleY:
        image_height = widget.allocation.height
    else:
        image_height = image.get_height()
    
    # Draw button.
    pixbuf = image
    if pixbuf.get_width() != image_width or pixbuf.get_height() != image_height:
        pixbuf = image.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)
    
    # Draw font.
    if button_label:
        draw_font(cr, button_label, font_size, 
                  label_dcolor.get_color(),
                  rect.x, rect.y, rect.width, rect.height)

    # Propagate expose to children.
    propagate_expose(widget, event)
    
    return True

def draw_max_button(widget, sub_dir, max_path_prefix, unmax_path_prefix):
    '''Create max button.'''
    # Init request size.
    pixbuf = ui_theme.get_pixbuf("%s/%s_normal.png" % (sub_dir, unmax_path_prefix)).get_pixbuf()
    widget.set_size_request(pixbuf.get_width(), pixbuf.get_height())
    
    # Redraw.
    widget.connect("expose-event", lambda w, e: 
                   expose_max_button(w, e, sub_dir, max_path_prefix, unmax_path_prefix))
                
def expose_max_button(widget, event, sub_dir, max_path_prefix, unmax_path_prefix):
    '''Expose function to replace event box's image.'''
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
        pixbuf = image.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)

    # Propagate expose to children.
    propagate_expose(widget, event)
    
    return True

class ToggleButton(gtk.ToggleButton):
    '''Image button.'''
	
    def __init__(self, 
                 inactive_normal_dpixbuf, active_normal_dpixbuf, 
                 inactive_hover_dpixbuf=None, active_hover_dpixbuf=None, 
                 inactive_press_dpixbuf=None, active_press_dpixbuf=None,
                 button_label=None, padding_x=0):
        '''Init font button.'''
        gtk.ToggleButton.__init__(self)
        font_size = DEFAULT_FONT_SIZE
        label_dcolor = ui_theme.get_color("buttonDefaultFont")
        self.button_press_flag = False
        
        self.inactive_pixbuf_group = (inactive_normal_dpixbuf,
                                      inactive_hover_dpixbuf,
                                      inactive_press_dpixbuf)
        
        self.active_pixbuf_group = (active_normal_dpixbuf,
                                    active_hover_dpixbuf,
                                    active_press_dpixbuf)

        # Init request size.
        label_width = 0
        button_width = inactive_normal_dpixbuf.get_pixbuf().get_width()
        button_height = inactive_normal_dpixbuf.get_pixbuf().get_height()
        if button_label:
            label_width = get_content_size(button_label, font_size)[0]
        self.set_size_request(button_width + label_width + padding_x * 2,
                              button_height)
        
        self.connect("button-press-event", self.button_press_cb)
        self.connect("button-release-event", self.button_release_cb)
        
        # Expose button.
        self.connect("expose-event", lambda w, e : self.expose_toggle_button(
                w, e,
                button_label, padding_x, font_size, label_dcolor))
        
    def button_press_cb(self, widget, event):    
        self.button_press_flag = True
        self.queue_draw()
        
    def button_release_cb(self, widget, event):    
        self.button_press_flag = False
        self.queue_draw()    
        
    def expose_toggle_button(self, widget, event, 
                             button_label, padding_x, font_size, label_dcolor):
        '''Expose function to replace event box's image.'''
        # Init.
        inactive_normal_dpixbuf, inactive_hover_dpixbuf, inactive_press_dpixbuf = self.inactive_pixbuf_group
        active_normal_dpixbuf, active_hover_dpixbuf, active_press_dpixbuf = self.active_pixbuf_group
        rect = widget.allocation
        image = inactive_normal_dpixbuf.get_pixbuf()
        
        # Get pixbuf along with button's sate.
        if widget.state == gtk.STATE_NORMAL:
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
        if button_label:
            draw_font(cr, button_label, font_size, 
                      label_dcolor.get_color(),
                      rect.x + image.get_width() + padding_x * 2,
                      rect.y, 
                      rect.width - image.get_width() - padding_x * 2,
                      rect.height,
                      ALIGN_START)
    
        # Propagate expose to children.
        propagate_expose(widget, event)
        
        return True
    
    def set_inactive_pixbuf_group(self,  new_group):
        self.inactive_pixbuf_group = new_group
        
    def set_active_pixbuf_group(self, new_group):    
        self.active_pixbuf_group = new_group

class ActionButton(gtk.Button):
    '''Action button.'''
	
    def __init__(self, actions, index=0):
        '''Action button.'''
        gtk.Button.__init__(self)
        self.actions = actions
        self.index = index
        
        pixbuf = self.actions[self.index][0][0].get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        
        self.connect("expose-event", self.expose_action_button)
        self.connect("clicked", lambda w: self.update_action_index(w))
        
    def update_action_index(self, widget):
        '''Update action index.'''
        # Call click callback.
        self.actions[self.index][1](widget)
        
        # Update index.
        self.index += 1
        if self.index >= len(self.actions):
            self.index = 0
        
        # Redraw.
        self.queue_draw()    
        
    def expose_action_button(self, widget, event):
        '''Expose action button.'''
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
    '''Check button.'''
	
    def __init__(self, label_text=None, padding_x=8):
        '''Init check button.'''
        ToggleButton.__init__(
            self,
            ui_theme.get_pixbuf("button/check_button_inactive_normal.png"),
            ui_theme.get_pixbuf("button/check_button_active_normal.png"),
            ui_theme.get_pixbuf("button/check_button_inactive_hover.png"),
            ui_theme.get_pixbuf("button/check_button_active_hover.png"),
            ui_theme.get_pixbuf("button/check_button_inactive_press.png"),
            ui_theme.get_pixbuf("button/check_button_active_press.png"),
            label_text, padding_x
            )
        
gobject.type_register(CheckButton)

class RadioButton(ToggleButton):
    '''Radio button.'''
	
    def __init__(self, label_text=None, padding_x=8):
        '''Init radio button.'''
        ToggleButton.__init__(
            self,
            ui_theme.get_pixbuf("button/radio_button_inactive_normal.png"),
            ui_theme.get_pixbuf("button/radio_button_active_normal.png"),
            ui_theme.get_pixbuf("button/radio_button_inactive_hover.png"),
            ui_theme.get_pixbuf("button/radio_button_active_hover.png"),
            ui_theme.get_pixbuf("button/radio_button_inactive_press.png"),
            ui_theme.get_pixbuf("button/radio_button_active_press.png"),
            label_text,
            padding_x
            )

        self.switch_lock = False    
        self.connect("clicked", self.click_radio_button)
        
    def click_radio_button(self, widget):
        '''Click radio button.'''
        if not self.switch_lock:
            for w in get_same_level_widgets(self):
                w.switch_lock = True
                w.set_active(w == self)
                w.switch_lock = False
        
gobject.type_register(RadioButton)
