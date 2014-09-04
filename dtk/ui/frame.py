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

import gobject
import gtk

class HorizontalFrame(gtk.Alignment):
    '''
    Horizontal frame to padding 1 pixel round child.
    '''

    def __init__(self,
                 padding=1,
                 xalign=0.0,
                 yalign=0.0,
                 xscale=1.0,
                 yscale=1.0):
        '''
        Initialize HorizontalFrame class.

        @param padding: Padding value.
        @param xalign: The fraction of horizontal free space to the left of the child widget. Ranges from 0.0 to 1.0.
        @param yalign: The fraction of vertical free space above the child widget. Ranges from 0.0 to 1.0.
        @param xscale: The fraction of horizontal free space that the child widget absorbs, from 0.0 to 1.0.
        @param yscale: The fraction of vertical free space that the child widget absorbs, from 0.0 to 1.0.
        '''
        # Init.
        gtk.Alignment.__init__(self)
        self.set(xalign, yalign, xscale, yscale)
        self.set_padding(0, 0, padding, padding)

gobject.type_register(HorizontalFrame)

class VerticalFrame(gtk.Alignment):
    '''
    Vertical frame to padding 1 pixel round child.
    '''

    def __init__(self,
                 padding=1,
                 xalign=0.0,
                 yalign=0.0,
                 xscale=1.0,
                 yscale=1.0):
        '''
        Initialize VerticalFrame class.

        @param padding: Padding value.
        @param xalign: The fraction of horizontal free space to the left of the child widget. Ranges from 0.0 to 1.0.
        @param yalign: The fraction of vertical free space above the child widget. Ranges from 0.0 to 1.0.
        @param xscale: The fraction of horizontal free space that the child widget absorbs, from 0.0 to 1.0.
        @param yscale: The fraction of vertical free space that the child widget absorbs, from 0.0 to 1.0.
        '''
        # Init.
        gtk.Alignment.__init__(self)
        self.set(xalign, yalign, xscale, yscale)
        self.set_padding(padding, padding, 0, 0)

gobject.type_register(VerticalFrame)
