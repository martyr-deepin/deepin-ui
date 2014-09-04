#!/usr/bin/env python
#-*- coding:utf-8 -*-

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
from button import Button
from theme import ui_theme
from menu import Menu
from constant import  DEFAULT_FONT_SIZE
from draw import (draw_line, draw_text, draw_pixbuf)
from utils import (get_content_size, cairo_disable_antialias,
                   alpha_color_hex_to_cairo, cairo_state)
import gtk
import gobject
import pango
from poplist import Poplist

ARROW_BUTTON_WIDTH = 20

class Bread(gtk.HBox):
    '''
    Bread widget is a container which can hold crumbs widget.

    @undocumented: create_crumb
    @undocumented: enter_notify
    @undocumented: leave_notify
    @undocumented: event_box_press
    @undocumented: enter_cb
    @undocumented: redraw_bg
    @undocumented: click_cb
    @undocumented: move_right
    @undocumented: move_left
    '''

    __gsignals__= {
        "entry-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "item_clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,gobject.TYPE_STRING,))
        }

    def __init__(self,
                 crumb,
                 arrow_right=ui_theme.get_pixbuf("treeview/arrow_right.png"),
                 arrow_down=ui_theme.get_pixbuf("treeview/arrow_down.png"),
                 show_others=False,
                 show_entry=False,
                 show_left_right_box=True
                 ):
        '''
        Initialize Bread class.

        @param crumb: Crumb instance or a list of crumb instances
        @param arrow_right: Dynamic pixbuf for right arrow, default is \"treeview/arrow_right.png\" from ui theme.
        @param arrow_down: Dynamic pixbuf for down arrow, default is \"treeview/arrow_down.png\" from ui theme.
        @param show_others: If True, crumbs will not be destroyed, otherwise all crumbs on the right side will be destroyed.
        @param show_entry: If True, an entry will pop up when click space area in Bread.
        '''
        # Init.
        super(Bread, self).__init__(spacing = 0)
        self.arrow_right = arrow_right
        self.arrow_down = arrow_down
        self.item_list = list()
        self.show_others = show_others
        self.show_entry = show_entry
        self.crumb = self.create_crumb(crumb)
        self.button_width = ARROW_BUTTON_WIDTH # for left & right buttons
        self.in_event_box = False

        # Init left button and right button.
        self.show_left_right_box = show_left_right_box
        left_box = gtk.HBox(spacing = 0)
        right_box = gtk.HBox(spacing = 0)

        # FIXME: left && right box static setting size
        #        it is better to consider whether or not shown left && right box
        #        at runtime
        if self.show_left_right_box:
            left_box.set_size_request(self.button_width, -1)
            right_box.set_size_request(self.button_width, -1)
        self.left_btn = Button("&lt;")
        self.right_btn = Button("&gt;")
        self.left_btn.set_no_show_all(True)
        self.right_btn.set_no_show_all(True)
        self.right_btn.connect("clicked", self.move_right)
        self.left_btn.connect("clicked", self.move_left)
        self.left_btn.set_size_request(self.button_width, -1)
        self.right_btn.set_size_request(self.button_width, -1)
        left_box.pack_start(self.left_btn, False, False)
        right_box.pack_start(self.right_btn, False, False)

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
        self.scroll_win = ScrolledWindow()
        self.pack_start(left_box, False, True)
        self.pack_start(self.hbox, True, True)

        # Add Bread Items
        self.adj = self.scroll_win.get_hadjustment()

        self.add(self.crumb)

    def create_crumb(self, crumb):
        '''
        Internal function to create a Crumb list for different types of inputs.

        @param crumb: Support inputs are:
                      ["a label", Menu]
                      [("a label",[(None, "menu label", None)])]

                      Crumb instance
                      [Crumb, Crumb]

        '''
        if isinstance(crumb, Crumb):
            return [crumb,]
        elif isinstance(crumb[0], str):
            return [Crumb(crumb[0], crumb[1]),]
        elif isinstance(crumb[0], Crumb):
            return crumb
        else:
            return [Crumb(c[0], c[1]) for c in crumb]

    def enter_notify(self, widget, event):
        '''
        Internal callback function to "enter-notify-event" signal.

        @param widget: gtk.EventBox.
        @param event: The pointer event of type gtk.gdk.Event.
        '''
        self.in_event_box = True

    def leave_notify(self, widget, event):
        '''
        Internal callback function to "leave-notify-event" signal.

        @param widget: Gtk.EventBox.
        @param event: The pointer event of type gtk.gdk.Event.
        '''
        self.in_event_box = False

    def event_box_press(self, widget, event):
        '''
        Internal callback function to "button-press-event" signal.

        @param widget: gtk.eventbox.
        @param event: event of type gtk.gdk.event.
        '''
        obj = self.hbox.get_children()
        label = []
        for o in obj[:-1]:
            label.append("/"+o.label)
            o.destroy()
        self.entry = gtk.Entry()
        self.entry.connect("activate", self.enter_cb)
        self.entry.set_text("".join(label))
        self.entry.show()
        self.entry.select_region(0, len(self.entry.get_text()))
        self.eventbox.hide()
        self.hbox.pack_start(self.entry, True, True)

    def enter_cb(self, widget):
        '''
        Internal callback function to "press-return" signal.

        @param widget: gtk.Entry widget instance.
        '''
        label = widget.get_text()
        widget.destroy()
        self.eventbox.show()
        self.emit("entry-changed", label)

    def redraw_bg(self, widget, event):
        '''
        Internal callback function to "expose-event" signal.

        @param widget: gtk.EventBox
        @param event: event of type gtk.gdk.event
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw backgroud.
        with cairo_state(cr):
            cr.set_source_rgba(*alpha_color_hex_to_cairo(("#def5ff", 1)))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        return False

    def add(self, crumbs):
        '''
        Add crumbs. Can accept Crumb instance or a list of Crumb instances

        @param crumbs: Supported inputs are:
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
        page_size = self.adj.page_size

        # Show right button if crumbs exceed scrolled window size.
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

    def remove_node_after_index(self, index):
        '''
        Remove any nodes after given index.

        @param index: To specified remove after given index.
        '''
        for i in self.hbox.get_children()[(index + 1): -1]:
            i.destroy()
        self.item_list[(index + 1):] = []

    def click_cb(self, widget, index, label):
        '''
        Internal callback function to "clicked" signal.

        @param widget: Crumb instance.
        @param index: The index value of clicked crumb.
        @param label: Label of the crumb.
        '''
        if not self.show_others:
            for i in self.hbox.get_children()[(index + 1): -1]:
                i.destroy()
            self.item_list[(index + 1):] = []

        self.emit("item_clicked", index, label)

    def move_right(self, widget):
        '''
        Internal callback function to "clicked" signal.

        @param widget: Right button.
        '''
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
        '''
        Internal callback function to "clicked" signal.

        @param widget: Left button.
        '''
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

    def set_size(self, width, height):
        '''
        Set Bread size.

        @param width: Width of Bread.
        @param height: Height of Bread.
        '''
        self.scroll_win.set_size_request(width - 2 * self.button_width, height)
        self.hbox.set_size_request(-1, self.hbox.get_children()[0].height)

