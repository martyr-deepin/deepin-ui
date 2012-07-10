#!/usr/bin/env python

from animation import Animation, LinerInterpolator
from gtk import gdk
from label import Label
from theme import ui_theme
from utils import propagate_expose, color_hex_to_cairo, cairo_disable_antialias
import cairo
import gobject
import gtk

#!!!!!!!!!!!!!!!!maybe you want to goto to the line of *388* !!!!!!!!!!!!!!!!!!#

class ChildLocation:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.child = None
        self.container = None

def window_to_alloc(widget, x, y):
    if widget.get_has_window() and widget.parent:
        (wx, wy) = widget.window.get_position()
        x += wx - widget.allocation.x
        y += wy - widget.allocation.y
    else:
        x -= widget.allocation.x
        y -= widget.allocation.y
    return (x, y)

def child_location_foreach(widget, cl): #cl = child_location
    if not widget.is_drawable():
        return
    if not cl.child :
        (x, y) = cl.container.translate_coordinates(widget, int(cl.x), int(cl.y))
        if x >= 0 and x < widget.allocation.width and \
            y >=0 and y < widget.allocation.height:
                if isinstance(widget, gtk.Container):
                    tmp = ChildLocation()
                    (tmp.x, tmp.y, tmp.container) = (x, y, widget)
                    widget.forall(child_location_foreach, tmp)
                    if tmp.child:
                        cl.child = tmp.child
                    else:
                        cl.child = widget
                else:
                    cl.child = widget

def coords_to_parent(window, x, y):
    if window.get_window_type() == gdk.WINDOW_OFFSCREEN:
        (px, py) = (-1, -1)
        window.emit("to-embedder", window, x, y, px, py)
        return (px, py)
    else:
        p = window.get_position()
        return (x + p[0], y + p[1])

def find_at_coords(gdkwindow, window_x, window_y):
    cl = ChildLocation()

    widget = gdkwindow.get_user_data()
    if widget == None:
        return (None, cl.x, cl.y)

    cl.x = window_x
    cl.y = window_y

    while gdkwindow and gdkwindow != widget.window:
        (cl.x, cl.y) = coords_to_parent(gdkwindow, cl.x, cl.y)
        gdkwindow = gdkwindow.get_effective_parent()

    if not gdkwindow:
        return (None, cl.x, cl.y)

    (cl.x, cl.y) = window_to_alloc(widget, cl.x, cl.y)

    #find child
    if isinstance(widget, gtk.Container):
        cl.container = widget
        cl.child = None
        tmp_widget = widget

        widget.forall(child_location_foreach, cl)

        if cl.child and WidgetInfo.get_info(cl.child):
            widget = cl.child
        elif cl.container and WidgetInfo.get_info(cl.container):
            widget = cl.container

        (cl.x, cl.y) = tmp_widget.translate_coordinates(widget, int(cl.x), int(cl.y))


    if WidgetInfo.get_info(widget):
        return (widget, cl.x, cl.y)


    p = widget.get_parent()
    while p:
        if WidgetInfo.get_info(p):
            return (p, cl.x, cl.y)
        else:
            p = p.get_parent()

    return (None, cl.x, cl.y)


#TODO: reduce the time!!!!
def update_tooltip(display):
    if TooltipInfo.enable_count == 0:
        return
    try :
        (window, x, y) = display.get_window_at_pointer()
    except:
        return True

    (widget, tx, ty) = find_at_coords(window, x, y)
    if widget == None:
        pass
        # print "nop"
    if not widget \
            or tx < 0 or tx >= widget.allocation.width \
            or ty < 0 or ty >= widget.allocation.height:
        hide_tooltip()
        return True

    if TooltipInfo.widget != widget:
        TooltipInfo.prewidget = widget
        TooltipInfo.winfo = WidgetInfo.get_info(widget)
        TooltipInfo.show_delay = TooltipInfo.winfo.show_delay

    TooltipInfo.tmpwidget = widget
    (rx, ry) = window.get_origin()

    if TooltipInfo.pos_info != (int(rx+x), int(ry+y)) and TooltipInfo.show_id != 0:
        hide_tooltip()

    if TooltipInfo.show_id == 0:
        if TooltipInfo.in_quickshow:
            show_delay = 300
        else:
            show_delay = TooltipInfo.winfo.show_delay
        TooltipInfo.pos_info = (int(rx+x), int(ry+y))
        TooltipInfo.show_id = gobject.timeout_add(show_delay, lambda : show_tooltip(*TooltipInfo.pos_info))


