#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#	          Zhai Xiang <zhaixiang@linuxdeepin.com>
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

# Import skin and theme, those must before at any other modules.
# from skin import ui_theme, app_theme
import time
start_time = time.time()

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


# Load other modules.
from dtk.ui.application import Application
from dtk.ui.browser import WebView
from dtk.ui.button import CheckButton, RadioButton, ComboButton
from dtk.ui.button import ImageButton, LinkButton, Button
from dtk.ui.categorybar import Categorybar
from dtk.ui.star_view import StarView
from dtk.ui.color_selection import ColorButton
from dtk.ui.combo import ComboBox
from dtk.ui.constant import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, WIDGET_POS_BOTTOM_LEFT
from dtk.ui.droplist import Droplist
from dtk.ui.new_entry import InputEntry, ShortcutKeyEntry, PasswordEntry
from dtk.ui.frame import HorizontalFrame
from dtk.ui.iconview import IconView, IconItem
from dtk.ui.label import Label
from dtk.ui.listview import ListItem, ListView
from dtk.ui.menu import Menu
from dtk.ui.navigatebar import Navigatebar
from dtk.ui.notebook import Notebook
from dtk.ui.osd_tooltip import OSDTooltip
from dtk.ui.paned import HPaned
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.slider import Wizard
from dtk.ui.spin import SpinBox
from dtk.ui.poplist import Poplist, IconTextItem
from dtk.ui.statusbar import Statusbar
from dtk.ui.tab_window import TabWindow, TabBox
from dtk.ui.treeview import TreeView, TreeViewItem
from dtk.ui.unique_service import UniqueService, is_exists
from dtk.ui.utils import container_remove_all, get_widget_root_coordinate
from dtk.ui.volume_button import VolumeButton
from dtk.ui.breadcrumb import Bread, Crumb
from dtk.ui.dialog import OpenFileDialog
import dbus
import dbus.service
import gtk
import sys
import time

print time.time() - start_time

def m_motion_item(widget, item, x, y):
    print widget, item, x, y

def print_delete_select_items(list_view, items):
    print items

def print_right_press(list_view, list_item, column, offset_x, offset_y):
    print column, offset_x, offset_y

def print_button_press(list_view, list_item, column, offset_x, offset_y):
    '''Print button press.'''
    print "* Button press: %s" % (str((list_item.title, list_item.artist, list_item.length)))

def print_double_click(list_view, list_item, column, offset_x, offset_y):
    '''Print double click.'''
    print "* Double click: %s" % (str((list_item.title, list_item.artist, list_item.length)))
    list_view.set_highlight(list_item)

def print_single_click(list_view, list_item, column, offset_x, offset_y):
    '''Print single click.'''
    print "* Single click: %s" % (str((list_item.title, list_item.artist, list_item.length)))
    list_view.clear_highlight()

def print_motion_notify(list_view, list_item, column, offset_x, offset_y):
    '''Print motion notify.'''
    print "* Motion notify: %s" % (str((list_item.title, list_item.artist, list_item.length, column, offset_x, offset_y)))
    
def print_entry_action(entry, entry_text):
    '''Print entry action.'''
    print entry_text
    
def clicked_test(button):
    print "clicked"
    
def simulate_redraw_request(items, items_length):
    '''Simulate item's redraw request.'''
    item_index = int(time.time() * 100) % items_length
    print items[item_index].length
    items[item_index].emit_redraw_request()
    
    return True

def switch_tab(notebook_box, tab_box):
    '''Switch tab 1.'''
    if not tab_box in notebook_box.get_children():
        container_remove_all(notebook_box)
        notebook_box.add(tab_box)
    
        notebook_box.show_all()
        
def create_tab_window_item(name):
    '''docs'''
    align = gtk.Alignment()
    align.set(0.5, 0.5, 0.0, 0.0)
    align.add(gtk.Button(name))
    
    return (name, align)

def open_file_dlg_click_ok(filename):
    print "opened %s" % filename

