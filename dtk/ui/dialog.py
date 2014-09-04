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
from entry import InputEntry
from label import Label
from locales import _
from mask import draw_mask
from skin_config import skin_config
from theme import ui_theme
from titlebar import Titlebar
from utils import container_remove_all, alpha_color_hex_to_cairo, place_center
from window import Window
from treeview import TreeView, TextItem, IconTextItem, draw_background
from box import BackgroundBox
import pango
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

        @note: This function will use new buttons B{instead} old buttons in button box.

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

        @note: This function will use new buttons B{instead} old buttons in button box.

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
                 resizable=False,
                 window_type=gtk.WINDOW_TOPLEVEL,
                 ):
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
        @param close_callback: The callback that will call when close dialog box, callback don't need input argument.
        @param modal: If modal is True the window becomes modal. Modal windows prevent interaction with other windows in the same application.
        @param window_hint: Sets the window type hint, default is gtk.gdk.WINDOW_TYPE_HINT_DIALOG, it allow use below value:
         - gtk.gdk.WINDOW_TYPE_HINT_NORMAL                          A normal toplevel window.
         - gtk.gdk.WINDOW_TYPE_HINT_DIALOG                          A dialog window.
         - gtk.gdk.WINDOW_TYPE_HINT_MENU                            A window used to implement a menu.
         - gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR                         A window used to implement a toolbar.
         - gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN                    A window used to implement a splash screen
         - gtk.gdk.WINDOW_TYPE_HINT_UTILITY
         - gtk.gdk.WINDOW_TYPE_HINT_DOCK                            A window used to implement a docking bar.
         - gtk.gdk.WINDOW_TYPE_HINT_DESKTOP                         A window used to implement a desktop.
         - gtk.gdk.WINDOW_TYPE_HINT_DROPDOWN_MENU                   A menu that belongs to a menubar.
         - gtk.gdk.WINDOW_TYPE_HINT_POPUP_MENU                      A menu that does not belong to a menubar, e.g. a context menu.
         - gtk.gdk.WINDOW_TYPE_HINT_TOOLTIP                         A tooltip.
         - gtk.gdk.WINDOW_TYPE_HINT_NOTIFICATION                    A notification - typically a "bubble" that belongs to a status icon.
         - gtk.gdk.WINDOW_TYPE_HINT_COMBO                           A popup from a combo box.
         - gtk.gdk.WINDOW_TYPE_HINT_DND                             A window that is used to implement a DND cursor.
        @param window_pos: The window position of window, it can use below value:
         - gtk.WIN_POS_NONE                      No influence is made on placement.
         - gtk.WIN_POS_CENTER                    Windows should be placed in the center of the screen.
         - gtk.WIN_POS_MOUSE                     Windows should be placed at the current mouse position.
         - gtk.WIN_POS_CENTER_ALWAYS             Keep window centered as it changes size, etc.
         - gtk.WIN_POS_CENTER_ON_PARENT          Center the window on its transient parent (see the gtk.Window.set_transient_for()) method.
        @param skip_taskbar_hint: Set True to make desktop environment not to display the window in the task bar, default is True.
        @param resizable: Whether allowed user resizable dialog, default is False.
        '''
        Window.__init__(
            self,
            enable_resize=resizable,
            window_type=window_type,
            )
        self.default_width = default_width
        self.default_height = default_height
        self.mask_type = mask_type
        self.close_callback = close_callback

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

        if self.close_callback:
            self.titlebar.close_button.connect("clicked", lambda w: self.close_callback())
            self.connect("destroy", lambda w: self.close_callback())
            self.connect("delete-event", lambda w, e: self.close_callback())
        else:
            self.titlebar.close_button.connect("clicked", lambda w: self.destroy())
            self.connect("destroy", lambda w: self.destroy())
            self.connect("delete-event", lambda w, e: self.destroy())

        self.draw_mask = self.get_mask_func(self, 1, 1, 0, 1)

        self.keymap = {
            "Escape" : self.close,
            }

        self.connect("key-press-event", self.key_press_dialog_box)

    def key_press_dialog_box(self, widget, event):
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

            return True
        else:
            return False

    def close(self):
        if self.close_callback:
            self.close_callback()
        else:
            self.destroy()

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
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
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
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
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
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
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
        @param x: X coordinate of draw area.
        @param y: Y coordinate of draw area.
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

    def place_center(self, window=None):
        '''
        Place dialog at center place.

        @param window: Place dialog at screen center place if window is None, otherwise place center place of given window.
        '''
        if window == None:
            self.set_position(gtk.WIN_POS_CENTER)
        else:
            place_center(self, window)

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
                 cancel_first=True,
                 message_text_size=11,
                 window_type=gtk.WINDOW_TOPLEVEL,
                 close_callback=None,
                 text_wrap_width=None,
                 ):
        '''
        Initialize ConfirmDialog class.

        @param title: Title for confirm dialog.
        @param message: Confirm message.
        @param default_width: Dialog width, default is 330 pixel.
        @param default_height: Dialog height, default is 145 pixel.
        @param confirm_callback: Callback when user click confirm button.
        @param cancel_callback: Callback when user click cancel button.
        @param cancel_first: Set as True if to make cancel button before confirm button, default is True.
        @param message_text_size: Text size of message, default is 11.
        '''
        # Init.
        DialogBox.__init__(
            self, title, default_width, default_height, DIALOG_MASK_SINGLE_PAGE,
            window_type=window_type,
            close_callback=close_callback,
            )
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback

        self.label_align = gtk.Alignment()
        self.label_align.set(0.5, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, 8, 8)
        self.label = Label(
            message,
            text_x_align=ALIGN_MIDDLE,
            text_size=message_text_size,
            wrap_width=text_wrap_width,
            )

        self.confirm_button = Button(_("OK"))
        self.cancel_button = Button(_("Cancel"))

        self.confirm_button.connect("clicked", lambda w: self.click_confirm_button())
        self.cancel_button.connect("clicked", lambda w: self.click_cancel_button())
        self.cancel_button.connect("key-press-event", self.key_press_confirm_dialog)

        # Connect widgets.
        self.body_box.pack_start(self.label_align, True, True)
        self.label_align.add(self.label)

        if cancel_first:
            self.right_button_box.set_buttons([self.cancel_button, self.confirm_button])
        else:
            self.right_button_box.set_buttons([self.confirm_button, self.cancel_button])

        self.keymap = {
            "Return" : self.click_confirm_button,
            "Escape" : self.close,
            }

    def key_press_confirm_dialog(self, widget, event):
        key_name = get_keyevent_name(event)
        if self.keymap.has_key(key_name):
            self.keymap[key_name]()

            return True
        else:
            return False

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
    @undocumented: m_key_press
    '''

    def __init__(self,
                 title,
                 init_text,
                 default_width=330,
                 default_height=145,
                 confirm_callback=None,
                 cancel_callback=None,
                 cancel_first=True):
        '''
        Initialize InputDialog class.

        @param title: Input dialog title.
        @param init_text: Initialize input text.
        @param default_width: Width of dialog, default is 330 pixel.
        @param default_height: Height of dialog, default is 330 pixel.
        @param confirm_callback: Callback when user click confirm button, this callback accept one argument that return by user input text.
        @param cancel_callback: Callback when user click cancel button, this callback not need argument.
        @param cancel_first: Set as True if to make cancel button before confirm button, default is True.
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
        Internal function to handle click confirm button.
        '''
        if self.confirm_callback != None:
            self.confirm_callback(self.entry.get_text())

        self.destroy()

    def click_cancel_button(self):
        '''
        Infernal function to handle click cancel button.
        '''
        if self.cancel_callback != None:
            self.cancel_callback()

        self.destroy()

