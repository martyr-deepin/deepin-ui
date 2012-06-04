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

class HSV(gtk.ColorSelection):
    '''HSV.'''
	
    def __init__(self):
        '''Init color selection.'''
        gtk.ColorSelection.__init__(self)
        
        # Remove right buttons.
        self.get_children()[0].remove(self.get_children()[0].get_children()[1])
        
        # Remove bottom color pick button.
        self.get_children()[0].get_children()[0].remove(self.get_children()[0].get_children()[0].get_children()[1])

gobject.type_register(HSV)
