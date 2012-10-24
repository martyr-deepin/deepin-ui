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

class TalkView(ScrolledWindow):
    '''
    View widget for Deepin Talk.
    '''
	
    def __init__(self,
                 right_space=2,
                 top_bottom_space=3):
        '''
        Initialize TalkView class.
        '''
        # Init.
        ScrolledWindow.__init__(self, right_space, top_bottom_space)
        self.draw_area = gtk.DrawingArea()
        self.draw_align = gtk.Alignment()
        self.draw_align.set(0.5, 0.5, 1, 1)
        
        self.draw_align.add(self.draw_area)
        self.add_child(self.draw_align)
        
gobject.type_register(TalkView)

class TalkItem(gobject.GObject):
    '''
    Talk item for L{ I{TalkView} <TalkView>}.
    '''
	
    def __init__(self):
        '''
        Initialize TalkItem class.
        '''
        gobject.GObject.__init__(self)
        
    def get_size(self):
        '''
        Get size of talk item.
        '''
        print "TalkItem.get_size: Your should implement this interface in your own class!"
        
    def render(self, cr, rect):
        '''
        Render talk item.
        '''
        print "TalkItem.render: Your should implement this interface in your own class!"
    

gobject.type_register(TalkItem)
