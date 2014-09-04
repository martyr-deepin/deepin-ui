#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from deepin_utils import core, file, process, ipc, date_time, net
from deepin_utils.core import merge_list
from contextlib import contextmanager
import cairo
import gobject
import gtk
import gio
import os
import pango
import pangocairo
import traceback
import sys
import time
from constant import (WIDGET_POS_TOP_LEFT, WIDGET_POS_TOP_RIGHT,
                      WIDGET_POS_TOP_CENTER, WIDGET_POS_BOTTOM_LEFT,
                      WIDGET_POS_BOTTOM_CENTER, WIDGET_POS_BOTTOM_RIGHT,
                      WIDGET_POS_LEFT_CENTER, WIDGET_POS_RIGHT_CENTER,
                      WIDGET_POS_CENTER, DEFAULT_FONT, COLOR_NAME_DICT,
                      BLACK_COLOR_MAPPED, WHITE_COLOR_MAPPED, SIMILAR_COLOR_SEQUENCE,
                      DEFAULT_FONT_SIZE)

def repeat(msg, num):
    return ' '.join([msg] * num)

def get_entry_text(entry):
    '''
    Get text of entry.

    @param entry: Gtk.Entry instance.
    @return: Return text of entry.
    '''
    return entry.get_text().split(" ")[0]

def set_cursor(cursor_widget, cursor_type=None):
    '''
    Set cursor type with given widget.

    @param cursor_widget: Gtk.Widget or Gdk.Window instance.
    @param cursor_type: The cursor type of gtk.gdk.Cursor, please set with None if you want reset widget's cursor as default.
    @return: Always return False
    '''
    if isinstance(cursor_widget, gtk.Widget):
        cursor_window = cursor_widget.window
    elif isinstance(cursor_widget, gtk.gdk.Window):
        cursor_window = cursor_widget
    else:
        print "set_cursor: impossible!"

    if cursor_type == None:
        cursor_window.set_cursor(None)
    else:
        cursor_window.set_cursor(gtk.gdk.Cursor(cursor_type))

    return False

def set_clickable_cursor(widget):
    '''
    Show gtk.gdk.HAND2 cursor when mouse hover widget.

    @param widget: Gtk.Widget instance.
    '''
    set_hover_cursor(widget, gtk.gdk.HAND2)

def set_hover_cursor(widget, cursor_type):
    '''
    Set cursor type when mouse hover widget.

    @param widget: Gtk.Widget instance.
    @param cursor_type: The cursor type of gtk.gdk.Cursor.
    '''
    widget.connect("enter-notify-event", lambda w, e: set_cursor(w, cursor_type))
    widget.connect("leave-notify-event", lambda w, e: set_cursor(w))

def get_widget_root_coordinate(widget, pos_type=WIDGET_POS_BOTTOM_CENTER, translate_coordinate=True):
    '''
    Get root coordinate with given widget.

    @param widget: Gtk.Widget instance.
    @param pos_type: The position of widget's area, you can set with below constants:
     - WIDGET_POS_TOP_LEFT
     - WIDGET_POS_TOP_RIGHT
     - WIDGET_POS_TOP_CENTER
     - WIDGET_POS_BOTTOM_LEFT
     - WIDGET_POS_BOTTOM_RIGHT
     - WIDGET_POS_BOTTOM_CENTER
     - WIDGET_POS_LEFT_CENTER
     - WIDGET_POS_RIGHT_CENTER
     - WIDGET_POS_CENTER
    @return: Return (x, y) as root coordination.
    '''
    # Get coordinate.
    (wx, wy) = widget.window.get_origin()
    toplevel_window = widget.get_toplevel()
    if translate_coordinate and toplevel_window:
        '''
        FIXME: translate_coordinates wrong toward ComboBox
        '''
        (x, y) = widget.translate_coordinates(toplevel_window, wx, wy)
    else:
        (x, y) = (wx, wy)

    # Get offset.
    rect = widget.allocation
    if pos_type == WIDGET_POS_TOP_LEFT:
        offset_x = 0
        offset_y = 0
    elif pos_type == WIDGET_POS_TOP_RIGHT:
        offset_x = rect.width
        offset_y = 0
    elif pos_type == WIDGET_POS_TOP_CENTER:
        offset_x = rect.width / 2
        offset_y = 0
    elif pos_type == WIDGET_POS_BOTTOM_LEFT:
        offset_x = 0
        offset_y = rect.height
    elif pos_type == WIDGET_POS_BOTTOM_RIGHT:
        offset_x = rect.width
        offset_y = rect.height
    elif pos_type == WIDGET_POS_BOTTOM_CENTER:
        offset_x = rect.width / 2
        offset_y = rect.height
    elif pos_type == WIDGET_POS_LEFT_CENTER:
        offset_x = 0
        offset_y = rect.height / 2
    elif pos_type == WIDGET_POS_RIGHT_CENTER:
        offset_x = rect.width
        offset_y = rect.height / 2
    elif pos_type == WIDGET_POS_CENTER:
        offset_x = rect.width / 2
        offset_y = rect.height / 2

    return (x + offset_x, y + offset_y)

