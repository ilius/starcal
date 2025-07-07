from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

import mytz
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gtk, pack
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.utils import (
	dialog_add_button,
	window_set_size_aspect,
)

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventContainerType

__all__ = ["EventsBulkEditDialog"]


class EventsBulkEditDialog(Dialog):
	def __init__(
		self,
		container: EventContainerType,
		transient_for: gtk.Window | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry

		self._container = container
		Dialog.__init__(self, transient_for=transient_for)
		self.set_title(_("Bulk Edit Events"))
		# ----
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
			label=_("_Perform"),
		)
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# ----
		try:
			title = container.title
		except AttributeError:
			event_count = len(container)
			msg = _(
				"Here you are going to modify these {eventCount} events at once.",
			).format(eventCount=event_count)
		else:
			msg = _(
				"Here you are going to modify all events "
				'inside group "{groupTitle}" at once.',
			).format(groupTitle=title)
		msg += " "
		msg += _(
			"You better make a backup from your events before doing this."
			' Just right click on group and select "Export"'
			" (or a full backup: menu File -> Export)",
		)
		msg += "\n\n"
		label = gtk.Label(label=msg)
		label.set_line_wrap(True)
		pack(self.vbox, label)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.iconRadio = gtk.RadioButton(label=_("Icon"))
		pack(hbox, self.iconRadio, 1, 1)
		self.summaryRadio = gtk.RadioButton(
			label=_("Summary"),
			group=self.iconRadio,
		)
		pack(hbox, self.summaryRadio, 1, 1)
		self.descriptionRadio = gtk.RadioButton(
			label=_("Description"),
			group=self.iconRadio,
		)
		pack(hbox, self.descriptionRadio, 1, 1)
		self.timeZoneRadio = gtk.RadioButton(
			label=_("Time Zone"),
			group=self.iconRadio,
		)
		pack(hbox, self.timeZoneRadio, 1, 1)
		pack(self.vbox, hbox)
		# ---
		self.iconRadio.connect("clicked", self.firstRadioChanged)
		self.summaryRadio.connect("clicked", self.firstRadioChanged)
		self.descriptionRadio.connect("clicked", self.firstRadioChanged)
		self.timeZoneRadio.connect("clicked", self.firstRadioChanged)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.iconChangeCombo = gtk.ComboBoxText()
		self.iconChangeCombo.append_text("----")
		self.iconChangeCombo.append_text(_("Change"))
		self.iconChangeCombo.append_text(_("Change if empty"))
		pack(hbox, self.iconChangeCombo)
		pack(hbox, gtk.Label(label="  "))
		self.iconSelect = IconSelectButton()
		if hasattr(container, "icon") and container.icon:
			self.iconSelect.set_filename(container.icon)
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		self.iconHbox = hbox
		# ----
		self.textVbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.textChangeCombo = gtk.ComboBoxText()
		self.textChangeCombo.append_text("----")
		self.textChangeCombo.append_text(_("Add to beginning"))
		self.textChangeCombo.append_text(_("Add to end"))
		self.textChangeCombo.append_text(_("Replace text"))
		self.textChangeCombo.connect("changed", self.textChangeComboChanged)
		pack(hbox, self.textChangeCombo)
		pack(hbox, gtk.Label(), 1, 1)
		# CheckButton(_("Regexp"))
		pack(self.textVbox, hbox)
		# ---
		self.textInput1 = TextFrame()
		pack(self.textVbox, self.textInput1, 1, 1)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("with")))
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.textVbox, hbox, 1, 1)
		self.withHbox = hbox
		# ---
		self.textInput2 = TextFrame()
		pack(self.textVbox, self.textInput2, 1, 1)
		# ----
		pack(self.vbox, self.textVbox, 1, 1)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.timeZoneChangeCombo = gtk.ComboBoxText()
		self.timeZoneChangeCombo.append_text("----")
		self.timeZoneChangeCombo.append_text(_("Change"))
		self.timeZoneChangeCombo.append_text(_("Change if empty"))
		pack(hbox, self.timeZoneChangeCombo)
		pack(hbox, gtk.Label(label="  "))
		self.timeZoneInput = TimeZoneComboBoxEntry()
		pack(hbox, self.timeZoneInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox, 1, 1)
		self.timeZoneHbox = hbox
		# ----
		self.vbox.show_all()
		self.iconRadio.set_active(True)
		self.iconChangeCombo.set_active(0)
		self.textChangeCombo.set_active(0)
		self.firstRadioChanged()
		# ----
		window_set_size_aspect(self, 1.6)

	def firstRadioChanged(self, _w: gtk.Widget | None = None) -> None:
		if self.iconRadio.get_active():
			self.iconHbox.show()
			self.textVbox.hide()
			self.timeZoneHbox.hide()
		elif self.timeZoneRadio.get_active():
			self.iconHbox.hide()
			self.textVbox.hide()
			self.timeZoneHbox.show()
		elif self.summaryRadio.get_active() or self.descriptionRadio.get_active():
			self.iconHbox.hide()
			self.textChangeComboChanged()
			self.timeZoneHbox.hide()

	def textChangeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		self.textVbox.show_all()
		chType = self.textChangeCombo.get_active()
		if chType == 0:
			self.textInput1.hide()
			self.withHbox.hide()
			self.textInput2.hide()
		elif chType in {1, 2}:
			self.withHbox.hide()
			self.textInput2.hide()

	def _doActionIcon(self) -> None:
		chType = self.iconChangeCombo.get_active()
		if chType == 0:
			return
		icon = self.iconSelect.get_filename()
		for event in self._container:
			if not (chType == 2 and event.icon):
				event.icon = icon
				event.afterModify()
				event.save()

	def _doActionTimeZone(self) -> None:
		chType = self.timeZoneChangeCombo.get_active()
		timeZone = self.timeZoneInput.get_text()
		if chType != 0:
			# mytz.gettz does not raise exception, returns None if invalid
			if mytz.gettz(timeZone):
				for event in self._container:
					if not (chType == 2 and event.timeZone):
						event.timeZone = timeZone
						event.afterModify()
						event.save()
			else:
				log.error(f"Invalid Time Zone {timeZone!r}")

	def _doActionText(self) -> None:
		chType = self.textChangeCombo.get_active()
		if chType == 0:
			return
		text1 = self.textInput1.get_text()
		text2 = self.textInput2.get_text()
		if self.summaryRadio.get_active():
			for event in self._container:
				if chType == 1:
					event.summary = text1 + event.summary
				elif chType == 2:
					event.summary += text1
				elif chType == 3:
					event.summary = event.summary.replace(text1, text2)
				event.afterModify()
				event.save()
		elif self.descriptionRadio.get_active():
			for event in self._container:
				if chType == 1:
					event.description = text1 + event.description
				elif chType == 2:
					event.description += text1
				elif chType == 3:
					event.description = event.description.replace(text1, text2)
				event.afterModify()
				event.save()

	def doAction(self) -> None:
		if self.iconRadio.get_active():
			self._doActionIcon()
		elif self.timeZoneRadio.get_active():
			self._doActionTimeZone()
		else:
			self._doActionText()
