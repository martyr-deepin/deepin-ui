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
from scrolled_window import ScrolledWindow

class TreeView(ScrolledWindow):
    '''
    TreeView widget.
    '''
	
    def __init__(self,
                 items=[],
                 sort_methods=[],
                 row_normal_height=None,
                 row_select_height=None,
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
