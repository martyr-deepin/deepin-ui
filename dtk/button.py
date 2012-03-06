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

from utils import *
from draw import *
import gtk
import gobject

class Button(gtk.Button):
    '''Button.'''
    
    def __init__(self, label="", width=69, height=22, padding_x=10, padding_y=3):
        '''Init button.'''
        # Init.
        gtk.Button.__init__(self)
        self.label = label
        
        # Init button size.
        (font_width, font_height) = get_content_size(label, DEFAULT_FONT_SIZE)
        self.set_size_request(max(width, font_width + 2 * padding_x), max(height, font_height + 2 * padding_y))
        
        # Handle signal.
        self.connect("expose-event", self.expose_button)
        
    def expose_button(self, widget, event):
        '''Callback for button 'expose-event' event.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        top_left = ui_theme.get_dynamic_pixbuf("button.png").get_pixbuf()
        top_right = top_left.rotate_simple(90)
        bottom_right = top_left.rotate_simple(180)
        bottom_left = top_left.rotate_simple(270)
        
        # Clip rectangle with four corner.
        with cairo_state(cr):
            cr.rectangle(x + 1, y, w - 2, 1)
            cr.rectangle(x, y + 1, w, h - 2)
            cr.rectangle(x + 1, y + h - 1, w - 2, 1)
            cr.clip()
            
            # Draw background.
            if widget.state == gtk.STATE_NORMAL:
                background_color = ui_theme.get_dynamic_shadow_color("buttonBackgroundNormal").get_color_info()
                border_color = ui_theme.get_dynamic_color("buttonBorderNormal").get_color()
            elif widget.state == gtk.STATE_PRELIGHT:
                background_color = ui_theme.get_dynamic_shadow_color("buttonBackgroundPrelight").get_color_info()
                border_color = ui_theme.get_dynamic_color("buttonBorderPrelight").get_color()
            elif widget.state == gtk.STATE_ACTIVE:
                background_color = ui_theme.get_dynamic_shadow_color("buttonBackgroundActive").get_color_info()
                border_color = ui_theme.get_dynamic_color("buttonBorderActive").get_color()
            draw_vlinear(cr, x, y, w, h, background_color)    

        # Draw button corner.
        draw_pixbuf(cr, top_left, x, y)
        draw_pixbuf(cr, top_right, x + w - 2, y)
        draw_pixbuf(cr, bottom_right, x + w - 2, y + h - 2)
        draw_pixbuf(cr, bottom_left, x, y + h - 2)
        
        # Draw button corner mask.
        (r, g, b) = color_hex_to_cairo(border_color)
        cr.set_source_rgba(r, g, b, 0.4)
        
        # Draw top-left corner mask.
        draw_line(cr, x + 1, y + 1, x + 2, y + 1)
        draw_line(cr, x, y + 2, x + 2, y + 2)
        
        # Draw top-right corner mask.
        draw_line(cr, x + w - 2, y + 1, x + w - 1, y + 1)
        draw_line(cr, x + w - 2, y + 2, x + w, y + 2)
        
        # Draw bottom-left corner mask.
        draw_line(cr, x + 1, y + h, x + 2, y + h)
        draw_line(cr, x, y + h - 1, x + 2, y + h - 1)

        # Draw bottom-right corner mask.
        draw_line(cr, x + w - 2, y + h, x + w - 1, y + h)
        draw_line(cr, x + w - 2, y + h - 1, x + w, y + h - 1)
        
        # Draw button border.
        cr.set_source_rgb(*color_hex_to_cairo(border_color))
        draw_line(cr, x + 2, y + 1, x + w - 2, y + 1)
        draw_line(cr, x + 2, y + h, x + w - 2, y + h)
        draw_line(cr, x + 1, y + 2, x + 1, y + h - 2)
        draw_line(cr, x + w, y + 2, x + w, y + h - 2)
        
        # Draw font.
        if self.label != "":
            draw_font(cr, self.label, DEFAULT_FONT_SIZE, 
                      ui_theme.get_dynamic_color("buttonFont").get_color(),
                      x, y, w, h)
        
        return True        

gobject.type_register(Button)

class ImageButton(gtk.Button):
    '''Image button.'''
	
    def __init__(self, content, sub_dir="button", icon_path_prefix="button", scale_x=False):
        '''Init font button.'''
        gtk.Button.__init__(self)
        draw_button(self, sub_dir, icon_path_prefix, scale_x, content)
        
gobject.type_register(ImageButton)

class ThemeButton(gtk.Button):
    '''Theme button.'''
	
    def __init__(self, sub_dir="button", icon_path_prefix="window_theme"):
        '''Init theme button.'''
        gtk.Button.__init__(self)
        draw_button(self, sub_dir, icon_path_prefix)
        
gobject.type_register(ThemeButton)

class MenuButton(gtk.Button):
    '''Menu button.'''
	
    def __init__(self, sub_dir="button", icon_path_prefix="window_menu"):
        '''Init menu button.'''
        gtk.Button.__init__(self)
        draw_button(self, sub_dir, icon_path_prefix)
        
gobject.type_register(MenuButton)

class MinButton(gtk.Button):
    '''Min button.'''
	
    def __init__(self, sub_dir="button", icon_path_prefix="window_min"):
        '''Init min button.'''
        gtk.Button.__init__(self)
        draw_button(self, sub_dir, icon_path_prefix)
        
gobject.type_register(MinButton)

class CloseButton(gtk.Button):
    '''Close button.'''
	
    def __init__(self, sub_dir="button", icon_path_prefix="window_close"):
        '''Init close button.'''
        gtk.Button.__init__(self)
        draw_button(self, sub_dir, icon_path_prefix)
        
gobject.type_register(CloseButton)

class MaxButton(gtk.Button):
    '''Max button.'''
	
    def __init__(self,sub_dir="button", max_path_prefix="window_max", unmax_path_prefix="window_unmax"):
        '''Init max button.'''
        gtk.Button.__init__(self)
        draw_max_button(self, sub_dir, max_path_prefix, unmax_path_prefix)
        
gobject.type_register(MaxButton)

def draw_button(widget, sub_dir, icon_path_prefix, scale_x=False,
                button_label=None, font_size=DEFAULT_FONT_SIZE, label_dcolor="buttonDefaultFont"):
    '''Create button.'''
    # Get dynamic pixbuf.
    normal_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_normal.png" % (sub_dir, icon_path_prefix))
    hover_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_hover.png" % (sub_dir, icon_path_prefix))
    press_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_press.png" % (sub_dir, icon_path_prefix))
    
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
    pixbuf = image.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)
    
    # Draw font.
    if button_label:
        draw_font(cr, button_label, font_size, 
                  ui_theme.get_dynamic_color(label_dcolor).get_color(),
                  rect.x, rect.y, rect.width, rect.height)

    # Propagate expose to children.
    propagate_expose(widget, event)
    
    return True

def draw_max_button(widget, sub_dir, max_path_prefix, unmax_path_prefix):
    '''Create max button.'''
    # Init request size.
    pixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_normal.png" % (sub_dir, unmax_path_prefix)).get_pixbuf()
    widget.set_size_request(pixbuf.get_width(), pixbuf.get_height())
    
    # Redraw.
    widget.connect("expose-event", lambda w, e: 
                   expose_max_button(w, e, sub_dir, max_path_prefix, unmax_path_prefix))
                
def expose_max_button(widget, event, sub_dir, max_path_prefix, unmax_path_prefix):
    '''Expose function to replace event box's image.'''
    # Get dynamic pixbuf.
    if window_is_max(widget):
        normal_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_normal.png" % (sub_dir, unmax_path_prefix))
        hover_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_hover.png" % (sub_dir, unmax_path_prefix))
        press_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_press.png" % (sub_dir, unmax_path_prefix))
    else:
        normal_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_normal.png" % (sub_dir, max_path_prefix))
        hover_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_hover.png" % (sub_dir, max_path_prefix))
        press_dpixbuf = ui_theme.get_dynamic_pixbuf("%s/%s_press.png" % (sub_dir, max_path_prefix))

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
    pixbuf = image.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
    cr = widget.window.cairo_create()
    draw_pixbuf(cr, pixbuf, widget.allocation.x, widget.allocation.y)

    # Propagate expose to children.
    propagate_expose(widget, event)
    
    return True

