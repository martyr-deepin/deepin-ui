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

from keymap import get_keyevent_name
from button import Button
from constant import ALIGN_MIDDLE
from draw import draw_vlinear, draw_blank_mask
from new_entry import InputEntry
from label import Label
from locales import _
from mask import draw_mask
from skin_config import skin_config
from theme import ui_theme
from titlebar import Titlebar
from utils import container_remove_all
from window import Window
import gobject
import gtk

DIALOG_MASK_SINGLE_PAGE = 0
DIALOG_MASK_GLASS_PAGE = 1
DIALOG_MASK_MULTIPLE_PAGE = 2
DIALOG_MASK_TAB_PAGE = 3

class DialogLeftButtonBox(gtk.HBox):
    '''
    HBox to handle left side buttons in DialogBox.
    '''
	
    def __init__(self):
        '''
        Initialize DialogLeftButtonBox class.
        '''
        gtk.HBox.__init__(self)
        self.button_align = gtk.Alignment()
        self.button_align.set(0.0, 0.5, 0, 0)
        self.button_align.set_padding(5, 9, 7, 0)
        self.button_box = gtk.HBox()
        
        self.button_align.add(self.button_box)    
        self.pack_start(self.button_align, True, True)

    def set_buttons(self, buttons):
        '''
        Set buttons in box.

        @note: This functin will use new buttons B{instead} old buttons in button box.
        
        @param buttons: A list of Gtk.Widget instance.
        '''
        container_remove_all(self.button_box)
        for button in buttons:
            self.button_box.pack_start(button, False, False, 4)
            
gobject.type_register(DialogLeftButtonBox)

class DialogRightButtonBox(gtk.HBox):
    '''
    HBox to handle right side buttons in DialogBox.
    '''
	
    def __init__(self):
        '''
        Initialize DialogRightButtonBox class.
        '''
        gtk.HBox.__init__(self)
        self.button_align = gtk.Alignment()
        self.button_align.set(1.0, 0.5, 0, 0)
        self.button_align.set_padding(5, 9, 0, 7)
        self.button_box = gtk.HBox()
        
        self.button_align.add(self.button_box)    
        self.pack_start(self.button_align, True, True)

    def set_buttons(self, buttons):
        '''
        Set buttons in box.

        @note: This functin will use new buttons B{instead} old buttons in button box.
        
        @param buttons: A list of Gtk.Widget instance.
        '''
        container_remove_all(self.button_box)
        for button in buttons:
            self.button_box.pack_start(button, False, False, 4)
            
gobject.type_register(DialogRightButtonBox)

