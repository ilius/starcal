import sys
from os.path import join
from time import localtime

from scal3.cal_types import gregorian
from scal3.path import *
from scal3.utils import printError

DATE_GREG = 0  # Gregorian (common calendar)
modules = [gregorian]


def myRaise():
	i = sys.exc_info()
	sys.stdout.write("File \"%s\", line %s: %s: %s\n" % (
		__file__,
		i[2].tb_lineno,
		i[0].__name__,
		i[1],
	))


for name in open(join(modDir, "modules.list")).read().split("\n"):
	name = name.strip()
	if not name:
		continue
	if name.startswith("#"):
		continue
	#try:
	mod = __import__("scal3.cal_types.%s" % name, fromlist=[name])
	#mod = __import__(name) # Need to "sys.path.insert(0, modDir)" before
	#except:
	#	myRaise()
	#	print("Could not load calendar modules "%s"" % name)
	#	continue
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
			printError(
				"Invalid calendar module: " +
				"module \"%s\" has no attribute \"%s\"\n" % (name, attr)
			)
	modules.append(mod)


class CalTypesHolder:
	byName = {
		mod.name: mod for mod in modules
	}
	names = [
		mod.name for mod in modules
	]
	# calOrigLang = [m.origLang for m in modules]

	def __len__(self):
		return len(self.names)

	def __init__(self):
		self.activeNames = ["gregorian"]
		self.inactiveNames = []
		self.update()

	#@attributemethod
	#def primary(self):
	#	return self.active[0]

	def primaryModule(self):
		return modules[self.primary]

	def update(self):
		self.active = []
		self.inactive = []  # range(len(modules))
		remainingNames = self.names[:]
		for name in self.activeNames:
			try:
				i = self.names.index(name)
			except ValueError:
				pass
			else:
				self.active.append(i)
				remainingNames.remove(name)
		####
		inactiveToRemove = []
		for name in self.inactiveNames:
			try:
				i = self.names.index(name)
			except ValueError:
				pass
			else:
				if i in self.active:
					inactiveToRemove.append(name)
				else:
					self.inactive.append(i)
					remainingNames.remove(name)
		for name in inactiveToRemove:
			self.inactiveNames.remove(name)
		####
		for name in remainingNames:
			try:
				i = self.names.index(name)
			except ValueError:
				pass
			else:
				self.inactive.append(i)
				self.inactiveNames.append(name)
		####
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

	def allIndexes(self):
		return self.active + self.inactive

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.byName[key]
		if isinstance(key, int):
			return modules[key]
		else:
			raise TypeError("invalid key %r given to %s.__getitem__" % (
				key,
				self.__class__.__name__,
			))


calTypes = CalTypesHolder()


def jd_to(jd, target):
	return modules[target].jd_to(jd)


def to_jd(y, m, d, source):
	return modules[source].to_jd(y, m, d)


def convert(y, m, d, source, target):
	return (
		(y, m, d) if source == target
		else modules[target].jd_to(
			modules[source].to_jd(y, m, d)
		)
	)


def getSysDate(mode):
	if mode == DATE_GREG:
		return localtime()[:3]
	else:
		gy, gm, gd = localtime()[:3]
		return convert(gy, gm, gd, DATE_GREG, mode)
