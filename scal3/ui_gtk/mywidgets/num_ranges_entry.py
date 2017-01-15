# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

import sys
import os
import time

from scal3.utils import (
	toBytes,
	toStr,
	numRangesEncode,
	numRangesDecode,
)
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import (
	numDecode,
	textNumEncode,
	textNumDecode,
)

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *


def myRaise():
	i = sys.exc_info()
	try:
		print("line %s: %s: %s" % (
			i[2].tb_lineno,
			i[0].__name__,
			i[1],
		))
	except:
		print(i)


@registerType
class NumRangesEntry(gtk.Entry):
	def __init__(self, _min, _max, page_inc=10):
		self._min = _min
		self._max = _max
		self.digs = locale_man.digits[locale_man.langSh]
		self.page_inc = page_inc
		####
		gtk.Entry.__init__(self)
		self.connect("key-press-event", self.keyPress)
		self.set_direction(gtk.TextDirection.LTR)
		self.set_alignment(0.5)

	def insertText(self, s, clearSeceltion=True):
		selection = self.get_selection_bounds()
		if selection and clearSeceltion:
			start, end = selection
			text = toStr(self.get_text())
			text = text[:start] + s + text[end:]
			self.set_text(text)
			self.set_position(start + len(s))
		else:
			pos = self.get_position()
			self.insert_text(s, pos)
			self.set_position(pos + len(s))

	def numPlus(self, plus):
		pos = self.get_position()
		text = toStr(self.get_text())
		n = len(text)
		commaI = text.rfind(",", 0, pos)
		if commaI == -1:
			startI = 0
		else:
			if text[commaI + 1] == " ":
				startI = commaI + 2
			else:
				startI = commaI + 1
		nextCommaI = text.find(",", pos)
		if nextCommaI == -1:
			endI = n
		else:
			endI = nextCommaI
		dashI = text.find("-", startI, endI)
		if dashI != -1:
			#print("dashI=%r"%dashI)
			if pos < dashI:
				endI = dashI
			else:
				startI = dashI + 1
		thisNumStr = text[startI:endI]
		#print(startI, endI, thisNumStr)
		if thisNumStr:
			thisNum = numDecode(thisNumStr)
			newNum = thisNum + plus
			if not self._min <= newNum <= self._max:
				return
		else:
			if plus > 0:
				newNum = self._max
			else:
				newNum = self._min
		newNumStr = _(newNum)
		newText = text[:startI] + newNumStr + text[endI:]
		self.set_text(newText)
		#print("new end index", endI - len(thisNumStr) + len(newNumStr))
		self.set_position(pos)
		self.select_region(
			startI,
			endI - len(thisNumStr) + len(newNumStr),
		)

	def keyPress(self, obj, gevent):
		kval = gevent.keyval
		kname = gdk.keyval_name(gevent.keyval).lower()
		#print(kval, kname)
		if kname in (
			"tab",
			"escape",
			"backspace",
			"delete",
			"insert",
			"home",
			"end",
			"control_l",
			"control_r",
			"iso_next_group",
		):
			return False
		elif kname == "return":
			self.validate()
			return False
		elif kname == "up":
			self.numPlus(1)
		elif kname == "down":
			self.numPlus(-1)
		elif kname == "page_up":
			self.numPlus(self.page_inc)
		elif kname == "page_down":
			self.numPlus(-self.page_inc)
		elif kname == "left":
			return False  # FIXME
		elif kname == "right":
			return False  # FIXME
		#elif kname in ("braceleft", "bracketleft"):
		#	self.insertText(u"[")
		#elif kname in ("braceright", "bracketright"):
		#	self.insertText(u"]")
		elif kname in ("comma", "arabic_comma"):
			self.insertText(", ", False)
		elif kname == "minus":
			pos = self.get_position()
			text = toStr(self.get_text())
			n = len(text)
			if pos == n:
				start = numDecode(text.split(",")[-1].strip())
				self.insertText("-" + _(start + 2), False)
			else:
				self.insertText("-", False)
		elif ord("0") <= kval <= ord("9"):
			self.insertText(self.digs[kval - ord("0")])
		else:
			uniVal = gdk.keyval_to_unicode(kval)
			#print("uniVal=%r"%uniVal)
			if uniVal != 0:
				ch = chr(uniVal)
				#print("ch=%r"%ch)
				if ch in self.digs:
					self.insertText(ch)
				if gevent.get_state() & gdk.ModifierType.CONTROL_MASK:
					# Shortcuts like Ctrl + [A, C, X, V]
					return False
			else:
				print(kval, kname)
		return True

	def getValues(self):
		return numRangesDecode(
			textNumDecode(self.get_text())
		)

	def setValues(self, values):
		return self.set_text(
			textNumEncode(
				numRangesEncode(values),
				changeSpecialChars=False,
			)
		)

	def validate(self):
		return self.setValues(self.getValues())


if __name__ == "__main__":
	from scal3 import core
	###
	entry = NumRangesEntry(0, 9999)
	win = gtk.Dialog(parent=None)
	win.vbox.add(entry)
	win.vbox.show_all()
	win.resize(100, 40)
	win.run()
