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

from box import EventBox
from constant import DEFAULT_FONT_SIZE
from draw import draw_line, draw_pixbuf, draw_text
from theme import ui_theme
from utils import widget_fix_cycle_destroy_bug, propagate_expose
import gobject
import gtk
import pango

class Navigatebar(EventBox):
    '''Navigatebar.'''
    
    def __init__(self, items, add_separator=False, font_size=DEFAULT_FONT_SIZE, padding_x=10, padding_y=10):
        '''Init navigatebar.'''
        # Init event box.
        EventBox.__init__(self)
        self.nav_index = 0
        
        # Init nav box.
        self.nav_box = gtk.VBox()
        self.add(self.nav_box)
        
        # Init item box.
        self.nav_item_box = gtk.HBox()
        self.nav_box.pack_start(self.nav_item_box, False, False)
        
        # Add navigate item.
        if items:
            for (index, item) in enumerate(items):
                nav_item = NavItem(item, index, font_size, padding_x, padding_y, self.set_index, self.get_index)
                self.nav_item_box.pack_start(nav_item.item_box, False, False)
                
        # Add separator.
        if add_separator:                
            self.separator = gtk.HBox()
            self.separator.set_size_request(-1, 2)
            self.separator.connect("expose-event", self.expose_navseparator)
            self.nav_box.pack_start(self.separator, False, False)
        
        # Show.
        self.show_all()
        
    def set_index(self, index):
        '''Set index.'''
        self.nav_item_box.queue_draw()
        self.nav_index = index
        
    def get_index(self):
        '''Get index.'''
        return self.nav_index
    
    def expose_navseparator(self, widget, event):
        '''Expose nav separator.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
    
        # Draw separator.
        cr.set_source_rgba(1, 1, 1, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 1, rect.x + rect.width - 1, rect.y + 1)
    
        cr.set_source_rgba(0, 0, 0, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 2, rect.x + rect.width - 1, rect.y + 2)
        
        return True

gobject.type_register(Navigatebar)

class NavItem(object):
    '''Navigate item.'''
	
    def __init__(self, element, index, font_size, padding_x, padding_y, set_index, get_index):
        '''Init navigate item.'''
        # Init.
        self.index = index
        self.font_size = font_size
        self.set_index = set_index
        self.get_index = get_index
        (self.icon_dpixbuf, self.content, self.clicked_callback) = element
        pixbuf = ui_theme.get_pixbuf("navigatebar/nav_item_hover.png").get_pixbuf()
        
        # Init item button.
        self.item_button = gtk.Button()
        self.item_button.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        
        widget_fix_cycle_destroy_bug(self.item_button)
        
        self.item_button.connect("expose-event", self.expose_nav_item)
        self.item_button.connect("clicked", lambda w: self.wrap_nav_item_clicked_action())
        
        # Init item box.
        self.item_box = gtk.Alignment()
        self.item_box.set(0.0, 0.0, 0.0, 0.0)
        self.item_box.set_padding(padding_y, padding_y, padding_x, padding_x)
        self.item_box.add(self.item_button)

    def wrap_nav_item_clicked_action(self):
        '''Wrap clicked action.'''
        if self.clicked_callback:
            self.clicked_callback()
        self.set_index(self.index)
        
    def expose_nav_item(self, widget, event):
        '''Expose navigate item.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        select_index = self.get_index()
        hover_pixbuf = ui_theme.get_pixbuf("navigatebar/nav_item_hover.png").get_pixbuf()
        press_pixbuf = ui_theme.get_pixbuf("navigatebar/nav_item_press.png").get_pixbuf()
        
        # Draw background.
        if widget.state == gtk.STATE_NORMAL:
            if select_index == self.index:
                select_pixbuf = press_pixbuf
            else:
                select_pixbuf = None
        elif widget.state == gtk.STATE_PRELIGHT:
            if select_index == self.index:
                select_pixbuf = press_pixbuf
            else:
                select_pixbuf = hover_pixbuf
        elif widget.state == gtk.STATE_ACTIVE:
            select_pixbuf = press_pixbuf
            
        if select_pixbuf:
            draw_pixbuf(cr, select_pixbuf, rect.x, rect.y)
        
        # Draw navigate item.
        nav_item_pixbuf = self.icon_dpixbuf.get_pixbuf()
        draw_pixbuf(
            cr, nav_item_pixbuf, 
            rect.x + (rect.width - nav_item_pixbuf.get_width()) / 2,
            rect.y)
        
        # Draw font.
        draw_text(cr, 
                  self.content, 
                  rect.x, 
                  rect.y + nav_item_pixbuf.get_height() - 3, 
                  rect.width, 
                  rect.height - nav_item_pixbuf.get_height(),
                  text_color="#FFFFFF",
                  alignment=pango.ALIGN_CENTER,
                  gaussian_radious=2, gaussian_color="#000000",
                  border_radious=1, border_color="#000000", 
                  )
        
        # Propagate expose to children.
        propagate_expose(widget, event)
    
        return True
    