class TooltipInfo:
    widget = None
    tmpwidget = None
    prewidget = None
    pos_info = None
    window = None
    alignment = None
    winfo = None
    offset_x = 5
    offset_y = 5
    on_showing = False
    need_update = True
    #displays = []
    stamp = 0
    enable_count = 0
    show_id = 0

    in_quickshow = False
    quickshow_id = 0
    quickshow_delay = 2500

def generate_tooltip_content():
    """ generate child widget and update the TooltipInfo"""
    if TooltipInfo.widget == TooltipInfo.prewidget and TooltipInfo.alignment.child and not TooltipInfo.need_update:
        return

    TooltipInfo.widget = TooltipInfo.tmpwidget

    TooltipInfo.winfo = WidgetInfo.get_info(TooltipInfo.widget)
    winfo = TooltipInfo.winfo

    pre_child = TooltipInfo.alignment.child

    if pre_child and winfo == WidgetInfo.get_info(pre_child) and not TooltipInfo.need_update:
        return

    if winfo.custom:
        child = winfo.custom(*winfo.custom_args, **winfo.custom_kargs)
    elif winfo.text:
        child = Label(winfo.text, *winfo.text_args, **winfo.text_kargs)
    else:
        raise Warning, "tooltip enable's widget must has text or custom property"

    if pre_child:
        TooltipInfo.alignment.remove(pre_child)
        pre_child.destroy()

    TooltipInfo.alignment.set_padding(winfo.padding_t, winfo.padding_l, winfo.padding_b, winfo.padding_r)
    TooltipInfo.alignment.add(child)
    TooltipInfo.alignment.show_all()

    allocation = gtk.gdk.Rectangle(0, 0, *TooltipInfo.alignment.child.size_request())
    allocation.width += winfo.padding_l + winfo.padding_r
    allocation.height += winfo.padding_t + winfo.padding_b
    TooltipInfo.window.size_allocate(allocation)
    TooltipInfo.window.modify_bg(gtk.STATE_NORMAL, winfo.background)
    if winfo.always_update:
        TooltipInfo.need_update = True
    else:
        TooltipInfo.need_update = False


def enable_quickshow():
    def disable_q():
        TooltipInfo.in_quickshow = False
        if TooltipInfo.quickshow_id != 0:
            gobject.source_remove(TooltipInfo.quickshow_id)
    TooltipInfo.in_quickshow = True
    if TooltipInfo.quickshow_id == 0:
        TooltipInfo.quickshow_id = gobject.timeout_add(TooltipInfo.quickshow_delay, disable_q)
    else:
        gobject.source_remove(TooltipInfo.quickshow_id)
        TooltipInfo.quickshow_id = gobject.timeout_add(TooltipInfo.quickshow_delay, disable_q)


def hide_tooltip():
    TooltipInfo.window.hide()
    TooltipInfo.on_showing = False
    if TooltipInfo.show_id != 0:
        gobject.source_remove(TooltipInfo.show_id)
        TooltipInfo.show_id = 0
    if TooltipInfo.window.get_realized():
        TooltipInfo.window.animation.stop()
    return False

def show_tooltip(x, y):
    if TooltipInfo.enable_count == 0 or not TooltipInfo.winfo.enable:
        return
    generate_tooltip_content()
    enable_quickshow()

    #What will happen if the content widget is very big?
    #----------------------------------------------
    (p_w, p_h) = (10, 10)  #TODO: pointer size ?
    (w, h) = TooltipInfo.window.get_root_window().get_size()
    (t_w, t_h) = TooltipInfo.window.size_request()

    if x + p_w + t_w > w:
        POS_H =  0 #left
    else:
        POS_H =  1 #right

    if y + p_h + t_h > h:
        POS_V = 2 #top
    else:
        POS_V = 4 #bttom

    p = POS_H + POS_V
    ######################################
    #            LEFT(0)        RIGHT(1) #
    #------------------------------------#
    #TOP(2)         2             3      #
    #------------------------------------#
    #BOTTOM(4)      4             5      #
    ######################################
    if p == 2:
        TooltipInfo.window.move(x - t_w, y - t_h)
    elif p == 3:
        TooltipInfo.window.move(x, y - t_h)
    elif p == 4:
        TooltipInfo.window.move(x - t_w, y)
    elif p == 5:
        TooltipInfo.window.move(x + p_w, y + p_h)
    else:
        assert False, "This shouldn't appaer!!!!!!"
    #------------------------------------------

    TooltipInfo.window.show()
    TooltipInfo.on_showing = True




