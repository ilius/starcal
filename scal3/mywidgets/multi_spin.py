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


from collections.abc import Sequence

from scal3 import locale_man
from scal3.locale_man import (
	floatEncode,
	numEncode,
	textNumDecode,
)

__all__ = [
	"ContainerField",
	"DateTimeFieldType",
	"DayField",
	"Field",
	"FloatField",
	"HourField",
	"IntField",
	"MonthField",
	"NumField",
	"StrConField",
	"YearField",
	"Z60Field",
]


class Field[T]:
	# ValueType: type[object]
	value: T

	myKeys: set[str] = set()

	def setDefault(self) -> None:
		raise NotImplementedError

	def setValue(self, value: T) -> None:
		raise NotImplementedError

	def getValue(self) -> T:  # noqa: PLR6301
		raise NotImplementedError

	def plus(self, p: T) -> None:
		"""P is usually 1, -1, 10, -10."""
		raise NotImplementedError

	def setText(self, text: str) -> None:
		raise NotImplementedError

	def getText(self) -> str:
		raise NotImplementedError

	def getMaxWidth(self) -> int:
		raise NotImplementedError

	def getFieldAt(self, text: str, pos: int) -> Field:  # noqa: ARG002
		raise NotImplementedError


class NumField[T: (int, float)](Field[T]):
	# ValueType: type[T]
	minim: T
	maxim: T

	def setRange(self, minim: T, maxim: T) -> None:
		self.minim = minim
		self.maxim = maxim
		self.setValue(self.value)

	def setDefault(self) -> None:
		self.value = self.minim

	def setValue(self, v: T) -> None:
		if v < self.minim:
			v = self.minim
		elif v > self.maxim:
			v = self.maxim
		self.value = v

	def getValue(self) -> T:
		return self.value

	def getFieldAt(self, text: str, pos: int) -> Field[T]:  # noqa: ARG002
		return self


class IntField(NumField[int]):
	# ValueType = int

	def __init__(self, minim: int, maxim: int, fill: int = 0) -> None:
		self.minim = minim
		self.maxim = maxim
		self.fill = fill
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text: str) -> None:
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

	def setValue(self, v: int) -> None:
		NumField.setValue(self, int(v))

	def getText(self) -> str:
		return numEncode(self.value, fillZero=self.fill)

	def getMaxWidth(self) -> int:
		return max(
			len(str(self.minim)),
			len(str(self.maxim)),
		)

	def plus(self, p: int) -> None:
		self.setValue(self.value + p)


class FloatField(NumField[float]):
	# ValueType = float

	def __init__(self, minim: float, maxim: float, digits: int) -> None:
		self.minim = minim
		self.maxim = maxim
		self.digits = digits
		self.myKeys = locale_man.getAvailableDigitKeys()
		self.setDefault()

	def setText(self, text: str) -> None:
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

	def getText(self) -> str:
		return floatEncode(f"{self.value:.{self.digits}f}")

	def getMaxWidth(self) -> int:
		return max(
			len(f"{self.minim:.{self.digits}f}"),
			len(f"{self.maxim:.{self.digits}f}"),
		)

	def plus(self, p: float) -> None:
		self.setValue(
			self.value + p,
		)


class YearField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, -9999, 9999)


class MonthField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 1, 12, 2)


class DayField(IntField):
	def __init__(self, pad: int = 2) -> None:
		IntField.__init__(self, 1, 31, pad)

	def setMax(self, maxim: int) -> None:
		self.maxim = maxim
		# if self.value > maxim:
		# 	self.value = maxim


class HourField(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 0, 24, 2)


class Z60Field(IntField):
	def __init__(self) -> None:
		IntField.__init__(self, 0, 59, 2)


class StrConField(Field[str]):
	# ValueType = str

	def __init__(self, text: str) -> None:
		self._text = text

	def getValue(self) -> str:
		return self._text

	def getText(self) -> str:
		return self._text

	def getMaxWidth(self) -> int:
		return len(self._text)


class ContainerField[T](Field[Sequence[T]]):
	# ValueType = Sequence[str]

	def __len__(self) -> int:
		return len(self.children)

	def __init__(
		self,
		sep: str,
		*children: Field[T],
	) -> None:
		self.sep = sep
		self.children = children
		for child in children:
			self.myKeys.update(child.myKeys)

	def setDefault(self) -> None:
		for child in self.children:
			child.setDefault()

	def setValue(self, value: Sequence[T]) -> None:
		assert isinstance(value, tuple | list), f"{value=}"
		n = min(len(value), len(self))
		for i in range(n):
			self.children[i].setValue(value[i])

	def getValue(self) -> list[T]:
		return [child.getValue() for child in self.children]

	def setText(self, text: str) -> None:
		parts = text.split(self.sep)
		n = len(self)
		pn = min(n, len(parts))
		# pn <= n
		for i in range(pn):
			self.children[i].setText(parts[i])
		for i in range(pn, n):
			self.children[i].setDefault()

	def getText(self) -> str:
		return self.sep.join([child.getText() for child in self.children])

	def getMaxWidth(self) -> int:
		return len(self.sep) * (len(self) - 1) + sum(
			child.getMaxWidth() for child in self.children
		)

	def getFieldAt(self, text: str, pos: int) -> Field[T]:
		assert self.children
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


type DateTimeFieldType = ContainerField[Sequence[int]]
