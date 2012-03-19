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

from dtk.ui.application import Application
from dtk.ui.constant import *
from dtk.ui.menu import *
from dtk.ui.navigatebar import *
from dtk.ui.statusbar import *
from dtk.ui.categorybar import *
from dtk.ui.scrolled_window import *
from dtk.ui.box import *
from dtk.ui.button import *
from dtk.ui.listview import *
from dtk.ui.tooltip import *
from dtk.ui.popup_window import *
from dtk.ui.frame import *
from dtk.ui.dragbar import *
from dtk.ui.scalebar import *
from dtk.ui.volume_button import *
import time

app_theme = Theme(os.path.join((os.path.dirname(os.path.realpath(__file__))), "app_theme"))

def print_button_press(list_view, list_item, column, offset_x, offset_y):
    '''Print button press.'''
    print "* Button press: %s" % (str((list_item.title, list_item.artist, list_item.length)))

def print_double_click(list_view, list_item, column, offset_x, offset_y):
    '''Print double click.'''
    print "* Double click: %s" % (str((list_item.title, list_item.artist, list_item.length)))

def print_single_click(list_view, list_item, column, offset_x, offset_y):
    '''Print single click.'''
    print "* Single click: %s" % (str((list_item.title, list_item.artist, list_item.length)))

def print_motion_notify(list_view, list_item, column, offset_x, offset_y):
    '''Print motion notify.'''
    print "* Motion notify: %s" % (str((list_item.title, list_item.artist, list_item.length, column, offset_x, offset_y)))
    
def simulate_redraw_request(items, items_length):
    '''Simulate item's redraw request.'''
    item_index = int(time.time() * 100) % items_length
    print items[item_index].length
    items[item_index].emit_redraw_request()
    
    return True
    
