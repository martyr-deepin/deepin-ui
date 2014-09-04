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
                   alpha_color_hex_to_cairo)

def draw_radial_ring(cr, x, y, outer_radius, inner_radius, color_infos, clip_corner=None):
    '''
    Draw radial ring.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param outer_radius: Radious for outter ring.
    @param inner_radius: Radious for inner ring.
    @param color_infos: A list of ColorInfo, ColorInfo format as [(color_pos, (color_hex_value, color_alpha))].
    '''
    with cairo_state(cr):
        # Clip corner.
        if clip_corner:
            if clip_corner == "top-left":
                cr.rectangle(x - outer_radius, y - outer_radius, outer_radius, outer_radius)
            elif clip_corner == "top-right":
                cr.rectangle(x, y - outer_radius, outer_radius, outer_radius)
            elif clip_corner == "bottom-left":
                cr.rectangle(x - outer_radius, y, outer_radius, outer_radius)
            elif clip_corner == "bottom-right":
                cr.rectangle(x, y, outer_radius, outer_radius)

            cr.clip()

        # Clip.
        cr.arc(x, y, outer_radius, 0, pi * 2)
        cr.arc(x, y, inner_radius, 0, pi * 2)
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.clip()

        # Draw radial round.
        draw_radial_round(cr, x, y, outer_radius, color_infos)

def get_desktop_pixbuf():
    '''
    Get screenshot of desktop.

    @return: Return desktop screenshot as gtk.gdk.Pixbuf.
    '''
    rootWindow = gtk.gdk.get_default_root_window()
    [width, height] = rootWindow.get_size()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    return pixbuf.get_from_drawable(rootWindow, rootWindow.get_colormap(), 0, 0, 0, 0, width, height)

def draw_round_rectangle(cr, x, y, width, height, r):
    '''
    Draw round rectangle.

    @param cr: Cairo context.
    @param x: X coordiante of rectangle area.
    @param y: Y coordiante of rectangle area.
    @param width: Width of rectangle area.
    @param height: Width of rectangle area.
    @param r: Radious of rectangle corner.
    '''
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
    '''
    Draw pixbuf on cairo context, this function use frequently for image render.

    @param cr: Cairo context.
    @param pixbuf: gtk.gdk.Pixbuf
    @param x: X coordiante of draw area.
    @param y: Y coordiante of draw area.
    @param alpha: Alpha value to render pixbuf, float value between 0 and 1.0
    '''
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
    '''
    Draw window frame.

    @param cr: Cairo context.
    @param x: X coordiante of draw area.
    @param y: Y coordiante of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param color_frame_outside_1: Use for draw outside 8 points.
    @param color_frame_outside_2: Use for draw middle 4 points.
    @param color_frame_outside_3: Use for draw inside 4 points.
    @param color_frame_inside_1: Use for draw outside frame.
    @param color_frame_inside_2: Use for draw inner frame and inside 4 points.
    '''
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
    '''
    Draw window rectangle.

    @param cr: Cairo context.
    @param sx: Source x coordinate.
    @param sy: Source y coordinate.
    @param ex: Target x coordinate.
    @param ey: Target x coordinate.
    @param r: Window frame radious.
    '''
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

TEXT_ALIGN_TOP = 1
TEXT_ALIGN_MIDDLE = 2
TEXT_ALIGN_BOTTOM = 3

