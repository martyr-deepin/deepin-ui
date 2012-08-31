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

from contextlib import contextmanager 
import cairo
import gobject
import gtk
import math
import os
import pango
import pangocairo
import socket
import subprocess
import time
import traceback
import sys
from constant import (WIDGET_POS_TOP_LEFT, WIDGET_POS_TOP_RIGHT, 
                      WIDGET_POS_TOP_CENTER, WIDGET_POS_BOTTOM_LEFT, 
                      WIDGET_POS_BOTTOM_CENTER, WIDGET_POS_BOTTOM_RIGHT, 
                      WIDGET_POS_LEFT_CENTER, WIDGET_POS_RIGHT_CENTER, 
                      WIDGET_POS_CENTER, DEFAULT_FONT, COLOR_NAME_DICT, 
                      BLACK_COLOR_MAPPED, WHITE_COLOR_MAPPED, SIMILAR_COLOR_SEQUENCE,
                      DEFAULT_FONT_SIZE)

def tree_view_get_toplevel_node_count(treeview):
    '''
    Get node count number of TreeView.
    
    @param treeview: Gtk.TreeView instance.
    @return: Return number of node.
    
    Return 0 if treeview haven't model.
    '''
    model = treeview.get_model()
    if model != None:
        return model.iter_n_children(None)
    else:
        return 0
    
def tree_view_get_selected_path(treeview):
    '''
    Get selected path of TreeView.
    
    @param treeview: Gtk.TreeView instance.
    @return: Return selected path of treeview.
    
    Return None if haven't any path selected.
    '''
    selection = treeview.get_selection()
    (_, tree_paths) = selection.get_selected_rows()
    if len(tree_paths) != 0:
        return (tree_paths[0])[0]
    else:
        return None
 
def tree_view_focus_first_toplevel_node(treeview):
    '''
    Focus first toplevel node of TreeView.
    
    @param treeview: Gtk.TreeView instance.
    '''
    treeview.set_cursor((0))
    
def tree_view_focus_last_toplevel_node(treeview):
    '''
    Focus last toplevel node of TreeView.

    @param treeview: Gtk.TreeView instance.
    '''
    node_count = tree_view_get_toplevel_node_count(treeview)
    if node_count > 0:
        path = (node_count - 1)
    else:
        path = (0)
    treeview.set_cursor(path)
    
def tree_view_scroll_vertical(treeview, scroll_up=True):
    '''
    Scroll TreeView vertically.
    
    @param treeview: Gtk.TreeView instance.
    @param scroll_up: Defalut value is True, set as False if you want scroll down.
    '''
    # Init.
    scroll_num = 9
    candidate_count = tree_view_get_toplevel_node_count(treeview)
    cursor = treeview.get_cursor()
    (path, column) = cursor
    max_candidate = candidate_count - 1
    
    # Get candidate at cursor.
    if path == None:
        current_candidate = max_candidate
    else:
        (current_candidate,) = path
        
    # Set cursor to new candidate.
    if scroll_up:
        new_candidate = max(0, current_candidate - scroll_num)
    else:
        new_candidate = min(current_candidate + scroll_num, max_candidate)
        
    treeview.set_cursor((new_candidate))
    
def tree_view_focus_next_toplevel_node(treeview):
    '''
    Focus next toplevel node of TreeView.

    @param treeview: Gtk.TreeView instance.
    '''
    selected_path = tree_view_get_selected_path(treeview)
    if selected_path != None:
        node_count = tree_view_get_toplevel_node_count(treeview)
        if selected_path < node_count - 1:
            treeview.set_cursor((selected_path + 1))

def tree_view_focus_prev_toplevel_node(treeview):
    '''
    Focus previous toplevel node of TreeView.
    
    @param treeview: Gtk.TreeView instance.
    '''
    selected_path = tree_view_get_selected_path(treeview)
    if selected_path != None:
        if selected_path > 0:
            treeview.set_cursor((selected_path - 1))

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

