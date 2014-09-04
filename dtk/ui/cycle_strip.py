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
from cache_pixbuf import CachePixbuf
from draw import draw_pixbuf

class CycleStrip(gtk.HBox):
    '''
    CycleStrip class.

    This widget use for cycle drawing background, but use CachePixbuf to accelerate render.

    @undocumented: expose_cycle_strip
    '''

    def __init__(self, background_dpixbuf):
        '''
        Initialize CycleStrip class.

        @param background_dpixbuf: DynamicPixbuf background.
        '''
        gtk.HBox.__init__(self)
        self.background_dpixbuf = background_dpixbuf
        self.cache_pixbuf = CachePixbuf()

        self.set_size_request(-1, self.background_dpixbuf.get_pixbuf().get_height())

        self.connect("expose-event", self.expose_cycle_strip)

    def expose_cycle_strip(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        background_pixbuf = self.background_dpixbuf.get_pixbuf()

        self.cache_pixbuf.scale(
            background_pixbuf,
            rect.width,
            rect.height)

        draw_pixbuf(
            cr,
            self.cache_pixbuf.get_cache(),
            rect.x,
            rect.y)

        return False

gobject.type_register(CycleStrip)