class DialogBox(Window):
    '''
    Dialog box to standard dialog layout and ui detail.
    
    If you want build a dialog, you should use this standard.
    
    @undocumented: draw_mask_single_page
    @undocumented: draw_mask_glass_page
    @undocumented: draw_mask_multiple_page
    @undocumented: draw_mask_tab_page
    '''
	
    def __init__(self, 
                 title, 
                 default_width=None, 
                 default_height=None, 
                 mask_type=None, 
                 close_callback=None,
                 modal=True,
                 window_hint=gtk.gdk.WINDOW_TYPE_HINT_DIALOG,
                 window_pos=None,
                 skip_taskbar_hint=True,
                 resizable=False):
        '''
        Initialize DialogBox class.
        
        @param title: Dialog title.
        @param default_width: Width of dialog, default is None.
        @param default_height: Height of dialog, default is None.
        @param mask_type: Background mask type, it allow use below type:
         - DIALOG_MASK_SINGLE_PAGE      single mask style, use in single page that background mask include dialog button area.
         - DIALOG_MASK_GLASS_PAGE       glass mask style, similar DIALOG_MASK_SINGLE_PAGE but with different color.
         - DIALOG_MASK_MULTIPLE_PAGE    multiple mask style, use in multiple page that background mask not include dialog button area.
         - DIALOG_MASK_TAB_PAGE         tab mask style, use in preference page that background mask not include button area.
        '''
        Window.__init__(self, resizable)
        self.default_width = default_width
        self.default_height = default_height
        self.mask_type = mask_type
        
        if window_pos:
            self.set_position(window_pos)
        self.set_modal(modal)                                # grab focus to avoid build too many skin window
        if window_hint:
            self.set_type_hint(window_hint)
        self.set_skip_taskbar_hint(skip_taskbar_hint) # skip taskbar
        if self.default_width != None and self.default_height != None:
            self.set_default_size(self.default_width, self.default_height)
            
            if not resizable:
                self.set_geometry_hints(None, self.default_width, self.default_height, -1, -1, -1, -1, -1, -1, -1, -1)
            
        self.padding_left = 2
        self.padding_right = 2

        self.titlebar = Titlebar(
            ["close"],
            None,
            title)
        self.add_move_event(self.titlebar)
        self.body_box = gtk.VBox()
        self.body_align = gtk.Alignment()
        self.body_align.set(0.5, 0.5, 1, 1)
        self.body_align.set_padding(0, 0, self.padding_left, self.padding_right)
        self.body_align.add(self.body_box)
        self.button_box = gtk.HBox()
        self.left_button_box = DialogLeftButtonBox()
        self.right_button_box = DialogRightButtonBox()

        self.button_box.pack_start(self.left_button_box, True, True)
        self.button_box.pack_start(self.right_button_box, True, True)
        
        self.window_frame.pack_start(self.titlebar, False, False)
        self.window_frame.pack_start(self.body_align, True, True)
        self.window_frame.pack_start(self.button_box, False, False)

        if close_callback:
            self.titlebar.close_button.connect("clicked", lambda w: close_callback())
            self.connect("destroy", lambda w: close_callback())
        else:
            self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
            self.connect("destroy", lambda w: self.destroy())
        
        self.draw_mask = self.get_mask_func(self, 1, 1, 0, 1)
        
    def get_mask_func(self, widget, padding_left=0, padding_right=0, padding_top=0, padding_bottom=0):
        '''
        Get mask function to render background, you can use this function to return \"render function\" to draw your ui to keep same style.

        @param widget: DialogBox widget.
        @param padding_left: Padding at left side. 
        @param padding_right: Padding at right side. 
        @param padding_top: Padding at top side. 
        @param padding_bottom: Padding at bottom side. 
        '''
        if self.mask_type == DIALOG_MASK_SINGLE_PAGE:
            return lambda cr, x, y, w, h: draw_mask(
                widget, x + padding_left, 
                y + padding_top, 
                w - padding_left - padding_right, 
                h - padding_top - padding_bottom,
                self.draw_mask_single_page)
        elif self.mask_type == DIALOG_MASK_GLASS_PAGE:
            return lambda cr, x, y, w, h: draw_mask(
                widget, x + padding_left, 
                y + padding_top, 
                w - padding_left - padding_right, 
                h - padding_top - padding_bottom,
                self.draw_mask_glass_page)
        elif self.mask_type == DIALOG_MASK_MULTIPLE_PAGE:
            return lambda cr, x, y, w, h: draw_mask(
                widget, x + padding_left, 
                y + padding_top, 
                w - padding_left - padding_right, 
                h - padding_top - padding_bottom,
                self.draw_mask_multiple_page)
        elif self.mask_type == DIALOG_MASK_TAB_PAGE:
            return lambda cr, x, y, w, h: draw_mask(
                widget, x + padding_left, 
                y + padding_top, 
                w - padding_left - padding_right, 
                h - padding_top - padding_bottom,
                self.draw_mask_tab_page)
        else:
            return lambda cr, x, y, w, h: draw_mask(
                widget, x + padding_left, 
                y + padding_top, 
                w - padding_left - padding_right, 
                h - padding_top - padding_bottom,
                draw_blank_mask)
        
    def draw_mask_single_page(self, cr, x, y, w, h):
        '''
        Internal render function for DIALOG_MASK_SINGLE_PAGE type.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        top_height = 70
        
        draw_vlinear(
            cr, x, y, w, top_height,
            ui_theme.get_shadow_color("mask_single_page_top").get_color_info(),
            )
        
        draw_vlinear(
            cr, x, y + top_height, w, h - top_height,
            ui_theme.get_shadow_color("mask_single_page_bottom").get_color_info(),
            )

    def draw_mask_glass_page(self, cr, x, y, w, h):
        '''
        Internal render function for DIALOG_MASK_GLASS_PAGE type.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        top_height = 70
        
        draw_vlinear(
            cr, x, y, w, top_height,
            ui_theme.get_shadow_color("mask_glass_page_top").get_color_info(),
            )
        
        draw_vlinear(
            cr, x, y + top_height, w, h - top_height,
            ui_theme.get_shadow_color("mask_glass_page_bottom").get_color_info(),
            )
        
    def draw_mask_multiple_page(self, cr, x, y, w, h):
        '''
        Internal render function for DIALOG_MASK_MULTIPLE_PAGE type.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        titlebar_height = self.titlebar.get_allocation().height
        button_box_height = self.right_button_box.get_allocation().height
        dominant_color = skin_config.dominant_color
        
        draw_vlinear(
            cr, x, y + titlebar_height, w, h - titlebar_height,
            ui_theme.get_shadow_color("mask_single_page_bottom").get_color_info(),
            )
        
        draw_vlinear(
            cr, x, y + h - button_box_height, w, button_box_height,
            [(0, (dominant_color, 1.0)),
             (1, (dominant_color, 1.0))])

        draw_vlinear(
            cr, x, y + h - button_box_height, w, button_box_height,
            ui_theme.get_shadow_color("mask_multiple_page").get_color_info(),
            )

    def draw_mask_tab_page(self, cr, x, y, w, h):
        '''
        Internal render function for DIALOG_MASK_TAB_PAGE type.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        button_box_height = self.right_button_box.get_allocation().height
        dominant_color = skin_config.dominant_color
        
        draw_vlinear(
            cr, x, y + h - button_box_height, w, button_box_height,
            [(0, (dominant_color, 1.0)),
             (1, (dominant_color, 1.0))])

        draw_vlinear(
            cr, x, y + h - button_box_height, w, button_box_height,
            ui_theme.get_shadow_color("mask_multiple_page").get_color_info(),
            )
        
