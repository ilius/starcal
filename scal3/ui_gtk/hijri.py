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

# Islamic (Hijri) calendar: http://en.wikipedia.org/wiki/Islamic_calendar

from scal3 import logger
log = logger.get()

import os
from os.path import isfile

from scal3.cal_types import calTypes, jd_to, to_jd
from scal3.cal_types import hijri

from scal3.date_utils import monthPlus
from scal3 import core
from scal3.locale_man import rtl, dateLocale
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.utils import (
	dialog_add_button,
	set_tooltip,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk import listener
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


hijriMode = calTypes.names.index("hijri")


def getCurrentYm():
	y, m, d = ui.todayCell.dates[hijriMode]
	return y * 12 + m - 1


class EditDbDialog(gtk.Dialog):
	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Tune Hijri Monthes"))
		self.connect("delete-event", self.onDeleteEvent)
		############
		self.altMode = 0
		self.altModeDesc = "Gregorian"
		############
		hbox = HBox()
		self.topLabel = gtk.Label()
		pack(hbox, self.topLabel)
		self.startDateInput = DateButton()
		self.startDateInput.set_editable(False)## FIXME
		self.startDateInput.connect("changed", lambda widget: self.updateEndDates())
		pack(hbox, self.startDateInput)
		pack(self.vbox, hbox)
		############################
		treev = gtk.TreeView()
		trees = gtk.ListStore(
			int,  # ym (hidden)
			str,  # localized year
			str,  # localized month
			int,  # monthLenCombo
			str,  # localized endDate
		)
		treev.set_model(trees)
		#treev.get_selection().connect("changed", self.plugTreevCursorChanged)
		#treev.connect("row-activated", self.plugTreevRActivate)
		#treev.connect("button-press-event", self.plugTreevButtonPress)
		###
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		######
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Year"), cell_renderer=cell, text=1)
		treev.append_column(col)
		######
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Month"), cell_renderer=cell, text=2)
		treev.append_column(col)
		######
		cell = gtk.CellRendererCombo(editable=True)
		mLenModel = gtk.ListStore(int)
		mLenModel.append([29])
		mLenModel.append([30])
		cell.set_property("model", mLenModel)
		#cell.set_property("has-entry", False)
		cell.set_property("text-column", 0)
		cell.connect("edited", self.monthLenCellEdited)
		col = gtk.TreeViewColumn(title=_("Month Length"), cell_renderer=cell, text=3)
		treev.append_column(col)
		######
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("End Date"), cell_renderer=cell, text=4)
		treev.append_column(col)
		######
		toolbar = StaticToolBox(self, vertical=True)
		###
		toolbar.append(ToolBoxItem(
			name="add",
			imageName="list-add.svg",
			onClick="onAddClick",
			desc=_("Add"),
			continuousClick=False,
		))
		###
		toolbar.append(ToolBoxItem(
			name="delete",
			imageName="edit-delete.svg",
			onClick="onDeleteClick",
			desc=_("Delete"),
			continuousClick=False,
		))
		######
		self.treev = treev
		self.trees = trees
		#####
		mainHbox = HBox()
		pack(mainHbox, swin, 1, 1)
		pack(mainHbox, toolbar)
		pack(self.vbox, mainHbox, 1, 1)
		######
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		##
		resetB = dialog_add_button(
			self,
			imageName="edit-undo.svg",
			label=_("_Reset to Defaults"),
			res=gtk.ResponseType.NONE,
		)
		resetB.connect("clicked", self.resetToDefaults)
		##
		self.connect("response", self.onResponse)
		# log.debug(dir(self.get_action_area()))
		#self.get_action_area().set_homogeneous(False)
		######
		self.vbox.show_all()

	def resetToDefaults(self, widget):
		if isfile(hijri.monthDb.userDbPath):
			os.remove(hijri.monthDb.userDbPath)
		hijri.monthDb.load()
		self.updateWidget()
		return True

	def onAddClick(self, obj=None):
		last = self.trees[-1]
		# 0 ym
		# 1 yearLocale
		# 2 monthLocale
		# 3 mLen
		# 4 endDate = ""
		ym = last[0] + 1
		mLen = 59 - last[3]
		year, month0 = divmod(ym, 12)
		self.trees.append((
			ym,
			_(year),
			_(hijri.monthName[month0]),
			mLen,
			"",
		))
		self.updateEndDates()
		self.selectLastRow()

	def selectLastRow(self):
		lastPath = (len(self.trees) - 1,)
		self.treev.scroll_to_cell(lastPath)
		self.treev.set_cursor(lastPath)

	def onDeleteClick(self, obj=None):
		if len(self.trees) > 1:
			del self.trees[-1]
		self.selectLastRow()

	def updateWidget(self):
		#for index, module in calTypes.iterIndexModule():
		#	if module.name != "hijri":
		for calType in calTypes.active:
			module, ok = calTypes[calType]
			if not ok:
				raise RuntimeError(f"cal type '{calType}' not found")
			calTypeDesc = module.desc
			if "hijri" not in calTypeDesc.lower():
				self.altMode = calType
				self.altModeDesc = calTypeDesc
				break
		self.topLabel.set_label(
			_("Start") +
			": " +
			dateLocale(*hijri.monthDb.startDate) +
			" " +
			_("Equals to") +
			" " +
			_(self.altModeDesc)
		)
		self.startDateInput.set_value(jd_to(hijri.monthDb.startJd, self.altMode))
		###########
		selectYm = getCurrentYm() - 1 ## previous month
		selectIndex = None
		self.trees.clear()
		for index, ym, mLen in hijri.monthDb.getMonthLenList():
			if ym == selectYm:
				selectIndex = index
			year, month0 = divmod(ym, 12)
			self.trees.append([
				ym,
				_(year),
				_(hijri.monthName[month0]),
				mLen,
				"",
			])
		self.updateEndDates()
		########
		if selectIndex is not None:
			self.treev.scroll_to_cell(str(selectIndex))
			self.treev.set_cursor(str(selectIndex))

	def updateEndDates(self):
		y, m, d = self.startDateInput.get_value()
		jd0 = to_jd(y, m, d, self.altMode) - 1
		for row in self.trees:
			mLen = row[3]
			jd0 += mLen
			row[4] = dateLocale(*jd_to(jd0, self.altMode))

	def monthLenCellEdited(self, combo, path_string, new_text):
		editIndex = int(path_string)
		mLen = int(new_text)
		if mLen not in (29, 30):
			return
		mLenPrev = self.trees[editIndex][3]
		delta = mLen - mLenPrev
		if delta == 0:
			return
		n = len(self.trees)
		self.trees[editIndex][3] = mLen
		if delta == 1:
			for i in range(editIndex + 1, n):
				if self.trees[i][3] == 30:
					self.trees[i][3] = 29
					break
		elif delta == -1:
			for i in range(editIndex + 1, n):
				if self.trees[i][3] == 29:
					self.trees[i][3] = 30
					break
		self.updateEndDates()

	def updateVars(self):
		y, m, d = self.startDateInput.get_value()
		hijri.monthDb.endJd = hijri.monthDb.startJd = to_jd(y, m, d, self.altMode)
		hijri.monthDb.monthLenByYm = {}
		for row in self.trees:
			ym = row[0]
			mLen = row[3]
			hijri.monthDb.monthLenByYm[ym] = mLen
			hijri.monthDb.endJd += mLen

		hijri.monthDb.expJd = hijri.monthDb.endJd
		hijri.monthDb.save()

	def run(self):
		hijri.monthDb.load()
		self.updateWidget()
		self.treev.grab_focus()
		gtk.Dialog.run(self)

	def onResponse(self, dialog, response_id):
		if response_id == gtk.ResponseType.OK:
			self.updateVars()
			self.destroy()
		elif response_id == gtk.ResponseType.CANCEL:
			self.destroy()
		return True

	def onDeleteEvent(self, dialog, gevent):
		self.destroy()
		return True


