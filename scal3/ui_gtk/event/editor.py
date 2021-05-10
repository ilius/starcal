#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.utils import showInfo
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly


class EventEditorDialog(gtk.Dialog):
	def __init__(
		self,
		event,
		typeChangable=True,
		isNew=False,
		useSelectedDate=False,
		**kwargs
	):
		checkEventsReadOnly()
		gtk.Dialog.__init__(self, **kwargs)
		# self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		self.isNew = isNew
		# self.connect("delete-event", lambda obj, e: self.destroy())
		# self.resize(800, 600)
		###
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
		###
		self.connect("response", lambda w, e: self.hide())
		###
		self.activeWidget = None
		self._group = event.parent
		self.eventTypeOptions = list(self._group.acceptsEventTypes)
		####
		if event.name not in self.eventTypeOptions:
			self.eventTypeOptions.append(event.name)
		eventTypeIndex = self.eventTypeOptions.index(event.name)
		####
		self.event = event
		#######
		if isNew and not event.timeZone:
			event.timeZone = str(core.localTz)## why? FIXME
		#######
		hbox = HBox()
		pack(hbox, gtk.Label(
			label=_("Group") + ": " + self._group.title
		))
		hbox.show_all()
		pack(self.vbox, hbox)
		#######
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Event Type")))
		if typeChangable:
			combo = gtk.ComboBoxText()
			for tmpEventType in self.eventTypeOptions:
				combo.append_text(event_lib.classes.event.byName[tmpEventType].desc)
			pack(hbox, combo)
			####
			combo.set_active(eventTypeIndex)
			####
			# self.activeWidget = makeWidget(event)
			combo.connect("changed", self.typeChanged)
			self.comboEventType = combo
		else:
			pack(hbox, gtk.Label(label=":  " + event.desc))
		pack(hbox, gtk.Label(), 1, 1)
		hbox.show_all()
		pack(self.vbox, hbox)
		#####
		if useSelectedDate:
			self.event.setJd(ui.cell.jd)
		self.activeWidget = makeWidget(event)
		if self.isNew:
			self.activeWidget.focusSummary()
		pack(self.vbox, self.activeWidget, 1, 1)
		self.vbox.show()

	def replaceEventWithType(self, eventType):
		if not self.isNew:
			self.event = self._group.copyEventWithType(self.event, eventType)
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

	def typeChanged(self, combo):
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		eventType = self.eventTypeOptions[combo.get_active()]
		self.replaceEventWithType(eventType)
		self._group.updateCache(self.event)## needed? FIXME
		self.activeWidget = makeWidget(self.event)
		if self.isNew:
			self.activeWidget.focusSummary()
		pack(self.vbox, self.activeWidget, 1, 1)
		# self.activeWidget.calTypeComboChanged()## apearantly not needed

	def run(self):
		# if not self.activeWidget:
		# 	return None
		parentWin = self.get_transient_for()
		if gtk.Dialog.run(self) != gtk.ResponseType.OK:
			try:
				filesBox = self.activeWidget.filesBox
			except AttributeError:
				pass
			else:
				filesBox.removeNewFiles()
			if parentWin is not None:
				parentWin.present()
			return None
		self.activeWidget.updateVars()
		self.event.afterModify()
		self.event.save()
		event_lib.lastIds.save()
		self.destroy()
		#####
		if self.event.isSingleOccur:
			occur = self.event.calcOccurrence(
				self.event.parent.startJd,
				self.event.parent.endJd,
			)
			if not occur:
				msg = _(
					"This event is outside of date range specified in "
					"it\'s group. You probably need to edit group "
					"\"{groupTitle}\" and change \"Start\" or \"End\" values"
				).format(groupTitle=self.event.parent.title)
				showInfo(msg)
		#####
		if parentWin is not None:
			parentWin.present()
		#####
		return self.event


def addNewEvent(group, eventType, typeChangable=False, **kwargs):
	event = group.create(eventType)
	if eventType == "custom":  # FIXME
		typeChangable = True
	event = EventEditorDialog(
		event,
		typeChangable=typeChangable,
		isNew=True,
		**kwargs
	).run()
	if event is None:
		return
	group.add(event)
	group.save()
	return event
