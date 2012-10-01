#!/usr/bin/env python
#-*- coding:utf-8 -*-

#             Zeng Zhi <zengzhilg@gmail.com>
# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Zeng Zhi
# 
# Author:     Zeng Zhi <zengzhilg@gmail.com>
# Maintainer: Zeng Zhi <zengzhilg@gmail.com>
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

from animation import Animation
from scrolled_window import ScrolledWindow
from button import Button # used for left,right button,maby use eventbox?
from theme import ui_theme
from skin_config import skin_config
from menu import Menu
from entry import Entry, InputEntry
from constant import  DEFAULT_FONT_SIZE
from draw import (draw_vlinear, draw_line, 
                         draw_text, draw_pixbuf,draw_round_rectangle)
from utils import (get_content_size,get_window_shadow_size, 
                          color_hex_to_cairo, get_match_parent)
import gtk 
import gobject
import pango
import cairo


class Bread(gtk.HBox):
    """
    Bread class is an container which can hold crumbs
    
    """

    __gsignals__= {
        "entry-changed" : (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE,
                          (gobject.TYPE_STRING,))}
    
    def __init__(self,
                 crumb,
                 arrow_right,
                 arrow_down,
                 show_others=False, 
                 show_entry=False):
        """
        Initialize Bread class.

        @param crumb: Crumb instance or a list of crumb instances
        @param arrow_right: Arrow_right pixbuf from theme
        @param arrow_down: Arrow_down pixbuf from theme
        @param show_others: If True, crumbs will not be destroyed, otherwise all crumbs on the right side will be destroyed
        @param show_entry: If True, an entry will pop up when click space area          in Bread
        """
        
        super(Bread, self).__init__(spacing = 0)
        # Init
        self.arrow_right = arrow_right
        self.arrow_down = arrow_down
        self.item_list = list()
        self.show_others = show_others
        self.show_entry = show_entry
        self.crumb = self.create_crumb(crumb)
        self.button_width = 20 # for left & right buttons
        self.in_event_box = False

        # Init left button and right button
        left_box = gtk.HBox(spacing = 0)
        left_box.set_size_request(self.button_width, -1)
        right_box = gtk.HBox(spacing = 0)
        right_box.set_size_request(self.button_width, -1)
        self.left_btn = Button("<")
        self.right_btn = Button(">")
        self.left_btn.set_no_show_all(True)
        self.right_btn.set_no_show_all(True)
        self.right_btn.connect("clicked", self.move_right)
        self.left_btn.connect("clicked", self.move_left)
        self.left_btn.set_size_request(self.button_width, -1)
        self.right_btn.set_size_request(self.button_width, -1)
        left_box.pack_start(self.left_btn, False, False)
        right_box.pack_start(self.right_btn, False, False)
        
        # Init scrolled window
        self.scroll_win = ScrolledWindow()
        self.scroll_win.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        self.pack_start(left_box, False, True)
        self.pack_start(self.scroll_win, True, True)
        self.pack_end(right_box, False, True)
        # Init Hbox        
        self.hbox = gtk.HBox(False, 0)
        self.hbox.show()
        self.eventbox = gtk.EventBox()
        self.eventbox.set_visible_window(False)

        if self.show_entry:
            self.eventbox.connect("enter-notify-event", self.enter_notify)
            self.eventbox.connect("leave-notify-event", self.leave_notify)
            self.eventbox.connect("button-press-event", self.event_box_press)

        self.hbox.pack_end(self.eventbox, True, True)
        self.hbox.connect("expose-event", self.redraw_bg)
        self.scroll_win.add_with_viewport(self.hbox)
        #self.hbox.connect("realize", lambda w : self.add(self.crumb))
        # Add Bread Items
        self.adj = self.scroll_win.get_hadjustment()
        
        self.add(self.crumb)

    def create_crumb(self, crumb):
        """
        Internal function to create a Crumb list for different types of inputs,
        Support inputs are : ["a label", Menu]
                             [("a label",[(None, "menu label", None)])]
                             Crumb instance
                             [Crumb, Crumb]

        @param crumb: input
        """
        if isinstance(crumb, Crumb):
            return [crumb,]
        elif isinstance(crumb[0], str):
            return [Crumb(crumb[0], crumb[1]),]
        elif isinstance(crumb[0], Crumb):
            return crumb
        else:
            return [Crumb(c[0], c[1]) for c in crumb]

    def enter_notify(self, widget, event):
        """
        Internal callback function to "enter-notify-event" signal

        @param widget: gtk.EventBox
        @param event: The pointer event of type gtk.gdk.Event
        """
        self.in_event_box = True

    def leave_notify(self, widget, event):
        """
        Internal callback function to "leave-notify-event" signal

        @param widget: Gtk.EventBox
        @param event: The pointer event of type gtk.gdk.Event
        """
        self.in_event_box = False

    def event_box_press(self, widget, event):
        """
        internal callback function to "button-press-event" signal

        @param widget: gtk.eventbox
        @param event: event of type gtk.gdk.event
        """
        obj = self.hbox.get_children()
        label = []
        for o in obj[:-1]:
            label.append("/"+o.label)
            o.destroy()
        self.entry = gtk.Entry()
        #self.entry.set_has_frame(1)
        self.entry.connect("activate", self.enter_cb)
        self.entry.set_text("".join(label))
        #self.entry.grab_focus()
        self.entry.show()
        self.entry.select_region(0, len(self.entry.get_text()))
        self.eventbox.hide()
        self.hbox.pack_start(self.entry, True, True)
        #self.entry = InputEntry("".join(label))
        #self.entry.set_size(100, 26)
        ##self.entry.select_to_end()
        #self.entry.entry.connect("press-return", self.enter_cb)
        #self.entry.show()
        #self.eventbox.hide()
        #self.hbox.pack_start(self.entry, True, True)

    def enter_cb(self, widget):
        """
        internal callback function to "press-return" signal

        @param widget: gtk.entry
        """
        label = widget.get_text()
        widget.destroy()
        self.eventbox.show()
        self.emit("entry-changed", label)
        print "signal \"entry-changed\"", "with path:%s"%label
        
        
    def redraw_bg(self, widget, event):
        """
        Internal callback function to "expose-event" signal

        """
        cr = widget.window.cairo_create()
        win = get_match_parent(widget, ["ScrolledWindow"])
        win_x, win_y = win.allocation.x, win.allocation.y

        cr.translate(-win_x, -win_y)
        (shadow_x, shade_y) = get_window_shadow_size(self.get_toplevel())
        skin_config.render_background(cr, widget, shadow_x, shade_y)
        return False

    def add(self, crumbs):
        '''
        Add crumbs. Can accept Crumb instance or a list of Crumb instances

        @param crumbs: Supported inputs are : 
                       ["a label", Menu]
                       [("a label",[(None, "menu label", None)])]
                       Crumb instance
                       [Crumb, Crumb]
        '''
        crumbs = self.create_crumb(crumbs)
        for crumb in crumbs:
            crumb.show()
            crumb.arrow_right = self.arrow_right
            crumb.arrow_down = self.arrow_down
            crumb.index_id = len(self.item_list)
            crumb.connect("item_clicked", self.click_cb)
            self.hbox.pack_start(crumb, False, False)
            self.item_list.append(crumb.get_size_request()[0])
        self.change_sensitive(len(self.item_list) - 1)
        page_size = self.adj.page_size
        
        # show right button if crumbs exceed scrolled window size
        if sum(self.item_list) > page_size and not page_size == 1.0:
            self.right_btn.show()

    def change_node(self, index, crumbs):
        '''
        Change any nodes start from specified index

        @param index: Start index 
        @param crumbs: Crumb instance or Crumb list

        For instance, there exist a list contain [Crumb1, Crumb2],
        by using change_node(1, [Crumb3, Crumb4]), previous list will be change
        to [Crumb1, Crumb3, Crumb4]. In this way, application can operate crumbs
        '''
        objects = self.hbox.get_children()
        for i in objects[index: -1]:
            i.destroy()
        self.item_list[index:] = []
        self.add(crumbs)
        
    def change_sensitive(self, index):
        """
        Internal function to change all Crumbs back to gtk.STATE_NORMAL

        @param index: The index of crumb need set to insensitive
        """
        objects = self.hbox.get_children()
        for i in objects:
            i.set_sensitive(True) 
            i.btn_clicked = False
            i.set_state(gtk.STATE_NORMAL)

        objects[index].set_sensitive(False)
        if sum(self.item_list) < self.adj.page_size:
            self.right_btn.hide()
            self.left_btn.hide()

    def click_cb(self, widget, index, label):
        """
        Internal callback function to "clicked" signal
        
        @param widget: Crumb instance
        @param index: The index value of clicked crumb
        @param label: Label of the crumb
        """
        if self.show_others:
            self.change_sensitive(index)
        else:
            for i in self.hbox.get_children()[(index + 1): -1]:
                i.destroy()
            self.item_list[(index + 1):] = []
            self.change_sensitive(index)

    def move_right(self, widget):
        """
        Internal callback function to "clicked" signal

        @param widget: Right Button
        """
        upper, page_size, value = self.adj.upper, self.adj.page_size, self.adj.value
        shift_value = 0
        temp = 0
        if upper > (page_size + value):
            self.left_btn.show()
            for i in xrange(len(self.item_list)+1):
                temp += self.item_list[i]
                if temp > (page_size + value):
                    shift_value = temp - (page_size + value)
                    #play animation
                    ani = Animation(self.adj, lambda widget, v1: widget.set_value(v1),200,[value, value+shift_value])
                    ani.start()
                    break
        if not upper > (page_size + self.adj.value + shift_value):
            self.right_btn.hide()

    def move_left(self, widget):
        """
        Internal callback function to "clicked" signal

        @param widget: Left button
        """
        upper, page_size, value = self.adj.upper, self.adj.page_size, self.adj.value
        shift_value = 0
        temp = 0
        if not value == 0:
            self.right_btn.show()
            for i in xrange(len(self.item_list)):
                temp += self.item_list[i]
                if temp >= value:
                    shift_value = self.item_list[i] - (temp - value)
                    break
            #play animation
            ani = Animation(self.adj, lambda widget, v1: widget.set_value(v1),200,[value, value-shift_value])
            ani.start()
        if (self.adj.value - shift_value) == 0:
            self.left_btn.hide()

    def set_size(self, w, h):
        """
        Set Bread size

        @param w: Width of Bread
        @param h: Height of Bread
        """
        self.scroll_win.set_size_request(w - 2*self.button_width, h)
        self.hbox.set_size_request(-1, self.hbox.get_children()[0].height)

