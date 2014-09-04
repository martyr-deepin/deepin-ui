#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2012 smallevilbeast
#
# Author:     smallevilbeast <houshao55@gmail.com>
# Maintainer: smallevilbeast <houshao55@gmail.com>
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

from collections import defaultdict
from functools import partial
from types import FunctionType

class InvalidEvent(Exception):
    '''
    Raised if a non-defined event should be registered at a strict-mode
    event register.
    '''
    def __init__(self, event):
        self.event = event

    def __str__(self):
        return self.event


class EventRegister(object):
    '''
    Very simple event handler. Listening functions can register themselves
    and will be called when the signal they're listening for is emitted.
    There's no restriction for listening to events, you can listen to any
    event that might be never called if you want to.

    Example:
    >>> events = EventRegister()
    >>> @events.start
    ... def on_start_do_this():
    ...     print 'hi there'
    >>> @events.end
    ... def on_end_do_that(a, b):
    ...     print a, b

    >>> events.emit('foo') # nothing will happen 'cause nobody's listening
    >>> events.emit('start')
    hi there
    >>> event.emit('end', 42, 'x')
    42 x

    To avoid typos registering your events. you can use the 'strict' mode
    (subclass `EventRegister` and define an :attr:`__events__` list).
    Using the strict mode, you have to define all allowed events in the
    :attr:`__events__` attribute. Then, if someone wants to register an
    event not defined in that :attr:`__events__`, an `InvalidEvent` exception
    will be raised.

    >>> class MyStrictEvents(EventRegister):
    ...       __events__ = ('hi', 'there')
    >>> sevents = MyStrictEvents()
    >>> @sevents.hi
    ... def on_hi():
    ...     print 'Hi!'
    >>> @sevents.some_undefined_event
    ... def never_called():
    ...     pass
    Traceback (most recent call last):
    ...
    InvalidEvent: some_undefined_event

    You can have lazy callbacks, too:
    >>> events = EventRegister()
    >>> @events.some_signal
    ... def called_first():
    ...     print "First callback"
    >>> @events.some_signal(lazy=True)
    ... def called_last():
    ...     print "Last callback"
    >>> @events.some_signal
    ... def called_second():
    ...     print "Second callback"
    >>> events.emit('some_signal')
    First callback
    Second callback
    Last callback
    '''
    strict = False
    initialized = False

    def __init__(self):
        if hasattr(self, "__events__"):
            self.strict = True
            self.__events__ = list(self.__events__)

        self.events = defaultdict(list)
        self.all_events_listener = []

    def __getattr__(self, event):
        if event == "__events__":
            raise AttributeError(event)

        def register_event(*args, **kwargs):
            if args and isinstance(args[0], FunctionType):
                self.register_event(event, args[0])
                return args[0]
            else:
                def wrapper(func):
                    self.register_event(event, func, *args, **kwargs)
                    return func
                return wrapper
        return register_event

    def register_event(self, event, callback, lazy=False):
        '''
        Register `callback` for 'event', This is simliar to ::

            @myinstance.myevent
            def callback(...):
                ...

        where `myevent` is the value of the 'event' attribute.
        '''
        callback.__dict__['lazy'] = lazy
        if event == "all":
            self.all_events_listener.append(callback)
        elif self.strict and event not in self.__events__:
            raise InvalidEvent(event)
        else:
            self.events[event].append(callback)

    def emit(self, event, *args, **kwargs):
        '''
        Emit `event`. Calls all callbacks registered for this `event` and
        all callbacks rfegistered for *all* events

        (passing ``*args`` and ``**kwargs`` as parameters).

        Raises :exc:`InvalidEvent` if mode is strict and ``event`` is not
        defined in :attr:`__events__`.
        '''
        if self.strict and event not in self.__events__:
            raise InvalidEvent(event)

        lazy_callbacks = []

        if event in self.events:
            for func in self.events[event]:
                if func.__dict__['lazy']:
                    lazy_callbacks.append(func)
                else:
                    func(*args, **kwargs)

        for func in self.all_events_listener:
            if func.lazy:
                lazy_callbacks.append(partial(func, event))
            else:
                func(event, *args, **kwargs)

        for func in lazy_callbacks:
            func(*args, **kwargs)

class GEventRegister(EventRegister):
    '''
    Event register for the :class:`GSignals` class.
    Automatically converts signal names with underscores('foo_bar')
    to names with hyphens ('foo-bar').

    Same API as :class:`EventRegister`.
    '''

    def __init__(self, events=None):
        if events is not None:
            self.__events__ = events
        EventRegister.__init__(self)

    def __getattr__(self, event):
        if event == '__events__':
            raise AttributeError(event)
        return EventRegister.__getattr__(self, event.replace("_", "-"))

class GSignals(object):
    '''
    GObject/GSignals-compatible class mixin.

    Connected callbacks always have to take a ``sender`` as first argument
    (this is for GSignals compatibility reasons).

    :attr:`events` attribute: The :class:`GEventRegister`.
    '''
    __gsignals__ = None

    def __init__(self):
        events = self.__events__
        if self.__gsignals__ is None:
            self.__gsignals__ = {}
        else:
            events += self.__gsignals__.keys()

        self.events = GEventRegister()

    def connect(self, signal, callback, lazy=False):
        self.events.register_event(signal, callback, lazy)

    def emit(self, signal, *args, **kwargs):
        self.events.emit(signal, self, *args, **kwargs)

    def add_events(self, events):
        '''
        Add a list of events to the allowed events.
        '''
        self.events.__events__ += list(events)

    def add_event(self, event):
        '''
        Add a event to the allowed events.
        '''
        self.events.__events__ += [event]
