#!/usr/bin/env python3
__all__ = [
	"rules",
	"notifiers",
	"occurrenceViews",
]

############################################

from scal3.utils import myRaise
from scal3 import event_lib


modPrefix = "scal3.ui_gtk.event"


def makeWidget(obj):
	"""
	obj is an instance of Event, EventRule, EventNotifier or EventGroup
	"""
	cls = obj.__class__
	try:
		WidgetClass = cls.WidgetClass
	except AttributeError:
		try:
			module = __import__(
				".".join([
					modPrefix,
					cls.tname,
					cls.name,
				]),
				fromlist=["WidgetClass"],
			)
			WidgetClass = cls.WidgetClass = module.WidgetClass
		except:
			myRaise()
			return
	widget = WidgetClass(obj)
	try:
		widget.show_all()
	except AttributeError:
		widget.show()
	widget.updateWidget()## FIXME
	return widget

def setActionFuncs(obj):
	"""
	obj is an instance of EventGroup
	"""
	cls = obj.__class__
	try:
		module = __import__(
			".".join([
				modPrefix,
				cls.tname,
				cls.name,
			]),
			fromlist=["WidgetClass"],
		)
	except:
		myRaise()
		return
	else:
		for actionName, actionFuncName in cls.actions:
			actionFunc = getattr(module, actionFuncName, None)
			if actionFunc is not None:
				print("setting %s.%s" % (cls.__name__, actionFuncName))
				setattr(cls, actionFuncName, actionFunc)



# Load accounts, groups and trash? FIXME
from os.path import join, isfile
from scal3.path import confDir
