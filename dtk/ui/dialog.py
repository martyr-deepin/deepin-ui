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

class DialogButtonBox(gtk.HBox):
    '''Dialog button box.'''
	
    def __init__(self):
        '''Init dialog button box.'''
        gtk.HBox.__init__(self)
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 1.0, 0, 0)
        self.button_align.set_padding(5, 9, 0, 7)
        self.button_box = gtk.HBox()
        
        self.button_align.add(self.button_box)    
        self.pack_start(self.button_align, True, True)

    def add_buttons(self, buttons):
        '''Add buttons.'''
        for button in buttons:
            self.button_box.pack_start(button, False, False, 4)
            
gobject.type_register(DialogButtonBox)

class DialogBox(Window):
    '''Dialog box.'''
	
    def __init__(self, title, default_width=None, default_height=None):
        '''Dialog box.'''
        Window.__init__(self)
        self.set_modal(True)                                # grab focus to avoid build too many skin window
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG) # keeep above
        self.set_skip_taskbar_hint(True)                    # skip taskbar
        self.set_resizable(False)
        self.default_width = default_width
        self.default_height = default_height
        if self.default_width != None and self.default_height != None:
            self.set_default_size(self.default_width, self.default_height)
            self.set_geometry_hints(None, self.default_width, self.default_height, -1, -1, -1, -1, -1, -1, -1, -1)

        self.titlebar = Titlebar(
            ["close"],
            None,
            None,
            title)
        self.add_move_event(self.titlebar)
        self.body_box = gtk.VBox()
        self.button_box = DialogButtonBox()
        
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.body_box, True, True)
        self.window_frame.pack_start(self.button_box, False, False)

        self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
        self.connect("destroy", lambda w: self.destroy())
        
gobject.type_register(DialogBox)

class ConfirmDialog(DialogBox):
    '''Confir dialog.'''
	
    def __init__(self, 
                 title, 
                 message, 
                 default_width=330,
                 default_height=145,
                 confirm_callback=None, 
                 cancel_callback=None):
        '''Init confirm dialog.'''
        # Init.
        DialogBox.__init__(self, title, default_width, default_height)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, 10, 10)
        self.label = Label(message, text_x_align=ALIGN_MIDDLE, text_size=11)
        
        self.confirm_button = Button("确认")
        self.cancel_button = Button("取消")
        
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        
        # Connect widgets.
        self.body_box.pack_start(self.label_align, True, True)
        self.label_align.add(self.label)
        
        self.button_box.add_buttons([self.confirm_button, self.cancel_button])
        
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

class InputDialog(DialogBox):
    '''Input dialog.'''
	
    def __init__(self, 
                 title, 
                 init_text, 
                 default_width=330,
                 default_height=145,
                 confirm_callback=None, 
                 cancel_callback=None):
        '''Init confirm dialog.'''
        # Init.
        DialogBox.__init__(self, title, default_width, default_height)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.entry_align = gtk.Alignment()
        self.entry_align.set(0.5, 0.5, 0, 0)
        self.entry_align.set_padding(0, 0, 10, 10)
        self.entry = TextEntry(init_text)
        self.entry.set_size(default_width - 20, 25)
        
        self.confirm_button = Button("确认")
        self.cancel_button = Button("取消")
        
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        
        self.entry_align.add(self.entry)
        self.body_box.pack_start(self.entry_align, True, True)
        
        self.button_box.add_buttons([self.confirm_button, self.cancel_button])
        
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


if __name__ == '__main__':
    dialog = ConfirmDialog("确认对话框", "你确定吗？", 200, 100)
    dialog.show_all()
    
    gtk.main()
