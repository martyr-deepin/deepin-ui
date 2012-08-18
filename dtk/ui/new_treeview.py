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
from utils import cairo_state, get_window_shadow_size
from skin_config import skin_config
from scrolled_window import ScrolledWindow

class TreeView(ScrolledWindow):
    '''
    TreeView widget.
    '''
	
    def __init__(self,
                 items=[],
                 sort_methods=[],
                 drag_data=None,
                 enable_multiple_select=True,
                 enable_drag_drop=True,
                 drag_icon_pixbuf=None,
                 start_drag_offset=50,
                 right_space=2,
                 top_bottom_space=3
                 ):
        '''
        Initialize TreeView class.
        '''
        # Init.
        ScrolledWindow.__init__(self, right_space, top_bottom_space)
        self.draw_area = gtk.DrawingArea()
        self.draw_align = gtk.Alignment()
        self.draw_align.set(0.5, 0.5, 1, 1)
        
        # Init treeview attributes.
        self.visible_items = []
        
        # Connect widgets.
        self.draw_align.add(self.draw_area)
        self.add_child(self.draw_align)
        
        # Handle signals.
        self.draw_area.connect("expose-event", self.expose_tree_view)
        
        # Add items.
        self.add_items(items)
        
    def add_items(self, items):
        '''
        Add items.
        '''
        self.visible_items += items
        
    def expose_tree_view(self, widget, event):
        '''
        Internal callback to handle `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw background.
        # (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
        # with cairo_state(cr):
        #     cr.translate(-self.allocation.x, -self.allocation.y)
        #     cr.rectangle(offset_x, offset_y, 
        #                  self.allocation.x + self.allocation.width, 
        #                  self.allocation.y + self.allocation.height)
        #     cr.clip()
            
        #     (shadow_x, shadow_y) = get_window_shadow_size(self.get_toplevel())
        #     skin_config.render_background(cr, widget, offset_x + shadow_x, offset_y + shadow_y)
        
        # Draw items.
        item_height = 0
        for item in self.visible_items:
            render_x = rect.x
            render_y = rect.y + item_height
            render_width = rect.width
            render_height = item.get_height()
            
            with cairo_state(cr):
                cr.rectangle(render_x, render_y, render_width, render_height)
                cr.clip()

                item.get_column_renders()[0](cr, gtk.gdk.Rectangle(render_x, render_y, render_width, render_height))
                
            item_height += item.get_height()    
        
        return False

    def get_offset_coordinate(self, widget):
        '''
        Get viewport offset coordinate and viewport.

        @param widget: ListView widget.
        @return: Return viewport offset and viewport: (offset_x, offset_y, viewport).
        '''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = self.get_child()
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)    

        else:
            return (0, 0, viewport)
        
gobject.type_register(TreeView)

class TreeItem(gobject.GObject):
    '''
    Tree item template use for L{ I{TreeView} <TreeView>}.
    '''
	
    __gsignals__ = {
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "add-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
        "remove-items" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self):
        '''
        Initialize TreeItem class.
        '''
        gobject.GObject.__init__(self)
        self.parent_item = None
        self.chlid_items = None
        self.row_index = None
        self.column_index = None
        
    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_height(self):
        pass
    
    def get_column_widths(self):
        pass
    
    def get_column_renders(self):
        pass
        
gobject.type_register(TreeItem)