gobject.type_register(InputDialog)

class OpenFileDialog(gtk.FileChooserDialog):
    '''
    Simple dialog to open file.
    '''

    def __init__(self,
                 title,
                 parent,
                 ok_callback=None,
                 cancel_callback=None,
                 ):
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

    def __init__(self,
                 title,
                 parent,
                 ok_callback=None,
                 cancel_callback=None,
                 ):
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

class PreferenceDialog(DialogBox):
    '''
    PreferenceDialog class.

    @undocumented: button_press_preference_item
    @undocumented: set_item_widget
    @undocumented: draw_treeview_mask
    '''

    def __init__(self,
                 default_width=575,
                 default_height=495,
                 ):
        '''
        Initialize PreferenceDialog class.

        @param default_width: The default width, default is 575 pixels.
        @param default_height: The default height, default is 495 pixels.
        '''
        DialogBox.__init__(
            self,
            _("Preferences"),
            default_width,
            default_height,
            mask_type=DIALOG_MASK_MULTIPLE_PAGE,
            close_callback=self.hide_dialog,
            )
        self.set_position(gtk.WIN_POS_CENTER)

        self.main_box = gtk.VBox()
        close_button = Button(_("Close"))
        close_button.connect("clicked", lambda w: self.hide_all())

        # Category bar
        category_bar_width = 132
        self.category_bar = TreeView(
            enable_drag_drop=False,
            enable_multiple_select=False,
            )
        self.category_bar.set_expand_column(1)
        self.category_bar.draw_mask = self.draw_treeview_mask
        self.category_bar.set_size_request(category_bar_width, 516)
        self.category_bar.connect("button-press-item", self.button_press_preference_item)

        category_box = gtk.VBox()
        background_box = BackgroundBox()
        background_box.set_size_request(category_bar_width, 11)
        background_box.draw_mask = self.draw_treeview_mask
        category_box.pack_start(background_box, False, False)

        category_bar_align = gtk.Alignment()
        category_bar_align.set(0, 0, 1, 1,)
        category_bar_align.set_padding(0, 1, 0, 0)
        category_bar_align.add(self.category_bar)
        category_box.pack_start(category_bar_align, True, True)

        # Pack widget.
        left_box = gtk.VBox()
        self.right_box = gtk.VBox()
        left_box.add(category_box)
        right_align = gtk.Alignment()
        right_align.set_padding(0, 0, 0, 0)
        right_align.add(self.right_box)

        body_box = gtk.HBox()
        body_box.pack_start(left_box, False, False)
        body_box.pack_start(right_align, False, False)
        self.main_box.add(body_box)

        # DialogBox code.
        self.body_box.pack_start(self.main_box, True, True)
        self.right_button_box.set_buttons([close_button])

    def hide_dialog(self):
        self.hide_all()

        return True

    def button_press_preference_item(self, treeview, item, column_index, offset_x, offset_y):
        if self.set_item_widget(item):
            self.show_all()

    def set_item_widget(self, item):
        if isinstance(item, PreferenceItem):
            container_remove_all(self.right_box)
            self.right_box.pack_start(item.item_widget)
            self.category_bar.select_items([item])

            return True
        else:
            return False

    def draw_treeview_mask(self, cr, x, y, width, height):
        cr.set_source_rgba(*alpha_color_hex_to_cairo(("#FFFFFF", 0.9)))
        cr.rectangle(x, y, width, height)
        cr.fill()

    def set_preference_items(self, preference_items):
        '''
        Set preference items.

        @param preference_items: The list of preference item, item format is:
         - (item_name, item_widget)
         - Item list support recursively add.
        '''
        items = []
        for (item_name, item_content) in preference_items:
            if isinstance(item_content, gtk.Widget):
                items.append(PreferenceItem(item_name, item_content))
            elif isinstance(item_content, list):
                expand_item = ExpandPreferenceItem(item_name)
                items.append(expand_item)

                child_items = []
                for (child_item_name, child_item_content) in item_content:
                    child_items.append(PreferenceItem(child_item_name, child_item_content))

                expand_item.add_items(child_items)

        self.category_bar.add_items(items)

        for item in items:
            if self.set_item_widget(item):
                break

