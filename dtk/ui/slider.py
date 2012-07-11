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

from draw import draw_pixbuf
from timeline import Timeline, CURVE_SINE
from utils import move_window, is_in_rect
from window import Window
import gobject
import gtk

class Slider(gtk.Viewport):
    active_widget = None
    _size_cache = None

    def __init__(self, slide_callback=None):
        gtk.Viewport.__init__(self)
        self.slide_callback = slide_callback
        self.timeouts = dict()

        self.set_shadow_type(gtk.SHADOW_NONE)

        self.layout = gtk.HBox(True)
        self.content = gtk.EventBox()
        self.content.add(self.layout)

        self.container = gtk.Fixed()
        self.container.add(self.content)
        self.add(self.container)

        self.connect('size-allocate', self.size_allocate_cb)

    def slide_to(self, widget):

        self.active_widget = widget

        def update(source, status):
            pos = end_position - start_position
            adjustment.set_value(start_position + int(round(status * pos)))

        adjustment = self.get_hadjustment()
        start_position = adjustment.get_value()
        end_position = widget.get_allocation().x

        if start_position != end_position:
            timeline = Timeline(500, CURVE_SINE)
            timeline.connect('update', update)
            timeline.run()
            
        if self.slide_callback:    
            self.slide_callback(self.layout.get_children().index(widget), widget)
            
    def size_allocate_cb(self, source, allocation):

        if self._size_cache != allocation and self.active_widget:
            adjustment = self.get_hadjustment()
            adjustment.set_value(self.active_widget.get_allocation().x)

        self._size_cache = allocation

        width = (len(self.layout.get_children()) or 1) * allocation.width
        self.content.set_size_request(width, allocation.height)

    def append_widget(self, widget):
        self.layout.pack_start(widget, True, True, 0)

    def add_slide_timeout(self, widget, milliseconds):
        """
        Adds a timeout for ``widget`` to slide in after ``seconds``.
        """
        if widget in self.timeouts:
            raise RuntimeError("A timeout for '%s' was already added" % widget)

        callback = lambda: self.slide_to(widget)
        self.timeouts[widget] = (gobject.timeout_add(milliseconds, callback),
                                 milliseconds)

    def remove_slide_timeout(self, widget):
        """
        Removes a timeout previously added by ``add_slide_timeout``.
        """
        try:
            gobject.source_remove(self.timeouts.pop(widget)[0])
        except KeyError:
            pass


    def reset_slide_timeout(self, widget, milliseconds=None):
        """
        Shorthand to ``remove_slide_timeout`` plus ``add_slide_timeout``.
        """
        if milliseconds is None:
            try:
                milliseconds = self.timeouts[widget][1]
            except KeyError:
                pass
            else:
                self.remove_slide_timeout(widget)
        self.add_slide_timeout(widget, milliseconds)

    def try_remove_slide_timeout(self, widget):
        try:
            self.remove_slide_timeout(widget)
        except RuntimeError:
            pass

    def try_reset_slide_timeout(self, widget, *args, **kwargs):
        """
        Like ``reset_slide_timeout``, but fails silently
        if the timeout for``widget`` does not exist.
        """
        if widget in self.timeouts:
            self.reset_slide_timeout(widget, *args, **kwargs)

gobject.type_register(Slider)