def get_widget_root_coordinate(widget, pos_type=WIDGET_POS_BOTTOM_CENTER):
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
    if toplevel_window:
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
    if "get_child" in dir(widget) and widget.get_child() != None:
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
    Whehter event is right button event.
    
    @param event: gtk.gdk.BUTTON_PRESS event.
    @return: Return True if event is right button event.
    '''
    return event.button == 3

def is_middle_button(event):
    '''
    Whehter event is middle button event.
    
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

def is_in_rect((tx, ty), (x, y, w, h)):
    '''
    Whether target coordinate in given rectangle.
    
    @param tx: Target x coordinate.
    @param ty: Target y coordinate.
    @param x: X coordinate of rectangle area.
    @param y: X coordinate of rectangle area.
    @param w: Width of rectangle area.
    @param h: Height of rectangle area.
    @return: Return True if target coordinate in given rectangle.
    '''
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
        layout_set_markup(layout, text)
        if wrap_width == None:
            layout.set_single_paragraph_mode(True)
        else:
            layout.set_width(wrap_width * pango.SCALE)
            layout.set_single_paragraph_mode(False)
            layout.set_wrap(pango.WRAP_WORD)
        
        return layout.get_pixel_size()
    else:
        return (0, 0)
    
def create_directory(directory, remove_first=False):
    '''
    Create directory.
    
    @param directory: Target directory to create.
    @param remove_first: If you want remove directory when directory has exist, set it as True.
    '''
    if remove_first and os.path.exists(directory):
        remove_directory(directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
def remove_file(path):
    '''
    Remove file if file exist.
    
    @param path: Target path to remove.
    '''
    if os.path.exists(path):
        os.remove(path)
        
def remove_directory(path):
    """
    Remove directory recursively, equivalent to command `rm -rf path`.

    @param path: Target directory to remove.
    """
    if os.path.exists(path):
        for i in os.listdir(path):
            full_path = os.path.join(path, i)
            if os.path.isdir(full_path):
                remove_directory(full_path)
            else:
                os.remove(full_path)
        os.rmdir(path)        

def touch_file(filepath):
    '''
    Touch file, equivalent to command `touch filepath`.
    
    If filepath's parent directory is not exist, this function will create parent directory first.

    @param filepath: Target path to touch.
    '''
    # Create directory first.
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        
    # Touch file.
    open(filepath, "w").close()

def read_file(filepath, check_exists=False):
    '''
    Read file content.
    
    @param filepath: Target filepath.
    @param check_exists: Whether check file is exist, default is False.
    
    @return: Return \"\" if check_exists is True and filepath not exist.
    
    Otherwise return file's content.
    '''
    if check_exists and not os.path.exists(filepath):
        return ""
    else:
        r_file = open(filepath, "r")
        content = r_file.read()
        r_file.close()
        
        return content

def read_first_line(filepath, check_exists=False):
    '''
    Read first line of file.
    
    @param filepath: Target filepath.
    @param check_exists: Whether check file is exist, default is False.
    @return: Return \"\" if check_exists is True and filepath not exist.
    
    Otherwise return file's first line.
    '''
    if check_exists and not os.path.exists(filepath):
        return ""
    else:
        r_file = open(filepath, "r")
        content = r_file.readline().split("\n")[0]
        r_file.close()
        
        return content

def eval_file(filepath, check_exists=False):
    '''
    Eval file content.
    
    @param filepath: Target filepath.
    @param check_exists: Whether check file is exist, default is False.
    @return: Return None if check_exists is True and file not exist.
    
    Return None if occur error when eval file.

    Otherwise return file content as python structure.
    '''
    if check_exists and not os.path.exists(filepath):
        return None
    else:
        try:
            read_file = open(filepath, "r")
            content = eval(read_file.read())
            read_file.close()
            
            return content
        except Exception, e:
            print "function eval_file got error: %s" % e
            traceback.print_exc(file=sys.stdout)
            
            return None

def write_file(filepath, content):
    '''
    Write file with given content.

    @param filepath: Target filepath to write.
    @param content: File content to write.
    '''
    f = open(filepath, "w")
    f.write(content)
    f.close()

def kill_process(proc):
    '''
    Kill process.

    @param proc: Subprocess instance.
    '''
    try:
        if proc != None:
            proc.kill()
    except Exception, e:
        print "function kill_process got error: %s" % (e)
        traceback.print_exc(file=sys.stdout)
    
def get_command_output_first_line(commands):
    '''
    Run command and return first line of output.
    
    @param commands: Input commands.
    @return: Return first line of command output.
    '''
    process = subprocess.Popen(commands, stdout=subprocess.PIPE)
    process.wait()
    return process.stdout.readline()

def get_command_output(commands):
    '''
    Run command and return output.
    
    @param commands: Input commands.
    @return: Return command output.
    '''
    process = subprocess.Popen(commands, stdout=subprocess.PIPE)
    process.wait()
    return process.stdout.readlines()
    
def run_command(command):
    '''
    Run command silencely.
    
    @param command: Input command.
    '''
    subprocess.Popen("nohup %s > /dev/null 2>&1" % (command), shell=True)
    
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

def get_current_time(time_format="%Y-%m-%d %H:%M:%S"):
    '''
    Get current time with given time format.

    @param time_format: Time format, default is %Y-%m-%d %H:%M:%S
    @return: Return current time with given time format.
    '''
    return time.strftime(time_format, time.localtime())

def add_in_list(e_list, element):
    '''
    Add element in list, don't add if element has in list.
    
    @param e_list: List to insert.
    @param element: Element will insert to list.
    '''
    if not element in e_list:
        e_list.append(element)
        
def remove_from_list(e_list, element):
    '''
    Try remove element from list, do nothing if element not in list.
    
    @param e_list: List to remove.
    @param element: Element try to remove from list.
    '''
    if element in e_list:
        e_list.remove(element)
        
def sort_alpha(e_list):
    '''
    Sort list with alpha order.
    
    @param e_list: List to sort.
    '''
    return sorted(e_list, key=lambda e: e)

def get_dir_size(dirname):
    '''
    Get size of given directory.
    
    @param dirname: Directory path.
    @return: Return total size of directory.
    '''
    total_size = 0
    for root, dirs, files in os.walk(dirname):
        for filepath in files:
            total_size += os.path.getsize(os.path.join(root, filepath))
            
    return total_size

def print_env():
    '''
    Print environment variable.
    '''
    for param in os.environ.keys():
        print "*** %20s %s" % (param,os.environ[param])                

def print_exec_time(func):
    '''
    Print execute time of function.
    
    @param func: Fucntion name.
    
    Usage:
    
    >>> @print_exec_time
    >>> def function_to_test():
    >>>     ...
    '''
    def wrap(*a, **kw):
        start_time = time.time()
        ret = func(*a, **kw)
        print "%s time: %s" % (str(func), time.time() - start_time)
        return ret
    return wrap

def get_font_families():
    '''
    Get all font families in system.
    
    @return: Return font families list in current system.
    '''
    fontmap = pangocairo.cairo_font_map_get_default()
    return map (lambda f: f.get_name(), fontmap.list_families())

def format_file_size(bytes, precision=2):
    '''
    Returns a humanized string for a given amount of bytes.
    
    @param bytes: Bytes number to format.
    @param precision: Number precision.
    @return: Return a humanized string for a given amount of bytes.
    '''
    bytes = int(bytes)
    if bytes is 0:
        return '0 B'
    else:
        log = math.floor(math.log(bytes, 1024))
        quotient = 1024 ** log
        size = bytes / quotient
        remainder = bytes % quotient
        if remainder < 10 ** (-precision): 
            prec = 0
        else:
            prec = precision
        return "%.*f %s" % (prec,
                            size,
                            ['B', 'KB', 'MB', 'GB', 'TB','PB', 'EB', 'ZB', 'YB']
                            [int(log)])

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
    """ 
    Convert a html (hex) RGB value to cairo color. 
     
    @param color: The color to convert. 
    @return: A color in cairo format, (red, green, blue). 
    """ 
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
    """ 
    Convert a 8 bit RGB value to cairo color. 
     
    @type color: a triple of integers between 0 and 255 
    @param color: The color to convert. 
    @return: A color in cairo format. 
    """ 
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

def map_value(value_list, get_value_callback):
    '''
    Return value with map list.
    
    @param value_list: A list to loop.
    @param get_value_callback: Callback for element in list.
    @return: Return a new list that every element is result of get_value_callback.
    '''
    if value_list == None:
        return []
    else:
        return map(get_value_callback, value_list)

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

def mix_list_max(list_a, list_b):
    '''
    Return new list that element is max value between list_a and list_b.

    @param list_a: List a.
    @param list_b: List b.
    @return: Return new list that element is max value between two list.
    
    Return empty list if any input list is empty or two list's length is not same.
    '''
    if list_a == []:
        return list_b
    elif list_b == []:
        return list_a
    elif len(list_a) == len(list_b):
        result = []
        for (index, item_a) in enumerate(list_a):
            if item_a > list_b[index]:
                result.append(item_a)
            else:
                result.append(list_b[index])
        
        return result        
    else:
        print "mix_list_max: two list's length not same."
        return []

def unzip(unzip_list):
    '''
    Unzip [(1, 'a'), (2, 'b'), (3, 'c')] to ([1, 2, 3], ['a', 'b', 'c']).
    
    @param unzip_list: List to unzip.
    @return: Return new unzip list.
    '''
    first_list, second_list = zip(*unzip_list)
    return (list(first_list), list(second_list))

def is_seriate_list(test_list):
    '''
    Whether is seriate list.

    @param test_list: Test list.
    @return: Return True is test list is seriate list.
    '''
    for (index, item) in enumerate(test_list):
        if item != test_list[0] + index:
            return False
    
    return True

def get_disperse_index(disperse_list, value):
    '''
    Get index in disperse list.
    
    @param disperse_list: Disperse list.
    @param value: Match value.
    @return: Return index in disperse list.
    '''
    for (index, _) in enumerate(disperse_list):
        start_value = sum(disperse_list[0:index])
        end_value = sum(disperse_list[0:index + 1])
        if start_value <= value < end_value:
            return (index, value - start_value)
        
    # Return last one.
    return (last_index(disperse_list), disperse_list[-1])

def window_is_max(widget):
    '''
    Whether window is maximized.
    
    @param widget: Gtk.Widget instance.
    @return: Return True if widget's toplevel window is maximized.
    '''
    toplevel_window = widget.get_toplevel()
    if toplevel_window.window.get_state() == gtk.gdk.WINDOW_STATE_MAXIMIZED:
        return True
    else:
        return False
    
def last_index(test_list):
    '''
    Return last index of list.
    
    @param test_list: Test list.
    @return: Return last index of list.
    '''
    return len(test_list) - 1

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

@contextmanager
def exec_time():
    '''
    Print execute time with given code block.
    
    Usage:

    >>> with exec_time():
    >>>     # Write any code at here.
    >>>     # ...
    '''
    start_time = time.time()
    try:  
        yield  
    except Exception, e:  
        print 'function exec_time got error %s' % e  
        traceback.print_exc(file=sys.stdout)
    else:  
        print "time: %f" % (time.time() - start_time)

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
    Find simliar color match search_color.
    
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

def end_with_suffixs(filepath, suffixs):
    '''
    Whether file endswith given suffixs.
    
    @param filepath: Filepath to test.
    @param suffixs: A list suffix to match.
    @return: Return True if filepath endswith with given suffixs.
    '''
    for suffix in suffixs:
        if filepath.endswith(suffix):
            return True
        
    return False    

def place_center(refer_window, place_window):
    '''
    Place place_window in center of refer_window.
    
    @param refer_window: Reference window.
    @param place_window: Place window.
    '''
    (center_x, center_y) = get_widget_root_coordinate(refer_window, WIDGET_POS_CENTER)
    place_window.move(
        center_x - place_window.allocation.width / 2,
        center_y - place_window.allocation.height / 2
        )

def get_pixbuf_support_foramts():
    '''
    Get formats that support by pixbuf.
    
    @return: Return formats that support by pixbuf.
    '''
    support_formats = []
    for support_format in gtk.gdk.pixbuf_get_formats():
        support_formats += support_format.get("extensions")
        
    return support_formats    

def get_parent_dir(filepath, level=1):
    '''
    Get parent directory with given return level.
    
    @param filepath: Filepath.
    @param level: Return level, default is 1
    @return: Return parent directory with given return level. 
    '''
    parent_dir = os.path.realpath(filepath)
    
    while(level > 0):
        parent_dir = os.path.dirname(parent_dir)
        level -= 1
    
    return parent_dir

def gdkcolor_to_string(gdkcolor):
    '''
    Gdk color to string.
    
    @param gdkcolor: Gdk.Color
    @return: Return string of gdk color.
    '''
    return "#%0.2X%0.2X%0.2X" % (gdkcolor.red / 256, gdkcolor.green / 256, gdkcolor.blue / 256)

def is_long(string):
    '''
    Is string can convert to long type.
    
    @param string: Test string.
    @return: Return True if string can convert to long type.
    '''
    if string == "":
        return True
    
    try:
        long(string)
        return True
    except ValueError:
        return False

def is_int(string):
    '''
    Is string can convert to int type.
    
    @param string: Test string.
    @return: Return True if string can convert to int type.
    '''
    if string == "":
        return True
    
    try:
        int(string)
        return True
    except ValueError:
        return False

def is_float(string):
    '''
    Is string can convert to float type.
    
    @param string: Test string.
    @return: Return True if string can convert to float type.
    '''
    if string == "":
        return True
    
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_hex_color(string):
    '''
    Is string can convert to hex color type.
    
    @param string: Test string.
    @return: Return True if string can convert to hex color type.
    '''
    HEX_CHAR = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                "a", "b", "c", "d", "e", "f",
                "A", "B", "C", "D", "E", "F",
                "#"
                ]
    
    if string == "":
        return True
    else:
        for c in string:
            if not c in HEX_CHAR:
                return False
            
        if string.startswith("#"):
            if len(string) > 7:
                return False
            else:
                return True
        else:            
            if len(string) > 6:
                return False
            else:
                return True    
            