gobject.type_register(Bread)

class Crumb(gtk.Button):
    """
    Crumb class 

    """
    __gsignals__= {
        "item_clicked" : (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE,
                          (gobject.TYPE_INT,gobject.TYPE_STRING,))}

    def __init__(self,
                 label,
                 menu_list = None,
                 font_size = DEFAULT_FONT_SIZE,
                 padding_x = 15,):
        """
        Initialize function

        @param label: Crumb item label
        @param menu_list: Crumb menu ,could be a Menu instance or a list, default is None
        @param font_size: Default font size
        @param padding_x: Default horizontal padding
        """
        super(Crumb, self).__init__()
        
        self.arrow_right = None
        self.arrow_down = None
        self.menu_min = 18 # menu bar width
        self.btn_min = 50 # button width
        self.height = 26 # crumb height
        self.font_size = font_size
        self.padding_x = padding_x
        self.menu_list = self.create_menu(menu_list)
        self.menu_list.connect("hide", self.hide_cb)
        self.menu_press = False
        self.menu_show = False
        self.index_id = 0
        self.set_label(label)
        self.in_button = True
        self.connect("expose_event", self.expose_cb)
        self.connect("button_press_event", self.button_press_cb)
        self.connect("clicked", self.button_clicked)

    def create_menu(self, menu_list):
        """
        Internal function to create menu
        
        @param menu_list: menu_list
        @return: Menu instance
        """
        if isinstance(menu_list, list):
            menu_list = Menu(menu_list, shadow_visible = False)
        menu_list.is_root_menu = True
        return menu_list

    def hide_cb(self, widget):
        """
        Internal callback function to Menu's ""hide" signal
        
        @param widget: Menu
        """
        if self.menu_press:
            self.set_state(gtk.STATE_PRELIGHT)
        else:
            self.menu_show = False
            self.set_state(gtk.STATE_NORMAL)

    def button_press_cb(self, widget, event):
        """
        Internal callback function to "button-press-event" signal

        @param widget: Crumb
        @param event: An event of gtk.gdk.Event
        """
        self.in_button = event.x < (widget.allocation.width - self.menu_min)
        self.menu_press = True

    def button_clicked(self, widget):
        """
        Intenal callback function to "clicked" signal

        @param widget: Crumb
        """
        if self.in_button:
            self.emit("item_clicked", self.index_id, self.label)
            print "\"item_clicked\" signal emitted, with index_id:%d, label:\"%s\""%(self.index_id, self.label)
        else:
            self.menu_press = False
            self.menu_show = not self.menu_show
            if self.menu_show:
                (win_x, win_y) = self.window.get_origin()
                self.menu_list.show(
                                (win_x + widget.allocation.x + self.button_width,
                                 win_y + widget.allocation.height),
                                 (0,0))

    def set_label(self, label, font_size = DEFAULT_FONT_SIZE):
        '''
        Set label for left button.

        @param label: Label
        @param font_size: label's Font size
        '''
        self.label = label
        (self.label_w, self.label_h) = get_content_size(self.label, font_size)
        self.set_size_request(
                max(self.label_w + 2 * self.padding_x + self.menu_min, self.btn_min + self.menu_min),
                self.height)

        self.button_width = self.get_size_request()[0] - self.menu_min
        self.queue_draw()

    def expose_cb(self, widget, event):
        """
        Internal expose callback function

        @param widget: Crumb
        @param event: An event of gtk.gdk.Event
        """
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        #!# should move this part to Bread class since app_theme is golobalized
        arrow_right = self.arrow_right
        arrow_down = self.arrow_down
        arrow_width, arrow_height = arrow_right.get_width(), arrow_right.get_height()
        arrow_pixbuf = arrow_right

        button_normal = [(0.5,("#effafc", 1)), (0.5,("#dbecf4",1))]
        button_prelight = [(0.5,("#e7f4fa", 1)),(0.5,("#b2d2e0", 1))]
        button_active = [(0.5,("#b2d2e0", 1)),(0.9,("#e7f4fa", 1 ))]

        if self.menu_show: 
            self.set_state(gtk.STATE_ACTIVE)

        if widget.state == gtk.STATE_NORMAL:
            text_color = ui_theme.get_color("button_font").get_color()
            button_color = button_normal            
            menu_color = button_normal
            arrow_pixbuf = arrow_right
            
        elif widget.state == gtk.STATE_PRELIGHT:
            text_color = ui_theme.get_color("button_font").get_color()
            border_color = "#7ab2db"
            arrow_pixbuf = arrow_right

            button_color = button_prelight
            menu_color = button_prelight

        elif widget.state == gtk.STATE_ACTIVE:
            text_color = ui_theme.get_color("button_font").get_color()
            border_color = "#7ab2db"
            if self.in_button:
                button_color = button_active
                menu_color = button_normal
                arrow_pixbuf = arrow_right
            else:
                button_color = button_normal
                menu_color = button_active
                arrow_pixbuf = arrow_down

        elif widget.state == gtk.STATE_INSENSITIVE:
            arrow_pixbuf = arrow_right
            text_color = ui_theme.get_color("disable_text").get_color()
            border_color = ui_theme.get_color("disable_frame").get_color()
            disable_bg = ui_theme.get_color("disable_background").get_color()
            button_color = [(0, (disable_bg, 1.0)),
                            (1, (disable_bg, 1.0))]
            menu_color = [(0, (disable_bg, 1.0)),
                            (1, (disable_bg, 1.0))]
        # Draw background.
        draw_vlinear(
            cr,
            x , y + 1  , self.button_width, h -1,
            button_color)

        draw_vlinear(
            cr,
            x + self.button_width, y + 1 , self.menu_min, h -1,
            menu_color)

        if not widget.state == gtk.STATE_NORMAL:
            # Draw button border.
            def draw_rectangle(cr, x, y , w, h):
                # Top
                draw_line(cr, x -1 , y , x + w, y)
                # Bottom
                draw_line(cr, x , y + h, x + w, y + h)
                # left
                draw_line(cr, x , y , x , y + h)
                # Right
                draw_line(cr, x + w , y , x + w , y + h)
                
            cr.set_source_rgb(*color_hex_to_cairo(border_color))
            # Draw button border
            draw_rectangle(cr, x + 1 , y + 1, self.button_width, h -1) 
            # Draw menu border
            draw_rectangle(cr, x + self.button_width + 1, y + 1, self.menu_min -1, h -1)

            # Draw innner border
            cr.set_source_rgb(1, 1, 1)
            draw_rectangle(cr, x + 2, y + 2, self.button_width - 2, h -3)
            draw_rectangle(cr, x + self.button_width + 2, y + 2, self.menu_min -3 , h -3)

        # Draw an arrow
        draw_pixbuf(cr, arrow_pixbuf, x + self.button_width + (self.menu_min - arrow_width)/2, y + (h - arrow_height)/2)

        # Draw text
        draw_text(cr, self.label, x, y , self.button_width, h, self.font_size, text_color,
                    alignment = pango.ALIGN_CENTER)
        return True

