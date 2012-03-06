import random
import gobject
import gtk

class MyIcon(gtk.EventBox):
    __gtype_name__ = "MyIcon"

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_app_paintable(True)

        self.drag_source_set(gtk.gdk.BUTTON1_MASK, [], 0)
        self.connect('drag-end', self._drag_end)
        self.connect('drag-drop', self._drag_drop)
        self.connect('drag-begin', self._drag_begin)
        self.connect('drag-data-delete', self._drag_data_delete)
        self.connect('drag-data-get', self._drag_data_get)
        self.connect('drag-data-received', self._drag_data_received)
        self.connect('drag-failed', self._drag_failed)
        self.connect('drag-leave', self._drag_leave)
        self.connect('drag-motion', self._drag_motion)

    def _drag_motion(self, widget, ctx, x,y, time):
        print "ICON DRAG MOTION", widget, ctx, x,y,  time

    def _drag_leave(self, widget, ctx, time):
        print "ICON DRAG LEAVE", widget, ctx, time

    def _drag_failed(self, widget, ctx, result):
        print "ICON DRAG FAILED", widget, ctx, result

    def _drag_drop(self, widget, ctx, x, y, time):
        print "ICON DRAG DROP", widget, ctx, x, y, time

    def _drag_data_received(self, widget, ctx, x, y, data, info, time):
        print "ICON DRAG DATA DELETE", widget, ctx, x, y, data, info, time

    def _drag_data_get(self, widget, ctx, data, info, time):
        print "ICON DRAG DATA DELETE", widget, ctx, info, time

    def _drag_data_delete(self, widget, ctx):
        print "ICON DRAG DATA DELETE", widget, ctx

    def _drag_begin(self, widget, ctx):
        print "ICON DRAG BEGIN", widget, ctx

    def _drag_end(self, drag, ctx):
        print "ICON DRAG END", drag, ctx

    def do_expose_event(self, event):
        print "ICON do expose", self
        allocation = self.get_allocation()

        cr = self.window.cairo_create()
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0);
        cr.paint()

        cr.set_source_rgba(1.0, 0.0, 0.0, 1.0);
        cr.rectangle(10, 0, 2, allocation.height)
        cr.fill()

    def do_size_request(self, req):
        print self.window
        req.width = 20
        req.height = 20


class MyContainer(gtk.Container):
    __gtype_name__ = "MyContainer"
    def __init__(self):
        gtk.Container.__init__(self)
        self._children = []
        self.drag_dest_set(0, [], 0)
        self.connect('drag-end', self._drag_end)
        self.connect('drag-drop', self._drag_drop)
        self.connect('drag-begin', self._drag_begin)
        self.connect('drag-data-delete', self._drag_data_delete)
        self.connect('drag-data-get', self._drag_data_get)
        self.connect('drag-data-received', self._drag_data_received)
        self.connect('drag-failed', self._drag_failed)
        self.connect('drag-leave', self._drag_leave)
        self.connect('drag-motion', self._drag_motion)

    def _drag_motion(self, widget, ctx, x,y, time):
        print "CONT DRAG MOTION", widget, ctx, x,y,  time

    def _drag_leave(self, widget, ctx, time):
        print "CONT DRAG LEAVE", widget, ctx, time

    def _drag_failed(self, widget, ctx, result):
        print "CONT DRAG fAILED", widget, ctx, result

    def _drag_drop(self, widget, ctx, x, y, time):
        print "CONT DRAG DROP", widget, ctx, x, y, time

    def _drag_data_received(self, widget, ctx, x, y, data, info, time):
        print "CONT DRAG DATA DELETE", widget, ctx, x, y, data, info, time

    def _drag_data_get(self, widget, ctx, data, info, time):
        print "CONT DRAG DATA DELETE", widget, ctx, info, time

    def _drag_data_delete(self, widget, ctx):
        print "CONT DRAG DATA DELETE", widget, ctx

    def _drag_begin(self, widget, ctx):
        print "CONT DRAG BEGIN", widget, ctx

    def _drag_end(self, drag, ctx):
        print "CONT DRAG END", drag, ctx

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)

        self.window = gtk.gdk.Window(
                self.get_parent_window(),
                width=self.allocation.width,
                height=self.allocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=self.get_events() | gtk.gdk.EXPOSURE_MASK
                        | gtk.gdk.BUTTON1_MOTION_MASK
                        | gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.POINTER_MOTION_HINT_MASK)
        self.window.set_user_data(self)

        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))

    def do_size_request(self, requisition):
        requisition.height = 300
        requisition.width = 300

    def do_forall(self, include_internals, callback, user_data):
        for widget in self._children:
            callback(widget, user_data)

    def do_remove(self, child):
        self._children.remove(child)

    def do_add(self, child):
        self._children.append(child)
        if child.flags() & gtk.REALIZED:
            child.set_parent_window(self.window)
        child.set_parent(self)

    def do_size_allocate(self, allocation):
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

        width = allocation.width
        height = allocation.height

        i = 0
        for child in self._children:
            i = i + 1
            nrect = gtk.gdk.Rectangle(i * 40, i * 40, 40, 40)
            child.size_allocate(nrect)

    def move_child(self, child, x, y):
        nrect = gtk.gdk.Rectangle(x, y, 40, 40)
        child.size_allocate(nrect)

class MyWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        cont = MyContainer()
        self.add(cont)
        cont.show()
        self.cont = cont
        self.drag_dest_set(0, [], 0)

        icon = MyIcon()
        cont.add(icon)
        icon.show()

        self.connect('drag-end', self._drag_end)
        self.connect('drag-drop', self._drag_drop)
        self.connect('drag-begin', self._drag_begin)
        self.connect('drag-data-delete', self._drag_data_delete)
        self.connect('drag-data-get', self._drag_data_get)
        self.connect('drag-data-received', self._drag_data_received)
        self.connect('drag-failed', self._drag_failed)
        self.connect('drag-leave', self._drag_leave)
        self.connect('drag-motion', self._drag_motion)

    def _drag_motion(self, widget, ctx, x,y, time):
        print "WIN DRAG MOTION", widget, ctx, x,y,  time
        ctx.drag_status(gtk.gdk.ACTION_MOVE, time)
        return True

    def _drag_leave(self, widget, ctx, time):
        print "WIN DRAG LEAVE", widget, ctx, time

    def _drag_failed(self, widget, ctx, result):
        print "WIN DRAG fAILED", widget, ctx, result

    def _drag_drop(self, widget, ctx, x, y, time):
        print "WIN DRAG DROP", widget, ctx, x, y, time

    def _drag_data_received(self, widget, ctx, x, y, data, info, time):
        print "WIN DRAG DATA DELETE", widget, ctx, x, y, data, info, time

    def _drag_data_get(self, widget, ctx, data, info, time):
        print "WIN DRAG DATA DELETE", widget, ctx, info, time

    def _drag_data_delete(self, widget, ctx):
        print "WIN DRAG DATA DELETE", widget, ctx

    def _drag_begin(self, widget, ctx):
        print "WIN DRAG BEGIN", widget, ctx

    def _drag_end(self, drag, ctx):
        print "WIN DRAG END", drag, ctx


def main():
    win = MyWindow()
    win.show()

    gtk.main()

if __name__ == "__main__":
    main()
