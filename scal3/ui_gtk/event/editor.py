from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import event_lib, locale_man, ui
from scal3.event_lib import ev
from scal3.event_lib.groups import EventGroup
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.utils import dialog_add_button, showInfo

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType

__all__ = ["EventEditorDialog", "addNewEvent"]


class EventEditorDialog(gtk.Dialog):
	def __init__(
		self,
		event: EventType,
		typeChangable: bool = True,
		isNew: bool = False,
		useSelectedDate: bool = False,
		**kwargs,
	) -> None:
		checkEventsReadOnly()
		assert event.parent is not None
		gtk.Dialog.__init__(self, **kwargs)
		# self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		self.isNew = isNew
		# self.connect("delete-event", lambda obj, e: self.destroy())
		# self.resize(800, 600)
		# ---
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
		)
		# ---
		self.connect("response", lambda _w, _e: self.hide())
		# ---
		self.activeWidget = None
		assert isinstance(event.parent, EventGroup)
		self._group = event.parent
		self.eventTypeOptions = list(self._group.acceptsEventTypes)
		# ----
		if event.name not in self.eventTypeOptions:
			self.eventTypeOptions.append(event.name)
		eventTypeIndex = self.eventTypeOptions.index(event.name)
		# ----
		self.event = event
		# -------
		if isNew and not event.timeZone:
			event.timeZone = str(locale_man.localTz)  # why? FIXME
		# -------
		hbox = HBox()
		pack(
			hbox,
			gtk.Label(
				label=_("Group") + ": " + self._group.title,
			),
		)
		hbox.show_all()
		pack(self.vbox, hbox)
		# -------
		hbox = HBox()
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
			self.event.setJd(ui.cells.current.jd)
		self.activeWidget = makeWidget(event)
		assert self.activeWidget is not None
		if self.isNew:
			self.activeWidget.focusSummary()
		pack(self.vbox, self.activeWidget, 1, 1)
		self.vbox.show()

	def replaceExistingEvent(self, eventType: str) -> None:
		assert isinstance(self._group, EventGroup)
		oldEvent = self.event
		newEvent = self._group.create(eventType)
		# ---
		newEvent.changeCalType(oldEvent.calType)
		newEvent.copyFrom(oldEvent)
		# ---
		newEvent.setId(oldEvent.id)
		oldEvent.invalidate()
		self.event = newEvent

	def replaceEventWithType(self, eventType: str) -> None:
		if not self.isNew:
			self.replaceExistingEvent(eventType)
			return

		restoreDict = {}
		if self.event:
			if self.event.summary and self.event.summary != self.event.desc:
				restoreDict["summary"] = self.event.summary
			if self.event.description:
				restoreDict["description"] = self.event.description
		self.event = self._group.create(eventType)
		for attr, value in restoreDict.items():
			setattr(self.event, attr, value)

	def typeChanged(self, combo: gtk.ComboBox) -> None:
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		eventType = self.eventTypeOptions[combo.get_active()]
		self.replaceEventWithType(eventType)
		self._group.updateCache(self.event)  # needed? FIXME
		self.activeWidget = makeWidget(self.event)
		assert self.activeWidget is not None
		if self.isNew:
			self.activeWidget.focusSummary()
		pack(self.vbox, self.activeWidget, 1, 1)
		# self.activeWidget.calTypeComboChanged()-- apearantly not needed

	def run(self) -> EventType | None:
		assert self.activeWidget is not None

		parentWin = self.get_transient_for()
		if gtk.Dialog.run(self) != gtk.ResponseType.OK:
			try:
				filesBox = self.activeWidget.filesBox  # type: ignore[union-attr]
			except AttributeError:
				pass
			else:
				filesBox.removeNewFiles()
			if parentWin is not None:
				parentWin.present()
			return None
		self.activeWidget.updateVars()

		event = self.event
		group = event.parent
		assert isinstance(group, EventGroup)
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
	**kwargs,
) -> EventType | None:
	event = group.create(eventType)
	if eventType == "custom":  # FIXME
		typeChangable = True
	return EventEditorDialog(
		event,
		typeChangable=typeChangable,
		isNew=True,
		**kwargs,
	).run()
