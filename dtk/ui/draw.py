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

from constant import DEFAULT_FONT, DEFAULT_FONT_SIZE
from math import pi
import cairo
import dtk_cairo_blur    
import gtk
import math
import pango
import pangocairo
from utils import (cairo_state, cairo_disable_antialias, color_hex_to_cairo, 
                   add_color_stop_rgba, propagate_expose, 
                   alpha_color_hex_to_cairo, layout_set_markup)

def draw_radial_ring(cr, x, y, outer_radius, inner_radius, color_infos):
    '''Draw radial ring.'''
    with cairo_state(cr):
        # Clip.
        cr.arc(x, y, outer_radius, 0, pi * 2)
        cr.arc(x, y, inner_radius, 0, pi * 2)
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.clip()
        
        # Draw radial round.
        draw_radial_round(cr, x, y, outer_radius, color_infos)
        
def get_desktop_pixbuf():
    '''Get desktop snapshot.'''
    rootWindow = gtk.gdk.get_default_root_window() 
    [width, height] = rootWindow.get_size() 
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    return pixbuf.get_from_drawable(rootWindow, rootWindow.get_colormap(), 0, 0, 0, 0, width, height) 
    
def draw_round_rectangle(cr, x, y, width, height, r):
    '''Draw round rectangle.'''
    # Adjust coordinate when width and height is negative.
    if width < 0:
        x = x + width
        width = -width
    if height < 0:
        y = y + height
        height = -height
    
    # Top side.
    cr.move_to(x + r, y)
    cr.line_to(x + width - r, y)
    
    # Top-right corner.
    cr.arc(x + width - r, y + r, r, pi * 3 / 2, pi * 2)
    
    # Right side.
    cr.line_to(x + width, y + height - r)
    
    # Bottom-right corner.
    cr.arc(x + width - r, y + height - r, r, 0, pi / 2)
    
    # Bottom side.
    cr.line_to(x + r, y + height)
    
    # Bottom-left corner.
    cr.arc(x + r, y + height - r, r, pi / 2, pi)
    
    # Left side.
    cr.line_to(x, y + r)
    
    # Top-left corner.
    cr.arc(x + r, y + r, r, pi, pi * 3 / 2)

    # Close path.
    cr.close_path()

def draw_pixbuf(cr, pixbuf, x=0, y=0, alpha=1.0):
    '''Draw pixbuf.'''
    if pixbuf != None:
        cr.set_source_pixbuf(pixbuf, x, y)
        cr.paint_with_alpha(alpha)
        