def get_event_root_coords(event):
    '''
    Get root coordinate with given event.

    @param event: Gdk.Event instance, general, we get event instance from gtk signal callback.
    @return: Return (x, y) as event's root coordination.
    '''
    (rx, ry) = event.get_root_coords()
    return (int(rx), int(ry))

def get_event_coords(event):
    '''
    Get coordinate with given event.

    @param event: Gdk.Event instance, general, we get event instance from gtk signal callback.
    @return: Return (x, y) as event's coordination.
    '''
    (rx, ry) = event.get_coords()
    return (int(rx), int(ry))

def propagate_expose(widget, event):
    '''
    Propagate expose to children.

    General, this function use at last position of `expose_event` callback to make child redraw after parent widget.

    And you must put \"return True\" after \"propagate_expose(widget, event)\".

    Example:

    >>> def expose_event_callback(widget, event):
    >>>     # Do something.
    >>>
    >>>     propagate_expose(widget, event)
    >>>     return True

    @param widget: Gtk.Container instance.

    This function do nothing if widget is not Gtk.Container instance or haven't any child widget.

    @param event: Gdk.Event instance.
    '''
    if hasattr(widget, "get_child") and widget.get_child() != None:
        widget.propagate_expose(widget.get_child(), event)

def move_window(widget, event, window):
    '''
    Move window with given widget and event.

    This function generic use for move window when mouse drag on target widget.

    @param widget: Gtk.Widget instance to drag.
    @param event: Gdk.Event instance, generic, event come from gtk signal callback.
    @param window: Gtk.Window instance.
    '''
    if is_left_button(event):
        widget.set_can_focus(True)
        widget.grab_focus()
        window.begin_move_drag(
            event.button,
            int(event.x_root),
            int(event.y_root),
            event.time)

    return False

def resize_window(widget, event, window, edge):
    '''
    Resize window with given widget and event.

    This function generic use for resize window when mouse drag on target widget.

    @param widget: Gtk.Widget instance to drag.
    @param event: Gdk.Event instance, generic, event come from gtk signal callback.
    @param window: Gtk.Window instance.
    '''
    if is_left_button(event):
        window.begin_resize_drag(
            edge,
            event.button,
            int(event.x_root),
            int(event.y_root),
            event.time)

    return False

def add_in_scrolled_window(scrolled_window, widget, shadow_type=gtk.SHADOW_NONE):
    '''
    Add widget in scrolled_window.

    Wrap function `add_with_viewport` with shadow type of Gtk.Viewport.

    @param scrolled_window: Gtk.ScrolledWindow instance.
    @param widget: Gtk.Widget instance.
    @param shadow_type: Shadow type of Viewport, default is gtk.SHADOW_NONE.
    '''
    scrolled_window.add_with_viewport(widget)
    viewport = scrolled_window.get_child()
    if viewport != None:
        viewport.set_shadow_type(shadow_type)
    else:
        print "add_in_scrolled_window: Impossible, no viewport widget in ScrolledWindow!"

def is_single_click(event):
    '''
    Whether an event is single click event.

    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is single click event.
    '''
    return event.button == 1 and event.type == gtk.gdk.BUTTON_PRESS

def is_double_click(event):
    '''
    Whether an event is double click event.

    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is double click event.
    '''
    return event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS

