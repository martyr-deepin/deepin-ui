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

class MplayerView(gtk.DrawingArea):
    '''
    View to offer a drawing area for mplayer.

    MplayerView default disable double buffered to avoid video blinking when mplayer draw on it.

    @undocumented: realize_mplayer_view
    '''

    __gsignals__ = {
        "get-xid" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (long,))
    }

    def __init__(self):
        '''
        Initialize MplayerView class.
        '''
        # Init.
        gtk.DrawingArea.__init__(self)
        self.unset_flags(gtk.DOUBLE_BUFFERED) # disable double buffered to avoid video blinking

        # Handle signal.
        self.connect("realize", self.realize_mplayer_view)

    def realize_mplayer_view(self, widget):
        '''
        Internal callback for `realize` signal.
        '''
        if self.get_window() and self.get_window().xid:
            self.emit("get-xid", self.get_window().xid)

gobject.type_register(MplayerView)