def draw_window_frame(cr, x, y, w, h,
                      color_frame_outside_1,
                      color_frame_outside_2,
                      color_frame_outside_3,
                      color_frame_inside_1,
                      color_frame_inside_2,
                      ):
    '''Draw window frame.'''
    with cairo_disable_antialias(cr):    
        # Set line width.
        cr.set_line_width(1)
        
        # Set OPERATOR_OVER operator.
        cr.set_operator(cairo.OPERATOR_OVER)
        
        # Draw outside 8 points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_outside_1.get_color_info()))
        
        cr.rectangle(x, y + 1, 1, 1) # top-left
        cr.rectangle(x + 1, y, 1, 1)
        
        cr.rectangle(x + w - 1, y + 1, 1, 1) # top-right
        cr.rectangle(x + w - 2, y, 1, 1)
        
        cr.rectangle(x, y + h - 2, 1, 1) # bottom-left
        cr.rectangle(x + 1, y + h - 1, 1, 1)
        
        cr.rectangle(x + w - 1, y + h - 2, 1, 1) # bottom-right
        cr.rectangle(x + w - 2, y + h - 1, 1, 1)
        
        cr.fill()
        
        # Draw outside 4 points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_outside_2.get_color_info()))
        
        cr.rectangle(x + 1, y + 1, 1, 1) # top-left
        
        cr.rectangle(x + w - 2, y + 1, 1, 1) # top-right
        
        cr.rectangle(x + 1, y + h - 2, 1, 1) # bottom-left
        
        cr.rectangle(x + w - 2, y + h - 2, 1, 1) # bottom-right
        
        cr.fill()
        
        # Draw outside frame.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_outside_3.get_color_info()))

        cr.rectangle(x + 2, y, w - 4, 1) # top side
        
        cr.rectangle(x + 2, y + h - 1, w - 4, 1) # bottom side
        
        cr.rectangle(x, y + 2, 1, h - 4) # left side
        
        cr.rectangle(x + w - 1, y + 2, 1, h - 4) # right side
        
        cr.fill()
        
        # Draw outside 4 points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_inside_1.get_color_info()))
        
        cr.rectangle(x + 1, y + 1, 1, 1) # top-left
        
        cr.rectangle(x + w - 2, y + 1, 1, 1) # top-right
        
        cr.rectangle(x + 1, y + h - 2, 1, 1) # bottom-left
        
        cr.rectangle(x + w - 2, y + h - 2, 1, 1) # bottom-right
        
        cr.fill()
        
        # Draw inside 4 points.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_inside_1.get_color_info()))
        
        cr.rectangle(x + 2, y + 2, 1, 1) # top-left
        
        cr.rectangle(x + w - 3, y + 2, 1, 1) # top-right
        
        cr.rectangle(x + 2, y + h - 3, 1, 1) # bottom-left
        
        cr.rectangle(x + w - 3, y + h - 3, 1, 1) # bottom-right
        
        cr.fill()
        
        # Draw inside frame.
        cr.set_source_rgba(*alpha_color_hex_to_cairo(color_frame_inside_2.get_color_info()))

        cr.rectangle(x + 2, y + 1, w - 4, 1) # top side
        
        cr.rectangle(x + 2, y + h - 2, w - 4, 1) # bottom side
        
        cr.rectangle(x + 1, y + 2, 1, h - 4) # left side
        
        cr.rectangle(x + w - 2, y + 2, 1, h - 4) # right side
        
        cr.fill()
        
def draw_window_rectangle(cr, sx, sy, ex, ey, r):
    '''Draw window rectangle.'''
    with cairo_disable_antialias(cr):    
        # Set line width.
        cr.set_line_width(1)
        
        # Set OPERATOR_OVER operator.
        cr.set_operator(cairo.OPERATOR_OVER)
        
        cr.move_to(sx + r, sy)  # top line
        cr.line_to(ex - r, sy)
        cr.stroke()
        
        cr.move_to(ex, sy + r)  # right side
        cr.line_to(ex, ey - r)
        cr.stroke()
        
        cr.move_to(ex - r, ey)  # bottom side
        cr.line_to(sx + r, ey)     
        cr.stroke()
        
        cr.move_to(sx, ey - r)  # left side
        cr.line_to(sx, sy + r)        
        cr.stroke()
        
        cr.arc(sx + r, sy + r, r, pi, pi * 3 / 2) # top-left
        cr.stroke()
        
        cr.arc(ex - r, sy + r, r, pi * 3 / 2, pi * 2) # top-right
        cr.stroke()
        
        cr.arc(ex - r, ey - r, r, 0, pi / 2) # bottom-right
        cr.stroke()
        
        cr.arc(sx + r, ey - r, r, pi / 2, pi) # bottom-left
        cr.stroke()
        
