#! /usr/bin/env python2

import gobject
import gtk
from gtk import gdk


def value2pos(value, height, upper):
    '''compute the scrollbar position by the adjustment value'''
    if upper * height == 0:
        return 0
    return float(value) / upper * height

def pos2value(pos, height, upper, page_size):
    '''compute the adjustment value by the scrollbar position'''
    ratio = float(pos) / height
    ratio2 = (upper - page_size) / upper
    #print "ratio:", ratio, "  ratio2:", ratio2
    if abs(ratio - ratio2) < 0.05:
        return upper-page_size
    else:
        return  ratio * upper

class ScrolledWindow(gtk.Bin):
    '''Scrolled window.'''

    def __init__(self):
        '''Init scrolled window.'''
        gtk.Bin.__init__(self)
        self.bar_min_length = 160
        self.bar_width = 10
        self.set_can_focus(True)
        self.set_has_window(False)
        self.connect("motion_notify_event", self.on_bar_motion)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("scroll-event", self.on_scroll)
        self.vinside = False
        self.vallocation = gdk.Rectangle()
        self.hallocation = gdk.Rectangle()
        self.set_vadjustment(gtk.Adjustment())
        self.set_hadjustment(gtk.Adjustment())

        class Record():
            def __init__(self):
                self.bar_len = 0     #scrollbar length
                self.last_pos = 0    #last mouse motion pointer (x or y)
                self.last_time = 0   #last mouse motion timestamp
                self.virtual_len = 0 #the virtual window height or width length
                self.bar_pos = 0     #the scrollbar topcorner/leftcorner position

        self._horizaontal = Record()
        self._vertical = Record()

    def on_scroll(self, w, e):
        value = self.vadjustment.value
        step = self.vadjustment.step_increment
        page_size = self.vadjustment.page_size
        upper = self.vadjustment.upper

        if e.direction == gdk.SCROLL_DOWN:
            self.vadjustment.set_value(min(upper-page_size-1, value+step))
            #print "value:%d, upper:%d, page_size:%d" % (value, upper, page_size)
        elif e.direction == gdk.SCROLL_UP:
            self.vadjustment.set_value(max(0, value-step))
        pass

    def on_leave(self, w, e):
        return False
        if e.window == self.vwindow:
            self.vwindow.shape_combine_region(gdk.region_rectangle(gdk.Rectangle(0, 0, 8, 100)), 8, 0)
            self.vwindow.set_background(gdk.Color("gray"))
            self.vinside = False
            self.queue_draw()
            return True
        return False
    
    def on_enter(self, w, e):
        return False
        if e.window == self.vwindow:
            self.vwindow.shape_combine_region(gdk.region_rectangle(gdk.Rectangle(0, 0, 20, 100)), 0, 0)
            self.vwindow.set_background(gdk.Color("blue"))
            self.vinside = True
            self.queue_draw()
            return True
        return False

    def on_bar_motion(self, w, e):
        if e.window == self.hwindow and e.state == gtk.gdk.BUTTON1_MASK:
            if self._horizaontal.last_time == 0:
                self._horizaontal.last_time = e.time
            elif e.time - self._horizaontal.last_time > 1000:
                self._horizaontal.last_time = 0
                self._horizaontal.last_pos = 0

            if self._horizaontal.last_pos == 0 or self._horizaontal.last_time == 0:
                self._horizaontal.last_pos  = e.x_root
                return False
            deltaX = e.x_root - self._horizaontal.last_pos
            #if abs(deltaX) < 8: return False
            upper = self.hadjustment.upper
            width = self.allocation.width
            self._horizaontal.bar_pos = min(max(self._horizaontal.bar_pos + deltaX, 0), width - self._horizaontal.bar_len)


            self.hadjustment.set_value(pos2value(self._horizaontal.bar_pos, self._horizaontal.virtual_len, upper, self.hadjustment.page_size))

            self._horizaontal.last_pos = e.x_root
            self._horizaontal.last_time = e.time
            return True

        elif e.window == self.vwindow and e.state == gtk.gdk.BUTTON1_MASK:
            if self._vertical.last_time == 0:
                self._vertical.last_time = e.time
            elif e.time - self._vertical.last_time > 1000:
                self._vertical.last_time = 0
                self._vertical.last_pos = 0

            if self._vertical.last_pos == 0 or self._vertical.last_time == 0:
                self._vertical.last_pos  = e.y_root
                return False
            deltaY = e.y_root - self._vertical.last_pos
            #if abs(deltaY) < self._vertical.bar_len * 0.01: return False
            upper = self.vadjustment.upper
            height = self.allocation.height

            self._vertical.bar_pos = min(max(self._vertical.bar_pos + deltaY, 0), height - self._vertical.bar_len)

            self.vadjustment.set_value(pos2value(self._vertical.bar_pos, self._vertical.virtual_len, upper, self.vadjustment.page_size))

            self._vertical.last_pos = e.y_root
            self._vertical.last_time = e.time
            return True

        else:
            return False

    def calc_vbar_length(self):
        self._vertical.virtual_len = self.allocation.height
        #print "self.allocation", self._height

        if self.vadjustment.upper == 0: return

        #this is an workaround, adjustment.page_size didn't update when viewport allocate
        self.vadjustment.page_size = self.allocation.height

        ratio = float(self.vadjustment.page_size) / (self.vadjustment.upper-self.vadjustment.lower)

        #because we set the page_size = self.allocation.height, so upper may smaller than adjustment.upper
        if ratio == 1 or self.vadjustment.upper < self.vadjustment.page_size:
            self._vertical.bar_len = 0
        else:
            bar_len = self._vertical.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._vertical.virtual_len -= (self.bar_min_length - bar_len)
            self._vertical.bar_len = max(bar_len, self.bar_min_length)

    def calc_vbar_allocation(self):
        #print "self.vpos", self.vpos
        self.vallocation = gdk.Rectangle(
                self.allocation.width - self.bar_width, int(self._vertical.bar_pos),
                self.bar_width, int(self._vertical.bar_len))

    def calc_hbar_length(self):
        self._horizaontal.virtual_len = self.allocation.width

        # self.hadjustment has'nt init
        if self.hadjustment.upper <= 1: return

        #this is an workaround, adjustment.page_size didn't update when viewport allocate
        self.hadjustment.page_size = self.allocation.width

        ratio = float(self.hadjustment.page_size) / (self.hadjustment.upper-self.hadjustment.lower)
        assert(self.hadjustment.lower == 0)

        if ratio == 1 or self.hadjustment.upper < self.hadjustment.page_size:
            self._horizaontal.bar_len = 0
        else:
            bar_len = self._horizaontal.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._horizaontal.virtual_len -= (self.bar_min_length - bar_len)
            self._horizaontal.bar_len = max(bar_len, self.bar_min_length)

    def calc_hbar_allocation(self):
        #assert 0 <= int(self.hpos) <= self.allocation.width - self.hbar_length,\
        #        "self.hpos %f   self.allocation.width %f self.hbar_lengh %f" % (self.hpos, self.allocation.width,
        #                self.hbar_length)
        self.hallocation = gdk.Rectangle(
                int(self._horizaontal.bar_pos), self.allocation.height - self.bar_width,
                int(self._horizaontal.bar_len), self.bar_width)

    def vadjustment_changed(self, adj):
        if self.get_realized():
            upper = self.vadjustment.upper
            assert(self.vadjustment.lower == 0)
            self._vertical.bar_pos = value2pos(adj.value, self._vertical.virtual_len, upper)
            self.calc_vbar_allocation()
            self.vwindow.move_resize(*self.vallocation)
            self.child.draw(self.allocation)
            self.queue_draw()
    def hadjustment_changed(self, adj):
        if self.get_realized():
            upper = self.hadjustment.upper
            self._horizaontal.bar_pos = value2pos(adj.value, self._horizaontal.virtual_len, upper)
            self.calc_hbar_allocation()
            self.hwindow.move_resize(*self.hallocation)
            self.child.queue_draw()


    def add(self, child):
        self.child = child
        child.set_parent(self)
        child.set_vadjustment(self.vadjustment)
        child.set_hadjustment(self.hadjustment)
        if self.get_realized():
            child.set_parent_window(self.binwindow)

    def add_with_viewport(self, child):
        vp = gtk.Viewport()
        vp.add(child)
        vp.show()
        self.add(vp)

    def add_child(self, child):
        self.add_with_viewport(child)
        #raise Exception, "use add_with_viewport instead add_child"

    def do_size_request(self, requsition):
        #print "do_size_request", (requsition.width, requsition.height)
        if self.child:
            self.child.do_size_request(self.child, requsition)
            #self.child_requistion = requsition

    def do_size_allocate(self, allocation):
        #print "do_size_allocate", allocation
        self.allocation = allocation


        vvalue = self.vadjustment.value
        hvalue = self.hadjustment.value

        self.calc_vbar_length()
        self._vertical.bar_pos = value2pos(vvalue, self._vertical.virtual_len, self.vadjustment.upper)
        self.calc_vbar_allocation()

        self.calc_hbar_length()
        self._horizaontal.bar_pos = value2pos(hvalue, self._horizaontal.virtual_len, self.hadjustment.upper)
        self.calc_hbar_allocation()


        if self.get_realized():
            self.vwindow.move_resize(*self.vallocation)
            self.hwindow.move_resize(*self.hallocation)
            self.binwindow.move_resize(*self.allocation)

        if self.child:
            allocation.x = 0
            allocation.y = 0
            self.child.do_size_allocate(self.child, allocation)

    def debug(self):
        print "hwindow:", self.hwindow.get_geometry()
        print "vwindow:", self.vwindow.get_geometry()
        print "binwindow:", self.binwindow.get_geometry()


    def do_unrealize(self):
        #print "do_unrealize"
        self.set_realized(False)
        assert(self.get_realized() == False)

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
        #print "self.get_parent_window():", self.get_parent_window()
        self.set_realized(True)
        #print "do_realize", self.get_realized()

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
                colormap=self.get_colormap(),
                event_mask=(self.get_events()
                    | gdk.ALL_EVENTS_MASK
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.vwindow.set_user_data(self)
        self.vwindow.set_opacity(1)
        #region = gdk.region_rectangle(gdk.Rectangle(0, 0, self.bar_width-3, int(self.vbar_length)))
        #self.vwindow.shape_combine_region(region, -3, 0)
        #self.vwindow.set_background(gdk.Color("gray"))


        self.hwindow = gtk.gdk.Window(self.binwindow,
                x=self.hallocation.x,
                y=self.hallocation.y,
                width=self.hallocation.width,
                height=self.hallocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                #wclass=gtk.gdk.INPUT_ONLY,
                wclass=gtk.gdk.INPUT_OUTPUT,
                colormap=self.get_colormap(),
                event_mask=(self.get_events()
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.hwindow.set_user_data(self)
        #region = gdk.region_rectangle(gdk.Rectangle(0, 0, int(self.hbar_length), self.bar_width))
        #self.hwindow.shape_combine_region(region, 0, -3)


        if self.child:
            self.child.set_parent_window(self.binwindow)

        gtk.Bin.do_realize(self)
        self.queue_resize()

    def do_remove(self, widget):
        self.vadjustment = None
        self.hadjustment = None
        
        if self.child == widget:
            widget.unparent()
            self.child = None

            if widget.flags() & gtk.VISIBLE and self.flags() & gtk.VISIBLE:
                self.queue_resize()

    def do_map(self):
        gtk.Bin.do_map(self)  #must before self.xwindow.show(), didn't know the reason.
        self.binwindow.show()
        self.hwindow.show()
        self.vwindow.show()
        if self.child and not self.child.get_mapped() and self.child.get_visible():
            #self.child.map()
            self.child.do_map(self.child)

    def do_unmap(self):
        #self.set_mapped(False)
        self.binwindow.hide()
        self.hwindow.hide()
        self.vwindow.hide()
        gtk.Bin.do_unmap(self)

    def get_vadjustment(self):
        return self.vadjustment
    def get_hadjustment(self):
        return self.hadjustment
    def set_hadjustment(self, adj):
        #? is python need disconnect?
        self.hadjustment = adj
        self.hadjustment.connect('value-changed', self.hadjustment_changed)
        self.hadjustment.connect('changed', self.hadjustment_changed)
    def set_vadjustment(self, adj):
        self.vadjustment = adj
        self.vadjustment.connect('value-changed', self.vadjustment_changed)
#        self.vadjustment.connect('changed', self.vadjustment_changed)


gobject.type_register(ScrolledWindow)