def __init_window():
    def on_realize(win):
        win.swindow = gtk.gdk.Window(win.get_parent_window(),
                width=0, height=0,
                window_type=gtk.gdk.WINDOW_TEMP,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=(win.get_events() | gdk.EXPOSURE_MASK),
                visual=win.get_visual(),
                colormap=win.get_colormap(),
                )
        win.swindow.set_user_data(win)

        #TODO: set duration dynamicly
        win.animation = Animation([win.window, win.swindow], gdk.Window.set_opacity, 1000, [0, 1],
                lambda *args: 1 - LinerInterpolator(*args))

    def on_map(win):
        winfo = TooltipInfo.winfo
        win.animation.init(1)
        win.animation.start_after(winfo.hide_delay)
        geo = win.window.get_geometry()
        win.swindow.move_resize(geo[0]+TooltipInfo.offset_x, geo[1]+TooltipInfo.offset_y,
                win.allocation.width, win.allocation.height)

        win.swindow.show()

    def on_expose_event(win, e):
        cr = win.swindow.cairo_create()
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        winfo = TooltipInfo.winfo
        if winfo.has_shadow:

            (x, y, width, height) = (0, 0, win.allocation.width, win.allocation.height)
            (o_x, o_y) = (5, 5)


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

        gtk.Alignment.do_expose_event(TooltipInfo.alignment, e)
        propagate_expose(win, e)
        return True

    def on_unmap(win):
        win.swindow.hide()

    def on_expose_alignment(widget, event):
        '''Expose tooltip label.'''
        rect = widget.allocation
        cr = widget.window.cairo_create()

        with cairo_disable_antialias(cr):
            cr.set_line_width(1)
            cr.set_source_rgba(*color_hex_to_cairo(ui_theme.get_color("tooltip_frame").get_color()))
            cr.rectangle(rect.x + 1, rect.y + 1, rect.width - 1, rect.height - 1)
            cr.stroke()
        return True

    TooltipInfo.window = gtk.Window(gtk.WINDOW_POPUP)
    TooltipInfo.window.set_colormap(gtk.gdk.Screen().get_rgba_colormap())
    TooltipInfo.alignment = gtk.Alignment()
    TooltipInfo.window.add(TooltipInfo.alignment)
    TooltipInfo.window.connect('realize', on_realize)
    TooltipInfo.window.connect('map', on_map)
    TooltipInfo.window.connect('unmap', on_unmap)
    TooltipInfo.window.connect('expose-event', on_expose_event)
    TooltipInfo.alignment.connect('expose-event', on_expose_alignment)
__init_window()


#TODO:detect display?
#FIXME:
display = None
def init_widget(widget):
    TooltipInfo.enable_count += 1
    w_info = WidgetInfo()
    WidgetInfo.set_info(widget, w_info)
    if widget.get_has_window():
        widget.add_events(gdk.POINTER_MOTION_MASK|gdk.POINTER_MOTION_HINT_MASK)
    else:
        widget.connect('realize',
                lambda w: w.window.set_events(w.window.get_events() | gdk.POINTER_MOTION_HINT_MASK | gdk.POINTER_MOTION_MASK))
    if not display:
        init_tooltip(widget)
    return w_info
def init_tooltip(win):
    global display
    if not display:
        display = win.get_display()
        #gobject.timeout_add(100, lambda : update_tooltip(display))
        #win.connect('focus-out-event', lambda w, e: hide_tooltip(True))
        win.connect('leave-notify-event', lambda w, e: hide_tooltip())



#
#the Interface of dtk Tooltip, the core is the WidgetInfo's attribute
#

