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
from constant import BACKGROUND_IMAGE
from theme import ui_theme
from utils import get_match_parent, cairo_state
from draw import draw_pixbuf

class IconView(gtk.DrawingArea):
    '''Icon view.'''
	
    def __init__(self, 
                 background_pixbuf=ui_theme.get_pixbuf(BACKGROUND_IMAGE)):
        '''Init icon view.'''
        # Init.
        gtk.DrawingArea.__init__(self)
        self.background_pixbuf = background_pixbuf
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_can_focus(True) # can focus to response key-press signal
        self.items = []
        
        # Signal.
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        self.connect("expose-event", self.expose_icon_view)    
        self.connect("motion-notify-event", self.motion_icon_view)
        self.connect("button-press-event", self.button_press_icon_view)
        self.connect("button-release-event", self.button_release_icon_view)
        self.connect("leave-notify-event", self.leave_icon_view)
        self.connect("key-press-event", self.key_press_icon_view)
        self.connect("key-release-event", self.key_release_icon_view)
        
        # Redraw.
        self.redraw_request_list = []
        self.redraw_delay = 100 # 100 milliseconds should be enough for redraw
        gtk.timeout_add(self.redraw_delay, self.update_redraw_request_list)
        
        self.keymap = {}
        
    def add_items(self, items, insert_pos=None):
        '''Add items.'''
        if insert_pos == None:
            self.items += items
        else:
            self.items = self.items[0:insert_pos] + items + self.items[insert_pos::]
            
        self.queue_draw()    
        
    def expose_icon_view(self, widget, event):
        '''Expose list view.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
            
        # Draw background.
        with cairo_state(cr):
            cr.translate(-viewport.allocation.x, -viewport.allocation.y)
            cr.rectangle(offset_x, offset_y, 
                         viewport.allocation.x + viewport.allocation.width, 
                         viewport.allocation.y + viewport.allocation.height)
            cr.clip()
            
            draw_pixbuf(cr, self.background_pixbuf.get_pixbuf(), offset_x, offset_y)
            
        # Draw item.
        if len(self.items) > 0:
            with cairo_state(cr):
                # Don't draw any item out of viewport area.
                cr.rectangle(offset_x, offset_y,
                             viewport.allocation.width, 
                             viewport.allocation.height)        
                cr.clip()
                
                # Draw item.
                item_width, item_height = self.items[0].get_width(), self.items[0].get_height()
                columns = int(rect.width / item_width)
                
                for (index, item) in enumerate(self.items):
                    row = int(index / columns)
                    column = index % columns
                    render_x = rect.x + column * item_width
                    render_y = rect.y + row * item_height
                    
                    with cairo_state(cr):
                        # Don't allow draw out of item area.
                        cr.rectangle(render_x, render_y, item_width, item_height)
                        cr.clip()
                        
                        item.render(cr, gtk.gdk.Rectangle(render_x, render_y, item_width, item_height))

    def motion_icon_view(self, widget, event):
        '''Motion list view.'''
        pass

    def button_press_icon_view(self, widget, event):
        '''Button press event handler.'''
        pass

    def button_release_icon_view(self, widget, event):
        '''Button release event handler.'''
        pass
        
    def leave_icon_view(self, widget, event):
        '''leave-notify-event signal handler.'''
        pass
        
    def key_press_icon_view(self, widget, event):
        '''Callback to handle key-press signal.'''
        pass

    def key_release_icon_view(self, widget, event):
        '''Callback to handle key-release signal.'''
        pass
        
    def update_redraw_request_list(self):
        '''Update redraw request list.'''
        pass
    
    def get_offset_coordinate(self, widget):
        '''Get offset coordinate.'''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = get_match_parent(widget, "Viewport")
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)
        else:
            return (0, 0, viewport)
            
gobject.type_register(IconView)

class IconItem(gobject.GObject):
    '''Icon item.'''
	
    def __init__(self, pixbuf):
        '''Init item icon.'''
        gobject.GObject.__init__(self)
        self.pixbuf = pixbuf
        self.padding_x = 24
        self.padding_y = 24
        
    def get_width(self):
        '''Get width.'''
        return self.pixbuf.get_width() + self.padding_x * 2
        
    def get_height(self):
        '''Get height.'''
        return self.pixbuf.get_height() + self.padding_y * 2
    
    def render(self, cr, rect):
        '''Render item.'''
        draw_pixbuf(
            cr, 
            self.pixbuf, 
            rect.x + self.padding_x,
            rect.y + self.padding_y)
        
gobject.type_register(IconItem)
