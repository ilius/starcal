from __future__ import annotations

__all__ = ["classes"]


class ClassGroup(list):
	def __init__(self, tname: str) -> None:
		list.__init__(self)
		self.tname = tname
		self.names = []
		self.byName = {}
		self.byDesc = {}
		self.main = None

	def register(self, cls: type[ClassGroup]) -> type[ClassGroup]:
		assert cls.name
		cls.tname = self.tname
		self.append(cls)
		self.names.append(cls.name)
		self.byName[cls.name] = cls
		self.byDesc[cls.desc] = cls
		if hasattr(cls, "nameAlias"):
			self.byName[cls.nameAlias] = cls
		return cls

	def setMain(self, cls: type[ClassGroup]) -> type[ClassGroup]:
		self.main = cls
		return cls


class classes:
	rule = ClassGroup("rule")
	notifier = ClassGroup("notifier")
	event = ClassGroup("event")
	group = ClassGroup("group")
	account = ClassGroup("account")
