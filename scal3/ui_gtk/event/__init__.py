__all__ = [
	"makeWidget",
	"setActionFuncs",
]

# --------------------------------------------

from scal3 import logger

log = logger.get()


modPrefix = "scal3.ui_gtk.event"


def getWidgetClass(obj):
	cls = obj.__class__

	if hasattr(cls, "WidgetClass"):
		return cls.WidgetClass

	modulePath = f"{modPrefix}.{cls.tname}.{cls.name}"
	try:
		module = __import__(modulePath, fromlist=["WidgetClass"])
	except Exception:
		log.exception("")
		return
	WidgetClass = cls.WidgetClass = module.WidgetClass
	log.info(f"getWidgetClass: {cls.__name__} -> {modulePath} -> {WidgetClass}")
	return WidgetClass


def makeWidget(obj):
	"""Obj is an instance of Event, EventRule, EventNotifier or EventGroup."""
	WidgetClass = getWidgetClass(obj)
	if WidgetClass is None:
		return
	widget = WidgetClass(obj)
	try:
		widget.show_all()
	except AttributeError:
		widget.show()
	widget.updateWidget()  # FIXME
	return widget


def setActionFuncs(obj):
	"""Obj is an instance of EventGroup."""
	cls = obj.__class__
	try:
		module = __import__(
			f"{modPrefix}.{cls.tname}.{cls.name}",
			fromlist=["WidgetClass"],
		)
	except Exception:
		log.exception("")
		return
	else:
		for _actionName, actionFuncName in cls.actions:
			actionFunc = getattr(module, actionFuncName, None)
			if actionFunc is not None:
				setattr(cls, actionFuncName, actionFunc)


# FIXME: Load accounts, groups and trash?
