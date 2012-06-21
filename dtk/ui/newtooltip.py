#!/usr/bin/env python

import gtk
from gtk import gdk
import gobject
from animation import Animation, LinerInterpolator
import cairo

_tooltip = None
class TooltipWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        #offset_x and offset_y has'nt support differnt value
        self.offset_x = 5
        self.offset_y = 5

        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("yellow"))
        self.is_need_shadow = True
        self.hide_delay = 3000

        self.padding_t = 5
        self.padding_b = 5
        self.padding_l = 5
        self.padding_r = 5
        ##########################################################

        self.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
        self.alignment = gtk.Alignment()
        self.alignment.set_padding(self.padding_t, self.padding_l, self.padding_b, self.padding_r)
        self.set_redraw_on_allocate(True)
        self.add(self.alignment)

    def generate_child(self):
        _tooltip.widget = _tooltip.tmpwidget
        if _tooltip.widget == _tooltip.prewidget and self.alignment.child:
            return

        callback = _tooltip.widget.get_data('__tooltip_callback')
        if callback != None:
            _tooltip.value = True
            child = callback()
            if child == self.alignment.child:
                return

        else:
            self.text = self.widget.get_data('__tooltip_text')
            if not self.text:
                self.text = "if you don't use tooltip...."

            child = gtk.Label(self.text)

        if self.alignment.child:
            self.alignment.child.hide()
            self.alignment.remove(self.alignment.child)
        self.alignment.add(child)
        self.alignment.show_all()
        self.queue_resize()

    def do_show(self):
        self.generate_child()

        allocation = gtk.gdk.Rectangle(0, 0, *self.alignment.child.size_request())
        allocation.width += self.padding_l + self.padding_r
        allocation.height += self.padding_t + self.padding_b
        self.size_allocate(allocation)


        gtk.Window.do_show(self)
        geo = self.window.get_geometry()

        #self.swindow.move_resize(geo[0]+self.offset_x, geo[1]+self.offset_y, allocation.width, allocation.height)
        self.swindow.move_resize(geo[0]+self.offset_x, geo[1]+self.offset_y, allocation.width, allocation.height)
        self.swindow.get_geometry() #must do this to query the allocation from X11 server.
        self.window.raise_()

        self.animation.init(1)
        self.animation.start_after(self.hide_delay)

    def do_hide(self):
        gtk.Window.do_hide(self)
        self.animation.stop()

    def do_realize(self):
        gtk.Window.do_realize(self)
        self.swindow = gtk.gdk.Window(self.get_parent_window(),
                x=self.allocation.x,
                y=self.allocation.y,
                width=self.allocation.width+30,
                height=self.allocation.height+30,
                window_type=gtk.gdk.WINDOW_TEMP,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=(self.get_events()| gdk.EXPOSURE_MASK | gdk.VISIBILITY_NOTIFY_MASK),
                visual=self.get_visual(),
                colormap=self.get_colormap(),
                )
        self.swindow.set_user_data(self)

        self.animation = Animation([self.window, self.swindow], gdk.Window.set_opacity, 1000, [0, 1],
                lambda *args: 1 - LinerInterpolator(*args))

    def do_map(self):
        gtk.Window.do_map(self)
        self.swindow.show()
    def do_unmap(self):
        gtk.Window.do_unmap(self)
        self.swindow.hide()

    def do_expose_event(self, e):
        if self.alignment.child:
            self.alignment.child.do_expose_event(self.alignment.child, e)

        cr = self.swindow.cairo_create()
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        if not self.is_need_shadow:
            return True
        #print self.allocation

        (x, y, width, height) = (0, 0, self.allocation.width, self.allocation.height)
        (o_x, o_y) = (self.offset_x, self.offset_y)


        #right-bottom corner
        radial = cairo.RadialGradient(width - o_x, height-o_y, 1,  width -o_x, height-o_y, o_x)
        radial.add_color_stop_rgba(0.0, 0,0,0, 0.3)
        radial.add_color_stop_rgba(0.6, 0,0,0, 0.1)
        radial.add_color_stop_rgba(1, 0,0,0, 0)
        cr.set_source(radial)
        cr.rectangle(width-o_x, height-o_y, o_x, o_y)
        cr.fill()

        #left-bottom corner
        radial = cairo.RadialGradient(o_x, height-o_y, 1,  o_x, height-o_y, o_x)
        radial.add_color_stop_rgba(0.0, 0,0,0, 0.3)
        radial.add_color_stop_rgba(0.6, 0,0,0, 0.1)
        radial.add_color_stop_rgba(1, 0,0,0, 0)
        cr.set_source(radial)
        cr.rectangle(0, height-o_y, o_x, o_y)
        cr.fill()

        #left-top corner
        radial = cairo.RadialGradient(width-o_x, o_y, 1, width-o_x, o_y, o_x)
        radial.add_color_stop_rgba(0.0, 0,0,0, 0.3)
        radial.add_color_stop_rgba(0.6, 0,0,0, 0.1)
        radial.add_color_stop_rgba(1, 0,0,0, 0)
        cr.set_source(radial)
        cr.rectangle(width-o_x, 0, o_x, o_y)
        cr.fill()


        vradial = cairo.LinearGradient(0, height-o_y, 0, height)
        vradial.add_color_stop_rgba(0.0, 0,0,0, .5)
        vradial.add_color_stop_rgba(0.4, 0,0,0, 0.25)
        vradial.add_color_stop_rgba(1, 0,0,0, 0.0)
        cr.set_source(vradial)
        cr.rectangle(o_x, height-o_x, width-2*o_x, height)
        cr.fill()

        hradial = cairo.LinearGradient(width-o_x, 0, width, 0)
        hradial.add_color_stop_rgba(0.0, 0,0,0, .5)
        hradial.add_color_stop_rgba(0.4, 0,0,0, 0.25)
        hradial.add_color_stop_rgba(1, 0,0,0, 0.0)
        cr.set_source(hradial)
        cr.rectangle(width-o_x, o_y, width, height-2*o_y)
        cr.fill()
    def set_value(self, v):
        print "set_value"
        _tooltip.value = True

    @staticmethod
    def set_text(widget, text):
        widget.set_data("__tooltip_text", text)
    @staticmethod
    def set_callback(widget, cb):
        widget.set_data("__tooltip_callback", cb)


    @staticmethod
    def attach_widget(widget, content=None):
        widget.set_has_tooltip(True)
        widget.set_tooltip_window(_tooltip)
        if callable(content):
            widget.set_data('__tooltip_callback', content)
        else:
            widget.set_data('__tooltip_text', content)

        def callback(w, x, y, k, t):
            _tooltip.tmpwidget = w
            if w != _tooltip.prewidget:
                _tooltip.prewidget = _tooltip.widget
            return _tooltip.value

        def hide_tooltip(w, e):
            if _tooltip.value and _tooltip.get_visible():
                _tooltip.value = False
                _tooltip.hide()
                gobject.timeout_add(1000, lambda : _tooltip.set_value(True))


        _tooltip.top = None
        if _tooltip.top != w.get_toplevel():
            _tooltip.top = w.get_toplevel()
        _tooltip.top.connect('motion-notify-event', hide_tooltip)

        widget.add_events(gdk.POINTER_MOTION_HINT_MASK|gdk.POINTER_MOTION_MASK)
        return widget.connect('query_tooltip', callback)

    @staticmethod
    def deattach_widget(widget, signal_id):
        gobject.source_remove(signal_id)
        widget.set_data('__tooltip_callback', None)
        if _tooltip.tmpwidget == widget:
            _tooltip.tmpwidget = None
        if _tooltip.widget == widget:
            _tooltip.widget = None
        if _tooltip.prewidget == widget:
            _tooltip.prewidget = None


