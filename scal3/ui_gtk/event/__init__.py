from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from scal3 import logger

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import Gtk as gtk

	from scal3.event_lib.pytypes import BaseClassType, EventGroupType

__all__ = [
	"EventWidgetType",
	"getWidgetClass",
	"makeWidget",
	"setActionFuncs",
]


log = logger.get()


modPrefix = "scal3.ui_gtk.event"


class ModuleType(Protocol):
	WidgetClass: type[gtk.Widget]


def load_account_google() -> ModuleType:
	from scal3.ui_gtk.event.account import google

	return google  # type: ignore[return-value]


def load_account_starcal() -> ModuleType:
	from scal3.ui_gtk.event.account import starcal

	return starcal  # type: ignore[return-value]


def load_event_allDayTask() -> ModuleType:
	from scal3.ui_gtk.event.event import allDayTask

	return allDayTask  # type: ignore[return-value]


def load_event_custom() -> ModuleType:
	from scal3.ui_gtk.event.event import custom

	return custom  # type: ignore[return-value]


def load_event_dailyNote() -> ModuleType:
	from scal3.ui_gtk.event.event import dailyNote

	return dailyNote  # type: ignore[return-value]


def load_event_largeScale() -> ModuleType:
	from scal3.ui_gtk.event.event import largeScale

	return largeScale  # type: ignore[return-value]


def load_event_lifetime() -> ModuleType:
	from scal3.ui_gtk.event.event import lifetime

	return lifetime  # type: ignore[return-value]


def load_event_monthly() -> ModuleType:
	from scal3.ui_gtk.event.event import monthly

	return monthly  # type: ignore[return-value]


def load_event_task() -> ModuleType:
	from scal3.ui_gtk.event.event import task

	return task  # type: ignore[return-value]


def load_event_universityClass() -> ModuleType:
	from scal3.ui_gtk.event.event import universityClass

	return universityClass  # type: ignore[return-value]


def load_event_universityExam() -> ModuleType:
	from scal3.ui_gtk.event.event import universityExam

	return universityExam  # type: ignore[return-value]


def load_event_weekly() -> ModuleType:
	from scal3.ui_gtk.event.event import weekly

	return weekly  # type: ignore[return-value]


def load_event_yearly() -> ModuleType:
	from scal3.ui_gtk.event.event import yearly

	return yearly  # type: ignore[return-value]


def load_group_group() -> ModuleType:
	from scal3.ui_gtk.event.group import group

	return group  # type: ignore[return-value]


def load_group_largeScale() -> ModuleType:
	from scal3.ui_gtk.event.group import largeScale

	return largeScale  # type: ignore[return-value]


def load_group_lifetime() -> ModuleType:
	from scal3.ui_gtk.event.group import lifetime

	return lifetime  # type: ignore[return-value]


def load_group_noteBook() -> ModuleType:
	from scal3.ui_gtk.event.group import noteBook

	return noteBook  # type: ignore[return-value]


def load_group_taskList() -> ModuleType:
	from scal3.ui_gtk.event.group import taskList

	return taskList  # type: ignore[return-value]


def load_group_universityTerm() -> ModuleType:
	from scal3.ui_gtk.event.group import universityTerm

	return universityTerm  # type: ignore[return-value]


def load_group_vcs() -> ModuleType:
	from scal3.ui_gtk.event.group import vcs

	return vcs  # type: ignore[return-value]


def load_group_vcsDailyStat() -> ModuleType:
	from scal3.ui_gtk.event.group import vcsDailyStat

	return vcsDailyStat  # type: ignore[return-value]


def load_group_vcsTag() -> ModuleType:
	from scal3.ui_gtk.event.group import vcsTag

	return vcsTag  # type: ignore[return-value]


def load_group_yearly() -> ModuleType:
	from scal3.ui_gtk.event.group import yearly

	return yearly  # type: ignore[return-value]


def load_notifier_alarm() -> ModuleType:
	from scal3.ui_gtk.event.notifier import alarm

	return alarm  # type: ignore[return-value]


def load_notifier_floatingMsg() -> ModuleType:
	from scal3.ui_gtk.event.notifier import floatingMsg

	return floatingMsg  # type: ignore[return-value]


def load_notifier_windowMsg() -> ModuleType:
	from scal3.ui_gtk.event.notifier import windowMsg

	return windowMsg  # type: ignore[return-value]


def load_rule_cycleLen() -> ModuleType:
	from scal3.ui_gtk.event.rule import cycleLen

	return cycleLen  # type: ignore[return-value]


def load_rule_date() -> ModuleType:
	from scal3.ui_gtk.event.rule import date

	return date  # type: ignore[return-value]


def load_rule_dateTime() -> ModuleType:
	from scal3.ui_gtk.event.rule import dateTime

	return dateTime  # type: ignore[return-value]