def draw_text(cr, markup, x, y, w, h, text_size=DEFAULT_FONT_SIZE, text_color="#000000", 
              text_font=DEFAULT_FONT, alignment=pango.ALIGN_LEFT,
              gaussian_radious=None, gaussian_color=None,
              border_radious=None, border_color=None, 
              wrap_width=None,
              ):
    if border_radious == None and border_color == None and gaussian_radious == None and gaussian_color == None:
        render_text(cr, markup, x, y, w, h, text_size, text_color, text_font, alignment,
                    wrap_width=wrap_width)
    elif (border_radious != None and border_color != None) or (gaussian_radious != None and gaussian_color != None):
        # Create text cairo context.
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        text_cr = cairo.Context(surface)
        
        # Draw gaussian light.
        if gaussian_radious != None and gaussian_color != None:
            text_cr.save()
            render_text(text_cr, markup, gaussian_radious, 
                        gaussian_radious, w - gaussian_radious * 2, h - gaussian_radious * 2, 
                        text_size, gaussian_color, alignment=alignment,
                        wrap_width=wrap_width)
            dtk_cairo_blur.gaussian_blur(surface, gaussian_radious)
            text_cr.restore()
        
        # Make sure border can render correctly.
        if gaussian_radious == None:
            gaussian_radious = 0
            
        # Draw gaussian border.
        if border_radious != None and border_radious != 0 and border_color != None:
            render_text(text_cr, markup, gaussian_radious, gaussian_radious, w - gaussian_radious * 2, 
                        h - gaussian_radious * 2, text_size, border_color, alignment=alignment,
                        wrap_width=wrap_width)
            dtk_cairo_blur.gaussian_blur(surface, border_radious)
        
        # Draw font.
        render_text(text_cr, markup, gaussian_radious, gaussian_radious, w - gaussian_radious * 2, 
                    h - gaussian_radious * 2, text_size, text_color, alignment=alignment,
                    wrap_width=wrap_width)
        
        # Render gaussian text to target cairo context.
        cr.set_source_surface(surface, x, y)
        cr.paint()
    
def render_text(cr, markup, x, y, w, h, text_size=DEFAULT_FONT_SIZE, text_color="#000000", 
                text_font=DEFAULT_FONT, alignment=pango.ALIGN_LEFT,
                wrap_width=None):
    '''Draw string.'''
    # Create pangocairo context.
    context = pangocairo.CairoContext(cr)
    
    # Set layout.
    layout = context.create_layout()
    layout.set_font_description(pango.FontDescription("%s %s" % (text_font, text_size)))
    layout_set_markup(layout, markup)
    layout.set_alignment(alignment)
    if wrap_width == None:
        layout.set_single_paragraph_mode(True)
        layout.set_width(w * pango.SCALE)
        layout.set_ellipsize(pango.ELLIPSIZE_END)
    else:
        layout.set_width(wrap_width * pango.SCALE)
        layout.set_wrap(pango.WRAP_WORD)
    (text_width, text_height) = layout.get_pixel_size()
    
    # Draw text.
    cr.move_to(x, y + (h - text_height) / 2)
    cr.set_source_rgb(*color_hex_to_cairo(text_color))
    context.update_layout(layout)
    context.show_layout(layout)
        
def draw_line(cr, sx, sy, ex, ey, line_width=1, antialias_status=cairo.ANTIALIAS_NONE):
    '''Draw line.'''
    # Save antialias.
    antialias = cr.get_antialias()
    
    # Draw line.
    cr.set_line_width(line_width)
    cr.set_antialias(antialias_status)
    cr.move_to(sx, sy)
    cr.line_to(ex, ey)
    cr.stroke()
    
    # Restore antialias.
    cr.set_antialias(antialias)

def draw_vlinear(cr, x, y, w, h, color_infos, radius=0, top_to_bottom=True):
    '''Draw linear rectangle.'''
    with cairo_state(cr):
        # Translate y coordinate, otherwise y is too big for LinearGradient cause render bug.
        cr.translate(0, y)
        
        if top_to_bottom:
            pat = cairo.LinearGradient(0, 0, 0, h)
        else:
            pat = cairo.LinearGradient(0, h, 0, 0)
            
        for (pos, color_info) in color_infos:
            add_color_stop_rgba(pat, pos, color_info) 
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source(pat)
        draw_round_rectangle(cr, x, 0, w, h, radius)
        
        cr.fill()

