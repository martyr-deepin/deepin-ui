#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Hou ShaoHui
# 
# Author:     Hou ShaoHui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
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
import pango
import gobject

from new_entry import Entry
from button import DisableButton
from new_poplist import AbstractPoplist
from theme import ui_theme
from label import Label
from new_treeview import TreeItem as AbstractItem
from draw import draw_text, draw_vlinear
from utils import (propagate_expose, cairo_disable_antialias,
                   color_hex_to_cairo, alpha_color_hex_to_cairo, get_content_size)
from constant import DEFAULT_FONT_SIZE

def draw_vlinear_mask(cr, rect, shadow_color):    
    draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, ui_theme.get_shadow_color(shadow_color).get_color_info())
    

class ComboTextItem(AbstractItem):
    
    def __init__(self, title, item_value, item_width=None, font_size=DEFAULT_FONT_SIZE):
        AbstractItem.__init__(self)
        self.column_index = 0
        self.item_height = 22
        self.spacing_x = 15
        self.padding_x = 5
        self.font_size = font_size
        if item_width == None:
            self.item_width, _ = get_content_size(title, font_size)
            self.item_width += self.spacing_x *2
        else:    
            self.item_width = item_width
        self.title = title
        self.item_value = item_value
        
    def get_height(self):    
            return self.item_height
    
    def get_column_widths(self):
        return (self.item_width,)
    
    def get_width(self):
        return self.item_width
    
    def get_column_renders(self):
        return (self.render_title,)
    
    def unselect(self):
        self.is_select = False
        self.emit_redraw_request()
        
    def emit_redraw_request(self):    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def select(self):        
        self.is_select = True
        self.emit_redraw_request()
        
    def render_title(self, cr, rect):        
        font_color = ui_theme.get_color("menu_font").get_color()
        
        if self.is_hover:    
            draw_vlinear_mask(cr, rect, "menu_item_select")
            font_color = ui_theme.get_color("menu_select_font").get_color()
        
        draw_text(cr, self.title, rect.x + self.padding_x,
                  rect.y, rect.width - self.padding_x * 2,
                  rect.height, text_size=self.font_size, 
                  text_color = font_color,
                  alignment=pango.ALIGN_LEFT)    
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_redraw_request()
    
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.emit_redraw_request()
        
    def button_press(self, column, offset_x, offset_y):
        pass
    
    def single_click(self, column, offset_x, offset_y):
        pass

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        pass
    
gobject.type_register(ComboTextItem)


        
class ComboList(AbstractPoplist):
    '''
    class docs
    '''
	
    def __init__(self,
                 items=[],
                 max_height=None,
                 max_width=None):
        '''
        init docs
        '''
        AbstractPoplist.__init__(self,
                         items, 
                         max_height,
                         False,
                         self.shape_combo_list_frame,
                         self.expose_combo_list_frame,
                         align_size=2,
                         min_width=80,
                         window_type=gtk.WINDOW_POPUP,
                         )
        
        self.treeview.draw_mask = self.draw_treeview_mask
        self.treeview.set_expand_column(0)
        self.expose_window_frame = self.expose_combo_list_frame
        
    def draw_treeview_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()
        
    def get_select_index(self):    
        select_rows = self.treeview.select_rows
        if len(select_rows) > 0:
            return select_rows[0]
        return 0
    
    def reset_status(self):
        self.treeview.left_button_press = False
        
    def set_select_index(self, index):
        self.treeview.set_select_rows([index])
        self.treeview.set_hover_row(index)
        
    def get_items(self):    
        return self.treeview.get_items()
        
    def hover_select_item(self):    
        self.treeview.set_hover_row(self.get_select_index())
        
    def shape_combo_list_frame(self, widget, event):
        pass
        
    def expose_combo_list_frame(self, widget, event):
        cr = widget.window.cairo_create()        
        rect = widget.allocation
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(*rect)
        cr.fill()

        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("droplist_frame").get_color()))
            cr.rectangle(rect.x + 1, rect.y + 1, rect.width - 1, rect.height - 1)
            cr.stroke()
            
            
gobject.type_register(ComboList)

