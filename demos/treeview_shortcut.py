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
from deepin_utils.file import get_parent_dir
import os

app_theme = init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )
from dtk.ui.treeview import TreeItem, TreeView
from dtk.ui.draw import draw_text
from dtk.ui.utils import (color_hex_to_cairo, is_left_button, 
                          is_double_click, is_single_click)
from gtk import gdk
from gtk import accelerator_name, accelerator_parse, accelerator_get_label
import gobject
import copy

class MyTreeView(TreeView):
    ''' my TreeView'''
    __gsignals__ = {
        "select"  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int)),
        "unselect": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, int))}

    def __init__(self,
                 items=[],
                 drag_data=None,
                 enable_hover=False,
                 enable_highlight=False,
                 enable_multiple_select=False,
                 enable_drag_drop=False,
                 drag_icon_pixbuf=None,
                 start_drag_offset=50,
                 mask_bound_height=24,
                 right_space=0,
                 top_bottom_space=3
                 ):
        super(MyTreeView, self).__init__(
                items, drag_data, enable_hover, enable_highlight,
                enable_multiple_select, enable_drag_drop, drag_icon_pixbuf,
                start_drag_offset, mask_bound_height, right_space, top_bottom_space)
        self.keymap["Shift + Up"] = self.keymap["Up"]
        self.keymap["Shift + Down"] = self.keymap["Down"]
        self.keymap["Shift + Home"] = self.keymap["Home"]
        self.keymap["Shift + End"] = self.keymap["End"]
        self.keymap["Ctrl + Up"] = self.keymap["Up"]
        self.keymap["Ctrl + Down"] = self.keymap["Down"]
        del self.keymap["Ctrl + a"]
        del self.keymap["Delete"]
    
    def add_items(self, items, insert_pos=None, clear_first=False):
        '''
        Add items.
        '''
        with self.keep_select_status():
            if clear_first:
                self.visible_items = []
            
            if insert_pos == None:
                self.visible_items += items
            else:
                self.visible_items = self.visible_items[0:insert_pos] + items + self.visible_items[insert_pos::]
            
            # Update redraw callback.
            # Callback is better way to avoid perfermance problem than gobject signal.
            for item in items:
                item.redraw_request_callback = self.redraw_request
                item.add_items_callback = self.add_items
                item.delete_items_callback = self.delete_items
                item.treeview = self
            
            self.update_item_index()    
            
            self.update_item_widths()
                
            self.update_vadjustment()
        
    def click_item(self, event):
        cell = self.get_cell_with_event(event)
        if cell != None:
            (click_row, click_column, offset_x, offset_y) = cell
            
            if self.left_button_press:
                if click_row == None:
                    self.unselect_all()
                else:
                    if self.enable_drag_drop and click_row in self.select_rows:
                        self.start_drag = True
                        # Record press_in_select_rows, disable select rows if mouse not move after release button.
                        self.press_in_select_rows = click_row
                    else:
                        self.start_drag = False
                        self.start_select_row = click_row
                        self.set_select_rows([click_row])
                        
                        self.visible_items[click_row].button_press(click_column, offset_x, offset_y)
                            
                if is_double_click(event):
                    self.double_click_row = copy.deepcopy(click_row)
                elif is_single_click(event):
                    self.single_click_row = copy.deepcopy(click_row)                
    
    def set_select_rows(self, rows):
        for select_row in self.select_rows:
            self.visible_items[select_row].unselect()
            
        self.select_rows = rows
        
        if rows == []:
            self.start_select_row = None
        else:
            for select_row in self.select_rows:
                self.visible_items[select_row].select()
                self.emit("select", self.visible_items[select_row], select_row)
    
    def release_item(self, event):
        if is_left_button(event):
            cell = self.get_cell_with_event(event)
            if cell is not None:
                (release_row, release_column, offset_x, offset_y) = cell
                
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
gobject.type_register(MyTreeView)
        
