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

from __future__ import annotations

from scal3 import logger

log = logger.get()


from typing import Never

from scal3 import locale_man
from scal3.locale_man import (
	floatEncode,
	numEncode,
	textNumDecode,
)

__all__ = [
	"ContainerField",
	"DayField",
	"Field",
	"FloatField",
	"HourField",
	"IntField",
	"MonthField",
	"NumField",
	"SingleCharField",
	"StrConField",
	"YearField",
	"Z60Field",
]


class Field:
	myKeys = set()

	def setDefault(self) -> None:
		pass

	def setValue(self, v) -> None:
		pass

	def getValue(self) -> None:  # noqa: PLR6301
		return None

	def plus(self, p) -> None:
		"""P is usually 1, -1, 10, -10."""

	def setText(self) -> None:
		pass

	def getText(self) -> None:
		pass

	def getMaxWidth(self) -> Never:
		raise NotImplementedError

	def getFieldAt(self, text, pos):  # noqa: ARG002
		return self


class NumField(Field):
	def setRange(self, minim, maxim) -> None:
		self.minim = minim
		self.maxim = maxim
		self.setValue(self.value)

	def setDefault(self) -> None:
		self.value = self.minim

	def setValue(self, v) -> None:
		if v < self.minim:
			v = self.minim
		elif v > self.maxim:
			v = self.maxim
		self.value = v

	def getValue(self):
		return self.value


class IntField(NumField):
	def __init__(self, minim, maxim, fill=0) -> None:
		self.minim = minim
		self.maxim = maxim
		self.fill = fill
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text) -> None:
		if not text:
			self.setDefault()
			return
		try:
			num = int(float(textNumDecode(text)))
		except ValueError:
			log.error(f"IntField: invalid {text = }")
			log.exception("")
			self.setDefault()
		else:
			self.setValue(num)

	def setValue(self, v):
		return NumField.setValue(self, int(v))

	def getText(self):
		return numEncode(self.value, fillZero=self.fill)

	def getMaxWidth(self):
		return max(
			len(str(self.minim)),
			len(str(self.maxim)),
		)

	def plus(self, p):
		return self.setValue(self.value + p)


class FloatField(NumField):
	def __init__(self, minim, maxim, digits) -> None:
		self.minim = minim
		self.maxim = maxim
		self.digits = digits
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text) -> None:
		if not text:
			self.setDefault()
			return
		try:
			num = float(textNumDecode(text))
		except ValueError:
			log.exception("")
			self.setDefault()
		else:
			self.setValue(num)

	def getText(self):
		return floatEncode(f"{self.value:.{self.digits}f}")

	def getMaxWidth(self):
		return max(
			len(f"{self.minim:.{self.digits}f}"),
			len(f"{self.maxim:.{self.digits}f}"),
		)

	def plus(self, p: float):
		return self.setValue(
			self.value + p,
		)


class YearField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, -9999, 9999)


class MonthField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 1, 12, 2)


class DayField(IntField):
	def __init__(self, pad=2) -> None:
		IntField.__init__(self, 1, 31, pad)

	def setMax(self, maxim) -> None:
		self.maxim = maxim
		# if self.value > maxim:
		# 	self.value = maxim


class HourField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 0, 24, 2)


class Z60Field(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 0, 59, 2)


class SingleCharField(Field):
	def __init__(self, *values) -> None:
		self.values = values
		self.myKeys = set(values)
		self.setDefault()

	def setDefault(self) -> None:
		self.value = 0

	def setValue(self, v) -> None:
		if v not in self.values:
			raise ValueError(
				f"SingleCharField.setValue: {v!r} is not a valid value",
			)
		self.value = v

	def getValue(self):
		return self.value

	def setText(self, text: str) -> None:
		self.setValue(text)

	def getText(self):
		return self.value

	def getMaxWidth(self) -> int:  # noqa: PLR6301
		return 1


class StrConField(Field):
	def __init__(self, text) -> None:
		self._text = text

	def getValue(self):
		return self._text

	def getText(self):
		return self._text

	def getMaxWidth(self):
		return len(self._text)


class ContainerField(Field):
	def __len__(self) -> int:
		return len(self.children)

	def __init__(self, sep, *children) -> None:
		self.sep = sep
		self.children = children
		for child in children:
			self.myKeys.update(child.myKeys)

	def setDefault(self) -> None:
		for child in self.children:
			child.setDefault()

	def setValue(self, value) -> None:
		if not isinstance(value, tuple | list):
			value = (value,)
		n = min(len(value), len(self))
		for i in range(n):
			self.children[i].setValue(value[i])

	def getValue(self):
		return [child.getValue() for child in self.children]

	def setText(self, text) -> None:
		parts = text.split(self.sep)
		n = len(self)
		pn = min(n, len(parts))
		# pn <= n
		for i in range(pn):
			self.children[i].setText(parts[i])
		for i in range(pn, n):
			self.children[i].setDefault()

	def getText(self):
		return self.sep.join([child.getText() for child in self.children])

	def getMaxWidth(self):
		return len(self.sep) * (len(self) - 1) + sum(
			child.getMaxWidth() for child in self.children
		)

	def getFieldAt(self, text, pos):
		if not self.children:
			return self
		fieldIndex = 0
		i = 0
		while 0 <= (i2 := text.find(self.sep, i + 1)) < pos:
			i = i2
			fieldIndex += 1
		return self.children[fieldIndex].getFieldAt(
			text[i:],
			pos - i,
		)

	# def getRegion(self, text, pos, fieldIndexPlus):
