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
from theme import ui_theme
from draw import draw_pixbuf
from utils import propagate_expose, get_event_coords

STAR_SIZE = 13

class StarBuffer(gobject.GObject):
    '''
    StarBuffer class.

    @undocumented: get_star_pixbufs
    '''

    def __init__(self,
                 star_level=5,
                 ):
        '''
        Initialize StarBuffer class.

        @param star_level: The level of star, default is 5.
        '''
        gobject.GObject.__init__(self)
        self.star_level = int(star_level)

    def render(self, cr, rect):
        '''
        Render star buffer on given cairo and rectangle.

        @param cr: The cairo object.
        @param rect: The render rectangle.
        '''
        for (star_index, star_pixbuf) in enumerate(self.get_star_pixbufs()):
            draw_pixbuf(cr,
                        star_pixbuf,
                        rect.x + star_index * STAR_SIZE,
                        rect.y + (rect.height - star_pixbuf.get_height()) / 2,
                        )

    def get_star_pixbufs(self):
        star_paths = ["star_background.png"] * 5

        for index in range(0, self.star_level / 2):
            star_paths[index] = "star_foreground.png"

        if self.star_level % 2 == 1:
            star_paths[self.star_level / 2] = "halfstar_background.png"

        return map(lambda path: ui_theme.get_pixbuf("star/%s" % path).get_pixbuf(), star_paths)

gobject.type_register(StarBuffer)

class StarView(gtk.Button):
    '''
    StarView class.

    @undocumented: expose_star_view
    @undocumented: motion_notify_star_view
    '''

    def __init__(self):
        '''
        Initialize StarView class.
        '''
        gtk.Button.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.star_buffer = StarBuffer()

        self.set_size_request(STAR_SIZE * 5, STAR_SIZE)

        self.connect("motion-notify-event", self.motion_notify_star_view)
        self.connect("expose-event", self.expose_star_view)

    def expose_star_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        self.star_buffer.render(cr, rect)

        # Propagate expose.
        propagate_expose(widget, event)

        return True

    def motion_notify_star_view(self, widget, event):
        (event_x, event_y) = get_event_coords(event)
        self.star_buffer.star_level = int(min(event_x / (STAR_SIZE / 2) + 1, 10))

        self.queue_draw()

gobject.type_register(StarView)
