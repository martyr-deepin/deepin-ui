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
import math

CURVE_LINEAR = lambda x: x
CURVE_SINE = lambda x: math.sin(math.pi / 2 * x)
FRAMERATE = 30.0

class Timeline(gobject.GObject):
    '''
    Timeline class.
    '''

    __gtype_name__ = 'Timeline'
    __gsignals__ = {
        'start': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_FLOAT,)),
        'stop': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'completed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

    def __init__(self,
                 duration,
                 curve,
                 ):
        '''
        Initialize Timeline class.

        @param duration: Animation duration.
        @param curve: Animation curve.
        '''
        gobject.GObject.__init__(self)

        self.duration = duration
        self.curve = curve

        self._states = []
        self._stopped = False
        self._started = False

    def run(self):
        '''
        Run.
        '''
        n_frames = (self.duration / 1000.0) * FRAMERATE

        while len(self._states) <= n_frames:
            self._states.append(self.curve(len(self._states) * (1.0 / n_frames)))
        self._states.reverse()

        self._started = True
        gobject.timeout_add(int(self.duration / n_frames), self.update)

    def stop(self):
        '''
        Stop.
        '''
        self._stopped = True
        self._started = False

    def update(self):
        '''
        Update.
        '''
        if self._started:
            self.emit("start")
            self._started = False

        if self._stopped:
            self.emit('stop')
            return False
        else:
            self.emit('update', self._states.pop())

            if len(self._states) == 0:
                self.emit('completed')
                return False
            return True

gobject.type_register(Timeline)