class Wizard(Window):
    '''Wizard.'''
	
    def __init__(self, 
                 slider_files,
                 navigate_files,
                 finish_callback=None,
                 window_width=548, 
                 window_height=373,
                 navigatebar_height=58,
                 slide_delay=4000,
                 close_area_width=32,
                 close_area_height=32,
                 ):
        '''Init wizard.'''
        # Init.
        Window.__init__(self)
        self.slider_files = slider_files
        self.finish_callback = finish_callback
        self.window_width = window_width
        self.window_height = window_height
        self.navigatebar_height = navigatebar_height
        self.slider_number = len(self.slider_files)
        self.slide_index = 0
        self.slide_delay = slide_delay # milliseconds
        self.close_area_width = close_area_width
        self.close_area_height = close_area_height
        
        # Init navigate pixbufs.
        self.select_pixbufs = []
        self.unselect_pixbufs = []
        for (select_file, unselect_file) in navigate_files:
            self.select_pixbufs.append(gtk.gdk.pixbuf_new_from_file(select_file))
            self.unselect_pixbufs.append(gtk.gdk.pixbuf_new_from_file(unselect_file))
        self.navigate_item_width = self.select_pixbufs[0].get_width()    
        
        # Set window attributes.
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(self.window_width, self.window_height)
        
        # Add widgets.
        self.main_box = gtk.VBox()
        self.slider = Slider(self.set_slide_page)
        self.navigatebar = gtk.EventBox()
        self.navigatebar.set_visible_window(False)
        self.navigatebar.set_size_request(-1, self.navigatebar_height)
        self.main_box.pack_start(self.slider, True, True)
        self.main_box.pack_start(self.navigatebar, True, True)
        self.main_align = gtk.Alignment()
        self.main_align.set(0.5, 0.5, 1, 1)
        self.main_align.set_padding(0, 0, 0, 0)
        self.main_align.add(self.main_box)
        self.window_frame.add(self.main_align)

        # Start animation.
        self.slider_widgets = []
        for (index, slider_file) in enumerate(self.slider_files):
            widget = gtk.image_new_from_file(slider_file)
            self.slider_widgets.append(widget)
            self.slider.append_widget(widget)
            self.slider.add_slide_timeout(widget, index * self.slide_delay)
            
        self.slider.connect("button-press-event", self.button_press_slider)    
        self.navigatebar.connect("button-press-event", self.button_press_navigatebar)        
        self.navigatebar.connect("expose-event", self.expose_navigatebar)
        
    def button_press_slider(self, widget, event):
        '''Button press slider.'''
        rect = widget.allocation
        (window_x, window_y) = widget.get_toplevel().window.get_origin()
        if (self.slide_index == self.slider_number - 1
            and is_in_rect((event.x_root, event.y_root), 
                           (window_x + rect.width - self.close_area_width,
                            window_y,
                            self.close_area_width,
                            self.close_area_height))):
            if self.finish_callback:
                self.finish_callback()
                
            self.destroy()    
        else:
            widget.connect("button-press-event", lambda w, e: move_window(w, e, self))            
    
    def button_press_navigatebar(self, widget, event):
        '''Button press navigatebar.'''
        # Init. 
        rect = widget.allocation
        
        # Get navigate index.
        navigate_index = int(event.x / (rect.width / self.slider_number))
        
        # Remove slider timeout.
        for widget in self.slider_widgets:
            self.slider.try_remove_slide_timeout(widget)
        
        # Slide select widget.
        self.slider.slide_to(self.slider_widgets[navigate_index])
        
        # Reset timeout.
        if navigate_index < self.slider_number - 1:
            for (index, widget) in enumerate(self.slider_widgets[navigate_index::]):
                self.slider.add_slide_timeout(widget, index * self.slide_delay)
                
    def expose_navigatebar(self, widget, event):
        '''Expose navigatebar.'''
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Render unselect item.
        for (index, unselect_pixbuf) in enumerate(self.unselect_pixbufs):
            if index != self.slide_index:
                draw_pixbuf(cr, unselect_pixbuf,
                            rect.x + index * self.navigate_item_width,
                            rect.y)
                
        # Render select item.
        draw_pixbuf(cr, self.select_pixbufs[self.slide_index],
                    rect.x + self.slide_index * self.navigate_item_width,
                    rect.y)        
        
        return True
    
    def set_slide_page(self, index, widget):
        '''Set slide page.'''
        self.slide_index = index
        self.navigatebar.queue_draw()    
        
gobject.type_register(Wizard)

if __name__ == "__main__":
    window = gtk.Window()    
    window.set_size_request(752, 452)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    image1 = gtk.image_new_from_file("/test/Download/ubiquity-slideshow-deepin-11.12.2/slideshows/deepin-zh-hans/slides/screenshots/1.png")
    image2 = gtk.image_new_from_file("/test/Download/ubiquity-slideshow-deepin-11.12.2/slideshows/deepin-zh-hans/slides/screenshots/2.png")
    image3 = gtk.image_new_from_file("/test/Download/ubiquity-slideshow-deepin-11.12.2/slideshows/deepin-zh-hans/slides/screenshots/3.png")
    image4 = gtk.image_new_from_file("/test/Download/ubiquity-slideshow-deepin-11.12.2/slideshows/deepin-zh-hans/slides/screenshots/4.png")
    
    slider = Slider()
    slider.append_widget(image1)
    slider.append_widget(image2)
    slider.append_widget(image3)
    slider.append_widget(image4)
    window.add(slider)
    
    slider.add_slide_timeout(image1, 1)
    slider.add_slide_timeout(image2, 2)
    slider.add_slide_timeout(image3, 3)
    slider.add_slide_timeout(image4, 4)
    
    window.show_all()
    gtk.main()