gobject.type_register(DialogBox)

class ConfirmDialog(DialogBox):
    '''
    Simple message confirm dialog.
    
    @undocumented: click_confirm_button
    @undocumented: click_cancel_button
    '''
	
    def __init__(self, 
                 title, 
                 message, 
                 default_width=330,
                 default_height=145,
                 confirm_callback=None, 
                 cancel_callback=None, 
                 cancel_first=False, 
                 message_text_size=11):
        '''
        Initialize ConfirmDialog class.
        
        @param title: Title for confirm dialog.
        @param message: Confirm message.
        @param default_width: Dialog width, default is 330 pixel.
        @param default_height: Dialog height, default is 145 pixel.
        @param confirm_callback: Callback when user click confirm button.
        @param cancel_callback: Callback when user click cancel button.
        '''
        # Init.
        DialogBox.__init__(self, title, default_width, default_height, DIALOG_MASK_SINGLE_PAGE)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, 8, 8)
        self.label = Label(message, text_x_align=ALIGN_MIDDLE, text_size=message_text_size)
        
        self.confirm_button = Button(_("OK"))
        self.cancel_button = Button(_("Cancel"))
        
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        
        # Connect widgets.
        self.body_box.pack_start(self.label_align, True, True)
        self.label_align.add(self.label)
        
        if cancel_first:
            self.right_button_box.set_buttons([self.cancel_button, self.confirm_button])
        else:
            self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])
        
    def click_confirm_button(self):
        '''
        Internal function to handle click confirm button.
        '''
        if self.confirm_callback != None:
            self.confirm_callback()        
        
        self.destroy()
        
    def click_cancel_button(self):
        '''
        Internal function to handle click cancel button.
        '''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.destroy()
        
