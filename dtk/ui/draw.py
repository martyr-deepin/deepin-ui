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

import gtk
import cairo
from theme import *
from math import pi
from utils import *
from constant import *
import math

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
        
def draw_round_rectangle(cr, x, y, width, height, r):
    '''Draw round rectangle.'''
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
        
def draw_window_rectangle(cr, sx, sy, ex, ey, r):
    '''Draw window rectangle.'''
    with cairo_disable_antialias(cr):    
        # Set line width.
        cr.set_line_width(1)
        
        # Set OPERATOR_OVER operator.
        cr.set_operator(cairo.OPERATOR_OVER)
        
        cr.move_to(sx + r, sy)        # top line
        cr.line_to(ex - r, sy)
        cr.stroke()
        
        cr.move_to(ex, sy + r)    # right side
        cr.line_to(ex, ey - r)
        cr.stroke()
        
        cr.move_to(ex - r, ey) # bottom side
        cr.line_to(sx + r, ey)     
        cr.stroke()
        
        cr.move_to(sx, ey - r)    # left side
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
        
def draw_font(cr, text, font_size, font_color, x, y, width, height, x_align=ALIGN_MIDDLE, y_align=ALIGN_MIDDLE):
    '''Draw font.'''
    # Create pangocairo context.
    context = pangocairo.CairoContext(cr)
    
    # Set layout.
    layout = context.create_layout()
    layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, font_size)))
    layout.set_text(text)
    
    # Get text size.
    (text_width, text_height) = layout.get_pixel_size()
    
    # Set text coordinate.
    if x_align == ALIGN_START:
        text_x = x
    elif x_align == ALIGN_END:
        text_x = x + width - text_width
    else:
        text_x = x + (width - text_width) / 2
        
    if y_align == ALIGN_START:
        text_y = y
    elif y_align == ALIGN_END:
        text_y = y + height
    else:
        text_y = y + (height + text_height) / 2
    cr.move_to(text_x, text_y - text_height)
    
    # Draw text.
    cr.set_source_rgb(*color_hex_to_cairo(font_color))
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
    if top_to_bottom:
        pat = cairo.LinearGradient(0, y, 0, y + h)
    else:
        pat = cairo.LinearGradient(0, y + h, 0, y)
    for (pos, color_info) in color_infos:
        add_color_stop_rgba(pat, pos, color_info)
    cr.set_source(pat)
    draw_round_rectangle(cr, x, y, w, h, radius)
    cr.fill()

def draw_hlinear(cr, x, y, w, h, color_infos, radius=0, left_to_right=True):
    '''Draw linear rectangle.'''
    if left_to_right:
        pat = cairo.LinearGradient(x, 0, x + w, 0)
    else:
        pat = cairo.LinearGradient(x + w, 0, x, 0)
    for (pos, color_info) in color_infos:
        add_color_stop_rgba(pat, pos, color_info)
    cr.set_source(pat)
    draw_round_rectangle(cr, x, y, w, h, radius)
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

def draw_radial_round(cr, x, y, r, color_infos):
    '''Draw radial round.'''
    radial = cairo.RadialGradient(x, y, r, x, y, 0)
    for (pos, color_info) in color_infos:
        add_color_stop_rgba(radial, pos, color_info)
    cr.arc(x, y, r, 0, 2 * math.pi)
    cr.set_source(radial)
    cr.fill()

# def draw_text(text, foreground, background, font_size, gaussian_radious):
#     '''Draw text.'''
#     (text_width, text_height) = get_content_size(text, font_size)
#     surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, text_width, text_height);
#     cr = cairo.Context(surface)
#     cr.set_source_rgb(1, 1, 1)
#     cr.rectangle(0, 0, text_width, text_height)
#     cr.fill()
    
#     cr.set_source_rgb(0, 0, 0)
#     cr.set_font_size(font_size)
#     cr.move_to(0, font_size)
#     cr.show_text(text)
#     cr.fill()
    
#     surface_gaussion_blur(surface, gaussian_radious)
    
#     # cr.set_source_rgb(0, 0, 1)
#     # cr.set_font_size(font_size)
#     # cr.move_to(0, font_size)
#     # cr.show_text(text)
#     # cr.fill()
        
#     surface.write_to_png("test.png")
    
# import copy    
# import math
    
# def surface_gaussion_blur(surface, radious):
#     '''Gaussian blur surface.'''
#     surface.flush()
#     width = surface.get_width()
#     height = surface.get_height()
    
#     tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height);
    
#     src = surface.get_data()    
#     src_stride = surface.get_stride()
    
#     print type(src)
#     print type(src_stride)
    
#     dst = tmp.get_data()
#     dst_stride = tmp.get_stride()
    
#     size = 17
#     half = 17 / 2

#     kernel = range(0, size)
#     a = 0
#     for i in range(0, size):
#         f = i - half
#         kernel[i] = math.exp(-f * f / 30.0) * 80
#         a += kernel[i]
        
#     for i in range(0, height):
#         s = src + i * src_stride
#         d = dst + i * dst_stride
#         for j in range(0, width):
#             if radious < j and j < width - radious:
#                 continue

#             x = y = z = w = 0
#             for k in range(0, size):
#                 if j - half + k < 0 or j - half + k >= width:
#                     continue
                
#                 p = s[j - half + k]
#                 x += ((p >> 24) & 0xff) * kernel[k]
#                 y += ((p >> 16) & 0xff) * kernel[k]
#                 z += ((p >> 8) & 0xff) * kernel[k]
#                 w += ((p >> 0) & 0xff) * kernel[k]
                
#             d[j] = (x / a << 24) | (y / a << 16) | (z / a << 8) | w / a

#     for i in range(0, height):
#         s = dst + i * dst_stride
#         d = src + i * src_stride
#         for j in range(0, width):
#             if radious <= i and i < height - radious:
#                 d[j] = s[j]
#                 continue

#             x = y = z = w = 0
#             for k in range(0, size):
#                 if i - half + k < 0 or i - half + k >= height:
#                     continue
                
#                 s = dst + (i - half + k) * dst_stride
#                 p = s[j]
                
#                 x += ((p >> 24) & 0xff) * kernel[k]
#                 y += ((p >> 16) & 0xff) * kernel[k]
#                 z += ((p >> 8) & 0xff) * kernel[k]
#                 w += ((p >> 0) & 0xff * kernel[k])
                
#             d[j] = (x / a << 24) | (y / a << 16) | (z / a << 8) | w / a    
            
#     surface.mark_dirty()

# draw_text("Linux Deepin", None, None, 11, 2)
