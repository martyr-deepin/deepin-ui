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

from PIL import Image
from constant import SHADOW_SIZE
from draw import draw_pixbuf, draw_vlinear, draw_hlinear
from utils import propagate_expose, color_hex_to_cairo, find_similar_color
import gtk
import scipy
import scipy.cluster
import scipy.misc
import urllib

__all__ = ["get_dominant_color"]

def get_dominant_color(image_path):
    '''
    Parse image and return dominant color in image.

    @param image_path: Image path to parse.
    @return: Return dominant color, format as hexadecimal number.
    '''
    # print 'reading image'
    im = Image.open(image_path)
    im = im.resize((150, 150))      # optional, to reduce time
    ar = scipy.misc.fromimage(im)
    shape = ar.shape
    ar = ar.reshape(scipy.product(shape[:2]), shape[2])

    # print 'finding clusters'
    NUM_CLUSTERS = 5
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    # print 'cluster centres:\n', codes

    vecs, dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences

    index_max = scipy.argmax(counts)                    # find most frequent
    peak = codes[index_max]
    colour = ''.join(chr(c) for c in peak).encode('hex')

    return "#%s" % (colour[0:6])

class ColorTestWidget(gtk.DrawingArea):
    '''
    Widget to test function get_dominant_color.
    '''

    def __init__(self):
        '''
        Initialize ColorTestWidget class.
        '''
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("expose-event", self.color_test_widget_expose)
        self.pixbuf = None
        self.background_color = "#000000"

        self.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_DROP,
            [("text/uri-list", 0, 1)],
            gtk.gdk.ACTION_COPY)

        self.connect("drag-data-received", self.color_test_widget_drag)

    def color_test_widget_drag(self, widget, drag_context, x, y, selection_data, info, timestamp):
        self.set_pixbuf(urllib.unquote(selection_data.get_uris()[0].split("file://")[1]))

    def set_pixbuf(self, filename):
        self.pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 800, 800)
        print filename
        self.background_color = get_dominant_color(filename)
        self.queue_draw()

    def color_test_widget_expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # Draw pixbuf.
        draw_pixbuf(cr, self.pixbuf, 0, 0)

        # Draw mask.
        draw_vlinear(
            cr, rect.x, rect.y + self.pixbuf.get_height() - SHADOW_SIZE, rect.width, SHADOW_SIZE,
            [(0, (self.background_color, 0)),
             (1, (self.background_color, 1))])

        draw_hlinear(
            cr, rect.x + self.pixbuf.get_width() - SHADOW_SIZE, rect.y, SHADOW_SIZE, rect.height,
            [(0, (self.background_color, 0)),
             (1, (self.background_color, 1))])

        # Draw background.
        (similar_color_name, similar_color_value) = find_similar_color(self.background_color)
        print (similar_color_name, self.background_color, similar_color_value)
        cr.set_source_rgb(*color_hex_to_cairo(similar_color_value))
        cr.rectangle(rect.x + self.pixbuf.get_width(), rect.y,
                     rect.width - self.pixbuf.get_width(), rect.height)
        cr.fill()
        cr.set_source_rgb(*color_hex_to_cairo(self.background_color))
        cr.rectangle(rect.x, rect.y + self.pixbuf.get_height(),
                     rect.width, rect.height - self.pixbuf.get_height())
        cr.fill()

        # cr.set_source_rgb(*color_hex_to_cairo(self.background_color))
        # cr.rectangle(rect.x + self.pixbuf.get_width(), rect.y,
        #              rect.width - self.pixbuf.get_width(), rect.height)
        # cr.rectangle(rect.x, rect.y + self.pixbuf.get_height(),
        #              rect.width, rect.height - self.pixbuf.get_height())

        # cr.fill()

        propagate_expose(widget, event)

        return True

if __name__ == '__main__':
    window = gtk.Window()
    window.set_title("从文件管理器拖动图片测试主色")
    window.connect("destroy", lambda w: gtk.main_quit())
    window.maximize()

    test = ColorTestWidget()
    test.set_pixbuf("/data/Picture/壁纸/1713311.jpg")
    window.add(test)

    window.show_all()

    gtk.main()