def is_left_button(event):
    '''
    Whether event is left button event.

    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is left button event.
    '''
    return event.button == 1

def is_right_button(event):
    '''
    Whether event is right button event.

    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is right button event.
    '''
    return event.button == 3

def is_middle_button(event):
    '''
    Whether event is middle button event.

    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is middle button event.
    '''
    return event.button == 2

def foreach_container(widget, callback):
    '''
    Make callback call for all children of widget.

    @param widget: Gtk.Container instance.
    @param callback: Callback.
    '''
    callback(widget)

    if isinstance(widget, gtk.Container):
        foreach_recursive(widget, callback)

def foreach_recursive(container, callback):
    '''
    Helper function for L{ I{foreach_container} <foreach_container>}.

    @param container: Gtk.Container instance.
    @param callback: Callback.
    '''
    container.foreach(lambda w: foreach_container(w, callback))

def container_remove_all(container):
    '''
    Handy function to remove all children widget from container.

    @param container: Gtk.Container instance.
    '''
    container.foreach(lambda widget: container.remove(widget))

def get_screen_size(widget):
    '''
    Get screen size from the toplevel window associated with widget.

    @param widget: Gtk.Widget instance.
    @return: Return screen size as (screen_width, screen_height)

    '''
    screen = widget.get_screen()
    width = screen.get_width()
    height = screen.get_height()
    return (width, height)

def is_in_rect((tx, ty), rect):
    '''
    Whether target coordinate in given rectangle.

    @param tx: Target x coordinate.
    @param ty: Target y coordinate.
    @param rect: The rectangle to test.
    @return: Return True if target coordinate in given rectangle.
    '''
    if isinstance(rect, gtk.gdk.Rectangle):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
    else:
        x, y, w, h = rect

    return (tx >= x and tx <= x + w and ty >= y and ty <= y + h)

def scroll_to_top(scrolled_window):
    '''
    Scroll scrolled_window to top position.

    @param scrolled_window: Gtk.ScrolledWindow instance.
    '''
    scrolled_window.get_vadjustment().set_value(0)

def scroll_to_bottom(scrolled_window):
    '''
    Scroll scrolled_window to bottom position.

    @param scrolled_window: Gtk.ScrolledWindow instance.
    '''
    vadjust = scrolled_window.get_vadjustment()
    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

def get_content_size(text, text_size=DEFAULT_FONT_SIZE, text_font=DEFAULT_FONT, wrap_width=None):
    '''
    Get text size, in pixel.

    @param text: String or markup string.
    @param text_size: Text size, in pixel.
    @param text_font: Text font.
    @param wrap_width: The width of wrap rule, default don't wrap.
    @return: Return text size as (text_width, text_height), return (0, 0) if occur error.
    '''
    if text:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0) # don't need give size
        cr = cairo.Context(surface)
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (text_font, text_size)))
        layout.set_markup(text)
        if wrap_width == None:
            layout.set_single_paragraph_mode(True)
        else:
            layout.set_width(wrap_width * pango.SCALE)
            layout.set_single_paragraph_mode(False)
            layout.set_wrap(pango.WRAP_WORD)

        return layout.get_pixel_size()
    else:
        return (0, 0)

def get_os_version():
    '''
    Get OS version with command `lsb_release -i`.

    @return: Return OS version string.
    '''
    version_infos = get_command_output_first_line(["lsb_release", "-i"]).split()

    if len(version_infos) > 0:
        return version_infos[-1]
    else:
        return ""

def print_env():
    '''
    Print environment variable.
    '''
    for param in os.environ.keys():
        print "*** %20s %s" % (param,os.environ[param])

def get_font_families():
    '''
    Get all font families in system.

    @return: Return font families list in current system.
    '''
    fontmap = pangocairo.cairo_font_map_get_default()
    return map (lambda f: f.get_name(), fontmap.list_families())

def add_color_stop_rgba(pat, pos, color_info):
    '''
    Add color stop as rgba format.

    @param pat: Pattern.
    @param pos: Stop position.
    @param color_info: (color, alpha), color is hex value, alpha value range: [0, 1]
    '''
    # Pick color.
    (color, alpha) = color_info
    (r, g, b) = color_hex_to_cairo(color)

    pat.add_color_stop_rgba(pos, r, g, b, alpha)