class ComboBox(gtk.VBox):
    
    __gsignals__ = {
        "item-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
        "key-release" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
    }
    
    def __init__(self, items=[], 
                 droplist_height=None,                 
                 select_index=0, 
                 max_width=None, 
                 fixed_width=None, 
                 editable=False,
                 ):
        
        gtk.VBox.__init__(self)
        self.set_can_focus(True)
        
        # Init variables.
        self.focus_flag = False
        self.select_index = select_index
        self.editable = editable
        self.default_poplist_height = 100
        self.default_width = 120
        self.max_width = max_width
        self.max_height = droplist_height
        self.fixed_width = fixed_width
        
        if self.editable:
            self.padding_x = 0
        else:
            self.padding_x = 5
            
        self.items = [ComboTextItem(item[0], item[1]) for item in items]
        self.combo_list = ComboList()        
        self.drop_button = DisableButton(
            (ui_theme.get_pixbuf("combo/dropbutton_normal.png"),
             ui_theme.get_pixbuf("combo/dropbutton_hover.png"),
             ui_theme.get_pixbuf("combo/dropbutton_press.png"),
             ui_theme.get_pixbuf("combo/dropbutton_disable.png")),
            )
        self.drop_button_width = ui_theme.get_pixbuf("combo/dropbutton_normal.png").get_pixbuf().get_width()        
        self.panel_align = gtk.Alignment()
        self.panel_align.set(0.5, 0.5, 0.0, 0.0)
        
        if self.editable:
            self.label = Entry()
        else:    
            self.label = Label("", enable_select=False, enable_double_click=False)
            
            self.label.connect("button-press-event", self.on_drop_button_press)
            self.panel_align.set_padding(0, 0, self.padding_x, 0)            
            
        self.panel_align.add(self.label)    
        
        # init items.
        self.add_items(items)
        
        hbox = gtk.HBox()
        hbox.pack_start(self.panel_align, True, False)
        hbox.pack_start(self.drop_button, False, False)
        box_align = gtk.Alignment()
        box_align.set(0.5, 0.5, 0.0, 0.0)
        box_align.add(hbox)
        self.add(box_align)
        
        # Connect signals.
        box_align.connect("expose-event", self.on_expose_combo_frame)
        self.drop_button.connect("button-press-event", self.on_drop_button_press)
        self.connect("focus-in-event", self.on_focus_in_combo)
        self.connect("focus-out-event", self.on_focus_out_combo)
        self.combo_list.treeview.connect("button-press-item", self.on_combo_single_click)
        
    def set_size_request(self, width, height):    
        pass
    
    def auto_set_size(self):
        valid_width = self.get_adjust_width()
        remained_width = valid_width - self.drop_button_width - self.padding_x
        if self.editable:
            self.label.set_size_request(remained_width, -1)
        else:    
            self.label.set_fixed_width(remained_width)

        self.combo_list.set_size(valid_width + 1, 
                                 self.max_height, self.default_poplist_height)
    
    def get_adjust_width(self):
        if self.fixed_width:
            return self.fixed_width
        if len(self.items) > 0:
            item_max_width = max([item.get_width() for item in self.items])
        else:                
            item_max_width = self.default_width
            
        if self.max_width:    
            return max(self.max_width, item_max_width)
        return item_max_width
        
    def add_items(self, items, select_index=0, pos=None, clear_first=True):    
        # Init combo widgets.
        if clear_first:
            self.combo_list.treeview.clear()
        combo_items = [ComboTextItem(item[0], item[1]) for item in items]
        self.combo_list.treeview.add_items(combo_items, insert_pos=pos)        
        self.auto_set_size()
        self.set_select_index(select_index)
        
    def on_drop_button_press(self, widget, event):    
        
        self.combo_list.hover_select_item()
        height = self.allocation.height
        x, y = self.window.get_root_origin()
        
        if self.combo_list.get_visible():
            self.combo_list.hide()
        else:
            wx, wy = int(event.x), int(event.y)
            (offset_x, offset_y) = widget.translate_coordinates(self, 0, 0)
            (_, px, py, modifier) = widget.get_display().get_pointer()
            droplist_x, droplist_y = px - wx - offset_x - 1, py - wy - offset_y + height - 1
            self.combo_list.show((droplist_x, droplist_y), (0, -height))
            
    def on_combo_single_click(self, widget, item, column, x, y):        
        self.label.set_text(item.title)
        self.combo_list.reset_status()
        if item:
            index = self.combo_list.get_select_index()
            self.combo_list.hide_self()
            self.emit("item-selected", item.title, item.item_value, index)
    
    def on_focus_in_combo(self, widget, event):
        self.focus_flag = True
        self.queue_draw()
        
    def on_focus_out_combo(self, widget, event):    
        self.focus_flag = False
        self.queue_draw()
        
    def set_select_index(self, item_index):    
        if 0 <= item_index < len(self.all_items):
            self.combo_list.set_select_index(item_index)        
            self.label.set_text(self.all_items[item_index].title)
            
    @property        
    def all_items(self):
        return self.combo_list.get_items()
            
    def get_item_with_index(self, item_index):        
        if 0 <= item_index < len(self.all_items):
            item = self.all_items[item_index]
            return (item.title, item.item_value)
        else:
            return None
        
    def get_current_item(self):    
        return self.get_item_with_index(self.get_select_index())
    
    def get_select_index(self):
        return self.combo_list.get_select_index()
        
    def on_expose_combo_frame(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            if self.get_sensitive():
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("combo_entry_frame").get_color()))
            else:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("disable_frame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            if self.focus_flag:
                color = (ui_theme.get_color("combo_entry_select_background").get_color(), 0.9)
                cr.set_source_rgba(*alpha_color_hex_to_cairo(color))
                cr.rectangle(rect.x, rect.y, rect.width - 1 - self.drop_button_width, rect.height - 1)
                cr.fill()
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x + rect.width - 1 - self.drop_button_width, rect.y, self.drop_button_width, rect.height - 1)
                cr.fill()
            else:
                cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("combo_entry_background").get_color(), 0.9)))
                cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
                cr.fill()
        
        # Propagate expose to children.
        propagate_expose(widget, event)
        
        return True
    
gobject.type_register(ComboBox)    

