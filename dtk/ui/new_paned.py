#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Deepin, Inc.
#               2013 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
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
from gtk import gdk

class Paned(gtk.Container):
    def __init__(self):
        gtk.Container.__init__(self)
        self.set_has_window(False)
        self.set_can_focus(True)
        self.__init_values()

    def __init_values(self):
        self.paint_handle_hd = self.__paint_handle_function
        self.__handle = None
        self.__child1 = None
        self.__child2 = None
        self.__type   = gtk.ORIENTATION_HORIZONTAL
        # 移动的属性值.
        self.__is_move_check = True
        self.__move_check = False
        self.__save_move_x = 0
        self.__save_move_y = 0
        #
        class HandlePos(object):
            x = self.allocation.x
            y = self.allocation.y
            w = self.allocation.width
            h = self.allocation.height
            #size = max(10, pixbuf_size)
            size = max(10, 20)
            can_visible = False
            can_move_child2  = True # 判断是否向child2移动.
            can_in           = True
            can_move         = False
        #
        self.handle_pos = HandlePos()

    def do_realize(self):
        self.set_flags(gtk.REALIZED)
        #
        self.window = self.get_parent_window()
        # init handle.
        self.__init_handle()
        #
        if self.__child1:
            self.__child1.set_parent_window(self.window)
        if self.__child2:
            self.__child2.set_parent_window(self.window)
        #
        self.queue_resize()

    def __init_handle(self):
        self.__handle = gtk.gdk.Window(
                parent=self.window,
                window_type=gdk.WINDOW_CHILD,
                wclass=gdk.INPUT_ONLY,
                x=self.handle_pos.x,
                y=self.handle_pos.y,
                width=self.handle_pos.w,
                height=self.handle_pos.h,
                event_mask=(
                    self.get_events()
                    | gtk.gdk.EXPOSURE_MASK
                    | gtk.gdk.BUTTON_PRESS_MASK
                    | gtk.gdk.BUTTON_RELEASE_MASK
                    | gtk.gdk.ENTER_NOTIFY_MASK
                    | gtk.gdk.LEAVE_NOTIFY_MASK
                    | gtk.gdk.POINTER_MOTION_MASK
                    | gtk.gdk.POINTER_MOTION_HINT_MASK
                    )
                )
        self.__handle.set_user_data(self)
        #
        if ((self.__child1 and self.__child1.get_visible()) and
            (self.__child2 and self.__child2.get_visible())):
            self.__handle.show()

    def do_unrealize(self):
        if self.__handle:
            self.__handle.set_user_data(None)
            self.__handle.destroy()
            self.__handle = None

    def do_map(self):
        self.set_flags(gtk.MAPPED)
        self.__handle.show()

    def do_unmap(self):
        gtk.Container.do_unmap(self)
        self.__handle.hide()

    def do_expose_event(self, e):
        gtk.Container.do_expose_event(self, e)
        if e.window == self.window:
            cr = e.window.cairo_create()
            # 绘制 child1, child2.
            child = self.get_child1()
            self.__paint_child_window(cr, child)
            child = self.get_child2()
            self.__paint_child_window(cr, child)
            # 使用者可以重载这个函数达到高度自由化.
            self.paint_handle_hd(cr, self.handle_pos)

        return False

    def __paint_child_window(self, cr, child):
        if child and child.window != self.window:
            cr.set_source_pixmap(
                child.window,
                *child.window.get_position())
            cr.paint_with_alpha(1.0)

    def __paint_handle_function(self, cr, handle_pos):
        if self.handle_pos.can_visible:
            # 绘制例子.
            if handle_pos.can_in:
                cr.set_source_rgba(0, 0, 1, 0.85)
                # 判断要向那个方向的控件靠拢.
                if handle_pos.can_move_child2:
                    #pixbuf = self.in_pixbuf
                    pass
                else:
                    #pixbuf = self.out_pixbuf
                    pass
            else:
                cr.set_source_rgba(1, 0, 0, 0.95)
                # 判断要向那个方向的控件靠拢.
                if handle_pos.can_move_child2:
                    #pixbuf = self.out_pixbuf
                    pass
                else:
                    #pixbuf = self.in_pixbuf
                    pass
            w, h = handle_pos.size, 100
            # 判断是否为纵向.
            if self.__type == gtk.ORIENTATION_VERTICAL:
                #pixbuf = pixbuf.rotate_simple(270)
            #draw_pixbuf(cr, pixbuf, handle_pos.x, handle_pos.y)
                w, h = 100, handle_pos.size
            cr.rectangle(handle_pos.x, handle_pos.y, w, h)
            cr.fill()
        #

    def do_enter_notify_event(self, e):
        self.handle_pos.can_visible = True
        self.queue_draw()
        self.__handle.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

    def do_leave_notify_event(self, e):
        self.handle_pos.can_visible = False
        self.queue_draw()

    def do_focus_notify_event(self, e):
        pass

    def do_button_press_event(self, e):
        # 判断是否是移动 而且 can_in是为True(这种情况是不隐藏起来).
        if self.__is_move_check and self.handle_pos.can_in:
            self.__move_check = True
            self.__save_move_x = e.x
            self.__save_mvoe_y = e.y

    def do_button_release_event(self, e):
        if not self.handle_pos.can_move:
            self.handle_pos.can_in = not self.handle_pos.can_in
            self.do_size_allocate(self.allocation)
            self.queue_draw()
        self.handle_pos.can_move = False
        self.__move_check = False

    def do_motion_notify_event(self, e):
        if self.__move_check:
            #
            if self.handle_pos.can_move_child2:
                x = e.x - self.__save_move_x
                y = e.y - self.__save_move_y
                child = self.__child2
                move_child = self.__child1
            else:
                x = self.__save_move_x - e.x
                y = self.__save_move_y - e.y
                child = self.__child1
                move_child = self.__child2
            #
            if self.__type == gtk.ORIENTATION_HORIZONTAL: # 横向.
                w = child.get_size_request()[0] - (x)
                h = child.get_size_request()[1]
                w_padding = self.allocation.width - move_child.size_request()[0]
                if w > w_padding:
                    w = w_padding
            else:
                w = child.get_size_request()[0]
                h = child.get_size_request()[1] - (y)
                h_padding = self.allocation.height - move_child.size_request()[1]
                if h > h_padding:
                    h = h_padding
            #
            child.set_size_request(max(1, int(w)), max(1, int(h)))
            self.do_size_allocate(self.allocation)
            self.handle_pos.can_move = True

    def do_forall(self, include_internals, callback, data):
        if self.__child1:
            callback(self.__child1, data)
        if self.__child2:
            callback(self.__child2, data)

    def do_add(self, widget):
        gtk.Container.do_add(self, widget)

    def do_remove(self, widget):
        pass

    def do_size_request(self, requisition):
        requisition.width = 0
        requisition.height = 0
        if self.__child1 and self.__child1.get_visible():
            child_requisition = self.__child1.size_request()
            requisition.width = child_requisition[0]
            requisition.height = child_requisition[1]

        if self.__child2 and self.__child2.get_visible():
            child_requisition = self.__child2.size_request()
            #
            if self.__type ==  gtk.ORIENTATION_HORIZONTAL:
                requisition.width += child_requisition[0]
            else: # gtk.ORIENTATION_VERTICAL
                requisition.height += child_requisition[1]
        #gtk.Container.do_size_request(self, requisition)

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        child1_allocation = gdk.Rectangle()
        child2_allocation = gdk.Rectangle()
        #
        if ((self.__child1 and self.__child1.get_visible()) and
            (self.__child2 and self.__child2.get_visible())):
            # 获取child1, child2 的宽高.
            child1_requisition = self.__child1.get_child_requisition()
            child2_requisition = self.__child2.get_child_requisition()
            #
            if self.__type ==  gtk.ORIENTATION_HORIZONTAL: # 横向.
                self.handle_pos.x = self.allocation.x
                self.handle_pos.y = self.allocation.y
                self.handle_pos.w = self.handle_pos.size;
                self.handle_pos.h = self.allocation.height
                # set child1/2 (x, y, w, h)
                if self.handle_pos.can_move_child2:
                    child1_w = allocation.width - child2_requisition[0]
                    child2_w = child2_requisition[0]
                    if not self.handle_pos.can_in:
                        child1_w = allocation.width
                        child2_w = 1
                else:
                    child2_w = allocation.width - child1_requisition[0]
                    child1_w = child1_requisition[0]
                    if not self.handle_pos.can_in:
                        child2_w = allocation.width
                        child1_w = 1
                child1_allocation.x = allocation.x
                child1_allocation.y = allocation.y
                child1_allocation.width = max(1, child1_w)
                child1_allocation.height = max(1, allocation.height)
                child2_allocation.x = allocation.x + child1_allocation.width
                child2_allocation.y = child1_allocation.y
                child2_allocation.height = child1_allocation.height
                child2_allocation.width = max(1, child2_w)
                #
                if self.handle_pos.can_move_child2: #是否向child2方向移动.
                    self.handle_pos.x = child2_allocation.x - self.handle_pos.size
                else:
                    self.handle_pos.x = child2_allocation.x
            else:
                self.handle_pos.x = self.allocation.x
                self.handle_pos.y = self.allocation.y
                self.handle_pos.w = self.allocation.width
                self.handle_pos.h = self.handle_pos.size
                # set child1/2 (x, y, w, h)
                if self.handle_pos.can_move_child2:
                    child1_h = allocation.height - child2_requisition[1]
                    child2_h = child2_requisition[1]
                    if not self.handle_pos.can_in:
                        child1_h = allocation.height
                        child2_h = 1
                else:
                    child2_h = allocation.height - child1_requisition[1]
                    child1_h = child1_requisition[1]
                    if not self.handle_pos.can_in:
                        child2_h = allocation.height
                        child1_h = 1
                child1_allocation.x = allocation.x
                child1_allocation.y = allocation.y
                child1_allocation.width = max(1, allocation.width)
                child1_allocation.height = max(1, child1_h)
                child2_allocation.x = child1_allocation.x
                child2_allocation.y = allocation.y + child1_allocation.height
                child2_allocation.height = max(1, child2_h)
                child2_allocation.width = max(1, allocation.width)
                #
                if self.handle_pos.can_move_child2:
                    self.handle_pos.y = child2_allocation.y - self.handle_pos.size
                else:
                    self.handle_pos.y = child2_allocation.y

        if self.get_realized():
            if self.__type == gtk.ORIENTATION_HORIZONTAL: # 横向.
                # 设置位置和宽高.
                self.__handle.move_resize(
                        self.handle_pos.x,
                        self.handle_pos.y,
                        self.handle_pos.size,
                        self.handle_pos.h
                        )
            else:
                self.__handle.move_resize(
                        self.handle_pos.x,
                        self.handle_pos.y,
                        self.handle_pos.w,
                        self.handle_pos.size
                        )
        # 设置 child1, child2 (x, y, w, h)
        # 显示 child1, child2.
        if self.__child1:
            if not self.__child2:
                child1_allocation.x = allocation.x
                child1_allocation.y = allocation.y
                child1_allocation.width = allocation.width
                child1_allocation.height = allocation.height
            self.__child1.size_allocate(child1_allocation)
            self.__child1.set_child_visible(True)
        if self.__child2:
            if not self.__child1:
                child2_allocation.x = allocation.x
                child2_allocation.y = allocation.y
                child2_allocation.width = allocation.width
                child2_allocation.height = allocation.height
            self.__child2.size_allocate(child2_allocation)
            self.__child2.set_child_visible(True)
        #
        if self.get_mapped():
            self.__handle.show()

    ##############################################################3
    def add1(self, widget):
        self.__child1 = widget
        self.__child1.set_parent(self)

    def add2(self, widget):
        self.__add2_pack(widget)

    def __add1_pack(self, child):
        if (not self.__child1):
            self.__child1 = child
            self.__child1.set_parent(self)

    def __add2_pack(self, child):
        if (not self.__child2):
            self.__child2 = child
            self.__child2.connect("realize", self.__child2_realize_event)
            self.__child2.set_parent(self)

    def __child2_realize_event(self, widget):
        if widget.window and widget.window != self.window:
            widget.window.set_composited(True)

    def can_move_child2(self, check):
        # True 是向chidl2移动, False向child1移动.
        self.handle_pos.can_move_child2 = check

    def set_type(self, _type):
        self.__type = _type

    def get_type(self):
        return self.__type

    def get_handle(self):
        return self.__handle

    def get_child1(self):
        return self.__child1

    def get_child2(self):
        return self.__child2

