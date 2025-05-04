from __future__ import annotations

from scal3 import logger

log = logger.get()

from os.path import join
from time import localtime

from scal3.cal_types import gregorian
from scal3.path import modDir

__all__ = [
	"GREGORIAN",
	"calTypes",
	"convert",
	"getMonthLen",
	"getSysDate",
	"gregorian",
	"jd_to",
	"to_jd",
]
GREGORIAN = 0  # Gregorian (common calendar)
modules = [gregorian]


with open(join(modDir, "modules.list"), encoding="utf-8") as fp:
	for name in fp.read().split("\n"):
		name = name.strip()  # noqa: PLW2901
		if not name:
			continue
		if name.startswith("#"):
			continue
		# try:
		mod = __import__(f"scal3.cal_types.{name}", fromlist=[name])
		# mod = __import__(name) # Need to "sys.path.insert(0, modDir)" before
		# except:
		# 	log.exception("")
		# 	log.info(f"Could not load calendar modules {name!r}")
		# 	continue
		for attr in (
			"name",
			"desc",
			"origLang",
			"getMonthName",
			"getMonthNameAb",
			"minMonthLen",
			"maxMonthLen",
			"getMonthLen",
			"to_jd",
			"jd_to",
			"options",
			"save",
		):
			if not hasattr(mod, attr):
				log.error(
					"Invalid calendar module: "
					f"module {name!r} has no attribute {attr!r}\n",
				)
		# TODO: check argument names and count for funcs
		modules.append(mod)


class CalTypesHolder:
	byName = {mod.name: mod for mod in modules}
	names = [mod.name for mod in modules]
	# calOrigLang = [m.origLang for m in modules]

	def __len__(self) -> int:
		return len(self.names)

	def __init__(self) -> None:
		self.activeNames = ["gregorian"]
		self.inactiveNames = []
		self.update()

	# @attributemethod
	# def primary(self):
	# 	return self.active[0]

	def primaryModule(self):
		return modules[self.primary]

	def update(self) -> None:
		self.active = []
		self.inactive = []  # range(len(modules))
		remainingNames = self.names.copy()
		for name in self.activeNames:
			try:
				i = self.names.index(name)
			except ValueError:  # noqa: PERF203
				pass
			else:
				self.active.append(i)
				remainingNames.remove(name)
		# ----
		inactiveToRemove = []
		for name in self.inactiveNames:
			try:
				i = self.names.index(name)
			except ValueError:  # noqa: PERF203
				pass
			else:
				if i in self.active:
					inactiveToRemove.append(name)
				else:
					self.inactive.append(i)
					remainingNames.remove(name)
		for name in inactiveToRemove:
			self.inactiveNames.remove(name)
		# ----
		for name in remainingNames:
			try:
				i = self.names.index(name)
			except ValueError:  # noqa: PERF203
				pass
			else:
				self.inactive.append(i)
				self.inactiveNames.append(name)
		# ----
		self.primary = self.active[0]

	def __iter__(self):
		for i in self.active + self.inactive:
			yield modules[i]

	def iterIndexModule(self):
		for i in self.active + self.inactive:
			yield i, modules[i]

	def iterIndexModuleActive(self):
		for i in self.active:
			yield i, modules[i]

	def iterIndexModuleInactive(self):
		for i in self.inactive:
			yield i, modules[i]

	def __contains__(self, key) -> bool:
		if isinstance(key, str):
			return key in self.byName
		if isinstance(key, int):
			return 0 <= key < len(modules)
		raise TypeError(
			f"invalid key {key!r} given to {self.__class__.__name__!r}.__getitem__",
		)

	# returns (module, found) where found is bool
	def __getitem__(self, key):
		if isinstance(key, str):
			module = self.byName.get(key)
			if module is None:
				return None, False
			return module, True
		if isinstance(key, int):
			if key >= len(modules):
				return None, False
			return modules[key], True
		raise TypeError(
			f"invalid key {key!r} given to {self.__class__.__name__!r}.__getitem__",
		)

	def get(self, key, default=None):
		if isinstance(key, str):
			return self.byName.get(key, default)
		if isinstance(key, int):
			if key >= len(modules):
				return default
			return modules[key]
		raise TypeError(
			f"invalid key {key!r} given to {self.__class__.__name__!r}.__getitem__",
		)

	def getDesc(self, key):
		return self.get(key).desc

	@staticmethod
	def nameByIndex(index):
		if index >= len(modules):
			return ""
		return modules[index].name


calTypes = CalTypesHolder()


def jd_to(jd, target):
	return modules[target].jd_to(jd)


def to_jd(y, m, d, source):
	return modules[source].to_jd(y, m, d)


def convert(y, m, d, source, target):
	return (
		(y, m, d)
		if source == target
		else modules[target].jd_to(
			modules[source].to_jd(y, m, d),
		)
	)


def getMonthLen(year: int, month: int, calType: int) -> int:
	module, ok = calTypes[calType]
	if not ok:
		raise RuntimeError(f"cal type '{calType}' not found")
	return module.getMonthLen(year, month)


def getSysDate(calType) -> tuple[int, int, int]:
	if calType == GREGORIAN:
		return localtime()[:3]
	gy, gm, gd = localtime()[:3]
	return convert(gy, gm, gd, GREGORIAN, calType)


# def inputDateJd(msg: str) -> "int | None":
# 	date = inputDate(msg)
# 	if date:
# 		y, m, d = date
# 		return to_jd(y, m, d, GREGORIAN)
# 	return None