def alpha_color_hex_to_cairo((color, alpha)):
    '''
    Convert alpha color (color, alpha) to cairo color (r, g, b, alpha).

    @param color: Hex color.
    @param alpha: Alpha value.
    @return: Return cairo value (red, green, blue, alpha).
    '''
    (r, g, b) = color_hex_to_cairo(color)
    return (r, g, b, alpha)

def color_hex_to_rgb(color):
    '''
    Convert hex color to cairo color (r, g, b).

    @param color: Hex color value.
    @return: Return cairo value, (red, green, blue)
    '''
    if color[0] == '#':
        color = color[1:]
    return (int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16))

def color_hex_to_cairo(color):
    '''
    Convert a HTML (hex) RGB value to cairo color.

    @param color: The color to convert.
    @return: A color in cairo format, (red, green, blue).
    '''
    gdk_color = gtk.gdk.color_parse(color)
    return (gdk_color.red / 65535.0, gdk_color.green / 65535.0, gdk_color.blue / 65535.0)

def color_rgb_to_hex(rgb_color):
    '''
    Convert cairo color to hex color.

    @param rgb_color: (red, green, blue)
    @return: Return hex color.
    '''
    return "#%02X%02X%02X" % rgb_color

def color_rgb_to_cairo(color):
    '''
    Convert a 8 bit RGB value to cairo color.

    @type color: a triple of integers between 0 and 255
    @param color: The color to convert.
    @return: A color in cairo format.
    '''
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

def get_match_parent(widget, match_types):
    '''
    Get parent widget match given type.

    @param widget: Gtk.Widget instance.
    @param match_types: A list gtk widget types.
    @return: Return first parent widget match with given types.

    Return None if nothing match.
    '''
    parent = widget.get_parent()
    if parent == None:
        return None
    elif type(parent).__name__ in match_types:
        return parent
    else:
        return get_match_parent(parent, match_types)

def get_match_children(widget, child_type):
    '''
    Get all child widgets that match given widget type.

    @param widget: The container to search.
    @param child_type: The widget type of search.

    @return: Return all child widgets that match given widget type, or return empty list if nothing to find.
    '''
    child_list = widget.get_children()
    if child_list:
        match_widget_list = filter(lambda w: isinstance(w, child_type), child_list)
        match_children = (merge_list(map(
                    lambda w: get_match_children(w, child_type),
                    filter(
                        lambda w: isinstance(w, gtk.Container),
                        child_list))))
        return match_widget_list + match_children
    else:
        return []

def widget_fix_cycle_destroy_bug(widget):
    '''
    Fix bug that PyGtk destroys cycle too early.

    @param widget: Gtk.Widget instance.
    '''
    # This code to fix PyGtk bug <<Pygtk destroys cycle too early>>,
    # The cycle is wrongly freed
    # by Python's GC because Pygobject does not tell Python that the widget's
    # wrapper object is referenced by the underlying GObject.  As you have
    # found, in order to break the cycle Python zeros out the callback
    # closure's captured free variables, which is what causes the "referenced
    # before assignment" exception.
    # detail see: https://bugzilla.gnome.org/show_bug.cgi?id=546802 .
    #
    # Otherwise, will got error : "NameError: free variable 'self' referenced before assignment in enclosing scope".
    widget.__dict__

def get_same_level_widgets(widget):
    '''
    Get same type widgets that in same hierarchy level.

    @param widget: Gtk.Widget instance to search.
    @return: Return a list that type match given widget at same hierarchy level.
    '''
    parent = widget.get_parent()
    if parent == None:
        return []
    else:
        return filter(lambda w:type(w).__name__ == type(widget).__name__, parent.get_children())

def window_is_max(widget):
    '''
    Whether window is maximized.

    @param widget: Gtk.Widget instance.
    @return: Return True if widget's toplevel window is maximized.
    '''
    toplevel_window = widget.get_toplevel()
    if toplevel_window.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED:
        return True
    else:
        return False

@contextmanager
def cairo_state(cr):
    '''
    Protected cairo context state for operate cairo safety.

    @param cr: Cairo context.
    '''
    cr.save()
    try:
        yield
    except Exception, e:
        print 'function cairo_state got error: %s' % e
        traceback.print_exc(file=sys.stdout)
    else:
        cr.restore()