if __name__ == "__main__":
    # Build DBus name.
    app_dbus_name = "com.deepin.demo"
    app_object_name = "/com/deepin/demo"
    
    # Check unique.
    if is_exists(app_dbus_name, app_object_name):
        sys.exit()
    
    # Init application.
    application = Application()
    
    # Startup unique service, must after application code.
    app_bus_name = dbus.service.BusName(app_dbus_name, bus=dbus.SessionBus())
    UniqueService(app_bus_name, app_dbus_name, app_object_name, application.raise_to_top)
    
    # Set application default size.
    application.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    
    # Set application icon.
    application.set_icon(app_theme.get_pixbuf("icon.ico"))
    
    # Set application preview pixbuf.
    application.set_skin_preview(app_theme.get_pixbuf("frame.png"))
    
    # Add titlebar.
    application.add_titlebar(
        ["theme", "menu", "max", "min", "close"], 
        app_theme.get_pixbuf("logo.png"), 
        "深度图形库",
        "/home/andy/deepin-ui/loooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooony.py",
        )
    
    # Draw application background.
    button = gtk.Button()
    button.set_size_request(200,300)
    
    # Init menu callback.
    sub_menu_a = Menu(
        [(None, "子菜单A1", None),
         None,
         (None, "子菜单A2", None),
         (None, "子菜单A3", None),
         ])
    sub_menu_e = Menu(
        [(None, "子菜单E1", None),
         (None, "子菜单E2", None),
         None,
         (None, "子菜单E3", None),
         ])
    sub_menu_d = Menu(
        [(None, "子菜单D1", None),
         (None, "子菜单D2", None),
         None,
         (None, "子菜单D3", sub_menu_e),
         ])
    sub_menu_c = Menu(
        [(None, "子菜单C1", None),
         (None, "子菜单C2", None),
         None,
         (None, "子菜单C3", sub_menu_d),
         ])
    sub_menu_b = Menu(
        [(None, "子菜单B1", None),
         None,
         (None, "子菜单B2", None),
         None,
         (None, "子菜单B3", sub_menu_c),
         ])
    
    menu = Menu(
        [(None,
          "测试测试测试1", None),
         (None,
          "测试测试测试2", sub_menu_a),
         (None,
          "测试测试测试3", sub_menu_b),
         (None,
          "测试测试测试", None),
         (None,
          "测试测试测试", None),
         (None,
          "测试测试测试4", None, (1, 2, 3)),
         (None,
          "测试测试测试5", None),
         (None,
          "测试测试测试6", None),
         ],
        True
        )
    menu.set_menu_item_sensitive_by_index(1, False)
    application.set_menu_callback(lambda button: menu.show(
            get_widget_root_coordinate(button, WIDGET_POS_BOTTOM_LEFT),
            (button.get_allocation().width, 0)))
    
    # Add navigatebar.
    tab_window_items = map(create_tab_window_item, ["Tab1", "Tab2", "Tab3", "Tab4", "Tab5"])
    
    droplist = Droplist(
        [("测试测试测试1", None),
         ("测试测试测试2", None),
         ("测试测试测试3", None),
         None,
         ("测试测试测试", None),
         None,
         ("测试测试测试4", None),
         ("测试测试测试5", None),
         ("测试测试测试6", None),
         ],
        True
        )
    droplist.set_size_request(-1, 100)
    
    images_path = os.path.join(get_parent_dir(__file__, 1), "images")
    navigatebar = Navigatebar(
        [(app_theme.get_pixbuf("navigatebar/nav_recommend.png"), "导航1", 
          lambda : Wizard([os.path.join(images_path, "slide_1.jpg"),
                      os.path.join(images_path, "slide_2.jpg"),
                      os.path.join(images_path, "slide_3.jpg"),
                      os.path.join(images_path, "slide_4.jpg")],
                      [(os.path.join(images_path, "select_1.png"), os.path.join(images_path, "unselect_1.png")),
                       (os.path.join(images_path, "select_2.png"), os.path.join(images_path, "unselect_2.png")),
                       (os.path.join(images_path, "select_3.png"), os.path.join(images_path, "unselect_3.png")),
                       (os.path.join(images_path, "select_4.png"), os.path.join(images_path, "unselect_4.png")),
                       ]).show_all()),
         (app_theme.get_pixbuf("navigatebar/nav_repo.png"), "导航2", lambda : Poplist(map(lambda text: IconTextItem((app_theme.get_pixbuf("button/button_normal.png"),
                                                                                                          app_theme.get_pixbuf("button/button_normal.png"),
                                                                                                          app_theme.get_pixbuf("button/button_normal.png"),
                                                                                                          ), str(text)), range(0, 300)),
                                                                                  max_height=300
                                                                                ).show((450, 250))),
         (app_theme.get_pixbuf("navigatebar/nav_update.png"), "导航3", lambda : TabWindow("测试标签窗口", tab_window_items, dockfill=True, current_tab_index=2).show_all()),
         (app_theme.get_pixbuf("navigatebar/nav_uninstall.png"), "导航4", lambda : OpenFileDialog("打开文件", application.window, open_file_dlg_click_ok)),
         (app_theme.get_pixbuf("navigatebar/nav_download.png"), "导航5", None),
         (app_theme.get_pixbuf("navigatebar/nav_repo.png"), "导航6", None),
         (app_theme.get_pixbuf("navigatebar/nav_update.png"), "导航7", None),
         (app_theme.get_pixbuf("navigatebar/nav_uninstall.png"), "导航8", None),
         ])
    application.main_box.pack_start(navigatebar, False)
    application.window.add_move_event(navigatebar)
    application.window.add_toggle_event(navigatebar)
    

    notebook_box = gtk.VBox()
    tab_1_box = gtk.VBox()
    tab_2_box = gtk.VBox()
    tab_4_box = gtk.VBox()
    tab_5_box = gtk.VBox()
    
    notebook = Notebook(
        [(app_theme.get_pixbuf("music.png"), "分类列表", lambda : switch_tab(notebook_box, tab_1_box)),
         (app_theme.get_pixbuf("web.png"), "网络浏览器", lambda : switch_tab(notebook_box, tab_2_box)),
         (app_theme.get_pixbuf("music.png"), "专辑封面", lambda : switch_tab(notebook_box, tab_4_box)),
         (app_theme.get_pixbuf("music.png"), "自定义控件", lambda : switch_tab(notebook_box, tab_5_box)),
         ])
    notebook_frame = HorizontalFrame(20)
    notebook_frame.add(notebook)
    application.main_box.pack_start(notebook_frame, False, False)
    
    application.main_box.pack_start(notebook_box, True, True)
    
    notebook_box.add(tab_1_box)
    
    # Add body box.
    body_box = gtk.HBox()
    horizontal_frame = HorizontalFrame()
    horizontal_frame.add(body_box)
    tab_1_box.pack_start(horizontal_frame, True, True)
    
    # Add categorybar.
    # Note if you add list in categorybar make sure height is multiples of list length.
    # Otherwise last one item will heighter than Otherwise items.
    category_box = HPaned()
    osd_tooltip = OSDTooltip(category_box, offset_x=200, offset_y=50)
    body_box.add(category_box)
    categorybar = Categorybar([
            (app_theme.get_pixbuf("categorybar/word.png"), "测试分类", lambda : osd_tooltip.show("OSD tooltip lonoooooooo")),
            (app_theme.get_pixbuf("categorybar/win.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/web.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/professional.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/other.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/multimedia.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/graphics.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/game.png"), "测试分类", None),
            (app_theme.get_pixbuf("categorybar/driver.png"), "测试分类", None),
            ])
    category_box.add1(categorybar)
    
    # Add scrolled window.
    scrolled_window = ScrolledWindow()
    category_box.add2(scrolled_window)
    
    items_length = 1000

    items = map(lambda index: ListItem(
            "豆浆油条 测试标题 %04d" % index,
            "林俊杰 %04d" % index,
            "10:%02d" % index,
            ), range(0, items_length))
    
    list_view = ListView(
        [(lambda item: item.title, cmp),
         (lambda item: item.artist, cmp),
         (lambda item: item.length, cmp)], drag_data=([("text/deepin-webcasts", gtk.TARGET_SAME_APP, 1),], gtk.gdk.ACTION_COPY, 1))
    list_view.set_expand_column(0)
    list_view.add_titles(["歌名", "歌手", "时间"])
    list_view.add_items(items)
    list_view.hide_column([1])
    list_view.set_hide_column_flag(False)
    list_view.set_hide_column_resize(False)
    list_view.connect("double-click-item", lambda listview, item, i, x, y: list_view.set_highlight(item))
    list_view.connect("delete-select-items", print_delete_select_items)
    # list_view.connect("button-press-item", print_button_press)
    # list_view.connect("double-click-item", print_double_click)
    # list_view.connect("single-click-item", print_single_click)
    # list_view.connect("motion-notify-item", print_motion_notify)
    list_view.connect("right-press-items", print_right_press)

    scrolled_window.add_child(list_view)
    '''
    if len(list_view.items):
        list_view.set_highlight(list_view.items[6])
    '''
    # Add volume button.
    volume_button = VolumeButton(100, 50)
    volume_frame = gtk.Alignment()
    volume_frame.set(0.0, 0.5, 0, 0)
    volume_frame.set_padding(0, 0, 10, 0)
    volume_frame.add(volume_button)
    tab_1_box.pack_start(volume_frame, False, False)
    
    # Add entry widget.
    entry_button = ImageButton(
        app_theme.get_pixbuf("entry/search_normal.png"),
        app_theme.get_pixbuf("entry/search_hover.png"),
        app_theme.get_pixbuf("entry/search_press.png"),
        )
    entry = InputEntry("Linux Deepin", enable_clear_button=True)
    #entry.set_text("DEBUG")
    entry.connect("action-active", print_entry_action)
    entry.set_size(150, 48)
    password_entry = PasswordEntry("")
    password_entry.set_size(150, 24)
    shown_password = False
    password_entry.show_password(shown_password)
    password_check_button = CheckButton("Shown")
    password_check_button.set_active(shown_password)
    password_check_button.connect("toggled", lambda widget: password_entry.show_password(widget.get_active()))
    password_check_button_align = gtk.Alignment()
    password_check_button_align.set(0.0, 0.5, 0, 0)
    password_check_button_align.add(password_check_button)
    entry_label = Label("标签测试， 内容非常长")
    entry_label.set_text("标签的内容")
    entry_label.set_size_request(100, 30)
    entry_box = gtk.HBox(spacing=10)
    entry_box.pack_start(entry_label, False, False)
    entry_box.pack_start(entry, True, True)
    entry_box.pack_start(password_entry, True, True)
    entry_box.pack_start(password_check_button_align, True, True)
    
    #shortcust_entry = ShortcutKeyEntry("Ctrl + Alt + Q")
    shortcust_entry = ShortcutKeyEntry("")
    shortcust_entry.set_size(150, 24)
    shortcust_entry.set_shortcut_key("Ctrl + Alt + Q")
    entry_box.pack_start(shortcust_entry, False, False)
    
    test_button = Button("测试")
    test_button.connect("clicked", clicked_test)
    entry_box.pack_start(test_button, False, False)
    
    color_button = ColorButton()
    entry_box.pack_start(color_button, False, False)
    
    # combobox
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
    entry_box.pack_start(combo_box, False, False)    
    spin_box = SpinBox(3000, 0, 5000, 100)
    entry_box.pack_start(spin_box, False, False)
    
    entry_frame = HorizontalFrame(10, 0, 0, 0, 0)
    entry_frame.add(entry_box)
    tab_1_box.pack_start(entry_frame, False, False)

    # Combo button.
    combo_menu = Menu(
        [(None, "选项1", None),
         (None, "选项2", None),
         (None, "选项3", None),
         ],
        is_root_menu=True,
        )
    
    def click_combo_button(widget):
        print "click combo button"
        
    def show_combo_menu(widget, x, y, offset_x, offset_y):
        combo_menu.show((x, y), (offset_x, offset_y))
        
    combo_button = ComboButton(
        app_theme.get_pixbuf("button/button_normal.png"),
        app_theme.get_pixbuf("button/button_hover.png"),
        app_theme.get_pixbuf("button/button_press.png"),
        app_theme.get_pixbuf("button/button_normal.png"),
        app_theme.get_pixbuf("button/arrow_normal.png"),
        app_theme.get_pixbuf("button/arrow_hover.png"),
        app_theme.get_pixbuf("button/arrow_press.png"),
        app_theme.get_pixbuf("button/arrow_normal.png"),
        )
    combo_button.connect("button-clicked", click_combo_button)
    combo_button.connect("arrow-clicked", show_combo_menu)
    
    temp_hbox = gtk.HBox()
    tab_1_box.pack_start(temp_hbox, False, False)
    
    temp_hbox.pack_start(combo_button, False, False)
    
    star_view = StarView()
    temp_hbox.pack_start(star_view, False, False)
    
    # Add statusbar.
    statusbar = Statusbar(36)
    tab_1_box.pack_start(statusbar, False)
    application.window.add_move_event(statusbar)
    application.window.add_toggle_event(statusbar)
    
    link_button = LinkButton("加入我们", "http://www.linuxdeepin.com/joinus/job")
    statusbar.status_item_box.pack_start(link_button)
    
    web_view = WebView()
    web_scrolled_window = ScrolledWindow()
    web_scrolled_window.add(web_view)
    web_view.open("http://www.linuxdeepin.com")
    tab_2_box.pack_start(web_scrolled_window)
    
    icon_view_hframe = HorizontalFrame()
    icon_view_vframe = gtk.Alignment()
    icon_view_vframe.set(0, 0, 1, 1)
    icon_view_vframe.set_padding(0, 1, 0, 0)
    
    icon_view_scrolled_window = ScrolledWindow()
    icon_view = IconView(10, 10)
    icon_view_scrolled_window.add_child(icon_view)
    icon_view_hframe.add(icon_view_scrolled_window)
    
    icon_view_vframe.add(icon_view_hframe)
    
    icon_files = map(lambda index: os.path.join(os.path.dirname(__file__), "cover/%s.jpg" % (index)), range(1, 33))
    icon_items = map(lambda icon_file_path: IconItem(icon_file_path, 96, 96), icon_files * 100)
    only_one_icon_items = []
    only_one_icon_items.append(icon_items[0])
    icon_view.add_items(icon_items)
    icon_view.connect("motion-item", m_motion_item)
    
    tab_4_box.pack_start(icon_view_vframe, True, True)
    
    # Tab 5.
    button_box = gtk.VBox()
    check_button = CheckButton("Check Button")
    radio_button_1 = RadioButton("Radio Button1")
    radio_button_2 = RadioButton("Radio Button2")
    button_box.pack_start(check_button, False, False, 4)
    button_box.pack_start(radio_button_1, False, False, 4)
    button_box.pack_start(radio_button_2, False, False, 4)
    tab_5_box.pack_start(button_box, False, False)

    # Breadcrumb
    bread = Bread(["Root", None],
                  show_entry = True,
                  show_others = False)
    bread.connect("entry-changed", lambda w, p: bread.change_node(0,[(i,[(None, "test", None)]) for i in p.split("/")[1:]]))
    bread.set_size(100, -1)
     

    tab_5_box.pack_start(bread, False, False)
    btn = gtk.Button("add")
    btn.connect("clicked", lambda w: bread.add(Crumb("Child", Menu(
                                [(None, "Child", None),],
                                shadow_visible = False,
                                is_root_menu = True))))

    tab_5_box.pack_start(btn, False, False)
    
    #Tree view.
    def tree_view_single_click_cb(widget, item):
        pass    

    
    tree_view = TreeView()
    tree_view_scrolled_window = ScrolledWindow()
    tree_view_scrolled_window.add_child(tree_view)
    tree_view.connect("single-click-item", tree_view_single_click_cb)
    
    tab_5_box.pack_start(tree_view_scrolled_window)


    
    wuhan_node = tree_view.add_item(None, TreeViewItem("Linux Deepin"))

    wuhan_dev_node = tree_view.add_item(wuhan_node, TreeViewItem("test1"))
    wuhan_des_node = tree_view.add_item(wuhan_node, TreeViewItem("test2"))
    wuhan_sys_node = tree_view.add_item(wuhan_node, TreeViewItem("test3"))
    
    tree_view.add_item(wuhan_dev_node, TreeViewItem("Deepin Music Player"))    
    tree_view.add_item(wuhan_dev_node, TreeViewItem("Deepin Media Player"))
    tree_view.add_item(wuhan_dev_node, TreeViewItem("Deepin Software Center"))
    
    tree_view.add_item(wuhan_sys_node, TreeViewItem("Deepin Talk"))    
    tree_view.add_item(wuhan_sys_node, TreeViewItem("Deepin IM"))
    tree_view.add_item(wuhan_sys_node, TreeViewItem("Deepin Reader"))
    
    tree_view.add_item(wuhan_des_node, TreeViewItem("ZHL"))    
    tree_view.add_item(wuhan_des_node, TreeViewItem("ZHL"))
    tree_view.add_item(wuhan_des_node, TreeViewItem("zhm"))
    
    beijing_node = tree_view.add_item(None, TreeViewItem("深度 Linux"))    
    tree_view.add_items(beijing_node, [TreeViewItem(name) for name in ("开发部", "设计部", "系统部")])
    tree_view.set_index_text(1, "深度测试改名")
    #tree_view.expand()
    tree_view.set_highlight_index(3)
    # text_view = TextView("this is line one\nline break is awesome\nblahblahlooooooooooooooooooooooooooooooooooooooooooooooooooooooooog")
    # sw = ScrolledWindow()
    # text_viewport = gtk.Viewport()
    # text_viewport.add(text_view)
    # sw.add(text_viewport)
    # tab_5_box.pack_start(sw, True, True)
    
    # Run.
    application.run()
