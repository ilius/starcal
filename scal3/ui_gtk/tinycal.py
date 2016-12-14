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

import sys, os

from math import pi
import os.path

from scal3.path import *
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, rtlSgn
from scal3 import core
from scal3.core import myRaise, getMonthName, getMonthLen
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk.color_utils import rgbToGdkColor
from scal3.ui_gtk.drawing import fillColor, newTextLayout


class WeekStatus(list):
	## int year
	## int weeknum
	## list[list] dates
	def __init__(self):
		list.__init__(self)

class TextObject():
	def __init__(self, parent, x, y, color, font, center=True):
		self.parent = parent
		self.x = x
		self.y = y
		self.resizable = False
		###############
		self.color = color
		self.layout = widget.create_pango_layout('')
		if font:
			self.setFont(font)
		self.center = center ## ???????????????????
		#self.xAlign = 0.5
		#self.yAlign = 0.5
	def draw(self, cr):
		if self.center:
			w, h = self.layout.get_pixel_size()
			cr.move_to(self.x - w/2.0, self.y - h/2.0)
		else:
			cr.move_to(self.x, self.y)
		fillColor(cr, self.color)
		show_layout(cr, self.layout)
	def setFont(self, font):
		self.layout.set_font_description(pfontEncode(font))
	def getText(self):
		raise NotImplementedError
	def contains(self, px, py):
		w, h = self.layout.get_pixel_size()
		if self.center:
			return -w/2.0 <= px-self.x < w/2.0 \
				 and -h/2.0 <= py-self.y < h/2.0
		else:
			return 0 <= px-self.x < w \
				 and 0 <= py-self.y < h

class YearObject(TextObject):
	def __init__(self, parent, mode, x=0, y=0, color=(0,0,0), font=None):
		TextObject.__init__(self, parent, x, y, color, font)
		self.mode = mode
	getText = lambda self: _(self.parent.dates[self.mode][2], self.mode)

class MonthObject(TextObject):
	def __init__(self, parent, mode, x=0, y=0, color=(0,0,0), font=None):
		TextObject.__init__(self, parent, x, y, color, font)
		self.mode = mode
	getText = lambda self: _(self.parent.dates[self.mode][1], self.mode)

class MonthNameObject(TextObject):
	def __init__(self, parent, mode, x=0, y=0, color=(0,0,0), font=None):
		TextObject.__init__(self, parent, x, y, color, font)
		self.mode = mode
	getText = lambda self: getMonthName(self.mode, self.parent.dates[self.mode][1])

class PlainStrObject(TextObject):
	def __init__(self, parent, text='', x=0, y=0, color=(0,0,0), font=None):
		TextObject.__init__(self, parent, x, y, color, font)
		self.text = text
	getText = lambda self: self.text



class TinyCal(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		self.set_title(core.APP_DESC+' Tiny')
		self.set_decorated(False)
		self.set_property('skip-taskbar-hint', None)
		self.set_role(core.APP_NAME+'-tiny')
		##################
		self.objects = []
	def startEditing(self):
		pass
	def endEditing(self):
		pass




