gobject.type_register(Paned)

if __name__ == "__main__":
    # !! 建议不要将ui_theme绑在控件上，避免无法单独调用.
    from draw import draw_pixbuf
    from theme import ui_theme

    def test1_clicked(widget):
        top_paned.set_type(gtk.ORIENTATION_HORIZONTAL)

    def test2_clicked(widget):
        top_paned.set_type(gtk.ORIENTATION_VERTICAL)

    def test2_realize_event(widget):
        widget.window.set_composited(True)

    def top_paned_paint(cr, handle_pos):
        in_pixbuf = ui_theme.get_pixbuf("paned/in.png").get_pixbuf()
        out_pixbuf = ui_theme.get_pixbuf("paned/out.png").get_pixbuf()
        #
        if handle_pos.can_visible:
            # 绘制例子.
            if handle_pos.can_in:
                # 判断要向那个方向的控件靠拢.
                if handle_pos.can_move_child2:
                    pixbuf = in_pixbuf
                else:
                    pixbuf = out_pixbuf
            else:
                # 判断要向那个方向的控件靠拢.
                if handle_pos.can_move_child2:
                    pixbuf = out_pixbuf
                else:
                    pixbuf = in_pixbuf
            # 判断是否为纵向.
            if top_paned.get_type() == gtk.ORIENTATION_VERTICAL:
                pixbuf = pixbuf.rotate_simple(270)
            #
            draw_pixbuf(cr, pixbuf, handle_pos.x, handle_pos.y)

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_size_request(500, 500)
    win.connect("destroy", lambda w : gtk.main_quit())
    #
    top_paned = Paned()
    top_paned.paint_handle_hd = top_paned_paint
    top_paned.set_type(gtk.ORIENTATION_VERTICAL)
    top_paned.can_move_child2(False)
    test1 = gtk.Button("test1")
    top_paned.add1(test1)
    test2 = gtk.TextView()
    #test2 = gtk.Button()
    top_paned.add2(test2)
    #
    win.add(top_paned)
    win.show_all()
    gtk.main()



