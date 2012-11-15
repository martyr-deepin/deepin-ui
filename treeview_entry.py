#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Long Changjin
# 
# Author:     Long Changjin <admin@longchangjin.cn>
# Maintainer: Long Changjin <admin@longchangjin.cn>
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
from dtk.ui.new_entry import EntryBuffer, Entry
import gtk
import gobject

class MyTreeView(TreeView):
    ''' '''
    __gsignals__ = {
        "select"  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int)),
        "unselect": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int))}
    def __init__(self, 
            items=[],
            drag_data=None,
            enable_hover=False,
            enable_highlight=True,
            enable_multiple_select=False,
            enable_drag_drop=False,
            drag_icon_pixbuf=None,
            start_drag_offset=50,
            mask_bound_height=24,
            right_space=0,
            top_bottom_space=3):
        super(MyTreeView, self).__init__(
            items, drag_data, enable_hover,
            enable_highlight, enable_multiple_select,
            enable_drag_drop, drag_icon_pixbuf,
            start_drag_offset, mask_bound_height,
            right_space, top_bottom_space)
        #self.keymap.clear()
    
    def release_item(self, event):
        if is_left_button(event):
            cell = self.get_cell_with_event(event)
            if cell is not None:
                (release_row, release_column, offset_x, offset_y) = cell
                #print "release item:", offset_x, offset_y, event
                
                if release_row is not None:
                    if self.double_click_row == release_row:
                        self.visible_items[release_row].double_click(release_column, offset_x, offset_y)
                    elif self.single_click_row == release_row:
                        self.emit("clicked", self.visible_items[release_row], release_column)
                        self.visible_items[release_row].single_click(release_column, offset_x, offset_y)
                
                if self.start_drag and self.is_in_visible_area(event):
                    self.drag_select_items_at_cursor()
                    
                self.double_click_row = None    
                self.single_click_row = None    
                self.start_drag = False
                
                # Disable select rows when press_in_select_rows valid after button release.
                if self.press_in_select_rows:
                    self.set_select_rows([self.press_in_select_rows])
                    self.start_select_row = self.press_in_select_rows
                    self.press_in_select_rows = None
                
                self.set_drag_row(None)
        
class MyTreeItem(TreeItem):
    __gsignals__ = {
        "select" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,))}
    def __init__(self, title, content):
        #super(MyTreeItem, self).__init__()
        TreeItem.__init__(self)
        self.title = title
        self.entry = None
        self.entry_buffer = EntryBuffer(content)
        self.entry_buffer.set_property('cursor-visible', False)
        self.entry_buffer.connect("changed", self.entry_buffer_changed)
        self.entry_buffer.connect("insert-pos-changed", self.entry_buffer_changed)
        self.entry_buffer.connect("selection-pos-changed", self.entry_buffer_changed)
        self.child_items = []
        self.height = 24
        self.ENTRY_COLUMN = 1
    
    def entry_buffer_changed(self, bf):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def get_height(self):
        return self.height
    
    def get_column_widths(self):
        return [-1, 200]
    
    def get_column_renders(self):
        ''' '''
        return [self.render_title, self.render_content]
    
    def render_title(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            cr.set_source_rgb(*color_hex_to_cairo(bg_color))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.paint()
        else:
            text_color = "#000000"
        draw_text(cr, self.title, rect.x, rect.y, rect.width, rect.height, text_color=text_color)
    
    def render_content(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            cr.set_source_rgb(*color_hex_to_cairo(bg_color))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.paint()
        else:
            text_color = "#000000"
            self.entry_buffer.move_to_start()
        self.entry_buffer.set_text_color(text_color)
        height = self.entry_buffer.get_pixel_size()[1]
        offset = (self.height - height)/2
        if offset < 0 :
            offset = 0
        rect.y += offset
        if self.entry and self.entry.allocation.width == self.get_column_widths()[1]-4:
            #print "offset :", self.entry.offset_x, self.entry.allocation, self.get_column_widths()
            self.entry.calculate()
            rect.x += 2
            rect.width -= 4
            self.entry_buffer.set_text_color("#000000")
            self.entry_buffer.render(cr, rect, self.entry.im, self.entry.offset_x)
        else:
            self.entry_buffer.render(cr, rect)
    
    def unselect(self):
        print "unselect", self.title
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        #print "select"
        #self.emit("select")
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self, column, offset_x, offset_y):
        ''' '''
        print "hover:", column, offset_x, offset_y
    
    def unhover(self, column, offset_x, offset_y):
        ''' '''
        print 'unhover:', column, offset_x, offset_y
    
    def single_click(self, column, offset_x, offset_y):
        #print "single_click:", column, offset_x, offset_y
        #self.emit("clicked", column)
        #if self.is_expand:
            #self.unexpand()
        #else:
            #self.expand()
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    def expand(self):
        if self.is_expand:
            return
        self.is_expand = True
        self.add_items_callback(self.child_items, self.row_index+1)
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    def unexpand(self):
        self.is_expand = False
        self.delete_items_callback(self.child_items)
gobject.type_register(MyTreeItem)

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
        #print "motion has not pressed"
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
    #print "button motion:", event.x, event.y, event.x_root, event.y_root
    #print "cell:", cell

def edit_done(entry, box, item, tv):
    print "edit done"
    item.entry = None
    item.entry_buffer.set_property('cursor-visible', False)
    item.entry_buffer.move_to_start()
    item.redraw_request_callback(item)
    tv.draw_area.grab_focus()
    tv.set_data("entry_widget", None)

def entry_focus_changed(entry, event, item):
    #print "focus %d", event.in_, item.is_select, item.title
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
        item.entry = entry

if __name__ == '__main__':
    win = gtk.Window()
    win.set_size_request(300, 290)
    win.connect("destroy", gtk.main_quit)

    item1 = MyTreeItem("item1", "this is a tree item test")
    item2 = MyTreeItem("item2", "item2 test")
    item3 = MyTreeItem("item3", "third item test")
    item4 = MyTreeItem("item4", "third item test")
    item5 = MyTreeItem("item5", "third item test")
    item6 = MyTreeItem("item6", "third item test")
    item7 = MyTreeItem("item7", "third item test")
    item8 = MyTreeItem("item8", "third item test")
    item9 = MyTreeItem("item9", "third item test")
    item10 = MyTreeItem("item10", "third item test")
    item11 = MyTreeItem("item11", "third item test")
    item12 = MyTreeItem("item12", "third item test")
    item13 = MyTreeItem("item13", "third item test")
    item14 = MyTreeItem("item14", "third item test")
    item = [item1, item2, item3, item4, item5,
            item6, item7, item8, item9, item10,
            item11, item12, item13, item14]
    tree_view = MyTreeView(item)
    #tree_view = TreeView(item,
        #enable_hover=False, 
        #enable_multiple_select=False,
        #enable_drag_drop=False)
    tree_view.connect("clicked", select_click)
    tree_view.draw_area.connect("button-press-event", button_press_tree_view, tree_view)
    tree_view.draw_area.connect("button-release-event", button_release_tree_view, tree_view)
    tree_view.draw_area.connect("motion-notify-event", motion_tree_view, tree_view)

    win.add(tree_view)
    win.show_all()
    gtk.main()
