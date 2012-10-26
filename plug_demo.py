#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
python plug_demo.py
Plug ID= 46137376
把ID作为参数传递给socket_demo.py
'''

import pygtk
import gtk,sys

from dtk.ui.init_skin import init_skin
from dtk.ui.utils import get_parent_dir
import os
app_theme = init_skin(
    "deepin-ui-demo", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__), "skin"),
    os.path.join(get_parent_dir(__file__), "app_theme"),
    )

from dtk.ui.combo import ComboBox

Wid = 0L
if len(sys.argv) == 2:
    Wid = long(sys.argv[1])

plug = gtk.Plug(Wid)
print "Plug ID=", plug.get_id()

def embed_event(widget):
    print "I (", widget, ") have just been embedded!"

plug.connect("embedded", embed_event)

combo_box = ComboBox(
    [("测试测试测试1", 1),
     ("测试测试测试2", 2),
     ("测试测试测试3", 3),
     None,
     ("测试测试测试", 4),
     None,
     ("测试测试测试4", 5),
     ("测试测试测试5", 6),
     ("测试测试测试6", 7),
    ],
    100
    )

plug.connect("destroy", lambda w: gtk.main_quit())

plug.add(combo_box)
plug.show_all()

gtk.main()
