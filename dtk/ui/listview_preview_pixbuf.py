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

from utils import get_content_size
import cairo
import gtk
import pango
import sys

# Below import must at end, otherwise will got ImportError
from draw import draw_vlinear, draw_text

def render_pixbuf(widget, event, input_args):
    '''
    Render and save pixbuf.

    @param widget: Gtk.Widget instance.
    @param event: Expose event.
    @param input_args: Input arguments as format: (select_num, vlinear_color, text_color, filepath).
    '''
    # Init.
    (select_num, vlinear_color, text_color, filepath) = input_args

    cr = widget.window.cairo_create()
    rect = widget.allocation
    num_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, rect.width, rect.height)

    # Draw background.
    cr.set_operator(cairo.OPERATOR_OVER)
    draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, eval(vlinear_color))

    # Draw text.
    draw_text(cr, select_num, rect.x, rect.y, rect.width, rect.height, text_color=text_color,
              alignment=pango.ALIGN_CENTER)

    # Render pixbuf from drawing area.
    num_pixbuf.get_from_drawable(
        widget.window, widget.get_colormap(), 0, 0, 0, 0,
        rect.width, rect.height).save(filepath, "png")

    # Exit after generate png file.
    gtk.main_quit()

if __name__ == "__main__":
    # Get input arguments.
    input_args = sys.argv[1::]
    (select_num, vlinear_color, text_color, filepath) = input_args

    # Init.
    num_padding_x = 8
    num_padding_y = 1
    (num_width, num_height) = get_content_size(select_num)
    pixbuf_width = num_width + num_padding_x * 2
    pixbuf_height = num_height + num_padding_y * 2

    # Create window.
    window = gtk.Window(gtk.WINDOW_POPUP)
    window.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
    window.move(-pixbuf_width, -pixbuf_height) # move out of screen
    window.set_default_size(pixbuf_width, pixbuf_height)
    window.connect(
        "expose-event",
        lambda w, e: render_pixbuf(w, e, input_args))

    window.show_all()

    gtk.main()