@contextmanager
def cairo_disable_antialias(cr):
    '''
    Disable cairo antialias temporary.

    @param cr: Cairo context.
    '''
    # Save antialias.
    antialias = cr.get_antialias()

    cr.set_antialias(cairo.ANTIALIAS_NONE)
    try:
        yield
    except Exception, e:
        print 'function cairo_disable_antialias got error: %s' % e
        traceback.print_exc(file=sys.stdout)
    else:
        # Restore antialias.
        cr.set_antialias(antialias)

def remove_timeout_id(callback_id):
    '''
    Remove callback id.

    @param callback_id: Callback id.
    '''
    if callback_id:
        gobject.source_remove(callback_id)
        callback_id = None

def remove_signal_id(signal_id):
    '''
    Remove signal id.

    @param signal_id: Signal id that return by function gobject.connect.
    '''
    if signal_id:
        (signal_object, signal_handler_id) = signal_id
        if signal_object.handler_is_connected(signal_handler_id):
            signal_object.disconnect(signal_handler_id)
        signal_id = None

def print_callback_args(*args):
    '''
    Print callback arguments.

    Usage:

    >>> some_widget.connect(\"signal\", print_callback_args)
    '''
    print "Print callback argument: %s" % (args)

def enable_shadow(widget):
    '''
    Whether widget is support composited.

    @param widget: Gtk.Widget instance.
    @return: Return True if widget is support composited.
    '''
    return widget.is_composited()

def rgb2hsb(r_value, g_value, b_value):
    '''
    Convert color from RGB to HSB format.

    @param r_value: Red.
    @param g_value: Green.
    @param b_value: Blue.
    @return: Return color with HSB (h, s, b) format.
    '''
    r = r_value
    g = g_value
    b = b_value

    max_v = max(r, g, b)
    min_v = min(r, g, b)

    h = 0.0

    if max_v == min_v:
        h = 0
    elif max_v == r and g >= b:
        h = 60 * (g - b) / (max_v - min_v)
    elif max_v == r and g < b:
        h = 60 * (g - b) / (max_v - min_v) + 360
    elif max_v == g:
        h = 60 * (b - r) / (max_v - min_v) + 120
    elif max_v == b:
        h = 60 * (r - g) / (max_v - min_v) + 240

    if max_v == 0:
        s = 0.0
    else:
        s = 1.0 - min_v / max_v

    b = max_v

    return (h, s, b)

def find_similar_color(search_color):
    '''
    Find similar color match search_color.

    @param search_color: Color to search.
    @return: Return similar color name and value, (color_name, color_value).
    '''
    (search_h, search_s, search_b) = rgb2hsb(*color_hex_to_cairo(search_color))
    hsb_colors = map(lambda name: (name, rgb2hsb(*color_hex_to_cairo(COLOR_NAME_DICT[name]))), SIMILAR_COLOR_SEQUENCE)

    # Debug.
    # print (search_h, search_s, search_b)

    similar_color_name = None
    similar_color_value = None
    # Return black color if brightness (height) < 0.35
    if search_b < 0.35:
        similar_color_name = BLACK_COLOR_MAPPED
    # Return white color if saturation (radius) < 0.05
    elif search_s < 0.05:
        similar_color_name = WHITE_COLOR_MAPPED
    # Otherwise find nearest color in hsb color space.
    else:
        min_color_distance = None
        for (color_name, (h, s, b)) in hsb_colors:
            color_distance = abs(h - search_h)
            if min_color_distance == None or color_distance < min_color_distance:
                min_color_distance = color_distance
                similar_color_name = color_name

    similar_color_value = COLOR_NAME_DICT[similar_color_name]
    return (similar_color_name, similar_color_value)

def place_center(refer_window, place_window):
    '''
    Place place_window in center of refer_window.

    @param refer_window: Reference window.
    @param place_window: Place window.
    '''
    self_size = place_window.get_size()
    refer_window_pos = refer_window.get_position()
    refer_window_rect = refer_window.get_allocation()
    place_window.move(
        (refer_window_pos[0] + refer_window_rect.width / 2) - (self_size[0] / 2),
        (refer_window_pos[1] + refer_window_rect.height / 2) - (self_size[1] / 2))

