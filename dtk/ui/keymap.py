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
        modifiers.append("Ctrl")    
        
    # Add Super modifiers.
    if key_event.state & gdk.SUPER_MASK:
        modifiers.append("Super")
        
    # Add Hyper modifiers.
    if key_event.state & gdk.HYPER_MASK:
        modifiers.append("Hyper")
        
    # Add Alt modifier.
    if key_event.state & gdk.MOD1_MASK:
        modifiers.append("Alt")    
        
    # Don't need add Shift modifier if keyval is upper character.
    if key_event.state & gdk.SHIFT_MASK and (len(get_key_name(key_event.keyval)) != 1 or not gdk.keyval_is_upper(key_event.keyval)):
        modifiers.append("Shift")    
        
    return modifiers

def get_keyevent_name(key_event):
    '''Get key event name.'''
    if key_event.is_modifier:
        return ""
    else:
        key_modifiers = get_key_event_modifiers(key_event)
        key_name = get_key_name(key_event.keyval)
        if key_name == " ":
            key_name = "Space"
        
        if key_modifiers == []:
            return key_name
        else:
            return " + ".join(key_modifiers) + " + " + key_name
        
def parse_keyevent_name(keyevent_name):
    '''Parse keyevent name.'''
    keys = keyevent_name.split(" + ")
    if len(keys) == 1:
        keyval = int(gdk.keyval_from_name(keys[0]))
        modifier_mask = 0
    else:
        keyval = int(gdk.keyval_from_name(keys[-1]))
        modifier_mask = 0
        
        for modifier in keys[0:-1]:
            if modifier == "Ctrl":
                modifier_mask = modifier_mask | gdk.CONTROL_MASK
            elif modifier == "Super":
                modifier_mask = modifier_mask | gdk.SUPER_MASK
            elif modifier == "Hyper":
                modifier_mask = modifier_mask | gdk.HYPER_MASK
            elif modifier == "Alt":
                modifier_mask = modifier_mask | gdk.MOD1_MASK
            elif modifier == "Shift":
                modifier_mask = modifier_mask | gdk.SHIFT_MASK
                
        if gdk.keyval_is_upper(keyval) and len(get_key_name(keyval)) == 1:
            keyval = gdk.keyval_to_lower(keyval)
            modifier_mask = modifier_mask | gdk.SHIFT_MASK
            
    return (keyval, modifier_mask)

def has_ctrl_mask(key_event):
    '''Whether has ctrl mask in key event.'''
    return get_key_name(key_event.keyval) in ["Control_L", "Control_R"]

def has_shift_mask(key_event):
    '''Whether has shift mask in key event.'''
    return get_key_name(key_event.keyval) in ["Shift_L", "Shift_R"]
