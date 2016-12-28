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

from scal3.utils import toBytes, toStr
from scal3.utils import myRaise

from scal3 import locale_man
from scal3.locale_man import (
	numEncode,
	floatEncode,
	numDecode,
	textNumEncode,
	textNumDecode,
)

from scal3.cal_types import (
	to_jd,
	jd_to,
	convert,
)


class Field:
	myKeys = set()

	def setDefault(self):
		pass

	def setValue(self, v):
		pass

	def getValue(self):
		return None

	def plus(self, p):
		"""p is usually 1, -1, 10, -10"""
		pass

	def setText(self):
		pass

	def getText(self):
		pass

	def getMaxWidth(self):
		raise NotImplementedError

	def getFieldAt(self, text, pos):
		return self


class NumField(Field):
	def setRange(self, _min, _max):
		self._min = _min
		self._max = _max
		self.setValue(self.value)

	def setDefault(self):
		self.value = self._min

	def setValue(self, v):
		if v < self._min:
			v = self._min
		elif v > self._max:
			v = self._max
		self.value = v

	def getValue(self):
		return self.value


class IntField(NumField):
	def __init__(self, _min, _max, fill=0):
		self._min = _min
		self._max = _max
		self.fill = fill
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text):
		try:
			num = int(float(textNumDecode(text)))
		except:
			myRaise()
			self.setDefault()
		else:
			self.setValue(num)

	def setValue(self, v):
		return NumField.setValue(self, int(v))

	def getText(self):
		return numEncode(self.value, fillZero=self.fill)

	def getMaxWidth(self):
		return max(
			len(str(self._min)),
			len(str(self._max)),
		)

	def plus(self, p):
		return self.setValue(self.value + p)


class FloatField(NumField):
	def __init__(self, _min, _max, digits):
		self._min = _min
		self._max = _max
		self.digits = digits
		self.digDec = 10 ** digits
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text):
		try:
			num = float(textNumDecode(text))
		except:
			myRaise()
			self.setDefault()
		else:
			self.setValue(num)

	def getText(self):
		return floatEncode('%.*f' % (self.digits, self.value))

	def getMaxWidth(self):
		return max(
			len('%.*f' % (self.digits, self._min)),
			len('%.*f' % (self.digits, self._max)),
		)

	def plus(self, p):
		return self.setValue(
			self.value + float(p) / self.digDec
		)


class YearField(IntField):
	def __init__(self):
		IntField.__init__(self, -9999, 9999)


class MonthField(IntField):
	def __init__(self):
		IntField.__init__(self, 1, 12, 2)


class DayField(IntField):
	def __init__(self, pad=2):
		IntField.__init__(self, 1, 31, pad)

	def setMax(self, _max):
		self._max = _max
		#if self.value > _max:
		#	self.value = _max


class HourField(IntField):
	def __init__(self):
		IntField.__init__(self, 0, 24, 2)


class Z60Field(IntField):
	def __init__(self):
		IntField.__init__(self, 0, 59, 2)


class SingleCharField(Field):
	def __init__(self, *values):
		self.values = values
		self.myKeys = set(values)
		self.setDefault()

	def setDefault(self):
		self.value = 0

	def setValue(self, v):
		if v not in self.values:
			raise ValueError(
				'SingleCharField.setValue: %r is not a valid value' % v
			)
		self.value = v

	def getValue(self):
		return self.value

	def setText(text):
		return self.setValue(text)

	def getText(self):
		return self.value

	def getMaxWidth(self):
		return 1


class StrConField(Field):
	def __init__(self, text):
		self._text = text

	def getValue(self):
		return self._text

	def getText(self):
		return self_text

	def getMaxWidth(self):
		return len(self._text)


class ContainerField(Field):
	def __len__(self):
		return len(self.children)

	def __init__(self, sep, *children):
		self.sep = sep
		self.children = children
		for child in children:
			self.myKeys.update(child.myKeys)

	def setDefault(self):
		for child in self.children:
			child.setDefault()

	def setValue(self, value):
		if not isinstance(value, (tuple, list)):
			value = (value,)
		n = min(len(value), len(self))
		for i in range(n):
			self.children[i].setValue(value[i])

	def getValue(self):
		return [
			child.getValue()
			for child in self.children
		]

	def setText(self, text):
		parts = text.split(self.sep)
		n = len(self)
		pn = min(n, len(parts))
		## pn <= n
		for i in range(pn):
			self.children[i].setText(parts[i])
		for i in range(pn, n):
			self.children[i].setDefault()

	def getText(self):
		return self.sep.join([
			child.getText()
			for child in self.children
		])

	def getMaxWidth(self):
		return len(self.sep) * (len(self) - 1) + sum(
			child.getMaxWidth()
			for child in self.children
		)

	def getFieldAt(self, text, pos):
		if not self.children:
			return self
		fieldIndex = 0
		i = 0
		n = len(text)
		fn = len(self)
		while True:
			i2 = text.find(self.sep, i + 1)
			if i2 == -1 or i2 >= pos:
				break
			i = i2
			fieldIndex += 1
		return self.children[fieldIndex].getFieldAt(
			text[i:],
			pos - i,
		)

	#def getRegion(self, text, pos, fieldIndexPlus):
