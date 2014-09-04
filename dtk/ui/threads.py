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
import threading as td

def post_gui(func):
    '''
    Post GUI code in main thread.

    You should use post_gui wrap graphics function if function call from other threads.

    Usage:

    >>> @post_gui
    >>> def graphics_fun():
    >>>     ....
    '''
    def wrap(*a, **kw):
        gtk.gdk.threads_enter()
        ret = func(*a, **kw)
        gtk.gdk.threads_leave()
        return ret
    return wrap

class AnonymityThread(td.Thread):
    '''
    Anonymity thread.
    '''

    def __init__(self,
                 long_time_func,
                 render_func=None,
                 ):
        '''
        Initialize AnonymityThread class.

        @param long_time_func: Long time function.
        @param render_func: Render result function, this function have one input argument. By default, this argument is None.
        '''
        td.Thread.__init__(self)
        self.setDaemon(True)    # make thread exit when main program exit

        self.long_time_func = long_time_func
        self.render_func = render_func

    def run(self):
        '''Run.'''
        result = self.long_time_func()

        if self.render_func != None:
            self.render_func(result)

class Thread(td.Thread):
    '''
    Thread class that setDaemon(True)
    '''

    def __init__(self):
        '''
        Initialize Thread class.
        '''
        td.Thread.__init__(self)
        self.setDaemon(True)
