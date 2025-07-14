from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import event_lib, locale_man, ui
from scal3.event_lib import ev
from scal3.event_lib.groups import EventGroup
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gtk, pack
from scal3.ui_gtk.event import common, makeWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.utils import dialog_add_button, showInfo

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType

__all__ = ["EventEditorDialog", "addNewEvent"]


class EventEditorDialog(Dialog):
	def __init__(
		self,
		event: EventType,
		typeChangable: bool = True,
		isNew: bool = False,
		useSelectedDate: bool = False,
		title: str = "",
		transient_for: gtk.Window | None = None,
	) -> None:
		checkEventsReadOnly()
		assert event.parent is not None
		Dialog.__init__(self, title=title, transient_for=transient_for)
		# self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		self.isNew = isNew
		# self.connect("delete-event", lambda obj, e: self.destroy())
		# self.resize(800, 600)
		# ---
		dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Save"),
		)
		# ---
		self.connect("response", lambda _w, _e: self.hide())
		# ---
		self.activeWidget = None
		assert isinstance(event.parent, EventGroup), f"{event.parent=}"
		self._group: EventGroupType = event.parent
		self.eventTypeOptions = list(self._group.acceptsEventTypes)
		# ----
		if event.name not in self.eventTypeOptions:
			self.eventTypeOptions.append(event.name)
		eventTypeIndex = self.eventTypeOptions.index(event.name)
		# ----
		self._event = event
		# -------
		if isNew and not event.timeZone:
			event.timeZone = str(locale_man.localTz)  # why? FIXME
		# -------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(
			hbox,
			gtk.Label(
				label=_("Group") + ": " + self._group.title,
			),
		)
		hbox.show_all()
		pack(self.vbox, hbox)
		# -------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Event Type")))
		if typeChangable:
			combo = gtk.ComboBoxText()
			for tmpEventType in self.eventTypeOptions:
				combo.append_text(event_lib.classes.event.byName[tmpEventType].desc)
			pack(hbox, combo)
			# ----
			combo.set_active(eventTypeIndex)
			# ----
			# self.activeWidget = makeWidget(event)
			combo.connect("changed", self.typeChanged)
			self.comboEventType = combo
		else:
			pack(hbox, gtk.Label(label=":  " + event.desc))
		pack(hbox, gtk.Label(), 1, 1)
		hbox.show_all()
		pack(self.vbox, hbox)
		# -----
		if useSelectedDate:
			self._event.setJd(ui.cells.current.jd)
		activeWidget = self.activeWidget = makeWidget(event)
		if self.isNew and isinstance(activeWidget, common.WidgetClass):
			activeWidget.focusSummary()
		pack(self.vbox, activeWidget, 1, 1)  # type: ignore[arg-type]
		self.vbox.show()

	def replaceExistingEvent(self, eventType: str) -> None:
		assert isinstance(self._group, EventGroup), f"{self._group=}"
		oldEvent = self._event
		newEvent = self._group.create(eventType)
		# ---
		newEvent.changeCalType(oldEvent.calType)
		newEvent.copyFrom(oldEvent)
		# ---
		newEvent.setId(oldEvent.id)
		oldEvent.invalidate()
		self._event = newEvent

	def replaceEventWithType(self, eventType: str) -> None:
		if not self.isNew:
			self.replaceExistingEvent(eventType)
			return

		restoreDict = {}
		if self._event:
			if self._event.summary and self._event.summary != self._event.desc:
				restoreDict["summary"] = self._event.summary
			if self._event.description:
				restoreDict["description"] = self._event.description
		self._event = self._group.create(eventType)
		for attr, value in restoreDict.items():
			setattr(self._event, attr, value)

	def typeChanged(self, combo: gtk.ComboBox) -> None:
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		eventType = self.eventTypeOptions[combo.get_active()]
		self.replaceEventWithType(eventType)
		self._group.updateCache(self._event)  # needed? FIXME
		activeWidget = makeWidget(self._event)
		assert isinstance(activeWidget, common.WidgetClass), f"{activeWidget=}"
		if self.isNew:
			activeWidget.focusSummary()
		pack(self.vbox, activeWidget, 1, 1)
		# activeWidget.calTypeComboChanged()-- apearantly not needed
		self.activeWidget = activeWidget

	def run2(self) -> EventType | None:
		assert self.activeWidget is not None

		parentWin = self.get_transient_for()
		if Dialog.run(self) != gtk.ResponseType.OK:
			# try:
			# 	filesBox = self.activeWidget.filesBox  # type: ignore[union-attr]
			# except AttributeError:
			# 	pass
			# else:
			# 	filesBox.removeNewFiles()
			if parentWin is not None:
				parentWin.present()
			return None
		self.activeWidget.updateVars()

		event = self._event
		group = event.parent
		assert isinstance(group, EventGroup), f"{group=}"
		event.afterModifyBasic()
		event.save()
		if self.isNew:
			group.add(event)
			group.save()
		event.afterModifyInGroup()
		ev.lastIds.save()
		ev.notif.checkEvent(group, event)

		self.destroy()
		# -----
		if event.isSingleOccur:
			occur = event.calcEventOccurrenceIn(
				group.startJd,
				group.endJd,
			)
			if not occur:
				msg = _(
					"This event is outside of date range specified in "
					"it's group. You probably need to edit group "
					'"{groupTitle}" and change "Start" or "End" values',
				).format(groupTitle=group.title)
				showInfo(msg)
		# -----
		if parentWin is not None:
			parentWin.present()
		# -----
		return event


def addNewEvent(
	group: EventGroupType,
	eventType: str,
	typeChangable: bool = False,
	useSelectedDate: bool = False,
	title: str = "",
	transient_for: gtk.Window | None = None,
) -> EventType | None:
	event = group.create(eventType)
	if eventType == "custom":  # FIXME
		typeChangable = True
	return EventEditorDialog(
		event,
		typeChangable=typeChangable,
		isNew=True,
		useSelectedDate=useSelectedDate,
		title=title,
		transient_for=transient_for,
	).run2()
