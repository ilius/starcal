import typing

from scal3.s_object import SObj


class BasePlugin(SObj):
	name: "str | None"
	external: bool
	loaded: bool
	params: "typing.Sequence[str]"
	essentialParams: "typing.Sequence[str]"

	def getArgs(self):
		...

	def __bool__(self):
		...

	def __init__(
		self,
		_file,
	):
		...

	def getData(self):
		...

	def setData(self, data):
		...

	def clear(self):
		...

	def load(self):
		...

	def getText(self, year, month, day):
		...

	def updateCell(self, c):
		...

	def onCurrentDateChange(self, gdate):
		...

	def exportToIcs(self, fileName, startJd, endJd):
		...