gobject.type_register(TooltipWindow)

_tooltip = TooltipWindow()

#used to fetch the widget's tooltip text
_tooltip.widget = None
#used to deduce the times of create widgets
_tooltip.tmpwidget = None
_tooltip.prewidget = None
_tooltip.value = True






if __name__ == "__main__":
    def show_d(w):
        print "destroy......", w
        return False

    def custom_tooltip_cb():
        box = gtk.VBox()
        #box.set_size_request(800, 400)
        b = gtk.Button("abcdsdf")
        l = gtk.Label("huhuhuhuhuhulabellooooooooooooooooooooooooooooooooooooooooooooA")
        b.connect('destroy', show_d)
        l.connect('destroy', show_d)
        box.add(b)
        box.add(l)
        return box

    w = gtk.Window()
    w.set_size_request(500, 500)
    box = gtk.VBox()

    l = gtk.Label("label1")
    #custom tooltip
    ################################################################
    TooltipWindow.attach_widget(l, custom_tooltip_cb)
    #TooltipWindow.set_callback(b, custom_tooltip_cb)
    ################################################################
    #TooltipWindow.attach_widget(l)


    b = gtk.Button("button1")
    ################################################################
    #TooltipWindow.set_text(b, "huhu button")
    TooltipWindow.attach_widget(b, "tooltiiiiiiiiiiiiiiiiiipppp")
    ###############################################################


    box.pack_start(l)
    box.pack_start(b)

    w.add(box)
    w.connect('destroy', gtk.main_quit)
    w.show_all()
    gtk.main()