gobject.type_register(Bread)

class BreadMenu(Poplist):
    '''
    Popup menu for bread.

    @undocumented: draw_treeview_mask
    @undocumented: shape_bread_menu_frame
    @undocumented: expose_bread_menu_frame
    '''

    def __init__(self,
                 items,
                 max_height=None,
                 max_width=None,
                 ):
        '''
        Initialize BreadMenu class.

        @param items: Item for TreeView.
        @param max_height: Maximum height of bread menu, by default is None.
        @param max_width: Maximum width of bread menu, by default is None.
        '''
        Poplist.__init__(self,
                         items=items,
                         max_height=max_height,
                         max_width=max_width,
                         shadow_visible=False,
                         shape_frame_function=self.shape_bread_menu_frame,
                         expose_frame_function=self.expose_bread_menu_frame,
                         align_size=2,
                         )
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.treeview.draw_mask = self.draw_treeview_mask
        self.expose_window_frame = self.expose_bread_menu_frame

    def draw_treeview_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def shape_bread_menu_frame(self, widget, event):
        pass

    def expose_bread_menu_frame(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        with cairo_disable_antialias(cr):
            outside_border = alpha_color_hex_to_cairo(("#666666", 0.5))
            cr.set_line_width(1)
            cr.set_source_rgba(*outside_border)
            cr.rectangle(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)
            cr.fill()

gobject.type_register(BreadMenu)

class Crumb(gtk.Button):
    '''
    Crumb class .

    @undocumented: enter_button
    @undocumented: motion_notify_cb
    @undocumented: create_menu
    @undocumented: hide_cb
    @undocumented: button_press_cb
    @undocumented: button_clicked
    @undocumented: expose_cb
    '''
    __gsignals__= {
        "item_clicked" : (gobject.SIGNAL_RUN_LAST,
                          gobject.TYPE_NONE,
                          (gobject.TYPE_INT,gobject.TYPE_STRING,))}

    def __init__(self,
                 label,
                 menu_items = None,
                 font_size = DEFAULT_FONT_SIZE,
                 padding_x = 15,
                 ):
        '''
        Initialize Crumb class.

        @param label: Crumb item label
        @param menu_items: Crumb menu, could be a Menu instance or a list, default is None
        @param font_size: Font size, default is DEFAULT_FONT_SIZE.
        @param padding_x: Horizontal padding, default is 15 pixels.
        '''
        super(Crumb, self).__init__()

        self.arrow_right = None
        self.arrow_down = None
        self.menu_min = 18 # menu bar width
        self.btn_min = 50 # button width
        self.height = 24 # crumb height
        self.font_size = font_size
        self.padding_x = padding_x
        self.menu = self.create_menu(menu_items)
        if self.menu != None:
            self.menu.connect("hide", self.hide_cb)
        self.menu_press = False
        self.menu_show = False
        self.index_id = 0
        self.set_label(label)
        self.in_button = True
        self.in_menu = True
        self.connect("expose_event", self.expose_cb)
        self.connect("button_press_event", self.button_press_cb)
        self.connect("clicked", self.button_clicked)
        self.connect("motion-notify-event", self.motion_notify_cb)
        self.connect("enter-notify-event", self.enter_button)
        self.add_events(gtk.gdk.POINTER_MOTION_MASK)

    def enter_button(self, widget, event):
        in_menu = event.x > self.button_width
        self.in_menu =in_menu

    def motion_notify_cb(self, widget, event):
        '''
        Internal callback function to Crumb "motion-notify-event" signal.

        @param widget: Crumb
        @param event: an event of gtk.gdk.event
        '''
        in_menu = event.x > self.button_width
        if self.in_menu !=in_menu:
            self.in_menu = in_menu
            self.queue_draw()

    def create_menu(self, menu_items):
        '''
        Internal function to create menu.

        @param menu_items: menu_items
        @return: Menu instance
        '''
        if menu_items != None and isinstance(menu_items, list):
            return BreadMenu(menu_items)
        else:
            return None

    def hide_cb(self, widget):
        '''
        Internal callback function to Menu's ""hide" signal.

        @param widget: Menu
        '''
        if self.menu_press:
            self.set_state(gtk.STATE_PRELIGHT)
        else:
            self.menu_show = False
            self.set_state(gtk.STATE_NORMAL)

    def button_press_cb(self, widget, event):
        '''
        Internal callback function to "button-press-event" signal.

        @param widget: Crumb
        @param event: An event of gtk.gdk.Event
        '''
        if self.menu == None:
            self.in_button = True
            self.menu_press = False
        else:
            self.in_button = event.x < (widget.allocation.width - self.menu_min)
            if not self.in_button:
                self.menu_press = True

    def button_clicked(self, widget):
        '''
        Intenal callback function to "clicked" signal.

        @param widget: Crumb
        '''
        if self.in_button:
            self.emit("item_clicked", self.index_id, self.label)
        else:
            self.menu_press = False
            self.menu_show = not self.menu_show
            if self.menu_show:
                (wx, wy) = self.get_toplevel().window.get_root_origin()
                (offset_x, offset_y) = widget.translate_coordinates(self.get_toplevel(), 0, 0)
                (menu_width, menu_height) = widget.allocation.width, widget.allocation.height
                arrow_button_width = ARROW_BUTTON_WIDTH
                self.menu.show((wx + offset_x + menu_width - arrow_button_width,
                                wy + offset_y + menu_height,
                                ),
                               (0, 0))

    def set_label(self, label, font_size = DEFAULT_FONT_SIZE):
        '''
        Set label for left button.

        @param label: Label
        @param font_size: Label's Font size, default is DEFAULT_FONT_SIZE.
        '''
        self.label = label
        (self.label_w, self.label_h) = get_content_size(self.label, font_size)
        if self.menu == None:
            self.set_size_request(
                max(self.label_w + 2 * self.padding_x, self.btn_min),
                self.height)

            self.button_width = self.get_size_request()[0]
        else:
            self.set_size_request(
                max(self.label_w + 2 * self.padding_x + self.menu_min, self.btn_min + self.menu_min),
                self.height)

            self.button_width = self.get_size_request()[0] - self.menu_min

        self.queue_draw()

    def expose_cb(self, widget, event):
        '''
        Internal expose callback function.

        @param widget: Crumb instance.
        @param event: An event of gtk.gdk.Event.
        '''
        if self.menu == None:
            self.menu_min = 0
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Should move this part to Bread class since app_theme is golobalized.
        arrow_right = self.arrow_right
        arrow_down = self.arrow_down
        arrow_width, arrow_height = arrow_right.get_pixbuf().get_width(), arrow_right.get_pixbuf().get_height()
        arrow_pixbuf = arrow_right

        outside_border = alpha_color_hex_to_cairo(("#000000", 0.15))
        inner_border = alpha_color_hex_to_cairo(("#ffffff", 0.5))
        active_mask = alpha_color_hex_to_cairo(("#000000", 0.1))

        if self.menu_show:
            self.set_state(gtk.STATE_PRELIGHT)

        if widget.state == gtk.STATE_NORMAL:
            text_color = ui_theme.get_color("title_text").get_color()
            button_color = None
            menu_color = None
            arrow_pixbuf = arrow_right

        elif widget.state == gtk.STATE_PRELIGHT:
            text_color = ui_theme.get_color("title_text").get_color()
            if self.menu_show:
                arrow_pixbuf = arrow_down
            else:
                arrow_pixbuf = arrow_right

            if self.in_menu:
                button_color = None
                menu_color = inner_border
            else:
                button_color = inner_border
                menu_color = None

        elif widget.state == gtk.STATE_ACTIVE:
            text_color = ui_theme.get_color("title_text").get_color()
            if self.in_button:
                button_color = inner_border
                menu_color = None
                arrow_pixbuf = arrow_right
            else:
                button_color = None
                menu_color = inner_border
                arrow_pixbuf = arrow_down

        elif widget.state == gtk.STATE_INSENSITIVE:
            arrow_pixbuf = arrow_right
            text_color = ui_theme.get_color("disable_text").get_color()
            disable_bg = ui_theme.get_color("disable_background").get_color()
            button_color = [(0, (disable_bg, 1.0)),
                            (1, (disable_bg, 1.0))]
            menu_color = [(0, (disable_bg, 1.0)),
                            (1, (disable_bg, 1.0))]

        # Draw background.
        if not widget.state == gtk.STATE_NORMAL:
            # Draw button border.
            def draw_rectangle(cr, x, y , w, h):
                draw_line(cr, x -1 , y , x + w, y)          # top
                draw_line(cr, x , y + h, x + w, y + h)      # bottom
                draw_line(cr, x , y , x , y + h)            # left
                draw_line(cr, x + w , y , x + w , y + h -1) # right

            cr.set_source_rgba(*outside_border)
            if button_color:
                draw_rectangle(cr, x + 1 , y + 1 , self.button_width -1 , h -1)
            elif menu_color:
                draw_rectangle(cr, x + self.button_width, y + 1, self.menu_min, h - 1)

            # Draw innner border.
            cr.set_source_rgba(*inner_border)
            if button_color:
                draw_rectangle(cr, x + 2, y + 2, self.button_width - 3, h -3)
            elif menu_color:
                draw_rectangle(cr, x + self.button_width + 1, y + 2, self.menu_min - 2, h -3)

            if widget.state == gtk.STATE_ACTIVE:
                cr.set_source_rgba(*active_mask)
                if button_color:
                    cr.rectangle(x + 2, y + 2, self.button_width - 4, h -4)
                    cr.fill()
                elif menu_color:
                    cr.rectangle( x + self.button_width + 1, y + 2, self.menu_min - 3, h -4)
                    cr.fill()

        if self.menu != None:
            # Draw an arrow.
            draw_pixbuf(cr, arrow_pixbuf.get_pixbuf(), x + self.button_width + (self.menu_min - arrow_width) / 2, y + (h - arrow_height) / 2)

        # Draw text.
        draw_text(cr, self.label, x, y , self.button_width, h, self.font_size, text_color,
                    alignment = pango.ALIGN_CENTER)

        return True

gobject.type_register(Crumb)

if __name__ == "__main__":
    import gtk

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
