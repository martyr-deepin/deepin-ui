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
        
def get_desktop_pixbuf():
    '''Get desktop snapshot.'''
    rootWindow = gtk.gdk.get_default_root_window() 
    [width, height] = rootWindow.get_size() 
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    return pixbuf.get_from_drawable(rootWindow, rootWindow.get_colormap(), 0, 0, 0, 0, width, height) 
    
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
        text_y = y + height - text_height
    else:
        text_y = y + (height - text_height) / 2
        
    cr.move_to(text_x, text_y)
    
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

import cairo_blur    

def draw_text(cr, rx, ry, rw, rh, text, 
              text_color, gaussian_color, border_color, 
              font_size, gaussian_radious, border_radious):
    '''Draw text.'''
    # Get text size.
    (text_width, text_height) = get_content_size(text, font_size)
    width = max(text_width + gaussian_radious * 2, rw)
    height = max(text_height + gaussian_radious * 2, rh)
    
    # Create text cairo context.
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height);
    text_cr = cairo.Context(surface)
    
    # Draw gaussian light.
    text_cr.save()
    draw_font(text_cr, text, font_size, gaussian_color, 0, 0, width, height)
    cairo_blur.gaussian_blur(surface, gaussian_radious)
    text_cr.restore()

    # Draw gaussian border.
    draw_font(text_cr, text, font_size, border_color, 0, 0, width, height)
    cairo_blur.gaussian_blur(surface, border_radious)
    
    # Draw font.
    draw_font(text_cr, text, font_size, text_color, 0, 0, width, height)
    
    # Render gaussian text to target cairo context.
    cr.set_source_surface(surface, rx, ry)
    cr.paint()

def draw_test():
    '''docs'''
    width = 1366
    height = 768

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height);
    cr = cairo.Context(surface)
    
    gdkcr = gtk.gdk.CairoContext(cr)
    draw_pixbuf(gdkcr, get_desktop_pixbuf())

    cairo_blur.gaussian_blur(surface, 5)
    
    surface.write_to_png("test.png")
    
# draw_test()
