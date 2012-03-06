#!/usr/bin/env python
#======================================
# Search Bar Gtk Widget
# Partially compatible with gtk.entry()
# Render: Cairo   Theme: Dark
# By QB89Dragon 2008
#======================================

import gtk
import gobject
from gtk import gdk
import pygtk
import cairo
import pango
import math

class SearchBar(gtk.Widget):
	def __init__(self, BackImageFile=None, InitialText="", X=4, Y=17):
		gtk.Widget.__init__(self)
		self.connect("expose_event", self.expose)

		# Text Settings
		self.text = ""
		self.initialtext = InitialText
		self.cursor = 0
		self.selection = False
		self.cursorblink = False
		self.cursorvisible = False
		# Graphical Settings
		self.x = X
		self.y = Y
		self.hasrectangle = False
		self.cornerradius = 12
		
		if BackImageFile:
			self.BackImageBuffer = cairo.ImageSurface.create_from_png(BackImageFile)
		else:
			self.BackImageBuffer = None
		
	def do_realize(self):
		# Create events
		self.set_flags(self.flags() | gtk.REALIZED | gtk.CAN_FOCUS | gtk.HAS_FOCUS)
		
		# Create window for widget to be displayed in
			
		self.window = gtk.gdk.Window(
			self.get_parent_window(),
			width=self.allocation.width,
			height=self.allocation.height,
			window_type=gdk.WINDOW_CHILD,
			wclass=gdk.INPUT_OUTPUT,
			event_mask=self.get_events() | gtk.gdk.EXPOSURE_MASK | gtk.gdk.KEY_PRESS_MASK  | gtk.gdk.KEY_RELEASE_MASK | gtk.gdk.FOCUS_CHANGE_MASK)
#gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.POINTER_MOTION_HINT_MASK 
#| gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK
				
				
		# Associate the gdk.Window with ourselves, Gtk+ needs a reference
		# between the widget and the gdk window
		self.window.set_user_data(self)
		
		# Attach the style to the gdk.Window, a style contains colors and
		# GC contextes used for drawing
		self.style.attach(self.window)
		
		# The default color of the background should be what
		# the style (theme engine) tells us.
		self.style.set_background(self.window, gtk.STATE_NORMAL)
		self.window.move_resize(*self.allocation)
		
		# self.style is a gtk.Style object, self.style.fg_gc is
		# an array or graphic contexts used for drawing the forground
		# colours	
		self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
		self.connect("key_press_event", self.do_keypress)
		self.originalw = 0
		self.originalh = 0
		if self.cursorvisible:
			gobject.timeout_add(1000,self.blinkcursor)
		
	def do_keypress(self,widget,event):
		key = event.hardware_keycode
		if key==9:
			self.text=""
			self.window.invalidate_rect(None,False)						
		elif key==22 and self.cursor>0:
			self.text = self.text[0:len(self.text)-1]
			self.window.invalidate_rect(None,False)
		else:
			self.text=self.text+event.string
			self.cursor = self.cursor + 1
			self.window.invalidate_rect(None,False)
	
	def set_text(self,text):
		self.text = text
		self.window.invalidate_rect(None,False)
	
	def get_text(self):
		return self.text

	def expose(self, widget, event):
		# Redraw the window
		self.context = widget.window.cairo_create()
		# Set the region to be redrawn
		self.context.rectangle(event.area.x, event.area.x, event.area.width, event.area.height)
		self.context.clip()
		self.draw(self.context)
		return False
	
	def blinkcursor(self):
		self.cursorblink = not self.cursorblink
		#Fixme Invalidate only the leading cursor-edge region
		return True
	
	def draw(self,context):
		# Get widget dimensions
		rect = self.get_allocation()
		x = rect.x + rect.width / 2
		y = rect.y + rect.height / 2
		w = self.allocation.width
		h = self.allocation.height
		
		# If button has changed shape, redraw it's background
		if w!=self.originalw or h!=self.originalh:
			self.BuildBackground(w,h)
			self.originalw = w
			self.originalh = h

		# Draw background
		context.set_source_surface(self.buttonsurface,0,0)
		context.paint()
		
		# Draw text to the text box
		context.move_to(self.x,self.y)
		if self.text == "":
			context.select_font_face("Sans",cairo.FONT_SLANT_ITALIC,cairo.FONT_WEIGHT_NORMAL)
			context.set_font_size(12)
			context.set_source_rgba(.7,.7,.7,1)
			context.show_text (self.initialtext)
		else:
			context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
			context.set_font_size(12)
			context.set_source_rgba(0,0,0,1)
			context.show_text (self.text)

	def BuildBackground(self,w,h):
		self.buttonsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
		context = cairo.Context(self.buttonsurface)
		if self.BackImageBuffer:
				context.set_source_surface(self.BackImageBuffer, 0, 0)
				context.paint()
		if self.hasrectangle:
			# Draw the box
			self.DrawRoundedRect(context,0,0,w,h,self.cornerradius)
			# Fill
			pat = cairo.LinearGradient (0, 0,  0, h)
			pat.add_color_stop_rgba (0, 0, 0, 0, 1)
			pat.add_color_stop_rgba (.5, .1, .1,.1, 1)
			pat.add_color_stop_rgba (1, 0, 0, 0, 1)
			context.set_source(pat)
			context.fill_preserve()
			context.set_source_rgba(.5, .5, .5, 1)
			context.set_line_width(1.0)
			context.stroke()
		

	def DrawRoundedRect(self,context,x0,y0,w,h,radius):
		x1=x0+w
		y1=y0+h
		context.move_to(x0, y0 + radius)
		context.curve_to(x0 , y0, x0 , y0, x0 + radius, y0)
		context.line_to(x1 - radius, y0)
		context.curve_to(x1, y0, x1, y0, x1, y0 + radius)
		context.line_to(x1 , y1 - radius)
		context.curve_to(x1, y1, x1, y1, x1 - radius, y1)
		context.line_to(x0 + radius, y1)
		context.curve_to(x0, y1, x0, y1, x0, y1- radius)		 
		context.close_path()
		
# Test instance
def main():
	gobject.type_register(SearchBar)

	window = gtk.Window()
	entry = SearchBar(None,"Search")

	window.add(entry)
	
	window.connect("destroy", gtk.main_quit)
	window.show_all()

	gtk.main()
    
if __name__ == "__main__":
    main()
