#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
#
# Author:     Xia Bin <xiabin@linuxdeepin.com>
# Maintainer: Xia Bin <xiabin@linuxdeepin.com>
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

from gtk import gdk
from theme import ui_theme
from utils import remove_signal_id, color_hex_to_cairo
import gobject
import gtk

__all__ = ['ScrolledWindow']

# the p_range is the virtual width/height, it's value is smaller than
# the allocation.width/height when scrollbar's width/height smaller than
# the minimum scrollbar length.
# p_range =  allocation.width/height - (min_bar_len - *bar_len*)
#       the *bar_len* =  (adj.page_size / adj.upper) * allocation.width/height
# by this processing, 0~(adj.upper-adj.page_size) will be mapped to 0~p_range.
def value2pos(value, p_range, upper):
    '''
    Compute the scrollbar position by the adjustment value.
    '''
    if upper == 0: return 0
    return p_range * float(value) / upper

def pos2value(pos, p_range, upper):
    '''
    Compute the adjustment value by the scrollbar position.
    '''
    if p_range == 0 : return 0
    return pos * upper / p_range

class ScrolledWindow(gtk.Bin):
    '''
    The scrolled window with deepin's custom scrollbar.

    @undocumented: do_enter_notify_event
    @undocumented: _test_calc
    @undocumented: do_remove
    @undocumented: do_unmap
    @undocumented: do_map
    @undocumented: set_policy
    @undocumented: set_shadow_type
    @undocumented: do_realize
    @undocumented: do_size_request
    @undocumented: do_unrealize
    @undocumented: update_scrollbar
    @undocumented: do_size_allocate
    @undocumented: do_add
    @undocumented: hadjustment_changed
    @undocumented: vadjustment_changed
    @undocumented: calc_hbar_allocation
    @undocumented: calc_hbar_length
    @undocumented: calc_vbar_allocation
    @undocumented: calc_vbar_length
    @undocumented: do_motion_notify_event
    @undocumented: do_leave_notify_event
    @undocumented: do_scroll_event
    @undocumented: make_bar_bigger
    @undocumented: make_bar_smaller
    @undocumented: do_button_release_event
    @undocumented: draw_vbar
    @undocumented: draw_hbar
    @undocumented: do_expose_event
    '''

    __gsignals__ = {
        "vscrollbar-state-changed":(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_STRING,))
        }

    def __init__(self,
                 right_space=2,
                 top_bottom_space=3,
                 ):
        '''
        Init scrolled window.

        @param right_space: the space between right border and the vertical scrollbar.
        @param top_bottom_space: the space between top border and the vertical scrollbar.
        '''
        gtk.Bin.__init__(self)
        self.bar_min_length = 50  #scrollbar smallest height
        self.bar_small_width = 7
        self.bar_width = 14  #normal scrollbar width
        self.bar_background = ui_theme.get_color("scrolledbar")
        self.right_space = right_space
        self.top_bottom_space = top_bottom_space

        self.h_value_change_id = None
        self.h_change_id = None
        self.v_value_change_id = None
        self.v_change_id = None

        self.vscrollbar_state = None

        class Record():
            def __init__(self):
                self.bar_len = 0  # scrollbar length
                self.last_pos = 0 # last mouse motion pointer's position (x or y)

                # Last mouse motion times-tamp, if user moved the window
                # then the last_pos is likely become invalid so we need "last_time"
                # to deal with this situation.
                self.last_time = 0
                self.virtual_len = 0   # the virtual window height or width length
                self.bar_pos = 0       # the scrollbar top-corner/left-corner position
                self.is_inside = False # is pointer in the scrollbar region?
                self.in_motion = False # is user is dragging scrollbar?
                self.policy = gtk.POLICY_AUTOMATIC
                self.need_update_region = False # update gdk.Window's shape_region when need

        self._horizaontal = Record()
        self._vertical = Record()

        self.set_can_focus(True)
        self.vallocation = gdk.Rectangle()
        self.hallocation = gdk.Rectangle()
        self.set_vadjustment(gtk.Adjustment())
        self.set_hadjustment(gtk.Adjustment())
        self.set_has_window(False)

    def do_expose_event(self, e):
        if e.window == self.vwindow:
            self.draw_vbar()
            return True
        elif e.window == self.hwindow:
            self.draw_hbar()
            return True
        else:
            return False

    def draw_vbar(self):
        cr = self.vwindow.cairo_create()
        cr.set_source_rgb(*color_hex_to_cairo(self.bar_background.get_color()))
        cr.rectangle(0, 0, self.vallocation.width, self.vallocation.height)
        cr.fill()

    def draw_hbar(self):
        cr = self.hwindow.cairo_create()
        cr.set_source_rgb(*color_hex_to_cairo(self.bar_background.get_color()))
        cr.rectangle(0, 0, self.hallocation.width, self.hallocation.height)
        cr.fill()

    def do_button_press_event(self, e):
        if 0 <= e.x - self.vallocation.x <= self.bar_width:
            # Button press on vadjustment.
            press_pos = e.y - self.vadjustment.value
            value = pos2value(press_pos - self.vallocation.height / 2, self._vertical.virtual_len, self.vadjustment.upper)
            value = max(0, min(value, self.vadjustment.upper - self.vadjustment.page_size))

            if press_pos < self.vallocation.y:
                if self.vadjustment.value - value > self.vadjustment.page_size:
                    self.vadjustment.set_value(max(self.vadjustment.value - self.vadjustment.page_size,
                                                   0))
                else:
                    self.vadjustment.set_value(value)

                return True
            elif press_pos > self.vallocation.y + self.vallocation.height:
                if value - self.vadjustment.value > self.vadjustment.page_size:
                    self.vadjustment.set_value(min(self.vadjustment.value + self.vadjustment.page_size,
                                                   self.vadjustment.upper - self.vadjustment.page_size))
                else:
                    self.vadjustment.set_value(value)

                return True
            else:
                return False
        elif 0 <= e.y - self.hallocation.y <= self.bar_width:
            # Button press on hadjustment.
            press_pos = e.x - self.hadjustment.value
            value = pos2value(press_pos - self.hallocation.width / 2, self._horizaontal.virtual_len, self.hadjustment.upper)
            value = max(0, min(value, self.hadjustment.upper - self.hadjustment.page_size))

            if press_pos < self.hallocation.x:
                if self.hadjustment.value - value > self.hadjustment.page_size:
                    self.hadjustment.set_value(max(self.hadjustment.value - self.hadjustment.page_size,
                                                   0))
                else:
                    self.hadjustment.set_value(value)

                return True
            elif press_pos > self.hallocation.x + self.hallocation.width:
                if value - self.hadjustment.value > self.hadjustment.page_size:
                    self.hadjustment.set_value(min(self.hadjustment.value + self.hadjustment.page_size,
                                                   self.hadjustment.upper - self.hadjustment.page_size))
                else:
                    self.hadjustment.set_value(value)

                return True
            else:
                return False
        else:
            return False

    def do_button_release_event(self, e):
        if e.window == self.hwindow:
            self._horizaontal.in_motion = False
            if not self._horizaontal.is_inside:
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
            return True
        elif e.window == self.vwindow:
            self._vertical.in_motion = False
            if not self._vertical.is_inside:
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
            return True
        else:
            return False

    def make_bar_smaller(self, orientation):
        if orientation == gtk.ORIENTATION_HORIZONTAL:
            bar_len = self._horizaontal.bar_len
            if bar_len == 0:
                self._horizaontal.need_update_region = True
                return
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, int(bar_len), self.bar_small_width))

            if self.hallocation.x == 0:
                self.hwindow.shape_combine_region(region, self.top_bottom_space, self.bar_width - self.bar_small_width -self.right_space)
            else:
                self.hwindow.shape_combine_region(region, -self.top_bottom_space, self.bar_width - self.bar_small_width -self.right_space)
        elif orientation == gtk.ORIENTATION_VERTICAL:
            bar_len = self._vertical.bar_len
            if bar_len == 0:
                self._vertical.need_update_region = True
                return
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, self.bar_small_width, int(bar_len)))

            if self.vallocation.y == 0:
                self.vwindow.shape_combine_region(region, self.bar_width-self.bar_small_width - self.right_space, self.top_bottom_space)
            else:
                self.vwindow.shape_combine_region(region, self.bar_width-self.bar_small_width - self.right_space, -self.top_bottom_space)
        else:
            raise "make_bar_smaller's orientation must be gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL"

        return False

    def make_bar_bigger(self, orientation):
        if orientation == gtk.ORIENTATION_HORIZONTAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, int(self._horizaontal.bar_len), self.bar_width))

            if self.hallocation.x == 0:
                self.hwindow.shape_combine_region(region, self.top_bottom_space, -self.right_space)
            else:
                self.hwindow.shape_combine_region(region, -self.top_bottom_space, -self.right_space)
        elif orientation == gtk.ORIENTATION_VERTICAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, self.bar_width, int(self._vertical.bar_len)))

            if self.vallocation.y == 0:
                self.vwindow.shape_combine_region(region, -self.right_space, self.top_bottom_space)
            else:
                self.vwindow.shape_combine_region(region, -self.right_space, -self.top_bottom_space)
        else:
            raise "make_bar_bigger's orientation must be gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL"

    def do_scroll_event(self, e):
        value = self.vadjustment.value
        step = self.vadjustment.step_increment
        upper = self.vadjustment.upper
        page_size = self.vadjustment.page_size

        # Emit signal 'vscrollbar_state_changed'.
        self.emit_vscrollbar_state_changed(e)

        if e.direction == gdk.SCROLL_DOWN:
            self.vadjustment.set_value(min(upper-page_size-1, value+step))
        elif e.direction == gdk.SCROLL_UP:
            self.vadjustment.set_value(max(0, value-step))

        # WARNING: We need always return False here, otherwise nesting scrolled window can't work correctly.
        return False

    def do_leave_notify_event(self, e):
        if e.window == self.hwindow :
            self._horizaontal.is_inside = False
            if not self._horizaontal.in_motion:
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
            return True
        elif e.window == self.vwindow:
            self._vertical.is_inside = False
            if not self._vertical.in_motion:
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
            return True
        else:
            return False

    def do_enter_notify_event(self, e):
        if e.window == self.hwindow:
            self.make_bar_bigger(gtk.ORIENTATION_HORIZONTAL)
            self._horizaontal.is_inside = True
            return True
        elif e.window == self.vwindow:
            self.make_bar_bigger(gtk.ORIENTATION_VERTICAL)
            self._vertical.is_inside = True
            return True
        else:
            return False

    def do_visibility_notify_event(self, e):
        self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
        self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)

        return False

    def do_motion_notify_event(self, e):
        if not (e.window == self.hwindow or e.window == self.vwindow): return False

        if e.window == self.hwindow and (e.state & gtk.gdk.BUTTON1_MASK) == gtk.gdk.BUTTON1_MASK:
            self.make_bar_bigger(gtk.ORIENTATION_HORIZONTAL)
            if self._horizaontal.last_time == 0:
                self._horizaontal.last_time = e.time
            elif e.time - self._horizaontal.last_time > 1000:
                self._horizaontal.last_time = 0
                self._horizaontal.last_pos = 0

            if self._horizaontal.last_pos == 0 or self._horizaontal.last_time == 0:
                self._horizaontal.last_pos  = e.x_root
                return True
            deltaX = e.x_root - self._horizaontal.last_pos
            upper = self.hadjustment.upper

            # The pos maybe beyond the effective range,
            # but we will immediately corrected it's value.
            # the "invariant" is  the "value" always in the effective range.
            value = pos2value(self._horizaontal.bar_pos+deltaX, self._horizaontal.virtual_len, upper)
            value = max(0, min(value, self.hadjustment.upper-self.hadjustment.page_size))
            self.hadjustment.set_value(value)

            self._horizaontal.last_pos = e.x_root
            self._horizaontal.last_time = e.time
            self._horizaontal.in_motion = True
            return True

        elif e.window == self.vwindow and (e.state & gtk.gdk.BUTTON1_MASK) == gtk.gdk.BUTTON1_MASK:
            self.make_bar_bigger(gtk.ORIENTATION_VERTICAL)
            if self._vertical.last_time == 0:
                self._vertical.last_time = e.time
            elif e.time - self._vertical.last_time > 1000:
                self._vertical.last_time = 0
                self._vertical.last_pos = 0

            if self._vertical.last_pos == 0 or self._vertical.last_time == 0:
                self._vertical.last_pos  = e.y_root
                return True

            upper = self.vadjustment.upper
            deltaY = e.y_root - self._vertical.last_pos

            value = pos2value(self._vertical.bar_pos+deltaY, self._vertical.virtual_len, upper)
            value = max(0, min(value, self.vadjustment.upper-self.vadjustment.page_size))
            self.vadjustment.set_value(value)

            self._vertical.last_pos = e.y_root
            self._vertical.last_time = e.time
            self._vertical.in_motion = True

            return True

    def calc_vbar_length(self):
        self._vertical.virtual_len = self.allocation.height
        if self.vadjustment.upper <= 1 or self._vertical.policy == gtk.POLICY_NEVER:
            self._vertical.bar_len = 0
            return

        ratio = float(self.vadjustment.page_size) / (self.vadjustment.upper-self.vadjustment.lower)

        if ratio == 1:
            self._vertical.bar_len = 0
        else:
            bar_len = self._vertical.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._vertical.virtual_len -= (self.bar_min_length - bar_len)
            self._vertical.bar_len = max(bar_len, self.bar_min_length)

    def calc_vbar_allocation(self):
        bar_len = int(self._vertical.bar_len)
        if bar_len == 0:
            self.vallocation = gdk.Rectangle(0, 0, 0, 0)
            self.vwindow.hide()
        else:
            self.vwindow.show()
            self.vallocation = gdk.Rectangle(
                    self.allocation.width - self.bar_width, int(self._vertical.bar_pos),
                    self.bar_width, bar_len)

    def calc_hbar_length(self):
        self._horizaontal.virtual_len = self.allocation.width
        if self.hadjustment.upper <= 1 or self._horizaontal.policy == gtk.POLICY_NEVER:
            self._horizaontal.bar_len = 0
            return


        ratio = float(self.hadjustment.page_size) / (self.hadjustment.upper-self.hadjustment.lower)

        if ratio == 1:
            self._horizaontal.bar_len = 0
        else:
            bar_len = self._horizaontal.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._horizaontal.virtual_len -= (self.bar_min_length - bar_len)
            self._horizaontal.bar_len = max(bar_len, self.bar_min_length)

    def calc_hbar_allocation(self):
        bar_len = int(self._horizaontal.bar_len)
        if bar_len == 0:
            self.hallocation = gdk.Rectangle(0, 0, 0, 0)
            self.hwindow.hide()
        else:
            self.hwindow.show()
            self.hallocation = gdk.Rectangle(
                    int(self._horizaontal.bar_pos), self.allocation.height - self.bar_width,
                    bar_len, self.bar_width)

    def vadjustment_changed(self, adj):
        if self.get_realized():
            upper = self.vadjustment.upper
            self._vertical.bar_pos = value2pos(adj.value, self._vertical.virtual_len, upper)
            self.calc_vbar_allocation()
            self.vwindow.move_resize(*self.vallocation)

            self.emit_vscrollbar_state_changed()

            self.queue_draw()

    def hadjustment_changed(self, adj):
        if self.get_realized():
            upper = self.hadjustment.upper
            self._horizaontal.bar_pos = value2pos(adj.value, self._horizaontal.virtual_len, upper)
            self.calc_hbar_allocation()
            self.hwindow.move_resize(*self.hallocation)
            self.queue_draw()

    def add_with_viewport(self, child):
        '''
        Used to add children without native scrolling capabilities.

        If a child has native scrolling, use ScrolledWindow.add() instead

        of this function.

        @param child: the child without native scrolling.
        '''
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(child)
        vp.show()
        self.add(vp)

    def add_child(self, child):
        '''
        Add the child to this ScrolledWindow.The child should have

        native scrolling capabilities.

        @param child: the child with native scrolling.
        '''
        self.add_with_viewport(child)

    def do_add(self, child):
        self.child = None
        gtk.Bin.do_add(self, child)

        child.set_scroll_adjustments(self.hadjustment, self.vadjustment)

    def do_size_request(self, requisition):
        if self.child:
            self.child.do_size_request(self.child, requisition)

    def do_size_allocate(self, allocation):
        self.allocation = allocation

        if self.get_realized():
            self.binwindow.move_resize(*self.allocation)

        # Must before calc_xxx_length, because we need child to compute the adjustment value.
        if self.child:
            (allocation.x, allocation.y) = (0, 0)
            self.child.do_size_allocate(self.child, allocation)

            self.update_scrollbar()

            if self.get_realized():
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)

    def update_scrollbar(self, *arg, **argk):
        if self.get_realized():
            self.calc_vbar_length()
            self.calc_hbar_length()
            self.vadjustment.emit('value-changed')
            self.hadjustment.emit('value-changed')
            if self._horizaontal.need_update_region:
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
                self._horizaontal.need_update_region = False
                self.hwindow.show()
            if self._vertical.need_update_region:
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
                self._vertical.need_update_region = False
                self.vwindow.show()

    def do_unrealize(self):
        self.binwindow.set_user_data(None)
        self.binwindow.destroy()
        self.binwindow = None
        self.vwindow.set_user_data(None)
        self.vwindow.destroy()
        self.vwindow = None
        self.hwindow.set_user_data(None)
        self.hwindow.destroy()
        self.hwindow = None

        gtk.Bin.do_unrealize(self)

    def do_realize(self):
        gtk.Bin.do_realize(self)

        self.binwindow = gtk.gdk.Window(self.get_parent_window(),
                x=self.allocation.x,
                y=self.allocation.y,
                width=self.allocation.width,
                height=self.allocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=(self.get_events()| gdk.EXPOSURE_MASK | gdk.VISIBILITY_NOTIFY_MASK),
                visual=self.get_visual(),
                colormap=self.get_colormap(),
                )
        self.binwindow.set_user_data(self)

        self.vwindow = gtk.gdk.Window(self.binwindow,
                x=self.vallocation.x,
                y=self.vallocation.y,
                width=self.vallocation.width,
                height=self.vallocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                visual=self.get_visual(),
                colormap=self.get_colormap(),
                event_mask=(self.get_events()
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK | gdk.BUTTON_RELEASE_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.vwindow.set_user_data(self)

        self.hwindow = gtk.gdk.Window(self.binwindow,
                x=self.hallocation.x,
                y=self.hallocation.y,
                width=self.hallocation.width,
                height=self.hallocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                colormap=self.get_colormap(),
                visual=self.get_visual(),
                event_mask=(self.get_events()
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK | gdk.BUTTON_RELEASE_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.hwindow.set_user_data(self)

        if self.child:
            self.child.set_parent_window(self.binwindow)

        self.queue_resize()

    def set_shadow_type(self, t):
        return

    def set_policy(self, h, v):
        '''
        Set the policy of ScrolledWindow's scrollbar

        @param h: the horizontal scrollbar policy
        @param v: the vertical scrollbar policy
        '''
        self._horizaontal.policy = h
        self._vertical.policy = v
        return

    def do_map(self):
        gtk.Bin.do_map(self)    # must before self.xwindow.show(), didn't know the reason.
        self.binwindow.show()
        if self.child and not self.child.get_mapped() and self.child.get_visible():
            self.child.do_map(self.child)

    def do_unmap(self):
        self.binwindow.hide()
        self.hwindow.hide()
        self.vwindow.hide()
        gtk.Bin.do_unmap(self)

    def do_remove(self, child):
        gtk.Bin.do_remove(self, child)

    def get_vadjustment(self):
        '''
        Returns the vertical scrollbar's adjustment,
        used to connect the vertical scrollbar to the child widget's
        vertical scroll functionality.
        '''
        return self.vadjustment

    def get_hadjustment(self):
        '''
        Returns the horizontal scrollbar's adjustment,
        used to connect the horizontal scrollbar to the child
        widget's horizontal scroll functionality.
        '''
        return self.hadjustment

    def set_hadjustment(self, adj):
        '''
        Sets the gtk.Adjustment for the horizontal scrollbar.

        @param adj: horizontal scroll adjustment
        '''
        remove_signal_id(self.h_value_change_id)
        remove_signal_id(self.h_change_id)

        self.hadjustment = adj
        h_value_change_handler_id = self.hadjustment.connect('value-changed', self.hadjustment_changed)
        h_change_handler_id = self.hadjustment.connect('changed', self.update_scrollbar)
        self.h_value_change_id = (self.hadjustment, h_value_change_handler_id)
        self.h_change_id = (self.hadjustment, h_change_handler_id)

    def set_vadjustment(self, adj):
        '''
        Sets the gtk.Adjustment for the vertical scrollbar.

        @param adj: vertical scroll adjustment
        '''
        remove_signal_id(self.v_value_change_id)
        remove_signal_id(self.v_change_id)

        self.vadjustment = adj
        v_value_change_handler_id = self.vadjustment.connect('value-changed', self.vadjustment_changed)
        v_change_handler_id = self.vadjustment.connect('changed', self.update_scrollbar)
        self.v_value_change_id = (self.vadjustment, v_value_change_handler_id)
        self.v_change_id = (self.vadjustment, v_change_handler_id)

    def _test_calc(self):
        for i in xrange(0, int(self.vadjustment.upper-self.vadjustment.page_size), 30):
            pos = value2pos(i, self._vertical.virtual_len, self.vadjustment.upper)
            print "value:%f --> pos:%d" % (i, pos),
            assert(pos <= self.allocation.height-self._vertical.bar_len),\
                "pos(%f) should small than(%f)"  % (pos, self.allocation.height-self._vertical.bar_len)
            value = pos2value(pos, self._vertical.virtual_len, self.vadjustment.upper)
            print "\t pos:%d -->value:%f" % (pos, value)

        print "v_len:%f, height:%f, vir_bar_len:%d" % ( self._vertical.virtual_len,
                self.allocation.height, self._vertical.bar_len)

    def emit_vscrollbar_state_changed(self, e=None):
        value = self.vadjustment.value
        page_size = self.vadjustment.page_size
        upper = self.vadjustment.upper

        if e == None:
            bottom_value = upper - page_size
        elif e.type == gtk.gdk.MOTION_NOTIFY:
            bottom_value = upper - page_size
        elif e.type == gtk.gdk.SCROLL:
            bottom_value = upper - page_size - 1

        if upper != page_size:
            if value == 0 and self.vscrollbar_state != "top":
                self.vscrollbar_state = "top"
                self.emit("vscrollbar-state-changed", self.vscrollbar_state)
            elif value > 0 and value < bottom_value and self.vscrollbar_state != "center":
                self.vscrollbar_state = "center"
                self.emit("vscrollbar-state-changed", self.vscrollbar_state)
            elif value == bottom_value and self.vscrollbar_state != "bottom":
                self.vscrollbar_state = "bottom"
                self.emit("vscrollbar-state-changed", self.vscrollbar_state)

gobject.type_register(ScrolledWindow)
