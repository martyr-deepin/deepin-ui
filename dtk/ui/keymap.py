#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Wang Yong
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

import gtk.gdk as gdk
import pygtk
pygtk.require('2.0')

def get_key_name(keyval):
    '''Get key name.'''
    key_unicode = gdk.keyval_to_unicode(keyval)
    if key_unicode == 0:
        return gdk.keyval_name(keyval)
    else:
        return str(unichr(key_unicode))
    
def get_key_event_modifiers(key_event):
    '''Get key event modifiers.'''
    modifiers = []
    
    # Add Ctrl modifier.
    if key_event.state & gdk.CONTROL_MASK:
        modifiers.append("C")
        
    # Add Alt modifier.
    if key_event.state & gdk.MOD1_MASK:
        modifiers.append("M")
        
    # Don't need add Shift modifier if keyval is upper character.
    if key_event.state & gdk.SHIFT_MASK and (len(get_key_name(key_event.keyval)) != 1 or not gdk.keyval_is_upper(key_event.keyval)):
        modifiers.append("S")
        
    return modifiers

def get_keyevent_name(key_event):
    '''Get key event name.'''
    if key_event.is_modifier:
        return ""
    else:
        key_modifiers = get_key_event_modifiers(key_event)
        key_name = get_key_name(key_event.keyval)
        
        if key_modifiers == []:
            return key_name
        else:
            return "-".join(key_modifiers) + "-" + key_name

def has_ctrl_mask(key_event):
    '''Whether has ctrl mask in key event.'''
    return get_key_name(key_event.keyval) in ["Control_L", "Control_R"]

def has_shift_mask(key_event):
    '''Whether has shift mask in key event.'''
    return get_key_name(key_event.keyval) in ["Shift_L", "Shift_R"]
