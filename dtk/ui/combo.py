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
import gobject
from label import Label
from droplist import Droplist
from theme import ui_theme
from draw import draw_pixbuf
from utils import propagate_expose, cairo_disable_antialias, color_hex_to_cairo, get_widget_root_coordinate, WIDGET_POS_BOTTOM_LEFT, alpha_color_hex_to_cairo

class ComboBox(gtk.VBox):
    '''Combo box.'''
	
    __gsignals__ = {
        "item-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, gobject.TYPE_PYOBJECT, int,)),
    }

    def __init__(self, items, droplist_height=None, select_index=0, droplist_max_width=None):
        '''Init combo box.'''
        # Init.
        gtk.VBox.__init__(self)
        self.items = items
        self.droplist_height = droplist_height
        self.disable_flag = False
        self.select_index = select_index
        
        self.droplist = Droplist(self.items, max_width=droplist_max_width)
        if self.droplist_height:
            self.droplist.set_size_request(-1, self.droplist_height)
        self.width = self.droplist.get_droplist_width() 
        self.height = 22
        self.box = gtk.HBox()
        dropbutton_width = ui_theme.get_pixbuf("combo/dropbutton_normal.png").get_pixbuf().get_width()
        self.label = Label(self.items[select_index][0], label_size=(self.width - dropbutton_width - 1, self.height - 2))
        self.dropbutton = DropButton(
            (ui_theme.get_pixbuf("combo/dropbutton_normal.png"),
             ui_theme.get_pixbuf("combo/dropbutton_hover.png"),
             ui_theme.get_pixbuf("combo/dropbutton_press.png"),
             ui_theme.get_pixbuf("combo/dropbutton_disable.png")),
            self.get_disable
            )
                
        self.align = gtk.Alignment()
        self.align.set(0.5, 0.5, 0.0, 0.0)
        self.align.set_padding(1, 1, 1, 1)
        
        self.pack_start(self.align, False, False)
        self.align.add(self.box)
        self.box.pack_start(self.label, False, False)
        self.box.pack_start(self.dropbutton, False, False)
        
        self.align.connect("expose-event", self.expose_combobox_frame)
        self.label.connect("button-press-event", self.click_drop_button)
        self.dropbutton.connect("button-press-event", self.click_drop_button)
        self.droplist.connect("item-selected", self.update_select_content)
        
    def set_select_item(self, item):
        '''Set select item.'''
        if item in self.droplist.droplist_items:
            self.select_index = self.droplist.droplist_items.index(item)
            self.label.set_text(item.item[0])
            
    def set_select_index(self, item_index):
        '''Set select index.'''
        if 0 <= item_index < len(self.droplist_items):
            item = self.droplist.droplist_items[item_index]
            if isinstance(item.item_box, gtk.Button):
                self.select_index = item_index
                self.label.set_text(item.item[0])
                
    def update_select_content(self, droplist, item_content, item_value, item_index):
        '''Update select content.'''
        self.select_index = item_index
        self.label.set_text(item_content)
        
        self.emit("item-selected", item_content, item_value, item_index)
        
    def click_drop_button(self, *args):
        '''Click drop button.'''
        if self.droplist.get_visible():
            self.droplist.hide()
        else:
            (align_x, align_y) = get_widget_root_coordinate(self.align, WIDGET_POS_BOTTOM_LEFT)
            self.droplist.show(
                (align_x - 1, align_y - 1),
                (0, -self.height + 1))
            
            self.droplist.item_select_index = self.select_index
            self.droplist.active_item()
        
    def set_disable(self, disable_flag):
        '''Disable.'''
        self.disable_flag = disable_flag
        
        self.queue_draw()
        
    def get_disable(self):
        '''Get disable flag.'''
        return self.disable_flag
        
    def expose_combobox_frame(self, widget, event):
        '''Expose combo box frame.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw frame.
        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            if self.get_disable():
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("comboEntryDisableFrame").get_color()))
            else:
                cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("comboEntryFrame").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            cr.set_source_rgba(*alpha_color_hex_to_cairo((ui_theme.get_color("comboEntryBackground").get_color(), 0.9)))
            cr.rectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)
            cr.fill()
        
        # Propagate expose to children.
        propagate_expose(widget, event)
        
        return True
    
gobject.type_register(ComboBox)    

class DropButton(gtk.Button):
    '''Drop button.'''
	
    def __init__(self, dpixbufs, get_disable):
        '''Init drop button.'''
        gtk.Button.__init__(self)
        pixbuf = dpixbufs[0].get_pixbuf()
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        
        self.connect("expose-event", lambda w, e: self.expose_drop_button(w, e, dpixbufs, get_disable))
        
    def expose_drop_button(self, widget, event, dpixbufs, get_disable):
        '''Expose drop button.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        (normal_dpixbuf, hover_dpixbuf, press_dpixbuf, disable_dpixbuf) = dpixbufs
        
        # Draw.
        if get_disable():
            pixbuf = disable_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_NORMAL:
            pixbuf = normal_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_PRELIGHT:
            pixbuf = hover_dpixbuf.get_pixbuf()
        elif widget.state == gtk.STATE_ACTIVE:
            pixbuf = press_dpixbuf.get_pixbuf()
        
        draw_pixbuf(cr, pixbuf, rect.x, rect.y)    
        
        # Propagate expose to children.
        propagate_expose(widget, event)
        
        return True