def tuneHijriMonthes(widget=None):
	dialog = EditDbDialog(transient_for=ui.prefWindow)
	dialog.resize(400, 400)
	dialog.run()


def dbIsExpired() -> bool:
	if not hijri.hijriUseDB:
		return False
	expJd = hijri.monthDb.expJd
	if expJd is None:
		log.info("checkDbExpired: hijri.monthDb.expJd = None")
		return False
	if ui.todayCell.jd >= expJd:
		return True
	return False


class HijriMonthsExpirationDialog(gtk.Dialog):
	message = _("""Hijri months are expired.
Please update StarCalendar.
Otherwise, Hijri dates and Iranian official holidays would be incorrect.""")

	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Hijri months expired"))
		self.connect("response", self.onResponse)
		###
		pack(self.vbox, gtk.Label(label=self.message + "\n\n"), 1, 1)
		###
		hbox = HBox()
		checkb = gtk.CheckButton(label=_("Don't show this again"))
		pack(hbox, checkb)
		pack(self.vbox, hbox)
		self.noShowCheckb = checkb
		###
		dialog_add_button(
			self,
			imageName="dialog-close.svg",
			label=_("_Close"),
			res=gtk.ResponseType.OK,
		)
		###
		self.vbox.show_all()

	def onResponse(self, dialog, response_id):
		if self.noShowCheckb.get_active():
			open(hijri.monthDbExpiredIgnoreFile, "w").write("")
		self.destroy()
		return True


def checkHijriMonthsExpiration():
	if not dbIsExpired():
		# not expired
		return
	if isfile(hijri.monthDbExpiredIgnoreFile):
		# user previously checked "Don't show this again" checkbox
		return
	dialog = HijriMonthsExpirationDialog(transient_for=ui.mainWin)
	dialog.run()


class HijriMonthsExpirationListener():
	def onCurrentDateChange(self, gdate):
		checkHijriMonthsExpiration()


if __name__ == "__main__":
	tuneHijriMonthes()