class AccelBuffer(object):
    '''a buffer which store accelerator'''
    def __init__(self):
        super(AccelBuffer, self).__init__()
        self.state = None
        self.keyval = None
    
    def set_state(self, state):
        '''
        set state
        @param state: the state of the modifier keys, a GdkModifierType
        '''
        self.state = state & (~gdk.MOD2_MASK)
    
    def get_state(self):
        '''
        get state
        @return: the state of the modifier keys, a GdkModifierType or None
        '''
        return self.state
    
    def set_keyval(self, keyval):
        '''
        set keyval
        @param keyval: a keyval, an int type
        '''
        self.keyval = keyval
    
    def get_keyval(self):
        '''
        get keyval
        @return: a keyval, an int type or None
        '''
        return self.keyval
    
    def get_accel_name(self):
        '''
        converts the accelerator keyval and modifier mask into a string
        @return: a acceleratot string
        '''
        if self.state is None or self.keyval is None:
            return ''
        return accelerator_name(self.keyval, self.state)
    
    def get_accel_label(self):
        '''
        converts the accelerator keyval and modifier mask into a string
        @return: a accelerator string
        '''
        if self.state is None or self.keyval is None:
            return ''
        return accelerator_get_label(self.keyval, self.state)
    
    def set_from_accel(self, accelerator):
        '''
        parses the accelerator string and update keyval and state
        @parse accelerator: a accelerator string
        '''
        (self.keyval, self.state) = accelerator_parse(accelerator)
    
    def is_equal(self, accel_buffer):
        '''
        check an other AccelBuffer object is equal
        @param accel_buffer: a AccelBuffer object
        @return: True if their values are equal, otherwise False'''
        if self.get_state() == accel_buffer.get_state()\
                and self.get_keyval() == accel_buffer.get_keyval():
                return True
        else:
            return False

    def __eq__(self, accel_buffer):
        ''' '''
        return self.is_equal(accel_buffer)

class BaseItem(TreeItem):
    '''the base TreeItem class'''
    __gsignals__ = {"select": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,))}

    def __init__(self):
        super(BaseItem, self).__init__()
        self.treeview = None
    
    def get_treeview(self):
        '''
        get treeview
        @return: a TreeView type
        '''
        return self.treeview
    
    def unselect(self):
        if not self.is_select:
            return
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def select(self):
        self.is_select = True
        #self.emit("select", self.row_index)
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
gobject.type_register(BaseItem)

