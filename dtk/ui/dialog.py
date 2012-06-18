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
from window import Window
from titlebar import Titlebar
from label import Label
from button import Button
from entry import TextEntry
from constant import ALIGN_MIDDLE

class ConfirmDialog(Window):
    '''Confir dialog.'''
	
    def __init__(self, 
                 title, 
                 message, 
                 default_width,
                 default_height,
                 confirm_callback=None, 
                 cancel_callback=None):
        '''Init confirm dialog.'''
        # Init.
        Window.__init__(self)
        self.set_modal(True)                                # grab focus to avoid build too many skin window
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_skip_taskbar_hint(True)                    # skip taskbar
        self.default_width = default_width
        self.default_height = default_height
        self.set_default_size(self.default_width, self.default_height)
        self.set_geometry_hints(None, self.default_width, self.default_height, -1, -1, -1, -1, -1, -1, -1, -1)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            title)
        
        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 1, 1)
        self.label_align.set_padding(0, 0, 10, 10)
        self.label = Label(message, text_x_align=ALIGN_MIDDLE)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 5, 5)
        self.button_box = gtk.HBox()
        
        self.confirm_button = Button("确认")
        self.cancel_button = Button("取消")
        
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        self.connect("destroy", lambda w: self.destroy())
        
        # Connect widgets.
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.label_align, True, True)
        self.window_frame.pack_start(self.button_align, False, False)
        
        self.label_align.add(self.label)
        
        self.button_align.add(self.button_box)        
        self.button_box.pack_start(self.confirm_button, False, False, 5)
        self.button_box.pack_start(self.cancel_button, False, False, 5)
        
        # Add move action.
        self.add_move_event(self.titlebar)
        
    def click_confirm_button(self):
        '''Click confirm button.'''
        if self.confirm_callback != None:
            self.confirm_callback()        
        
        self.destroy()
        
    def click_cancel_button(self):
        '''Click cancel button.'''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.destroy()
        
gobject.type_register(ConfirmDialog)

class InputDialog(Window):
    '''Input dialog.'''
	
    def __init__(self, 
                 title, 
                 init_text, 
                 default_width,
                 default_height,
                 confirm_callback=None, 
                 cancel_callback=None):
        '''Init confirm dialog.'''
        # Init.
        Window.__init__(self)
        self.set_modal(True)                                # grab focus to avoid build too many skin window
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_skip_taskbar_hint(True)                    # skip taskbar
        self.default_width = default_width
        self.default_height = default_height
        self.set_default_size(self.default_width, self.default_height)
        self.set_geometry_hints(None, self.default_width, self.default_height, -1, -1, -1, -1, -1, -1, -1, -1)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            title)
        
        self.entry_align = gtk.Alignment()
        self.entry_align.set(0.5, 0.5, 1, 1)
        self.entry_align.set_padding(0, 0, 10, 10)
        self.entry = TextEntry(init_text)
        self.entry.set_size(default_width - 20, 25)
        
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.5, 0, 0)
        self.button_align.set_padding(10, 10, 5, 5)
        self.button_box = gtk.HBox()
        
        self.confirm_button = Button("确认")
        self.cancel_button = Button("取消")
        
        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        self.connect("destroy", lambda w: self.destroy())
        
        # Connect widgets.
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.entry_align, True, True)
        self.window_frame.pack_start(self.button_align, False, False)
        
        self.entry_align.add(self.entry)
        
        self.button_align.add(self.button_box)        
        self.button_box.pack_start(self.confirm_button, False, False, 5)
        self.button_box.pack_start(self.cancel_button, False, False, 5)
        
        # Add move action.
        self.add_move_event(self.titlebar)
        
    def click_confirm_button(self):
        '''Click confirm button.'''
        if self.confirm_callback != None:
            self.confirm_callback(self.entry.get_text())        
        
        self.destroy()
        
    def click_cancel_button(self):
        '''Click cancel button.'''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.destroy()
        
gobject.type_register(InputDialog)

class OpenFileDialog(gtk.FileChooserDialog):
    '''Open file dialog.'''
	
    def __init__(self, title, parent, ok_callback=None, cancel_callback=None):
        '''Open file dialog.'''
        gtk.FileChooserDialog.__init__(
            self,
            title,
            parent,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_local_only(True)
        response = self.run()
        filename = self.get_filename()
        if response == gtk.RESPONSE_ACCEPT:
            if ok_callback != None:
                ok_callback(filename)
        elif response == gtk.RESPONSE_REJECT:
            if cancel_callback != None:
                cancel_callback(filename)
        self.destroy()
        
gobject.type_register(OpenFileDialog)
        
class SaveFileDialog(gtk.FileChooserDialog):
    '''Save file dialog.'''
	
    def __init__(self, title, parent, ok_callback=None, cancel_callback=None):
        '''Save file dialog.'''
        gtk.FileChooserDialog.__init__(
            self,
            title,
            parent,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_local_only(True)
        response = self.run()
        filename = self.get_filename()
        if response == gtk.RESPONSE_ACCEPT:
            if ok_callback != None:
                ok_callback(filename)
        elif response == gtk.RESPONSE_REJECT:
            if cancel_callback != None:
                cancel_callback(filename)
        self.destroy()
        
gobject.type_register(SaveFileDialog)

class DialogButtonBox(gtk.VBox):
    '''Dialog button box.'''
	
    def __init__(self, buttons):
        '''Init dialog button box.'''
        gtk.VBox.__init__(self)
        self.button_align = gtk.Alignment()
        self.button_align.set(0.5, 0.5, 1, 1)
        self.button_align.set_padding(5, 7, 0, 10)
        self.button_box = gtk.HBox()
        
        for button in buttons:
            self.button_box.pack_start(button, False, False, 4)
            
        self.button_align.add(self.button_box)    
        self.pack_start(self.button_align, False, False)

if __name__ == '__main__':
    dialog = ConfirmDialog("确认对话框", "你确定吗？", 200, 100)
    dialog.show_all()
    
    gtk.main()
