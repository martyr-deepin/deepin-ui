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
from draw import draw_line
import gobject
import gtk

class Statusbar(EventBox):
    '''
    Statusbar.

    @undocumented: expose_status_separator
    '''

    def __init__(self,
                 height,
                 add_separator=False,
                 ):
        '''
        Initialize Statusbar class.

        @param height: Statusbar height.
        @param add_separator: Whether add separator between statusbar and window body, default is False.
        '''
        # Init.
        EventBox.__init__(self)
        self.set_size_request(-1, height)

        # Init status box.
        self.status_box = gtk.VBox()
        self.add(self.status_box)

        # Init separator.
        if add_separator:
            self.separator = gtk.HBox()
            self.separator.set_size_request(-1, 2)
            self.separator.connect("expose-event", self.expose_status_separator)
            self.status_box.pack_start(self.separator, False, False)

        # Init status item box.
        self.status_item_box = gtk.HBox()
        self.status_box.pack_start(self.status_item_box, True, True)

        # Show.
        self.show_all()

    def expose_status_separator(self, widget, event):
        '''
        Internal callback for `expose-event` signal.
        '''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw separator.
        cr.set_source_rgba(0, 0, 0, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 1, rect.x + rect.width - 1, rect.y + 1)

        cr.set_source_rgba(1, 1, 1, 0.5)
        draw_line(cr, rect.x + 1, rect.y + 2, rect.x + rect.width - 1, rect.y + 2)

        return True

gobject.type_register(Statusbar)
