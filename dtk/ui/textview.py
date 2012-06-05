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
				content = "", 
				padding_x = 5, 
				padding_y = 2, 
				line_spacing = 5, 
				font_size = DEFAULT_FONT_SIZE, 
				text_color="#000000", 
				text_select_color="#000000", 
				background_select_color="#000000", ):
		gtk.EventBox.__init__(self)
		self.set_visible_window(False) # for transparent background
		self.content = self.__parse_content(content)
		self.padding_x = padding_x
		self.padding_y = padding_y
		self.line_spacing = line_spacing
		self.font_size = font_size
		self.offset_x = 0
		self.text_color = text_color
		self.text_select_color = text_select_color
		self.background_select_color = background_select_color
		self.grab_focus_flag = False
		self.set_can_focus(True)
		self.current_line = len(self.content.keys()) - 1 # currrent line index
		self.current_line_offset = len(self.content[self.current_line]) # offset in current line
		
		self.im = gtk.IMMulticontext()
		self.im.connect("commit", lambda im, input_text: self.commit_entry(input_text))
		
		# Add keymap.
		self.keymap = {
				"Left" : self.move_to_left,
				"Right" : self.move_to_right,
				"Up" : self.move_up, 
				"Down" : self.move_down, 
				"Home" : self.move_to_start,
				"End" : self.move_to_end,
				"BackSpace" : self.backspace,
				"Delete" : self.press_delete,
				"S-Left" : self.select_to_left,
				"S-Right" : self.select_to_right,
				"S-Home" : self.select_to_start,
				"S-End" : self.select_to_end,
				"C-a" : self.select_all,
				"C-x" : self.cut_to_clipboard,
				"C-c" : self.copy_to_clipboard,
				"C-v" : self.paste_from_clipboard,
				"Return" : self.press_return }

		self.connect("key-press-event", self.key_press_textview)
		self.connect("expose-event", self.expose_textview)
		self.connect("focus-in-event", self.focus_in_textview)
		self.connect("focus-out-event", self.focus_out_textview)
		self.connect("button-press-event", self.button_press_textview)
		self.connect("motion-notify-event", self.motion_notify_text_view)
		
	def __parse_content(self, text):
		content = dict()
		split = text.split("\r\n")
		index = 0
		for x in split:
			content[index] = x.rstrip("\r\n")
			index += 1
		
		return content
		
	def move_to_left(self):
		if self.current_line_offset >= 1:
			self.current_line_offset -= 1
			self.queue_draw()
		else:
			if self.current_line != 0:
				self.current_line -= 1
				self.current_line_offset = len(self.content[self.current_line])
				self.queue_draw()
    
	def move_to_right(self):
		if self.current_line_offset != len(self.content[self.current_line]):
			self.current_line_offset += 1 # forward cursor
			self.queue_draw()
		else:
			if self.current_line < len(self.content.keys()) - 1:
				self.current_line += 1 # go to next line
				self.current_line_offset = 0 # line start
				self.queue_draw()
		pass
	
	def move_up(self):
		if self.current_line != 0:
			self.current_line -= 1
			offset = self.current_line_offset
			if offset < len(self.content[self.current_line]):
				#line is long enough, so keep current offset
				pass
			else:
				#line is not long enouth, go to line end
				self.current_line_offset = len(self.content[self.current_line])
				
			self.queue_draw()
	
	def move_down(self):
		if self.current_line != len(self.content) - 1:
			# not the last line
			self.current_line += 1
			offset = self.current_line_offset
			if offset < len(self.content[self.current_line]):
				#line is long enough, so keep current offset
				pass
			else:
				#line is not long enouth, go to line end
				self.current_line_offset = len(self.content[self.current_line])
				
			self.queue_draw()
		
	def move_to_start(self):
		pass
	
	def move_to_end(self):
		pass
	
	def backspace(self):
		"""when press backspace, delete one char"""
		if self.current_line_offset == 0:
			# at line start
			if self.current_line != 0:
				# not the first line
				char_left = len(self.content[self.current_line])
				self.__join_line(self.current_line - 1)
				self.current_line -= 1
				self.current_line_offset = len(self.content[self.current_line]) - char_left
		else:
			self.__delete_text(self.current_line, self.current_line_offset, 1)
			self.current_line_offset -= 1
		
		self.queue_draw()
		
	
	def press_delete(self):
		"""when press backspace, delete one char"""
		if self.current_line_offset == len(self.content[self.current_line]):
			# offset at line end
			if self.current_line != len(self.content.keys()) - 1:
				# not the last line
				self.__join_line(self.current_line)
		else:
			self.__delete_text(self.current_line, self.current_line_offset + 1, 1)
		
		self.queue_draw()
	
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
		self.__insert_new_line(self.current_line, self.current_line_offset)
		self.current_line += 1
		self.current_line_offset = 0
		
		self.queue_draw()
		pass
	
	def motion_notify_text_view(self, widget, event):
		print self.current_line, self.current_line_offset
		self.queue_draw()
		
	def button_press_textview(self, widget, event):
		'''Button press entry.'''
		# Get input focus.
		self.grab_focus()
		
		self.grab_focus_flag = True

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
		
		# draw text
		self.draw_text(cr, rect)
		
		# draw cursor
		if self.grab_focus_flag:
			self.draw_cursor(cr, rect)
		
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
			cr.move_to(draw_x + self.padding_x , draw_y + self.padding_y)
			
			cr.set_source_rgb(0,0,0)
			context.update_layout(layout)
			context.show_layout(layout)

	def draw_cursor(self, cr, rect):
		x, y, w, h = rect.x, rect.y, rect.width, rect.height
		left_str = self.get_text(self.current_line)[0:self.current_line_offset]
		left_str_width = self.get_content_width(left_str) + self.get_content_width("x") / 3 * 2
		
		line_offset = get_content_size("Height", self.font_size)[-1] * (self.current_line)
		
		cr.set_source_rgb(0,0,0)
		cr.rectangle(x + self.padding_x + left_str_width, y + self.padding_y + line_offset, 1, get_content_size("Height", self.font_size)[-1])
		cr.fill()
		
		
	def set_text(self, text):
		self.content = self.__parse_content(text)
		self.current_line = len(self.content.keys()) - 1 # currrent line index
		self.current_line_offset = len(self.content[self.current_line]) # offset in current line
		self.queue_draw()
		
	def get_text(self, line = 0):
		if line != -1:
			return self.content[line]
		else:
			result = ""
			for x in self.content.keys():
				result += self.content[x]
				result += "\r"
			result.rstrip("\r")
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
	
	def __insert_text(self, line, offset, text):
		if line < len(self.content.keys()):
			temp = self.content[line]
			self.content[line] = temp[0:offset] + text + temp[offset:len(temp)]
		else:
			raise Exception()
	
	def __delete_text(self, line, offset, length):
		if line < len(self.content.keys()) or (offset + length) > len(self.content[line]):
			temp = self.content[line]
			self.content[line] = temp[0:offset - length] + temp[offset:len(temp)]
		else:
			raise Exception()
	
	def __insert_new_line(self, after_line, line_offset):
		temp = self.content.copy()
		if after_line < len(self.content.keys()):
			chars_left = self.content[after_line][line_offset:len(self.content[after_line])]
			self.content[after_line] = self.content[after_line][0: line_offset]
			for x in range(after_line + 1, len(self.content.keys())):
				self.content[x+1] = temp[x]
			self.content[after_line + 1] = chars_left
		else:
			raise Exception()
			
	def __join_line(self, after_line):
		temp = self.content.copy()
		if after_line < len(self.content.keys()):
			self.content[after_line] += self.content[after_line + 1]
			for x in range(after_line + 2, len(self.content.keys())):
				self.content[x-1] = temp[x]
			self.content.pop(len(self.content.keys()) - 1)
		else:
			raise Exception()
	
	def commit_entry(self, input_text):
		self.__insert_text(self.current_line, self.current_line_offset, input_text)
		self.current_line_offset += len(input_text)
		self.queue_draw()
			
gobject.type_register(TextView)
	
	
def click(widget, event):
	children = widget.get_children()
	tv = children[0]
	tv.key_press_textview(tv, event)

if __name__ == "__main__":
	window = gtk.Window()
	
	tv = TextView(content = "hello\r\nworld\r\nline3")
	
	window.add(tv)
	
	window.set_size_request(300, 200)
	
	window.connect("destroy", lambda w: gtk.main_quit())
	
	window.connect("key-press-event", click)
	
	window.show_all()
	
	gtk.main()