def get_window_shadow_size(window):
    '''
    Get window shadow size.
    
    @param window: Test window.
    @return: Return shadow size as (width, height), or return (0, 0) if window haven't shadow.
    '''
    if "get_shadow_size" in dir(window):
        return window.get_shadow_size()
    else:
        return (0, 0)

def layout_set_markup(layout, markup):
    '''
    Set layout markup.
    
    @param layout: Pango layout.
    @param markup: Markup string.
    '''
    if "&" in markup or "<" in markup or ">" in markup:
        layout.set_markup(markup.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    else:
        layout.set_markup(markup)

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

def unique_print(text):
    '''
    Unique print, generic for test code.
    
    @param text: Test text.
    '''
    print "%s: %s" % (time.time(), text)

def check_connect_by_port(port, retry_times=6, sleep_time=0.5):
    """
    Check connect has active with given port.
    
    @param port: Test port.
    @param retry_times: Retry times.
    @param sleep_time: Sleep time between retry, in seconds.
    @return: Return True if given port is active.
    """
    ret_val = False
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    retry_time = 0
    while (True):
        try:
            test_socket.connect(("localhost", port))
            ret_val = True
            break
        except socket.error:
            time.sleep(sleep_time)
            retry_time += 1
            if retry_time >= retry_times:
                break
            else:
                continue
    return ret_val

def is_network_connected():
    '''
    Is network connected, if nothing in file `/proc/net/arp`, network is disconnected.
    
    @return: Return True if network is connected.
    '''
    return len(filter(lambda line: line != '', open("/proc/net/arp", "r").read().split("\n")) )> 1