def draw_hlinear(cr, x, y, w, h, color_infos, radius=0, left_to_right=True):
    '''Draw linear rectangle.'''
    with cairo_state(cr):
        # Translate x coordinate, otherwise x is too big for LinearGradient cause render bug.
        cr.translate(x, 0)
        
        if left_to_right:
            pat = cairo.LinearGradient(0, 0, w, 0)
        else:
            pat = cairo.LinearGradient(w, 0, 0, 0)
        for (pos, color_info) in color_infos:
            add_color_stop_rgba(pat, pos, color_info)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source(pat)
        draw_round_rectangle(cr, 0, y, w, h, radius)
        cr.fill()
    
def expose_linear_background(widget, event, color_infos):
    '''Expose linear background.'''
    # Init.
    cr = widget.window.cairo_create()
    rect = widget.allocation
    
    # Draw linear background.
    draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, color_infos)
    
    # Propagate expose.
    propagate_expose(widget, event)
    
    return True

def draw_window_shadow(cr, x, y, w, h, r, p, color_window_shadow):
    '''Draw window shadow.'''
    color_infos = color_window_shadow.get_color_info()
    with cairo_state(cr):
        # Clip four corner.
        cr.rectangle(x, y, r - 1, r - 1) # top-left
        cr.rectangle(x + r - 1, y, 1, r - 2) # vertical
        cr.rectangle(x, y + r - 1, r - 2, 1) # horizontal
        
        cr.rectangle(x + w - r + 1, y, r - 1, r - 1) # top-right
        cr.rectangle(x + w - r, y, 1, r - 2)         # vertical
        cr.rectangle(x + w - r + 2, y + r - 1, r - 2, 1) # horizontal
        
        cr.rectangle(x, y + h - r + 1, r - 1, r - 1) # bottom-left
        cr.rectangle(x + r - 1, y + h - r + 2, 1, r - 2) # vertical
        cr.rectangle(x, y + h - r, r - 2, 1)     # horizontal
        
        cr.rectangle(x + w - r + 1, y + h - r + 1, r - 1, r - 1) # bottom-right
        cr.rectangle(x + w - r, y + h - r + 2, 1, r - 2)         # vertical
        cr.rectangle(x + w - r + 2, y + h - r, r - 2, 1) # horizontal
        
        cr.clip()
        
        # Draw four round.
        draw_radial_round(cr, x + r, y + r, r, color_infos)
        draw_radial_round(cr, x + r, y + h - r, r, color_infos)
        draw_radial_round(cr, x + w - r, y + r, r, color_infos)
        draw_radial_round(cr, x + w - r, y + h - r, r, color_infos)
    
    with cairo_state(cr):
        # Clip four side.
        cr.rectangle(x, y + r, p, h - r * 2)
        cr.rectangle(x + w - p, y + r, p, h - r * 2)
        cr.rectangle(x + r, y, w - r * 2, p)
        cr.rectangle(x + r, y + h - p, w - r * 2, p)
        cr.clip()
        
        # Draw four side.
        draw_vlinear(
            cr, 
            x + r, y, 
            w - r * 2, r, color_infos)
        draw_vlinear(
            cr, 
            x + r, y + h - r, 
            w - r * 2, r, color_infos, 0, False)
        draw_hlinear(
            cr, 
            x, y + r, 
            r, h - r * 2, color_infos)
        draw_hlinear(
            cr, 
            x + w - r, y + r, 
            r, h - r * 2, color_infos, 0, False)

def draw_radial_round(cr, x, y, r, color_infos):
    '''Draw radial round.'''
    radial = cairo.RadialGradient(x, y, r, x, y, 0)
    for (pos, color_info) in color_infos:
        add_color_stop_rgba(radial, pos, color_info)
    cr.arc(x, y, r, 0, 2 * math.pi)
    cr.set_source(radial)
    cr.fill()

def draw_blank_mask(cr, x, y, w, h):
    '''Draw blank mask.'''
    pass

