#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from typing import Any, ClassVar

from scal3 import logger

log = logger.get()

from scal3 import ui
from scal3.cal_types import calTypes, convert, jd_to
from scal3.date_dnd import parseDroppedDate
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gdk, gtk, pack
from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.option_box.date import DateButtonOption
from scal3.ui_gtk.mywidgets.ymd import YearMonthDayBox
from scal3.ui_gtk.signals import registerSignals
from scal3.ui_gtk.utils import dialog_add_button, openWindow

__all__ = ["SelectDateDialog"]


@registerSignals
class SelectDateDialog(Dialog):
	signals: ClassVar[list[tuple[str, list[Any]]]] = [
		("response-date", [int, int, int]),
	]

	def __init__(self, transient_for: gtk.Window | None = None) -> None:
		Dialog.__init__(self, transient_for=transient_for)
		self.set_title(_("Select Date..."))
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		self.connect("delete-event", self.onDeleteEvent)
		self.calType = calTypes.primary
		# Receiving dropped day!
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_dest_add_text_targets()
		self.connect("drag-data-received", self.dragRec)
		self.vbox.set_spacing(5)
		# ------
		hb0 = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=4)
		pack(hb0, gtk.Label(label=_("Date Mode")))
		combo = CalTypeCombo()
		combo.set_active(self.calType)
		pack(hb0, combo)
		pack(self.vbox, hb0)
		# -----------------------
		self.addDateBox1()
		self.addDateBox2()
		self.addDaysPlusBox()
		self.addJdBox()

		# -------
		dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			onClick=self.onCancelClick,
		)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
			onClick=self.ok,
		)
		# -------
		self.calTypeCombo = combo
		# -------
		combo.connect("changed", self.calTypeComboChanged)
		self.dateRadio1.connect_after("clicked", self.radioChanged)
		self.dateRadio2.connect_after("clicked", self.radioChanged)
		self.plusRadio.connect_after("clicked", self.radioChanged)
		self.jdRadio.connect_after("clicked", self.radioChanged)
		self.dateInput2.connect("activate", self.ok)
		self.plusDaysInput.connect("activate", self.ok)
		self.jdInput.connect("activate", self.ok)
		self.radioChanged()
		# -------
		self.vbox.show_all()
		self.resize(1, 1)

	def addDateBox1(self) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		self.dateRadio1 = gtk.RadioButton(label=" ")
		# rb1.num = 1
		pack(hbox, self.dateRadio1)
		self.dateInput1 = YearMonthDayBox()
		pack(hbox, self.dateInput1)
		pack(self.vbox, hbox)
		self.dateBox1 = self.dateInput1

	def addDateBox2(self) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=4)
		pack(hbox, gtk.Label(label="yyyy/mm/dd"))
		self.dateInput2 = DateButtonOption(hist_size=16)
		pack(hbox, self.dateInput2)
		self.dateRadio2 = gtk.RadioButton(label=" ", group=self.dateRadio1)
		# rb2.num = 2
		hbox2 = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		pack(hbox2, self.dateRadio2)
		pack(hbox2, hbox)
		pack(self.vbox, hbox2)
		self.dateBox2 = hbox

	def addDaysPlusBox(self) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
		pack(hbox, gtk.Label(label=_("From selected day")))
		self.plusDaysInput = IntSpinButton(-999999, 999999)
		self.plusDaysInput.set_value(0)
		pack(hbox, self.plusDaysInput)
		pack(hbox, gtk.Label(label=_(" days")))
		self.plusRadio = gtk.RadioButton(label=" ", group=self.dateRadio1)
		# rb3.num = 4
		hbox2 = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		pack(hbox2, self.plusRadio)
		pack(hbox2, hbox)
		pack(self.vbox, hbox2)
		self.plusBox = hbox

	def addJdBox(self) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
		pack(hbox, gtk.Label(label=_("Julian Day Number")))
		self.jdInput = IntSpinButton(0, 9999999)
		pack(hbox, self.jdInput)
		self.jdRadio = gtk.RadioButton(label=" ", group=self.dateRadio1)
		# rb3.num = 3
		hbox2 = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		pack(hbox2, self.jdRadio)
		pack(hbox2, hbox)
		pack(self.vbox, hbox2)
		self.jdBox = hbox

	def dragRec(
		self,
		_obj: gtk.Widget,
		_context: gdk.DragContext,
		_x: int,
		_y: int,
		selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> bool:
		text = selection.get_text()
		if text is None:
			return False
		date = parseDroppedDate(text)
		if date is None:
			log.info(f"selectDateDialog: dropped text {text!r}")
			return False
		log.info(f"selectDateDialog: dropped date: {date!r}")
		calType = self.calTypeCombo.getActive()
		if calType is not None and calType != ui.dragGetCalType:
			date = convert(
				date[0],
				date[1],
				date[2],
				ui.dragGetCalType,
				calType,
			)
		self.dateInput2.set_value(date)
		self.dateInput2.add_history()
		return True

	def show(self) -> None:
		# Show a window that ask the date and set on the calendar
		calType = calTypes.primary
		y, m, d = ui.cells.current.dates[calType]
		self.setCalType(calType)
		self.set(y, m, d)
		self.jdInput.set_value(ui.cells.current.jd)
		openWindow(self)

	def onResponse(self) -> None:
		self.hide()
		parentWin = self.get_transient_for()
		if parentWin is not None:
			parentWin.present()

	def onDeleteEvent(self, _w: gtk.Widget, _ge: gdk.Event | None = None) -> bool:
		self.onResponse()
		return True

	def onCancelClick(self, _w: gtk.Widget) -> None:
		self.onResponse()

	def set(self, y: int, m: int, d: int) -> None:
		self.dateInput1.set_value((y, m, d))
		self.dateInput2.set_value((y, m, d))
		self.dateInput2.add_history()

	def setCalType(self, calType: int) -> None:
		self.calType = calType
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		self.calTypeCombo.setActive(calType)
		self.dateInput1.setCalType(calType)
		self.dateInput2.setMaxDay(module.maxMonthLen)

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		calType = self.calTypeCombo.getActive()
		if calType is None:
			return

		prevCalType = self.calType
		prevDate = self.get()
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		if prevDate is None:
			y, m, d = ui.cells.current.dates[calType]
		else:
			y0, m0, d0 = prevDate
			y, m, d = convert(y0, m0, d0, prevCalType, calType)
		self.dateInput1.setCalType(calType)
		self.dateInput2.setMaxDay(module.maxMonthLen)
		self.set(y, m, d)
		self.calType = calType

	def get(self) -> tuple[int, int, int]:
		calType = self.calTypeCombo.getActive()
		assert calType is not None
		if self.dateRadio1.get_active():
			return self.dateInput1.get_value()
		if self.dateRadio2.get_active():
			return self.dateInput2.get_value()
		if self.jdRadio.get_active():
			jd = self.jdInput.get_value()
			return jd_to(jd, calType)
		if self.plusRadio.get_active():
			days = self.plusDaysInput.get_value()
			jd = ui.cells.current.jd + days
			return jd_to(jd, calType)
		raise RuntimeError("None of radio buttons are active")

	def ok(self, _w: gtk.Widget) -> None:
		calType = self.calTypeCombo.getActive()
		if calType is None:
			return
		date = self.get()
		if date is None:
			return
		y0, m0, d0 = date
		if calType == calTypes.primary:
			y, m, d = (y0, m0, d0)
		else:
			y, m, d = convert(y0, m0, d0, calType, calTypes.primary)
		# if not core.validDate(calType, y, m, d):
		# 	log.error(f"bad date: {calType=}, date={y}/{m}/{d}")
		# 	return
		self.emit("response-date", y, m, d)
		self.onResponse()
		self.dateInput2.set_value((y0, m0, d0))
		self.dateInput2.add_history()

	def radioChanged(self, _w: gtk.Widget | None = None) -> None:
		radiosAndBoxes: list[tuple[gtk.RadioButton, gtk.Box]] = [
			(self.dateRadio1, self.dateBox1),
			(self.dateRadio2, self.dateBox2),
			(self.plusRadio, self.plusBox),
			(self.jdRadio, self.jdBox),
		]
		for radio, box in radiosAndBoxes:
			box.set_sensitive(radio.get_active())