def load_rule_day() -> ModuleType:
	from scal3.ui_gtk.event.rule import day

	return day  # type: ignore[return-value]


def load_rule_dayTime() -> ModuleType:
	from scal3.ui_gtk.event.rule import dayTime

	return dayTime  # type: ignore[return-value]


def load_rule_dayTimeRange() -> ModuleType:
	from scal3.ui_gtk.event.rule import dayTimeRange

	return dayTimeRange  # type: ignore[return-value]


def load_rule_duration() -> ModuleType:
	from scal3.ui_gtk.event.rule import duration

	return duration  # type: ignore[return-value]


def load_rule_ex_dates() -> ModuleType:
	from scal3.ui_gtk.event.rule import ex_dates

	return ex_dates  # type: ignore[return-value]


def load_rule_month() -> ModuleType:
	from scal3.ui_gtk.event.rule import month

	return month  # type: ignore[return-value]


def load_rule_weekDay() -> ModuleType:
	from scal3.ui_gtk.event.rule import weekDay

	return weekDay  # type: ignore[return-value]


def load_rule_weekMonth() -> ModuleType:
	from scal3.ui_gtk.event.rule import weekMonth

	return weekMonth  # type: ignore[return-value]


def load_rule_weekNumMode() -> ModuleType:
	from scal3.ui_gtk.event.rule import weekNumMode

	return weekNumMode  # type: ignore[return-value]


def load_rule_year() -> ModuleType:
	from scal3.ui_gtk.event.rule import year

	return year  # type: ignore[return-value]


widgetClassLoaderByName: dict[str, Callable[[], ModuleType]] = {
	"account.google": load_account_google,
	"account.starcal": load_account_starcal,
	"event.allDayTask": load_event_allDayTask,
	"event.custom": load_event_custom,
	"event.dailyNote": load_event_dailyNote,
	"event.largeScale": load_event_largeScale,
	"event.lifetime": load_event_lifetime,
	"event.monthly": load_event_monthly,
	"event.task": load_event_task,
	"event.universityClass": load_event_universityClass,
	"event.universityExam": load_event_universityExam,
	"event.weekly": load_event_weekly,
	"event.yearly": load_event_yearly,
	"group.group": load_group_group,
	"group.largeScale": load_group_largeScale,
	"group.lifetime": load_group_lifetime,
	"group.noteBook": load_group_noteBook,
	"group.taskList": load_group_taskList,
	"group.universityTerm": load_group_universityTerm,
	"group.vcs": load_group_vcs,
	"group.vcsDailyStat": load_group_vcsDailyStat,
	"group.vcsTag": load_group_vcsTag,
	"group.yearly": load_group_yearly,
	"notifier.alarm": load_notifier_alarm,
	"notifier.floatingMsg": load_notifier_floatingMsg,
	"notifier.windowMsg": load_notifier_windowMsg,
	"rule.cycleLen": load_rule_cycleLen,
	"rule.date": load_rule_date,
	"rule.dateTime": load_rule_dateTime,
	"rule.day": load_rule_day,
	"rule.dayTime": load_rule_dayTime,
	"rule.dayTimeRange": load_rule_dayTimeRange,
	"rule.duration": load_rule_duration,
	"rule.ex_dates": load_rule_ex_dates,
	"rule.month": load_rule_month,
	"rule.weekDay": load_rule_weekDay,
	"rule.weekMonth": load_rule_weekMonth,
	"rule.weekNumMode": load_rule_weekNumMode,
	"rule.year": load_rule_year,
}


def getWidgetClass(obj: BaseClassType) -> type[gtk.Widget] | None:
	cls = obj.__class__

	if hasattr(cls, "WidgetClass"):
		return cls.WidgetClass  # type: ignore[no-any-return]

	try:
		module = widgetClassLoaderByName[f"{cls.tname}.{cls.name}"]()
	except Exception:
		log.exception("")
		return None
	WidgetClass: type[gtk.Widget] = module.WidgetClass
	cls.WidgetClass = WidgetClass
	log.info(
		f"getWidgetClass: {cls.__name__} -> {cls.tname}.{cls.name} -> {WidgetClass}"
	)
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
	widget: EventWidgetType = WidgetClass(obj)  # type: ignore[assignment, arg-type]
	widget.show()
	widget.updateWidget()
	return widget


def setActionFuncs(obj: EventGroupType) -> None:
	"""Obj is an instance of EventGroup."""
	cls = obj.__class__
	module = widgetClassLoaderByName[f"{cls.tname}.{cls.name}"]()
	for _actionName, actionFuncName in cls.actions:
		actionFunc = getattr(module, actionFuncName, None)
		# log.info(f"setActionFuncs: {module.__name__}: {actionFunc}")
		if actionFunc is not None:
			setattr(cls, actionFuncName, actionFunc)


# FIXME: Load accounts, groups and trash?
