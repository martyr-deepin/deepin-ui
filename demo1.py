#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
from dtk.ui.window import Window
from dtk.ui.paned import HPaned

class PaneWindow:
    '''Horizontal Pane test '''
    def __init__(self):
        window = Window()
        window.set_title('Panes')
        window.set_border_width(10)
        window.set_size_request(225, 150)
        window.connect('destroy', lambda w: gtk.main_quit())
        hpaned = HPaned()

        button1 = gtk.Button('Resize')
        button2 = gtk.Button('Me!')

        hpaned.add1(button1)
        hpaned.add2(button2)
        # hpaned.pack1(button1, True, True)
        # hpaned.pack2(button2, True, True)

        window.window_frame.pack_start(hpaned)
        window.show_all()

        gtk.main()

if __name__ == '__main__':
    PaneWindow()

