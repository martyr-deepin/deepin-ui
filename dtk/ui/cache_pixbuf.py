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

class CachePixbuf(object):
    '''
    Cache pixbuf use to cache pixbuf to avoid new pixbuf generate by scale_simple.

    gtk.gdk.pixbuf.scale_simple is function will make application very slow,

    We use CachePixbuf increase the call times of gtk.gdk.pixbuf.scale_simple.
    '''

    def __init__(self):
        '''
        Init cache pixbuf.
        '''
        self.pixbuf = None
        self.cache_pixbuf = None
        self.scale_width = None
        self.scale_height = None
        self.vertical_mirror = False
        self.horizontal_mirror = False

    def scale(self, pixbuf, scale_width, scale_height, vertical_mirror=False, horizontal_mirror=False):
        '''
        Scale with given sizce and return new pixbuf.

        @param pixbuf: Original pixbuf.
        @param scale_width: Scale width of pixbuf.
        @param scale_height: Scale height of pixbuf.
        @param vertical_mirror: Whether pixbuf mirror vertically.
        @param horizontal_mirror: Whether pixbuf mirror horizontally.
        '''
        if self.pixbuf != pixbuf or self.scale_width != scale_width or self.scale_height != scale_height:
            # Record init value.
            self.pixbuf = pixbuf # pixbuf always is same as create from file
            self.scale_width = scale_width
            self.scale_height = scale_height

            # Scale size.
            self.cache_pixbuf = pixbuf.scale_simple(scale_width, scale_height, gtk.gdk.INTERP_BILINEAR)

            # If vertical_mirror default is True, vertical mirror *original* pixbuf first.
            if self.vertical_mirror:
                self.cache_pixbuf = self.cache_pixbuf.flip(True)

            # If horizontal_mirror default is True, horizontal mirror *original* pixbuf first.
            if self.horizontal_mirror:
                self.cache_pixbuf = self.cache_pixbuf.flip(False)

        # If vertical_mirror changed, vertical mirror *self* first
        if self.vertical_mirror != vertical_mirror:
            self.vertical_mirror = vertical_mirror
            self.cache_pixbuf = self.cache_pixbuf.flip(True)

        # If horizontal_mirror changed, horizontal mirror *self* first
        if self.horizontal_mirror != horizontal_mirror:
            self.horizontal_mirror = horizontal_mirror
            self.cache_pixbuf = self.cache_pixbuf.flip(False)

    def get_cache(self):
        '''
        Get pixbuf cache.

        @return: Return cache pixbuf.
        '''
        return self.cache_pixbuf

