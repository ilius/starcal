# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import time
from time import time as now

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.mywidgets import MyColorButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton


rootWin = gdk.get_default_root_window()
screenWidth = rootWin.get_width()

@registerType
class FloatingMsg(gtk.DrawingArea):
	def on_realize(self, widget):
		self.animateStart()
	def __init__(self, text,
					   speed=100,
					   bgColor=(255, 255, 0),
					   textColor=(0, 0, 0),
					   refreshTime=10,
					   finishFunc=None,
					   finishOnClick=True,
					   createWindow=True):
		gtk.DrawingArea.__init__(self)
		## speed: pixels per second
		self.speed = speed
		self.bgColor = bgColor
		self.textColor = textColor
		self.refreshTime = refreshTime
		self.finishFunc = finishFunc
		self.isFinished = False
		if finishOnClick:
			self.connect('button-press-event', self.finish)
		########
		if isinstance(text, str):
			text = text.decode('utf8')
		lines = []
		for line in text.split('\n'):
			line = line.strip()
			if line:
				lines.append(line)
		self.linesNum = len(lines)
		self.layoutList = [newTextLayout(self, line) for line in lines]
		self.rtlList = [self.isRtl(lines[i], self.layoutList[i])
						for i in range(self.linesNum)]
		self.index = 0
		self.height = 30
		########
		self.connect('draw', self.onExposeEvent)
		self.connect('realize', self.on_realize)
		########
		if createWindow:
			self.win = gtk.Window(gtk.WindowType.POPUP)#gtk.WindowType.POPUP ## ????????????????
			self.win.add(self)
			self.win.set_decorated(False)
			self.win.set_property('skip-taskbar-hint', True)
			self.win.set_keep_above(True)
		else:
			self.win = False
	def isRtl(self, line, layout):
		for i in range(len(line)):
			if layout.index_to_pos(i)[2] != 0:
				return (layout.index_to_pos(i)[2] < 0)
		return False
	def updateLine(self):
		self.layout = self.layoutList[self.index]
		self.rtl = self.rtlList[self.index]
		self.rtlSign = 1 if self.rtl else -1
		size = self.layout.get_pixel_size()
		self.height = size[1]
		self.set_size_request(screenWidth, self.height)
		if self.win!=None:
			self.win.resize(screenWidth, self.height)
		self.textWidth = size[0]
		self.startXpos = -self.textWidth if self.rtl else screenWidth
		self.xpos = self.startXpos
	def finish(self, w=None, e=None):
		self.isFinished = True
		self.win.destroy()
		self.destroy()
		if self.finishFunc:
			self.finishFunc()
	def onExposeEvent(self, widget, gevent):
		cr = self.cr = self.get_window().cairo_create()
		#######
		cr.rectangle(0, 0, screenWidth, self.height)
		setColor(cr, self.bgColor)
		cr.fill()
		#######
		cr.move_to(self.xpos, 0)
		setColor(cr, self.textColor)
		show_layout(cr, self.layout)
	def animateStart(self):
		self.updateLine()
		self.startTime = now()
		self.animateUpdate()
	def animateUpdate(self):
		if self.isFinished:
			return
		GObject.timeout_add(self.refreshTime, self.animateUpdate)
		self.xpos = self.startXpos + (now()-self.startTime)*self.speed*self.rtlSign
		if self.xpos>screenWidth or self.xpos<-self.textWidth:
			if self.index >= self.linesNum-1:
				self.finish()
				return
			else:
				self.index += 1
				self.updateLine()
		self.queue_draw()
	def show(self):
		gtk.DrawingArea.show(self)
		self.win.show()


@registerType
class MyLabel(gtk.DrawingArea):
	def __init__(self, bgColor, textColor):
		gtk.DrawingArea.__init__(self)
		self.bgColor = bgColor
		self.textColor = textColor
		self.connect('draw', self.onExposeEvent)
	def set_label(self, text):
		self.text = text
		self.layout = newTextLayout(self, text)
		size = self.layout.get_pixel_size()
		self.height = size[1]
		self.width = size[0]
		self.set_size_request(self.width, self.height)
		self.rtl = self.isRtl()
		self.rtlSign = 1 if self.rtl else -1
	def onExposeEvent(self, widget, gevent):
		cr = self.cr = self.get_window().cairo_create()
		#######
		cr.rectangle(0, 0, self.width, self.height)
		setColor(cr, self.bgColor)
		cr.fill()
		#######
		cr.move_to(0, 0)
		setColor(cr, self.textColor)
		show_layout(cr, self.layout)
	def isRtl(self):
		for i in range(len(self.text)):
			if self.layout.index_to_pos(i)[2] != 0:
				return (self.layout.index_to_pos(i)[2] < 0)
		return False


@registerType
class NoFillFloatingMsgWindow(gtk.Window):
	def __init__(self, text,
					   speed=100,
					   bgColor=(255, 255, 0),
					   textColor=(0, 0, 0),
					   refreshTime=10,
					   finishFunc=None,
					   finishOnClick=True):
		gtk.Window.__init__(self)
		self.set_type_hint(gtk.WindowType.POPUP)#gtk.WindowType.POPUP ## ????????????????
		self.set_decorated(False)
		self.set_property('skip-taskbar-hint', True)
		self.set_keep_above(True)
		self.label = MyLabel(bgColor, textColor)
		self.add(self.label)
		self.label.show()
		## speed: pixels per second
		self.speed = speed
		self.refreshTime = refreshTime
		self.finishFunc = finishFunc
		self.isFinished = False
		if finishOnClick:
			self.connect('button-press-event', self.finish)
		########
		if isinstance(text, str):
			text = text.decode('utf8')
		text = text.replace('\\n', '\n').replace('\\t', '\t')
		lines = []
		for line in text.split('\n'):
			line = line.strip()
			if line:
				lines.append(line)
		self.linesNum = len(lines)
		self.lines = lines
		self.index = 0
		########
		self.connect('realize', lambda widget: self.animateStart())
	def updateLine(self):
		self.label.set_label(self.lines[self.index])
		self.startXpos = -self.label.width if self.label.rtl else screenWidth
		self.startTime = now()
	def finish(self, w=None, e=None):
		self.isFinished = True
		self.destroy()
		if self.finishFunc:
			self.finishFunc()
	def animateStart(self):
		self.updateLine()
		self.animateUpdate()
	def animateUpdate(self):
		if self.isFinished:
			return
		GObject.timeout_add(self.refreshTime, self.animateUpdate)
		xpos = int(self.startXpos + (now()-self.startTime)*self.speed*self.label.rtlSign)
		self.move(xpos, 0)
		self.resize(1, 1)
		if xpos>screenWidth or xpos<-self.label.width:
			if self.index >= self.linesNum-1:
				self.finish()
				return
			else:
				self.index += 1
				self.updateLine()




if __name__=='__main__':
	import sys
	if len(sys.argv)<2:
		sys.exit(1)
	text = ' '.join(sys.argv[1:])
	msg = NoFillFloatingMsgWindow(text, speed=200, finishFunc=gtk.main_quit)
	#msg = FloatingMsg(text, speed=200, finishFunc=gtk.main_quit)
	msg.show()
	gtk.main()