if __name__ == "__main__":
    # Init application.
    application = Application("demo")
    
    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    
    # Set application icon.
    application.set_icon(ui_theme.get_pixbuf("icon.ico"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "menu", "max", "min", "close"], 
        ui_theme.get_pixbuf("title.png"), 
        "深度图形库",
        "/home/andy/deepin-ui/demo.py")
    
    # Draw application background.
    button = gtk.Button()
    button.set_size_request(200,300)
    
    # Init menu callback.
    menu = Menu(
        [(ui_theme.get_pixbuf("menu/menuItem1.png"), "测试测试测试1", lambda : PopupWindow(application.window)),
         (ui_theme.get_pixbuf("menu/menuItem2.png"), "测试测试测试2", None),
         (ui_theme.get_pixbuf("menu/menuItem3.png"), "测试测试测试3", None),
         None,
         (None, "测试测试测试", None),
         (None, "测试测试测试", None),
         None,
         (ui_theme.get_pixbuf("menu/menuItem6.png"), "测试测试测试4", None),
         (ui_theme.get_pixbuf("menu/menuItem7.png"), "测试测试测试5", None),
         (ui_theme.get_pixbuf("menu/menuItem8.png"), "测试测试测试6", None),
         ])
    application.set_menu_callback(lambda button: menu.show(get_widget_root_coordinate(button)))
    
    # Add navigatebar.
    navigatebar = Navigatebar(
        [(ui_theme.get_pixbuf("navigatebar/nav_recommend.png"), "导航1", None),
         (ui_theme.get_pixbuf("navigatebar/nav_repo.png"), "导航2", None),
         (ui_theme.get_pixbuf("navigatebar/nav_update.png"), "导航3", None),
         (ui_theme.get_pixbuf("navigatebar/nav_uninstall.png"), "导航4", None),
         (ui_theme.get_pixbuf("navigatebar/nav_download.png"), "导航5", None),
         (ui_theme.get_pixbuf("navigatebar/nav_repo.png"), "导航6", None),
         (ui_theme.get_pixbuf("navigatebar/nav_update.png"), "导航7", None),
         (ui_theme.get_pixbuf("navigatebar/nav_uninstall.png"), "导航8", None),
         ]
        )
    application.main_box.pack_start(navigatebar.nav_event_box, False)
    application.add_move_window_event(navigatebar.nav_event_box)
    application.add_toggle_window_event(navigatebar.nav_event_box)
    
    # Add body box.
    body_box = gtk.HBox()
    horizontal_frame = HorizontalFrame()
    horizontal_frame.add(body_box)
    application.main_box.pack_start(horizontal_frame, True, True)
    
    # Add categorybar.
    # Note if you add list in categorybar make sure height is multiples of list length.
    # Otherwise last one item will heighter than Otherwise items.
    category_box = gtk.HBox()
    body_box.add(category_box)
    categorybar = Categorybar([
            (app_theme.get_pixbuf("categorybar/word.png"), "测试分类", lambda : Tooltip("测试分类", 600, 400)),
            (app_theme.get_pixbuf("categorybar/win.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/web.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/professional.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/other.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/multimedia.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/graphics.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/game.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/driver.png"), "测试分类", None),
            ])
    category_box.pack_start(categorybar.category_event_box, False)
    
    # Add scrolled window.
    scrolled_window = ScrolledWindow()
    category_box.pack_start(scrolled_window, True, True)
    
    items_length = 100
    # items_length = 10
    
    # items = map(lambda index: ListItem(
    #         "豆浆油条 %04d" % (index % 5),
    #         "林俊杰 %04d" % (index % 10),
    #         # "10:%02d" % (index % 60),
    #         "10:%02d" % index,
    #         ), range(0, items_length))

    items = map(lambda index: ListItem(
            "豆浆油条 %04d" % index,
            "林俊杰 %04d" % index,
            "10:%02d" % index,
            ), range(0, items_length))
    
    list_view = ListView(
        [(lambda item: item.title, cmp),
         (lambda item: item.artist, cmp),
         (lambda item: item.length, cmp)])
    list_view.add_titles(["歌名", "歌手", "时间"])
    list_view.add_items(items)
    
    # insert_items_length1 = 5
    # insert_items1 = map(lambda index: ListItem(
    #         "插入选项1 %04d" % (index % 5),
    #         "歌手1 %04d" % (index % 10),
    #         "10:%02d" % index,
    #         ), range(0, insert_items_length1))
    # list_view.add_items(insert_items1, 3)

    # insert_items_length2 = 3
    # insert_items2 = map(lambda index: ListItem(
    #         "插入选项2 %04d" % (index % 5),
    #         "歌手2 %04d" % (index % 10),
    #         "10:%02d" % index,
    #         ), range(0, insert_items_length2))
    # list_view.add_items(insert_items2, 10)
    
    # list_view.connect("button-press-item", print_button_press)
    # list_view.connect("double-click-item", print_double_click)
    # list_view.connect("single-click-item", print_single_click)
    # list_view.connect("motion-notify-item", print_motion_notify)
    
    # gtk.timeout_add(10, lambda : simulate_redraw_request(items, items_length))
        
    scrolled_window.add_child(list_view)
    
    # Add scalebar.
    scalebar = HScalebar()
    scalebar.set_range(0, 100)
    scalebar_frame = HorizontalFrame()
    scalebar_frame.add(scalebar)
    application.main_box.pack_start(scalebar_frame, False, False)
    
    # Add volume button.
    volume_button = VolumeButton(100, 0, 100, 2)
    volume_frame = HorizontalFrame(10, 0, 0, 0, 0)
    volume_frame.add(volume_button)
    application.main_box.pack_start(volume_frame, False, False)
    
    # Add statusbar.
    statusbar = Statusbar(36)
    application.main_box.pack_start(statusbar.status_event_box, False)
    application.add_move_window_event(statusbar.status_event_box)
    application.add_toggle_window_event(statusbar.status_event_box)
    
    # Run.
    application.run()
