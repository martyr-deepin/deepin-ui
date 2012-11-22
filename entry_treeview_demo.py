#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Long Changjin
# 
# Author:     Long Changjin <admin@longchangjin.cn>
# Maintainer: Long Changjin <admin@longchangjin.cn>
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

from dtk.ui.init_skin import init_skin
from dtk.ui.utils import get_parent_dir
import os

app_theme = init_skin(
    "deepin-ui-demo",
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )

from dtk.ui.new_treeview import TreeView, TreeItem
from dtk.ui.draw import draw_text
from dtk.ui.utils import color_hex_to_cairo, is_left_button, is_right_button
from dtk.ui.new_entry import Entry
from dtk.ui.entry_treeview import EntryTreeView, EntryTreeItem
import gtk
import gobject

def button_press_tree_view(widget, event, tv):
    if tv.get_data("entry_widget") is None:
        return
    cell = tv.get_cell_with_event(event)
    entry = tv.get_data("entry_widget")
    item = entry.get_data("item")
    # if pressed outside entry column area, destroy entry
    if cell is None:
        entry.get_parent().destroy()
        return
    (row, column, offset_x, offset_y) = cell
    if tv.visible_items[row] != item or column != item.ENTRY_COLUMN:
        entry.get_parent().destroy()
        return
    # right button the show menu
    if is_right_button(event):
        entry.right_menu.show((int(event.x_root), int(event.y_root)))
        return
    entry.set_data("button_press", True)
    send_event = event.copy()
    send_event.send_event = True
    send_event.x = float(offset_x)
    send_event.y = 1.0
    send_event.window = entry.window
    entry.event(send_event)
    send_event.free()

def button_release_tree_view(widget, event, tv):
    if tv.get_data("entry_widget") is None:
        return
    entry = tv.get_data("entry_widget")
    # has not been pressed
    if not entry.get_data("button_press"):
        return
    cell = tv.get_cell_with_event(event)
    if cell is None:
        offset_x = 1
    else:
        (row, column, offset_x, offset_y) = cell
    entry.grab_focus()
    entry.set_data("button_press", False)
    send_event = event.copy()
    send_event.send_event = True
    send_event.x = float(offset_x)
    send_event.y = 1.0
    send_event.window = entry.window
    entry.event(send_event)
    send_event.free()

def motion_tree_view(widget, event, tv):
    if tv.get_data("entry_widget") is None:
        return
    entry = tv.get_data("entry_widget")
    # has not been pressed
    if not entry.get_data("button_press"):
        return
    cell = tv.get_cell_with_event(event)
    item = entry.get_data("item")
    if cell is None:
        offset_x = 1
    else:
        (row, column, offset_x, offset_y) = cell
        if column != item.ENTRY_COLUMN:
            offset_x = 1
    send_event = event.copy()
    send_event.send_event = True
    send_event.x = float(offset_x)
    send_event.y = 1.0
    send_event.window = entry.window
    entry.event(send_event)
    send_event.free()

def edit_done(entry, box, item, tv):
    item.entry = None
    item.entry_buffer.set_property('cursor-visible', False)
    item.entry_buffer.move_to_start()
    item.redraw_request_callback(item)
    tv.draw_area.grab_focus()
    tv.set_data("entry_widget", None)

def entry_focus_changed(entry, event, item):
    if event.in_:
        item.entry_buffer.set_property('cursor-visible', True)
    else:
        item.entry_buffer.set_property('cursor-visible', False)

def select_click(treeview, item, column):
    if column == item.ENTRY_COLUMN:
        if item.entry:
            item.entry.grab_focus()
            return
        item.entry_buffer.set_property('cursor-visible', True)
        hbox = gtk.HBox(False)
        align = gtk.Alignment(0, 0, 1, 1)
        entry = Entry()
        entry.set_data("item", item)
        entry.set_data("button_press", False)
        entry.set_buffer(item.entry_buffer)
        entry.set_size_request(item.get_column_widths()[column]-4, 0)
        entry.connect("press-return", lambda w: hbox.destroy())
        entry.connect("destroy", edit_done, hbox, item, treeview)
        entry.connect_after("focus-in-event", entry_focus_changed, item)
        entry.connect_after("focus-out-event", entry_focus_changed, item)
        treeview.pack_start(hbox, False, False)
        treeview.set_data("entry_widget", entry)
        hbox.pack_start(entry, False, False)
        hbox.pack_start(align)
        hbox.show_all()
        entry.set_can_focus(True)
        entry.grab_focus()
        entry.select_all()
        item.entry = entry

if __name__ == '__main__':
    win = gtk.Window()
    win.set_size_request(300, 290)
    win.connect("destroy", gtk.main_quit)

    item1 = EntryTreeItem("item1", "this is a tree item test")
    item2 = EntryTreeItem("item2", "item2 test")
    item3 = EntryTreeItem("item3", "third item test")
    item4 = EntryTreeItem("item4", "third item test")
    item5 = EntryTreeItem("item5", "third item test")
    item6 = EntryTreeItem("item6", "third item test")
    item7 = EntryTreeItem("item7", "third item test")
    item8 = EntryTreeItem("item8", "third item test")
    item9 = EntryTreeItem("item9", "third item test")
    item10 = EntryTreeItem("item10", "third item test")
    item11 = EntryTreeItem("item11", "third item test")
    item12 = EntryTreeItem("item12", "third item test")
    item13 = EntryTreeItem("item13", "third item test")
    item14 = EntryTreeItem("item14", "third item test")
    item = [item1, item2, item3, item4, item5,
            item6, item7, item8, item9, item10,
            item11, item12, item13, item14]
    tree_view = EntryTreeView(item)
    tree_view.connect("double-click", select_click)
    tree_view.draw_area.connect("button-press-event", button_press_tree_view, tree_view)
    tree_view.draw_area.connect("button-release-event", button_release_tree_view, tree_view)
    tree_view.draw_area.connect("motion-notify-event", motion_tree_view, tree_view)

    win.add(tree_view)
    win.show_all()
    gtk.main()