def get_system_icon_info(icon_theme="Deepin", icon_name="NULL", size=48):
    '''
    Get system level icon info

    @param icon_theme: Gtk Icon Theme, for example, Deepin
    @param icon_name: the name of the icon to lookup, for example, preferences-power
    @param size: desired icon size, for example, 48
    '''
    __icon_theme = gtk.IconTheme()
    __icon_theme.set_custom_theme(icon_theme)
    return __icon_theme.lookup_icon(icon_name, size, gtk.ICON_LOOKUP_NO_SVG)

def get_pixbuf_support_formats():
    '''
    Get formats that support by pixbuf.

    @return: Return formats that support by pixbuf.
    '''
    support_formats = []
    for support_format in gtk.gdk.pixbuf_get_formats():
        support_formats += support_format.get("extensions")

    return support_formats

def gdkcolor_to_string(gdkcolor):
    '''
    Gdk color to string.

    @param gdkcolor: Gdk.Color
    @return: Return string of gdk color.
    '''
    return "#%0.2X%0.2X%0.2X" % (gdkcolor.red / 256, gdkcolor.green / 256, gdkcolor.blue / 256)

def get_window_shadow_size(window):
    '''
    Get window shadow size.

    @param window: Test window.
    @return: Return shadow size as (width, height), or return (0, 0) if window haven't shadow.
    '''
    if hasattr(window, "get_shadow_size"):
        return window.get_shadow_size()
    else:
        return (0, 0)

def get_resize_pixbuf_with_height(filepath, expect_height):
    pixbuf = gtk.gdk.pixbuf_new_from_file(filepath)
    if pixbuf.get_height() > expect_height:
        return pixbuf.scale_simple(
            int(float(expect_height) / pixbuf.get_height() * pixbuf.get_width()),
            expect_height,
            gtk.gdk.INTERP_BILINEAR)
    else:
        return pixbuf

def get_optimum_pixbuf_from_pixbuf(pixbuf, expect_width, expect_height, cut_middle_area=True):
    pixbuf_width, pixbuf_height = pixbuf.get_width(), pixbuf.get_height()
    if pixbuf_width >= expect_width and pixbuf_height >= expect_height:
        if float(pixbuf_width) / pixbuf_height == float(expect_width) / expect_height:
            scale_width, scale_height = expect_width, expect_height
        elif float(pixbuf_width) / pixbuf_height > float(expect_width) / expect_height:
            scale_height = expect_height
            scale_width = int(float(pixbuf_width) * expect_height / pixbuf_height)
        else:
            scale_width = expect_width
            scale_height = int(float(pixbuf_height) * expect_width / pixbuf_width)

        if cut_middle_area:
            subpixbuf_x = (scale_width - expect_width) / 2
            subpixbuf_y = (scale_height - expect_height) / 2
        else:
            subpixbuf_x = 0
            subpixbuf_y = 0

        return pixbuf.scale_simple(
            scale_width,
            scale_height,
            gtk.gdk.INTERP_BILINEAR).subpixbuf(subpixbuf_x,
                                               subpixbuf_y,
                                               expect_width,
                                               expect_height)
    elif pixbuf_width >= expect_width:
        scale_width = expect_width
        scale_height = int(float(expect_width) * pixbuf_height / pixbuf_width)

        if cut_middle_area:
            subpixbuf_x = (scale_width - expect_width) / 2
            subpixbuf_y = max((scale_height - expect_height) / 2, 0)
        else:
            subpixbuf_x = 0
            subpixbuf_y = 0

        return pixbuf.scale_simple(
            scale_width,
            scale_height,
            gtk.gdk.INTERP_BILINEAR).subpixbuf(subpixbuf_x,
                                               subpixbuf_y,
                                               expect_width,
                                               min(expect_height, scale_height))
    elif pixbuf_height >= expect_height:
        scale_width = int(float(expect_height) * pixbuf_width / pixbuf_height)
        scale_height = expect_height

        if cut_middle_area:
            subpixbuf_x = max((scale_width - expect_width) / 2, 0)
            subpixbuf_y = (scale_height - expect_height) / 2
        else:
            subpixbuf_x = 0
            subpixbuf_y = 0

        return pixbuf.scale_simple(
            scale_width,
            scale_height,
            gtk.gdk.INTERP_BILINEAR).subpixbuf(subpixbuf_x,
                                               subpixbuf_y,
                                               min(expect_width, scale_width),
                                               expect_height)
    else:
        return pixbuf

