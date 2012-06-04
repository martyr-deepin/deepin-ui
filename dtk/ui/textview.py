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
		self.buf = buf
		self.padding_x = padding_x
		self.padding_y = padding_y
		self.line_spacing = line_spacing
		self.font_size = font_size
		self.offset_x = 0
		self.text_color = text_color
		self.text_select_color = text_select_color
		self.background_select_color = background_select_color
		self.grab_focus_flag = False
		self.current_line = self.buf.get_line_count() - 1 # get currrent line index default set to last
		self.current_line_offset = self.buf.get_iter_at_line(self.current_line).get_chars_in_line() # get offset in current line default set to 0
		
		self.im = gtk.IMMulticontext()
		self.im.connect("commit", lambda im, input_text: self.commit_entry(input_text))
		
		# Add keymap.
		self.keymap = {
				"Left" : self.move_to_left,
				"Right" : self.move_to_right,
				"Home" : self.move_to_start,
				"End" : self.move_to_end,
				"BackSpace" : self.backspace,
				"Delete" : self.delete,
				"S-Left" : self.select_to_left,
				"S-Right" : self.select_to_right,
				"S-Home" : self.select_to_start,
				"S-End" : self.select_to_end,
				"C-a" : self.select_all,
				"C-x" : self.cut_to_clipboard,
				"C-c" : self.copy_to_clipboard,
				"C-v" : self.paste_from_clipboard,
				"Return" : self.press_return }
				
		self.connect_after("realize", self.realize_textview)
		self.connect("key-press-event", self.key_press_textview)
		self.connect("expose-event", self.expose_textview)
		self.connect("focus-in-event", self.focus_in_textview)
		self.connect("focus-out-event", self.focus_out_textview)
		
	def move_to_left(self):
		if self.current_line_offset >= 1:
			self.current_line_offset -= 1
		pass
    
	def move_to_right(self):
		pass
	
	def move_to_start(self):
		pass
	
	def move_to_end(self):
		pass
	
	def backspace(self):
		#TODO fix delete while there is a line-break
		ir = self.buf.get_iter_at_line(self.current_line)
		if self.current_line_offset == 0:
			self.current_line = self.current_line - 1
			self.current_line_offset = self.buf.get_iter_at_line(self.current_line).get_chars_in_line()
		else:
			ir.set_line_offset(self.current_line_offset)
			ir2 = self.buf.get_iter_at_line(self.current_line)
			ir2.set_line_offset(self.current_line_offset - 1 )
			self.buf.delete(ir2, ir)
			self.current_line_offset -= 1
		
		self.queue_draw()
		
	
	def delete(self):
		pass
	
	def select_to_left(self):
		pass
	
	def select_to_right(self):
		pass
	
	def select_to_start(self):
		pass
	
	def select_to_end(self):
		pass
	
	def select_all(self):
		pass
	
	def cut_to_clipboard(self):
		pass
	
	def copy_to_clipboard(self):
		pass
	
	def paste_from_clipboard(self):
		pass
	
	def press_return(self):
		pass

	def focus_in_textview(self, widget, event):
		'''Callback for `focus-in-event` signal.'''
		self.grab_focus_flag = True

		# Focus in IMContext.
		self.im.set_client_window(widget.window)
		self.im.focus_in()

		self.queue_draw()
            
	def focus_out_textview(self, widget, event):
		'''Callback for `focus-out-event` signal.'''
		self.grab_focus_flag = False

		# Focus out IMContext.
		self.im.focus_out()

		self.queue_draw()
    
	def expose_textview(self, widget, event):
		cr = widget.window.cairo_create()
		rect = widget.allocation
		self.draw_text(cr, rect)
		
		propagate_expose(widget, event)
		
		return True

	def realize_textview(self, widget):
		'''Realize entry.'''
		text_width = self.get_content_width(self.get_text(-1))
		rect = self.get_allocation()

		if text_width > rect.width - self.padding_x * 2 > 0:
			self.offset_x = text_width - rect.width + self.padding_x * 2
		else:
			self.offset_x = 0

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
			return result
			
	def key_press_textview(self, widget, event):
		input_method_filt = self.im.filter_keypress(event)
		if not input_method_filt:
			self.handle_key_event(event)
		return False
		
	def handle_key_event(self, event):
		'''Handle key event.'''
		key_name = get_keyevent_name(event)

		if self.keymap.has_key(key_name):
			self.keymap[key_name]()
			

	def get_content_width(self, content):
		'''Get content width.'''
		(content_width, content_height) = get_content_size(content, self.font_size)
		return content_width
	
	def commit_entry(self, input_text):
		ir = self.buf.get_iter_at_line(self.current_line)
		print "%s%s%s" % (self.current_line_offset, "|", ir.get_chars_in_line())
		ir.set_line_offset(self.current_line_offset)
		self.buf.insert(ir, input_text)
		self.current_line_offset += 1
		print "%s%s%s" % (self.current_line_offset, "|", ir.get_chars_in_line())
		self.queue_draw()
			
gobject.type_register(TextView)
	
	
def click(widget, event):
	children = widget.get_children()
	tv = children[0]
	tv.key_press_textview(tv, event)

if __name__ == "__main__":
	window = gtk.Window()
	tb = gtk.TextBuffer()
	tb.set_text("hello\nworld")
	tv = TextView(buf = tb)
	
	window.add(tv)
	
	window.set_size_request(300, 200)
	
	window.connect("destroy", lambda w: gtk.main_quit())
	
	window.connect("key-press-event", click)
	
	window.show_all()
	
	gtk.main()