def draw_text(cr, markup,
              x, y, w, h,
              text_size=DEFAULT_FONT_SIZE,
              text_color="#000000",
              text_font=DEFAULT_FONT,
              alignment=pango.ALIGN_LEFT,
              gaussian_radious=None,
              gaussian_color=None,
              border_radious=None,
              border_color=None,
              wrap_width=None,
              underline=False,
              vertical_alignment=TEXT_ALIGN_MIDDLE,
              clip_line_count=None,
              ellipsize=pango.ELLIPSIZE_END,
              ):
    '''
    Standard function for draw text.

    @param cr: Cairo context.
    @param markup: Pango markup string.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param text_size: Text size, default is DEFAULT_FONT_SIZE.
    @param text_color: Text color, default is \"#000000\".
    @param text_font: Text font, default is DEFAULT_FONT.
    @param alignment: Font alignment option, default is pango.ALIGN_LEFT. You can set pango.ALIGN_MIDDLE or pango.ALIGN_RIGHT.
    @param gaussian_radious: Gaussian radious, default is None.
    @param gaussian_color: Gaussian color, default is None.
    @param border_radious: Border radious, default is None.
    @param border_color: Border color, default is None.
    @param wrap_width: Wrap width of text, default is None.
    @param underline: Whether draw underline for text, default is False.
    @param vertical_alignment: Vertical alignment value, default is TEXT_ALIGN_MIDDLE, can use below value:
     - TEXT_ALIGN_TOP
     - TEXT_ALIGN_MIDDLE
     - TEXT_ALIGN_BOTTOM
    @param clip_line_count: The line number to clip text area, if set 2, all lines that above 2 will clip out, default is None.
    @param ellipsize: Ellipsize style of text when text width longer than draw area, it can use below value:
     - pango.ELLIPSIZE_START
     - pango.ELLIPSIZE_CENTER
     - pango.ELLIPSIZE_END
    '''
    if border_radious == None and border_color == None and gaussian_radious == None and gaussian_color == None:
        render_text(cr, markup, x, y, w, h, text_size, text_color, text_font, alignment,
                    wrap_width=wrap_width,
                    underline=underline,
                    vertical_alignment=vertical_alignment,
                    clip_line_count=clip_line_count,
                    ellipsize=ellipsize,
                    )
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
                        wrap_width=wrap_width,
                        underline=underline,
                        vertical_alignment=vertical_alignment,
                        clip_line_count=clip_line_count,
                        ellipsize=ellipsize,
                        )
            dtk_cairo_blur.gaussian_blur(surface, gaussian_radious)
            text_cr.restore()

        # Make sure border can render correctly.
        if gaussian_radious == None:
            gaussian_radious = 0

        # Draw gaussian border.
        if border_radious != None and border_radious != 0 and border_color != None:
            render_text(text_cr, markup, gaussian_radious, gaussian_radious, w - gaussian_radious * 2,
                        h - gaussian_radious * 2, text_size, border_color, alignment=alignment,
                        wrap_width=wrap_width,
                        underline=underline,
                        vertical_alignment=vertical_alignment,
                        clip_line_count=clip_line_count,
                        ellipsize=ellipsize,
                        )
            dtk_cairo_blur.gaussian_blur(surface, border_radious)

        # Draw font.
        render_text(text_cr, markup, gaussian_radious, gaussian_radious, w - gaussian_radious * 2,
                    h - gaussian_radious * 2, text_size, text_color, alignment=alignment,
                    wrap_width=wrap_width,
                    underline=underline,
                    vertical_alignment=vertical_alignment,
                    clip_line_count=clip_line_count,
                    ellipsize=ellipsize,
                    )

        # Render gaussian text to target cairo context.
        cr.set_source_surface(surface, x, y)
        cr.paint()

def render_text(cr, markup,
                x, y, w, h,
                text_size=DEFAULT_FONT_SIZE,
                text_color="#000000",
                text_font=DEFAULT_FONT,
                alignment=pango.ALIGN_LEFT,
                wrap_width=None,
                underline=False,
                vertical_alignment=TEXT_ALIGN_MIDDLE,
                clip_line_count=None,
                ellipsize=pango.ELLIPSIZE_END,
                ):
    '''
    Render text for function L{ I{draw_text} <draw_text>}, you can use this function individually.

    @param cr: Cairo context.
    @param markup: Pango markup string.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param text_size: Text size, default is DEFAULT_FONT_SIZE.
    @param text_color: Text color, default is \"#000000\".
    @param text_font: Text font, default is DEFAULT_FONT.
    @param alignment: Font alignment option, default is pango.ALIGN_LEFT. You can set pango.ALIGN_MIDDLE or pango.ALIGN_RIGHT.
    @param wrap_width: Wrap width of text, default is None.
    @param underline: Whether draw underline for text, default is False.
    @param vertical_alignment: Vertical alignment value, default is TEXT_ALIGN_MIDDLE, can use below value:
     - TEXT_ALIGN_TOP
     - TEXT_ALIGN_MIDDLE
     - TEXT_ALIGN_BOTTOM
    @param clip_line_count: The line number to clip text area, if set 2, all lines that above 2 will clip out, default is None.
    @param ellipsize: Ellipsize style of text when text width longer than draw area, it can use below value:
     - pango.ELLIPSIZE_START
     - pango.ELLIPSIZE_CENTER
     - pango.ELLIPSIZE_END
    '''
    with cairo_state(cr):
        # Set color.
        cr.set_source_rgb(*color_hex_to_cairo(text_color))

        # Create pangocairo context.
        context = pangocairo.CairoContext(cr)

        # Set layout.
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (text_font, text_size)))
        layout.set_markup(markup)
        layout.set_alignment(alignment)
        if wrap_width == None:
            layout.set_single_paragraph_mode(True)
            layout.set_width(w * pango.SCALE)
            layout.set_ellipsize(ellipsize)
        else:
            layout.set_width(wrap_width * pango.SCALE)
            layout.set_wrap(pango.WRAP_WORD)

        (text_width, text_height) = layout.get_pixel_size()

        if underline:
            if alignment == pango.ALIGN_LEFT:
                cr.rectangle(x, y + text_height + (h - text_height) / 2, text_width, 1)
            elif alignment == pango.ALIGN_CENTER:
                cr.rectangle(x + (w - text_width) / 2, y + text_height + (h - text_height) / 2, text_width, 1)
            else:
                cr.rectangle(x + w - text_width, y + text_height + (h - text_height) / 2, text_width, 1)
            cr.fill()

        # Set render y coordinate.
        if vertical_alignment == TEXT_ALIGN_TOP:
            render_y = y
        elif vertical_alignment == TEXT_ALIGN_MIDDLE:
            render_y = y + max(0, (h - text_height) / 2)
        else:
            render_y = y + max(0, h - text_height)

        # Clip area.
        if clip_line_count:
            line_count = layout.get_line_count()
            if line_count > 0:
                line_height = text_height / line_count
                cr.rectangle(x, render_y, text_width, line_height * clip_line_count)
                cr.clip()

        # Draw text.
        cr.move_to(x, render_y)
        context.update_layout(layout)
        context.show_layout(layout)