def get_optimum_pixbuf_from_file(filepath, expect_width, expect_height, cut_middle_area=True):
    '''
    Get optimum size pixbuf from file.

    @param filepath: Filepath to contain image.
    @param expect_width: Expect width.
    @param expect_height: Expect height.
    @param cut_middle_area: Default cut image with middle area.
    @return: Return optimum size pixbuf with expect size.
    '''
    pixbuf = gtk.gdk.pixbuf_new_from_file(filepath)
    return get_optimum_pixbuf_from_pixbuf(pixbuf, expect_width, expect_height, cut_middle_area)

def unique_print(text):
    '''
    Unique print, generic for test code.

    @param text: Test text.
    '''
    print "%s: %s" % (time.time(), text)

def invisible_window(window):
    '''
    Make window invisible.

    We use this function for global event that to hide event window.
    '''
    def shape_window(widget, rect):
        w, h = rect.width, rect.height
        bitmap = gtk.gdk.Pixmap(None, w, h, 1)
        cr = bitmap.cairo_create()

        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()

        widget.shape_combine_mask(bitmap, 0, 0)

    window.move(-10, -10)
    window.set_default_size(0, 0)
    window.set_decorated(False)
    window.connect("size-allocate", shape_window)

def split_with(split_list, condition_func):
    print "Please import deepin_utils.core.split_with, this function will departed in next release version."
    return core.split_with(split_list, condition_func)

def create_directory(directory, remove_first=False):
    print "Please import deepin_utils.file.create_directory, this function will departed in next release version."
    return file.create_directory(directory, remove_first=False)

def remove_file(path):
    print "Please import deepin_utils.file.remove_file, this function will departed in next release version."
    return file.remove_file(path)

def remove_directory(path):
    print "Please import deepin_utils.file.remove_directory, this function will departed in next release version."
    return file.remove_directory(path)

def touch_file(filepath):
    print "Please import deepin_utils.file.touch_file, this function will departed in next release version."
    return file.touch_file(filepath)

def touch_file_dir(filepath):
    print "Please import deepin_utils.file.touch_file_dir, this function will departed in next release version."
    return file.touch_file_dir(filepath)

def read_file(filepath, check_exists=False):
    print "Please import deepin_utils.file.read_file, this function will departed in next release version."
    return file.read_file(filepath, check_exists=False)

def read_first_line(filepath, check_exists=False):
    print "Please import deepin_utils.file.read_first_line, this function will departed in next release version."
    return file.read_first_line(filepath, check_exists=False)

def eval_file(filepath, check_exists=False):
    print "Please import deepin_utils.file.eval_file, this function will departed in next release version."
    return file.eval_file(filepath, check_exists=False)

def write_file(filepath, content, mkdir=False):
    print "Please import deepin_utils.file.write_file, this function will departed in next release version."
    return file.write_file(filepath, content, mkdir=False)

def kill_process(proc):
    print "Please import deepin_utils.process.kill_process, this function will departed in next release version."
    return process.kill_process(proc)

def get_command_output_first_line(commands, in_shell=False):
    print "Please import deepin_utils.process.get_command_output_first_line, this function will departed in next release version."
    return process.get_command_output_first_line(commands, in_shell=False)

def get_command_output(commands, in_shell=False):
    print "Please import deepin_utils.process.get_command_output, this function will departed in next release version."
    return process.get_command_output(commands, in_shell=False)

def run_command(command):
    print "Please import deepin_utils.process.run_command, this function will departed in next release version."
    return process.run_command(command)

def get_current_time(time_format="%Y-%m-%d %H:%M:%S"):
    print "Please import deepin_utils.date_time.get_current_time, this function will departed in next release version."
    return date_time.get_current_time(time_format="%Y-%m-%d %H:%M:%S")