gobject.type_register(ConfirmDialog)

class InputDialog(DialogBox):
    '''
    Simple input dialog.
    
    @undocumented: click_confirm_button
    @undocumented: click_cancel_button
    '''
	
    def __init__(self, 
                 title, 
                 init_text, 
                 default_width=330,
                 default_height=145,
                 confirm_callback=None, 
                 cancel_callback=None, 
                 cancel_first=False):
        '''
        Initialize InputDialog class.
        
        @param title: Input dialog title.
        @param init_text: Initialize input text.
        @param default_width: Width of dialog, default is 330 pixel.
        @param default_height: Height of dialog, default is 330 pixel.
        @param confirm_callback: Callback when user click confirm button, this callback accept one argument that return by user input text.
        @param cancel_callback: Callback when user click cancel button, this callback not need argument.
        '''
        # Init.
        DialogBox.__init__(self, title, default_width, default_height, DIALOG_MASK_SINGLE_PAGE)
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        
        self.entry_align = gtk.Alignment()
        self.entry_align.set(0.5, 0.5, 0, 0)
        self.entry_align.set_padding(0, 0, 8, 8)
        self.entry = InputEntry(init_text)
        self.entry.set_size(default_width - 20, 25)
        
        self.confirm_button = Button(_("OK"))
        self.cancel_button = Button(_("Cancel"))
        
        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        
        self.entry_align.add(self.entry)
        self.body_box.pack_start(self.entry_align, True, True)
        
        if cancel_first:
            self.right_button_box.set_buttons([self.cancel_button, self.confirm_button])
        else:
            self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])
        
        self.connect("show", self.focus_input)
        self.entry.connect("key-press-event", self.m_key_press)

        self.keymap = {
            "Return" : self.m_press_return,
            }
    
    def m_key_press(self, widget, event):
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

        return True
    
    '''
    TODO: Add press 'Enter' key binding to confirm_button
    '''
    def m_press_return(self):
        self.click_confirm_button()

    def focus_input(self, widget):
        '''
        Grab focus on input entry.
        
        @param widget: InputDialog widget.
        '''
        self.entry.entry.grab_focus()        
        
    def click_confirm_button(self):
        '''
        Inernal fucntion to handle click confirm button.
        '''
        if self.confirm_callback != None:
            self.confirm_callback(self.entry.get_text())        
        
        self.destroy()
        
    def click_cancel_button(self):
        '''
        Inernal fucntion to handle click cancel button.
        '''
        if self.cancel_callback != None:
            self.cancel_callback()
        
        self.destroy()
        
gobject.type_register(InputDialog)

class OpenFileDialog(gtk.FileChooserDialog):
    '''
    Simple dialog to open file.
    '''
	
    def __init__(self, title, parent, ok_callback=None, cancel_callback=None):
        '''
        Initialize OpenFileDialog class.
        
        @param title: Dialog title.
        @param parent: Parent widget to call open file dialog.
        @param ok_callback: Callback when user click ok button, this function accept one argument: filename.
        @param cancel_callback: Callback when user click cancel button, this function accept one argument: filename.
        '''
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
    '''
    Simple dialog to save file.
    '''
	
    def __init__(self, title, parent, ok_callback=None, cancel_callback=None):
        '''
        Initialize SaveFileDialog class.
        
        @param title: Dialog title.
        @param parent: Parent widget to call open file dialog.
        @param ok_callback: Callback when user click ok button, this function accept one argument: filename.
        @param cancel_callback: Callback when user click cancel button, this function accept one argument: filename.
        '''
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