def draw_line(cr, sx, sy, ex, ey, line_width=1, antialias_status=cairo.ANTIALIAS_NONE):
    '''
    Draw line.

    @param cr: Cairo context.
    @param sx: Souce X coordinate.
    @param sy: Souce Y coordinate.
    @param ex: Target X coordinate.
    @param ey: Target Y coordinate.
    @param line_width: Line width, default is 1 pixel.
    @param antialias_status: Antialias status, default is cairo.ANTIALITAS_NONE.
    '''
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
    '''
    Draw linear area vertically.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param color_infos: A list of ColorInfo, ColorInfo format: (color_stop_position, (color_hex_value, color_alpha))
    @param radius: Rectangle corner radious.
    @param top_to_bottom: Draw direction, default is from top to bottom, function will draw from bottom to top if set option as False.
    '''
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
    '''
    Draw linear area horticulturally.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param color_infos: A list of ColorInfo, ColorInfo format: (color_stop_position, (color_hex_value, color_alpha))
    @param radius: Rectangle corner radious.
    @param left_to_right: Draw direction, default is from left to right, function will draw from right to left if set option as False.
    '''
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
    '''
    Expose linear background.

    @param widget: Gtk.Widget instance.
    @param event: Expose event.
    @param color_infos: A list of ColorInfo, ColorInfo format: (color_stop_position, (color_hex_value, color_alpha))
    '''
    # Init.
    cr = widget.window.cairo_create()
    rect = widget.allocation

    # Draw linear background.
    draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, color_infos)

    # Propagate expose.
    propagate_expose(widget, event)

    return True

def draw_shadow(cr, x, y, w, h, r, color_window_shadow):
    '''
    Draw window shadow.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param r: Radious of window shadow corner.
    @param color_window_shadow: theme.DyanmicShadowColor.
    '''
    color_infos = color_window_shadow.get_color_info()
    with cairo_state(cr):
        # Clip four corner.
        cr.rectangle(x, y, r, r)
        cr.rectangle(x + w - r, y, r, r)
        cr.rectangle(x, y + h - r, r, r)
        cr.rectangle(x + w - r, y + h - r, r, r)

        cr.clip()

        # Draw four round.
        draw_radial_round(cr, x + r, y + r, r, color_infos)
        draw_radial_round(cr, x + r, y + h - r, r, color_infos)
        draw_radial_round(cr, x + w - r, y + r, r, color_infos)
        draw_radial_round(cr, x + w - r, y + h - r, r, color_infos)

    with cairo_state(cr):
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

    # Fill inside.
    cr.set_source_rgba(*alpha_color_hex_to_cairo(color_infos[-1][1]))
    cr.rectangle(x + r, y + r, w - r * 2, h - r * 2)
    cr.fill()

def draw_window_shadow(cr, x, y, w, h, r, p, color_window_shadow):
    '''
    Draw window shadow.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param r: Radious of window shadow corner.
    @param p: Padding between window shadow and window frame.
    @param color_window_shadow: theme.DyanmicShadowColor.
    '''
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
    '''
    Draw radial round.

    @param cr: Cairo context.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param r: Radious of radial round.
    @param color_infos: A list of ColorInfo, ColorInfo format: (color_stop_position, (color_hex_value, color_alpha))
    '''
    radial = cairo.RadialGradient(x, y, r, x, y, 0)
    for (pos, color_info) in color_infos:
        add_color_stop_rgba(radial, pos, color_info)
    cr.arc(x, y, r, 0, 2 * math.pi)
    cr.set_source(radial)
    cr.fill()

def draw_blank_mask(cr, x, y, w, h):
    '''
    Draw blank mask, use for as class interfaces for default mask function.

    @param cr: Cairo context.
    @param x: X coordiante of rectangle area.
    @param y: Y coordiante of rectangle area.
    @param w: Width of rectangle area.
    @param h: Width of rectangle area.
    '''
    pass