gobject.type_register(Crumb)

if __name__ == "__main__":

    def add_panel(widget):
        crumb = Crumb("Child",menu)
        bread.add(crumb)

    def change_root_node( widget):
        crumb1 = Crumb("Yet Another Root", menu)
        crumb2 = Crumb("Yet Another Child", menu)
        bread.change_node(0, [crumb1, crumb2])

    def change_entry(widget, path):
        # Application can check if path is valid or not 
        path_list = path.split("/")[1:]
        bread.change_node(0, [Crumb(i , menu) for i in path_list])

    menu = Menu([
            (None, "测试1", None),
            (None, "测试2", None),
            ],
            shadow_visible = False,
            )

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.connect("destroy", lambda w: gtk.main_quit())
    win.set_default_size(600,300)
    vbox = gtk.VBox()
######################################
    # test breadcrumb widget
    bread = Bread([("Root", menu),
                   ("Level1", menu)],
                    app_theme.get_pixbuf("nav_button/arrow_right.png").get_pixbuf(),
                    app_theme.get_pixbuf("nav_button/arrow_down.png").get_pixbuf(),
                    show_others = False,
                    show_entry = True)
    bread.add(["xxx",menu])
    # Must set_size 
    bread.set_size(200, -1)
    bread.connect("entry-changed", change_entry)
#####################################

    vbox.pack_start(bread, False, False, 0)
    # Test Item
    add_path_button = gtk.Button("Add Item")
    add_path_button.connect("clicked", add_panel)
    vbox.pack_start(add_path_button, True, False, 0)

    test_change_node = gtk.Button("Change Root node")
    test_change_node.connect("clicked", change_root_node)
    vbox.pack_start(test_change_node, True, False , 0)

    win.add(vbox)
    win.show_all()
    gtk.main()