def add_in_list(e_list, element):
    print "Please import deepin_utils.core.add_in_list, this function will departed in next release version."
    return core.add_in_list(e_list, element)

def remove_from_list(e_list, element):
    print "Please import deepin_utils.core.remove_from_list, this function will departed in next release version."
    return core.remove_from_list(e_list, element)

def get_dir_size(dirname):
    print "Please import deepin_utils.file.get_dir_size, this function will departed in next release version."
    return file.get_dir_size(dirname)

def print_exec_time(func):
    print "Please import deepin_utils.date_time.print_exec_time, this function will departed in next release version."
    return date_time.print_exec_time(func)

def format_file_size(bytes, precision=2):
    print "Please import deepin_utils.file.format_file_size, this function will departed in next release version."
    return file.format_file_size(bytes, precision=2)

def map_value(value_list, get_value_callback):
    print "Please import deepin_utils.core.map_value, this function will departed in next release version."
    return core.map_value(value_list, get_value_callback)

def mix_list_max(list_a, list_b):
    print "Please import deepin_utils.core.mix_list_max, this function will departed in next release version."
    return core.mix_list_max(list_a, list_b)

def unzip(unzip_list):
    print "Please import deepin_utils.core.unzip, this function will departed in next release version."
    return core.unzip(unzip_list)

def is_seriate_list(test_list):
    print "Please import deepin_utils.core.is_seriate_list, this function will departed in next release version."
    return core.is_seriate_list(test_list)

def get_disperse_index(disperse_list, value):
    print "Please import deepin_utils.core.get_disperse_index, this function will departed in next release version."
    return core.get_disperse_index(disperse_list, value)

def last_index(test_list):
    print "Please import deepin_utils.core.last_index, this function will departed in next release version."
    return core.last_index(test_list)

def end_with_suffixs(filepath, suffixs):
    print "Please import deepin_utils.file.end_with_suffixs, this function will departed in next release version."
    return file.end_with_suffixs(filepath, suffixs)

def get_current_dir(filepath):
    print "Please import deepin_utils.file.get_current_dir, this function will departed in next release version."
    return file.get_current_dir(filepath)

def get_parent_dir(filepath, level=1):
    print "Please import deepin_utils.file.get_parent_dir, this function will departed in next release version."
    return file.get_parent_dir(filepath, level)

def is_long(string):
    print "Please import deepin_utils.core.is_long, this function will departed in next release version."
    return core.is_long(string)

def is_int(string):
    print "Please import deepin_utils.core.is_int, this function will departed in next release version."
    return core.is_int(string)

def is_float(string):
    print "Please import deepin_utils.core.is_float, this function will departed in next release version."
    return core.is_float(string)

def is_hex_color(string):
    print "Please import deepin_utils.core.is_hex_color, this function will departed in next release version."
    return core.is_hex_color(string)

def check_connect_by_port(port, retry_times=6, sleep_time=0.5):
    print "Please import deepin_utils.net.check_connect_by_port, this function will departed in next release version."
    return net.check_connect_by_port(port, retry_times=6, sleep_time=0.5)

def is_network_connected():
    print "Please import deepin_utils.net.is_network_connected, this function will departed in next release version."
    return net.is_network_connected()

def is_dbus_name_exists(dbus_name, request_session_bus=True):
    print "Please import deepin_utils.ipc.is_dbus_name_exists, this function will departed in next release version."
    return ipc.is_dbus_name_exists(dbus_name, request_session_bus=True)

def get_unused_port(address="localhost"):
    print "Please import deepin_utils.net.get_unused_port, this function will departed in next release version."
    return net.get_unused_port(address="localhost")

def file_is_image(file, filter_type=get_pixbuf_support_formats()):
    gfile = gio.File(file)
    try:
        fileinfo = gfile.query_info('standard::type,standard::content-type')
        file_type = fileinfo.get_file_type()
        if file_type == gio.FILE_TYPE_REGULAR:
            content_type = fileinfo.get_attribute_as_string("standard::content-type")
            split_content = content_type.split("/")
            if len(split_content) == 2:
                if split_content[0] == "image" and split_content[1] in filter_type:
                    file_path = gfile.get_path()
                    if not file_path.endswith(".part"):
                        return True
    except:
        pass

    return False