class ShortcutItem(BaseItem):
    '''a shortcut item in TreeView'''
    def __init__(self, description, keyname): 
        super(ShortcutItem, self).__init__()
        self.description = description
        self.keyname = keyname
        self.height = 24
        self.padding_x = 5
        self.accel_buffer = AccelBuffer()
        self.COLUMN_ACCEL = 1
    
    def get_height(self):
        return self.height
    
    def get_column_widths(self):
        return [150, 270]
    
    def get_column_renders(self):
        return [self.render_description, self.render_keyname]
        
    def render_description(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            cr.set_source_rgb(*color_hex_to_cairo(bg_color))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.paint()
        else:
            text_color = "#000000"
        draw_text(cr, self.description, rect.x+self.padding_x, rect.y, rect.width, rect.height, text_color=text_color)
    
    def render_keyname(self, cr, rect):
        if self.is_select:
            text_color = "#FFFFFF"
            bg_color = "#3399FF"
            cr.set_source_rgb(*color_hex_to_cairo(bg_color))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.paint()
        else:
            text_color = "#000000"
        draw_text(cr, self.keyname, rect.x+self.padding_x, rect.y, rect.width, rect.height, text_color=text_color)
    
    def set_accel_buffer_from_event(self, event):
        '''
        set accel buffer value from an Event
        @param event: a gtk.gdk.KEY_PRESS
        '''
        if event.type != gdk.KEY_PRESS:
            return
        self.accel_buffer.set_state(event.state)
        self.accel_buffer.set_keyval(event.keyval)
    
    def set_accel_buffer_from_accel(self, accelerator):
        '''
        ser accel buffer value from an accelerator string
        @parse accelerator: a accelerator string
        '''
        self.accel_buffer.set_from_accel(accelerator)
    
    def update_accel_setting(self):
        ''' update the system setting '''
        self.keyname = self.accel_buffer.get_accel_label()
        if self.keyname == '':
            self.keyname = ('disable')
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        return True
gobject.type_register(ShortcutItem)

def shortcuts_clicked(treeview, item, column):
    ''' '''
    if column != item.COLUMN_ACCEL:
        return
    
    def button_press_callback(widget, event, item):
        print "clicked", event
        gtk.gdk.keyboard_ungrab(0)
        gtk.gdk.pointer_ungrab(0)
        widget.destroy()
        item.keyname = item.old_keyname
        item.redraw_request_callback(item)
    
    def key_press_callback(widget, event, item, tv):
        #print "key press", get_keyevent_name(event)
        if event.is_modifier:
            print "is modifier"
            return
        #print item.description, item.keyname, item.name
        gtk.gdk.keyboard_ungrab(0)
        gtk.gdk.pointer_ungrab(0)
        widget.destroy()
        tv.draw_area.grab_focus()
        keyval = event.keyval
        state = event.state & (~gtk.gdk.MOD2_MASK)  # ignore MOD2_MASK
        tmp_accel_buf = AccelBuffer()
        tmp_accel_buf.set_keyval(keyval)
        tmp_accel_buf.set_state(state)
        # cancel edit
        if keyval == gtk.keysyms.Escape:
            item.keyname = item.old_keyname
            item.redraw_request_callback(item)
            return
        # clear edit
        if keyval == gtk.keysyms.BackSpace:
            item.accel_buffer.set_keyval(0)
            item.accel_buffer.set_state(0)
            item.update_accel_setting()
            print "backspace:", item.keyname
            item.redraw_request_callback(item)
            return
        item.set_accel_buffer_from_event(event)
        item.update_accel_setting()
        print "OK", item.keyname
        item.redraw_request_callback(item)
    item.old_keyname = item.keyname
    item.keyname = ("New accelerator..")
    if item.redraw_request_callback:
        item.redraw_request_callback(item)
    event_box = gtk.EventBox()
    event_box.set_size_request(0, 0)
    treeview.pack_start(event_box, False, False)
    event_box.show_all()
    if gtk.gdk.keyboard_grab(event_box.window, False, 0) != gtk.gdk.GRAB_SUCCESS:
        event_box.destroy()
        return None
    if gtk.gdk.pointer_grab(event_box.window, False, gtk.gdk.BUTTON_PRESS_MASK, None, None, 0) != gtk.gdk.GRAB_SUCCESS:
        gtk.gdk.keyboard_ungrab(0)
        event_box.destroy()
        return None
    event_box.set_can_focus(True)
    event_box.grab_focus()
    event_box.add_events(gtk.gdk.BUTTON_PRESS_MASK)
    event_box.add_events(gtk.gdk.KEY_PRESS_MASK)
    event_box.connect("button-press-event", button_press_callback, item)
    event_box.connect("key-press-event", key_press_callback, item, treeview)
    
if __name__ == '__main__':
    import gtk
    win = gtk.Window()
    win.set_size_request(300, 400)
    win.connect("destroy", gtk.main_quit)

    item1 = ShortcutItem("item1", "Ctrl + a")
    item2 = ShortcutItem("item2", "Alt + a")
    item3 = ShortcutItem("item3", "Ctrl + b")
    item = [item1, item2, item3]
    tree_view = MyTreeView(item)
    tree_view.connect("clicked", shortcuts_clicked)

    win.add(tree_view)
    win.show_all()
    gtk.main()
