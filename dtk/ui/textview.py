#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Jack River
# 
# Author:     Jack River <ritksm@gmail.com>
# Maintainer: Jack River <ritksm@gmail.com>
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


from constant import DEFAULT_FONT_SIZE, DEFAULT_FONT
from contextlib import contextmanager 
from draw import draw_hlinear
from keymap import get_keyevent_name
from menu import Menu
from theme import ui_theme
from utils import propagate_expose, cairo_state, color_hex_to_cairo, get_content_size, is_double_click, is_right_button, is_left_button, alpha_color_hex_to_cairo
import gobject
import gtk
import pango
import pangocairo


class TextView(gtk.EventBox):
	
	def __init__(self, 
				buf = gtk.TextBuffer(), 
				padding_x = 5, 
				padding_y = 2, 
				line_spacing = 5, 
				font_size = DEFAULT_FONT_SIZE, 
				text_color="#000000", 
				text_select_color="#000000", 
				background_select_color="#000000", ):
		gtk.EventBox.__init__(self)
		self.connect("expose-event", self.expose_text_view)
		self.buf = buf
		self.padding_x = padding_x
		self.padding_y = padding_y
		self.line_spacing = line_spacing
		self.font_size = font_size
		self.offset_x = 0
		self.text_color = text_color
		self.text_select_color = text_select_color
		self.background_select_color = background_select_color
		pass
		
	def expose_text_view(self, widget, event):
		cr = widget.window.cairo_create()
		rect = widget.allocation
		self.draw_text(cr, rect)
		
		propagate_expose(widget, event)
		
		return True

	def draw_background(self, cr, rect):
		pass
		
	def draw_text(self, cr, rect):
		x, y, w, h = rect.x, rect.y, rect.width, rect.height
		with cairo_state(cr):
			draw_x = x + self.padding_x
			draw_y = y + self.padding_y
			draw_width = w - self.padding_x * 2
			draw_height = h - self.padding_y * 2
			cr.rectangle(draw_x, draw_y, draw_width, draw_height)
			cr.clip()
			
			# pango context
			context = pangocairo.CairoContext(cr)
			
			# pango layout
			layout = context.create_layout()
			layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
			
			text = self.get_text(-1)
			layout.set_text(text)
			
			(text_width, text_height) = layout.get_pixel_size()
			cr.move_to(draw_x - self.offset_x, draw_y + (draw_height - text_height) / 2)
			
			cr.set_source_rgb(0,0,0)
			context.update_layout(layout)
			context.show_layout(layout)
		
	def set_text(self, text):
		self.buf.set_text(text)
		self.queue_draw()
		
	def get_text(self, line = 0):
		if line != -1:
			ir = self.buf.get_iter_at_line(line)
			return self.buf.get_text(ir, self.buf.get_iter_at_offset(ir.get_offset()+ ir.get_chars_in_line()))
		else:
			result = ""
			for x in range(0, self.buf.get_line_count()):
				result += self.get_text(x)
				result += "\r\n"
			return result
		
    
gobject.type_register(TextView)
	
	
def click(widget):
	tv = widget.get_children()
	tv[0].set_text("changed\r\nhi")

if __name__ == "__main__":
	window = gtk.Window()
	tb = gtk.TextBuffer()
	tb.set_text("hello")
	tv = TextView(buf = tb)
	
	window.add(tv)
	
	window.set_size_request(300, 200)
	
	window.connect("destroy", lambda w: gtk.main_quit())
	
	window.connect("show", click)
	
	window.show_all()
	
	gtk.main()
