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

from iconview import IconView
from listview import ListView
from scrolled_window import ScrolledWindow
from utils import cairo_state, get_match_parent, get_window_shadow_size
from window import Window

def draw_mask(widget, x, y, w, h, render_callback):
    '''
    Draw mask with given render method.

    @param widget: Target widget.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param render_callback: Render callback.
    '''
    if isinstance(widget, Window):
        draw_window_mask(widget, x, y, w, h, render_callback)
    elif isinstance(widget, ScrolledWindow):
        draw_scrolled_window_mask(widget, x, y, w, h, render_callback)
    elif isinstance(widget, IconView):
        draw_icon_view_mask(widget, x, y, w, h, render_callback)
    elif isinstance(widget, ListView):
        draw_list_view_mask(widget, x, y, w, h, render_callback)
    else:
        print "draw_mask: unsupport widget: %s" % (widget)

def draw_window_mask(widget, x, y, w, h, render_callback):
    '''
    Draw window mask with given render method.

    @param widget: Target widget.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param render_callback: Render callback.
    '''
    # Init.
    cr = widget.window.cairo_create()

    with cairo_state(cr):
        cr.rectangle(x + 1, y, w - 2, 1)
        cr.rectangle(x, y + 1, w, h - 2)
        cr.rectangle(x + 1, y + h - 1, w - 2, 1)
        cr.clip()

        render_callback(cr, x, y, w, h)

def draw_scrolled_window_mask(widget, x, y, w, h, render_callback):
    '''
    Draw scrolled window mask with given render method.

    @param widget: Target widget.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param render_callback: Render callback.
    '''
    # Init.
    cr = widget.window.cairo_create()
    toplevel = widget.get_toplevel()
    (offset_x, offset_y) = widget.translate_coordinates(toplevel, 0, 0)

    with cairo_state(cr):
        cr.rectangle(x, y, w, h)
        cr.clip()

        render_callback(
            cr,
            x - offset_x,
            y - offset_y,
            toplevel.allocation.width,
            toplevel.allocation.height)

def draw_icon_view_mask(widget, x, y, w, h, render_callback):
    '''
    Draw icon view mask with given render method.

    @param widget: Target widget.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param render_callback: Render callback.
    '''
    cr = widget.window.cairo_create()
    viewport = get_match_parent(widget, ["Viewport"])
    toplevel = widget.get_toplevel()
    (offset_x, offset_y) = viewport.translate_coordinates(toplevel, 0, 0)
    (shadow_x, shadow_y) = get_window_shadow_size(toplevel)

    with cairo_state(cr):
        cr.rectangle(x, y, w, h)
        cr.clip()

        render_callback(
            cr,
            x - offset_x + shadow_x,
            y - offset_y + shadow_y,
            toplevel.allocation.width,
            toplevel.allocation.height)

def draw_list_view_mask(widget, x, y, w, h, render_callback):
    '''
    Draw list view mask with given render method.

    @param widget: Target widget.
    @param x: X coordinate of draw area.
    @param y: Y coordinate of draw area.
    @param w: Width of draw area.
    @param h: Height of draw area.
    @param render_callback: Render callback.
    '''
    cr = widget.window.cairo_create()
    viewport = get_match_parent(widget, ["Viewport"])
    toplevel = widget.get_toplevel()
    (offset_x, offset_y) = viewport.translate_coordinates(toplevel, 0, 0)
    (shadow_x, shadow_y) = get_window_shadow_size(toplevel)

    with cairo_state(cr):
        cr.rectangle(x, y, w, h)
        cr.clip()

        render_callback(
            cr,
            x - offset_x + shadow_x,
            y - offset_y + shadow_y,
            toplevel.allocation.width,
            toplevel.allocation.height)