class WidgetInfo(object):
    __DATA_NAME = "_deepin_tooltip_info"

    @staticmethod
    def get_info(widget):
        return widget.get_data(WidgetInfo.__DATA_NAME)
    @staticmethod
    def set_info(widget, info):
        return widget.set_data(WidgetInfo.__DATA_NAME, info)

    def __init__(self):
        object.__setattr__(self, "show_delay", 1000)
        object.__setattr__(self, "hide_delay", 3000)
        object.__setattr__(self, "hide_duration", 1000)
        object.__setattr__(self, "text", None)
        object.__setattr__(self, "text_args", None)
        object.__setattr__(self, "text_kargs", None)
        object.__setattr__(self, "custom", None)
        object.__setattr__(self, "custom_args", None)
        object.__setattr__(self, "custom_kargs", None)
        object.__setattr__(self, "background", gtk.gdk.Color(ui_theme.get_color("tooltip_background").get_color()))
        object.__setattr__(self, "padding_t", 5)
        object.__setattr__(self, "padding_b", 5)
        object.__setattr__(self, "padding_l", 5)
        object.__setattr__(self, "padding_r", 5)
        object.__setattr__(self, "has_shadow", True)
        object.__setattr__(self, "enable", False) #don't modify the "enable" init value
        object.__setattr__(self, "always_update", False)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            object.__setattr__(self, key, value)
        else:
            raise Warning, "Tooltip didn't support the \"%s\" property" % key
        TooltipInfo.need_update = True
        if key == "text" or key == "custom":
            self.enable = True

all_method = {}
def chainmethod(func):
    all_method[func.__name__] = func
    def wrap(*args, **kargs):
        return func(*args, **kargs)
    wrap.__dict__ = all_method
    return wrap

#
#you can write yourself wrap function use "set_value" or direct modify the WidgetInfo's attribute
#
@chainmethod
def set_value(widgets, kv):
    if not isinstance(widgets, list):
        widgets = [widgets]
    for w in widgets:
        w_info = WidgetInfo.get_info(w)
        if not w_info:
            w_info = init_widget(w)
        for k in kv:
            setattr(w_info, k, kv[k])
    return set_value

#------------------the default wrap function ---------------------------------------
@chainmethod
def text(widget, content, *args, **kargs):
    set_value(widget, {
        "text": content,
        "text_args":args,
        "text_kargs":kargs
        })
    return text

@chainmethod
def custom(widget, cb, *args, **kargs):
    set_value(widget, {
            "custom" : cb,
            "custom_args" : args,
            "custom_kargs" : kargs
            })
    return custom

@chainmethod
def show_delay(widget, delay):
    delay = max(250, delay)
    set_value(widget, {"show_delay": delay})
    return show_delay

@chainmethod
def hide_delay(widget, delay):
    set_value(widget, {"hide_delay": delay})
    return hide_delay

@chainmethod
def hide_duration(widget, delay):
    set_value(widget, {"hide_duration": delay})
    return hide_duration

@chainmethod
def background(widget, color):
    set_value(widget, {"background": color})
    return background

@chainmethod
def padding(widget, t, l, b, r):
    kv = {}
    if t >= 0:
        kv["padding_t"] = int(t)
    if b >= 0:
        kv["padding_b"] = int(b)
    if l >= 0:
        kv["padding_l"] = int(l)
    if r >= 0:
        kv["padding_r"] = int(r)

    set_value(widget, kv)
    return padding

@chainmethod
def has_shadow(widget, need):
    set_value(widget, {"has_shadow": need})
    return has_shadow

@chainmethod
def disable(widget, value):
    winfo = WidgetInfo.get_info(widget)
    if value:
        if winfo.enable :
            winfo.enable = False
            TooltipInfo.enable_count -= 1
    else:
        if not winfo.enable :
            winfo.enable = True
            TooltipInfo.enable_count += 1
    return disable

@chainmethod
def always_update(widget, need):
    set_value(widget, {"always_update" : need})
    return always_update

#------------------------this is global effect function---------------------
def disable_all(value):
    count = TooltipInfo.enable_count
    if value:
        if count > 0:
            TooltipInfo.enable_count = -count
    else:
        if count < 0:
            TooltipInfo.enable_count = -count


def tooltip_handler(event):
    gtk.main_do_event(event)
    if event.type == gdk.MOTION_NOTIFY:
        # print "leave", time.time()
        update_tooltip(display)
    elif event.type == gdk.LEAVE_NOTIFY:
        # print "leave", time.time()
        hide_tooltip()
gdk.event_handler_set(tooltip_handler)
