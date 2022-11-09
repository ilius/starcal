#!/usr/bin/env python3
__all__ = [
	"rules",
	"notifiers",
	"occurrenceViews",
]

############################################

from scal3 import logger
log = logger.get()

from scal3 import event_lib


modPrefix = "scal3.ui_gtk.event"


def getWidgetClass(obj):
	cls = obj.__class__

	if hasattr(cls, "WidgetClass"):
		return cls.WidgetClass

	modulePath = ".".join([
		modPrefix,
		cls.tname,
		cls.name,
	])
	try:
		module = __import__(modulePath, fromlist=["WidgetClass"])
	except Exception:
		log.exception("")
		return
	WidgetClass = cls.WidgetClass = module.WidgetClass
	log.info(f"getWidgetClass: {cls.__name__} -> {modulePath} -> {WidgetClass}")
	return WidgetClass


def makeWidget(obj):
	"""
	obj is an instance of Event, EventRule, EventNotifier or EventGroup
	"""
	WidgetClass = getWidgetClass(obj)
	if WidgetClass is None:
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
	except Exception:
		log.exception("")
		return
	else:
		for actionName, actionFuncName in cls.actions:
			actionFunc = getattr(module, actionFuncName, None)
			if actionFunc is not None:
				setattr(cls, actionFuncName, actionFunc)


# FIXME: Load accounts, groups and trash?
from os.path import join, isfile
from scal3.path import confDir
