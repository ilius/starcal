from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from scal3 import logger

if TYPE_CHECKING:
	from gi.repository import Gtk as gtk

	from scal3.event_lib.pytypes import BaseClassType, EventGroupType

__all__ = [
	"EventWidgetType",
	"makeWidget",
	"setActionFuncs",
]


log = logger.get()


modPrefix = "scal3.ui_gtk.event"


def getWidgetClass(obj: BaseClassType) -> type[gtk.Widget] | None:
	cls = obj.__class__

	if hasattr(cls, "WidgetClass"):
		return cls.WidgetClass

	modulePath = f"{modPrefix}.{cls.tname}.{cls.name}"
	try:
		module = __import__(modulePath, fromlist=["WidgetClass"])
	except Exception:
		log.exception("")
		return None
	WidgetClass = cls.WidgetClass = module.WidgetClass
	log.info(f"getWidgetClass: {cls.__name__} -> {modulePath} -> {WidgetClass}")
	return WidgetClass


class EventWidgetType(Protocol):
	w: gtk.Widget

	def updateWidget(self) -> None: ...
	def updateVars(self) -> None: ...
	def show(self) -> None: ...
	def destroy(self) -> None: ...


def makeWidget(obj: BaseClassType) -> EventWidgetType | None:
	"""Obj is an instance of Event, EventRule, EventNotifier or EventGroup."""
	WidgetClass = getWidgetClass(obj)
	if WidgetClass is None:
		return None
	widget: EventWidgetType = WidgetClass(obj)  # type: ignore
	widget.show()
	widget.updateWidget()
	return widget


def setActionFuncs(obj: EventGroupType) -> None:
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