class PreferenceItem(TextItem):
    '''
    PreferenceItem class.
    '''

    def __init__(self, preference_name, item_widget):
        '''
        Initialize PreferenceItem class.
        '''
        TextItem.__init__(self, preference_name)
        self.text_size = 10
        self.text_padding = 0
        self.alignment = pango.ALIGN_LEFT
        self.column_offset = 15
        self.height = 37
        self.item_widget = item_widget

    def get_column_widths(self):
        return [36, -1]

    def get_column_renders(self):
        return [lambda cr, rect: draw_background(self, cr, rect),
                self.render_text]

gobject.type_register(PreferenceItem)

class ExpandPreferenceItem(IconTextItem):
    '''
    ExpandPreferenceItem class.
    '''

    def __init__(self, preference_name):
        '''
        Initialize ExpandPreferenceItem class.
        '''
        IconTextItem.__init__(
            self,
            preference_name,
            (ui_theme.get_pixbuf("treeview/arrow_right.png"),
             ui_theme.get_pixbuf("treeview/arrow_right_hover.png")),
            (ui_theme.get_pixbuf("treeview/arrow_down.png"),
             ui_theme.get_pixbuf("treeview/arrow_down_hover.png")),
            )
        self.text_size = 10
        self.text_padding = 0
        self.alignment = pango.ALIGN_LEFT
        self.icon_padding = 15
        self.column_offset = 15
        self.height = 37

    def get_column_widths(self):
        return [36, -1]

    def button_press(self, column, offset_x, offset_y):
        if self.is_expand:
            self.unexpand()
        else:
            self.expand()

gobject.type_register(ExpandPreferenceItem)

if __name__ == '__main__':
    dialog = ConfirmDialog("确认对话框", "你确定吗？", 200, 100)
    dialog.show_all()

    gtk.main()
