#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

import os
import sys

from scal3.cal_types import calTypes, convert, jd_to
from scal3 import core
from scal3.core import getMonthName
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import openWindow, dialog_add_button
from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
from scal3.ui_gtk.mywidgets.multi_spin.option_box.date import DateButtonOption
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.ymd import YearMonthDayBox


@registerSignals
class SelectDateDialog(gtk.Dialog):
	signals = [
		("response-date", [int, int, int]),
	]

	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Select Date..."))
		#self.set_has_separator(False)
		#self.set_skip_taskbar_hint(True)
		self.connect("delete-event", self.hideMe)
		self.calType = calTypes.primary
		# #### Receiving dropped day!
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_dest_add_text_targets()
		self.connect("drag-data-received", self.dragRec)
		self.vbox.set_spacing(5)
		######
		hb0 = HBox(spacing=4)
		pack(hb0, gtk.Label(label=_("Date Mode")))
		combo = CalTypeCombo()
		combo.set_active(self.calType)
		pack(hb0, combo)
		pack(self.vbox, hb0)
		#######################
		hbox = HBox(spacing=5)
		rb1 = gtk.RadioButton.new_with_label(None, "")
		rb1.num = 1
		pack(hbox, rb1)
		self.ymdBox = YearMonthDayBox()
		pack(hbox, self.ymdBox)
		pack(self.vbox, hbox)
		########
		hb2 = HBox(spacing=4)
		pack(hb2, gtk.Label(label="yyyy/mm/dd"))
		dateInput = DateButtonOption(hist_size=16)
		pack(hb2, dateInput)
		rb2 = gtk.RadioButton.new_with_label_from_widget(rb1, "")
		rb2.num = 2
		#rb2.set_group([rb1])
		hb2i = HBox(spacing=5)
		pack(hb2i, rb2)
		pack(hb2i, hb2)
		pack(self.vbox, hb2i)
		########
		hb3 = HBox(spacing=10)
		pack(hb3, gtk.Label(label=_("Julian Day Number")))
		jdInput = IntSpinButton(0, 9999999)
		pack(hb3, jdInput)
		rb3 = gtk.RadioButton.new_with_label_from_widget(rb1, "")
		rb3.num = 3
		#rb3.set_group([rb1])
		hb3i = HBox(spacing=5)
		pack(hb3i, rb3)
		pack(hb3i, hb3)
		pack(self.vbox, hb3i)
		#######
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
			onClick=self.hideMe,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
			onClick=self.ok,
		)
		#######
		self.calTypeCombo = combo
		self.dateInput = dateInput
		self.jdInput = jdInput
		self.radio1 = rb1
		self.radio2 = rb2
		self.radio3 = rb3
		self.hbox2 = hb2
		self.hbox3 = hb3
		#######
		combo.connect("changed", self.calTypeComboChanged)
		rb1.connect_after("clicked", self.radioChanged)
		rb2.connect_after("clicked", self.radioChanged)
		dateInput.connect("activate", self.ok)
		jdInput.connect("activate", self.ok)
		self.radioChanged()
		#######
		self.vbox.show_all()
		self.resize(1, 1)

	def dragRec(self, obj, context, x, y, selection, target_id, etime):
		text = selection.get_text()
		if text is None:
			return
		date = ui.parseDroppedDate(text)
		if date is None:
			log.info(f"selectDateDialog: dropped text {text!r}")
			return
		log.info(f"selectDateDialog: dropped date: {date!r}")
		calType = self.calTypeCombo.get_active()
		if calType != ui.dragGetCalType:
			date = convert(
				date[0],
				date[1],
				date[2],
				ui.dragGetCalType,
				calType,
			)
		self.dateInput.set_value(date)
		self.dateInput.add_history()
		return True

	def show(self):
		# Show a window that ask the date and set on the calendar
		calType = calTypes.primary
		y, m, d = ui.cell.dates[calType]
		self.setCalType(calType)
		self.set(y, m, d)
		self.jdInput.set_value(ui.cell.jd)
		openWindow(self)

	def hideMe(self, widget, event=None):
		self.hide()
		return True

	def set(self, y, m, d):
		self.ymdBox.set_value((y, m, d))
		self.dateInput.set_value((y, m, d))
		self.dateInput.add_history()

	def setCalType(self, calType):
		self.calType = calType
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		self.calTypeCombo.set_active(calType)
		self.ymdBox.setCalType(calType)
		self.dateInput.setMaxDay(module.maxMonthLen)

	def calTypeComboChanged(self, widget=None):
		prevCalType = self.calType
		prevDate = self.get()
		calType = self.calTypeCombo.get_active()
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		if prevDate is None:
			y, m, d = ui.cell.dates[calType]
		else:
			y0, m0, d0 = prevDate
			y, m, d = convert(y0, m0, d0, prevCalType, calType)
		self.ymdBox.setCalType(calType)
		self.dateInput.setMaxDay(module.maxMonthLen)
		self.set(y, m, d)
		self.calType = calType

	def get(self):
		calType = self.calTypeCombo.get_active()
		if self.radio1.get_active():
			y0, m0, d0 = self.ymdBox.get_value()
		elif self.radio2.get_active():
			y0, m0, d0 = self.dateInput.get_value()
		elif self.radio3.get_active():
			jd = self.jdInput.get_value()
			y0, m0, d0 = jd_to(jd, calType)
		return (y0, m0, d0)

	def ok(self, widget):
		calType = self.calTypeCombo.get_active()
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
		#if not core.validDate(calType, y, m, d):
		#	log.error(f"bad date: calType={calType}, date={y}/{m}/{d}")
		#	return
		self.emit("response-date", y, m, d)
		self.hide()
		self.dateInput.set_value((y0, m0, d0))
		self.dateInput.add_history()

	def radioChanged(self, widget=None):
		if self.radio1.get_active():
			self.ymdBox.set_sensitive(True)
			self.hbox2.set_sensitive(False)
			self.hbox3.set_sensitive(False)
		elif self.radio2.get_active():
			self.ymdBox.set_sensitive(False)
			self.hbox2.set_sensitive(True)
			self.hbox3.set_sensitive(False)
		elif self.radio3.get_active():
			self.ymdBox.set_sensitive(False)
			self.hbox2.set_sensitive(False)
			self.hbox3.set_sensitive(True)
