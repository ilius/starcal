#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

import os
from os.path import dirname
import math

from scal3 import locale_man
from scal3.locale_man import tr as _
from pray_times_backend import timeNames, methodsList
from pray_times_utils import *

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	dialog_add_button,
	showMsg,
	newAlignLabel,
)
from scal3.ui_gtk.app_info import popenFile
from scal3.ui_gtk.about import AboutDialog
# do I have to duplicate AboutDialog class code?


dataDir = dirname(__file__)
earthR = 6370


def buffer_get_text(b):
	return b.get_text(
		b.get_start_iter(),
		b.get_end_iter(),
		True,
	)


def buffer_select_all(b):
	return b.select_range(
		b.get_start_iter(),
		b.get_end_iter(),
	)


def showDisclaimer(plug):
	showMsg(
		"\n".join([
			_(
				"Please note that a few minutes error in Pray Times is unavoidable,"
				" specially for large cities."
			),
			_(
				"For example in Tehran, there is a 2 minutes difference"
				" between far-east and far-west points of city."
			),
			_("(Usually the center of cities are taken into account)"),
			_("But also calculations are never accurate."),
			_(
				"Please allow at least 2 minutes as a precaution"
				" (for Fajr, at least 3 minutes)"
			),
		]),
		# imageName="",
		parent=None,
		title=_("Pray Times"),
	)


class LocationDialog(gtk.Dialog):
	def __init__(
		self,
		cityData,
		maxResults=200,
		width=600,
		height=600,
		**kwargs
	):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Location"))
		self.maxResults = maxResults
		self.resize(width, height)
		# width is used for CellRendererText as well
		###############
		cancelB = dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		okB = dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		self.okB = okB
		###############
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(label=_("Search Cities:")))
		entry = gtk.Entry()
		pack(hbox, entry, 1, 1)
		entry.connect("changed", self.entry_changed)
		pack(self.vbox, hbox)
		######################
		treev = gtk.TreeView()
		treev.set_headers_clickable(False)
		treev.set_headers_visible(False)
		trees = gtk.ListStore(int, str)
		treev.set_model(trees)
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(self.vbox, swin, 1, 1)
		self.treev = treev
		self.trees = trees
		treev.connect("cursor-changed", self.treev_cursor_changed)
		#########
		#cell = gtk.CellRendererText()
		#col = gtk.TreeViewColumn("Index", cell, text=0)
		#col.set_resizable(True)## No need!
		#treev.append_column(col)
		########
		cell = gtk.CellRendererText()
		cell.set_fixed_size(width - 30, -1)
		col = gtk.TreeViewColumn("City", cell, text=1)
		#col.set_resizable(True)## No need!
		treev.append_column(col)
		#########
		treev.set_search_column(1)
		###########
		frame = gtk.Frame()
		checkb = gtk.CheckButton()
		checkb.set_label(_("Edit Manually"))
		checkb.connect("clicked", self.edit_checkb_clicked)
		frame.set_label_widget(checkb)
		self.checkbEdit = checkb
		vbox = gtk.VBox()
		group = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		#####
		hbox = gtk.HBox()
		pack(hbox, newAlignLabel(sgroup=group, label=_("Name:")))
		entry = gtk.Entry()
		pack(hbox, entry, 1, 1)
		pack(vbox, hbox)
		self.entry_edit_name = entry
		####
		hbox = gtk.HBox()
		pack(hbox, newAlignLabel(sgroup=group, label=_("Latitude:")))
		spin = gtk.SpinButton()
		spin.set_increments(1, 10)
		spin.set_range(-180, 180)
		spin.set_digits(3)
		spin.set_direction(gtk.TextDirection.LTR)
		pack(hbox, spin)
		pack(vbox, hbox)
		self.spin_lat = spin
		####
		hbox = gtk.HBox()
		pack(hbox, newAlignLabel(sgroup=group, label=_("Longitude:")))
		spin = gtk.SpinButton()
		spin.set_increments(1, 10)
		spin.set_range(-180, 180)
		spin.set_digits(3)
		spin.set_direction(gtk.TextDirection.LTR)
		pack(hbox, spin)
		pack(vbox, hbox)
		self.spin_lng = spin
		####
		hbox = gtk.HBox()
		self.lowerLabel = newAlignLabel(sgroup=None, label="")
		pack(hbox, self.lowerLabel, 1, 1)
		button = gtk.Button(label=_("Calculate Nearest City"))
		button.connect("clicked", self.calc_clicked)
		pack(hbox, button)
		pack(vbox, hbox)
		####
		vbox.set_sensitive(False)
		frame.add(vbox)
		self.vbox_edit = vbox
		pack(self.vbox, frame)
		###
		self.vbox.show_all()
		#########
		self.cityData = cityData
		self.update_list()

	def calc_clicked(self, button):
		lat = self.spin_lat.get_value()
		lng = self.spin_lng.get_value()
		md = earthR * 2 * math.pi
		city = ""
		for (name, lname, lat2, lng2) in self.cityData:
			d = earthDistance(lat, lng, lat2, lng2)
			assert d >= 0
			if d < md:
				md = d
				city = lname
		self.lowerLabel.set_label(
			_("{distanceKM} kilometers from {place}").format(
				distanceKM=md,
				place=city,
			)
		)

	def treev_cursor_changed(self, treev):
		c = treev.get_cursor()[0]
		if c is not None:
			i = c[0]
			j, s = self.trees[i]
			self.entry_edit_name.set_text(s)
			self.spin_lat.set_value(self.cityData[j][2])
			self.spin_lng.set_value(self.cityData[j][3])
			self.lowerLabel.set_label(
				_("{distanceKM} kilometers from {place}").format(
					distanceKM=0.0,
					place=s,
				)
			)
		self.okB.set_sensitive(True)

	def edit_checkb_clicked(self, checkb):
		active = checkb.get_active()
		self.vbox_edit.set_sensitive(active)
		if not active:
			cur = self.treev.get_cursor()[0]
			if cur is None:
				lname = ""
				lat = 0
				lng = 0
			else:
				i = cur[0]
				j = self.trees[i][0]
				name, lname, lat, lng = self.cityData[j]
			self.entry_edit_name.set_text(lname)
			self.spin_lat.set_value(lat)
			self.spin_lng.set_value(lng)
		self.updateOkButton()

	def updateOkButton(self):
		return self.okB.set_sensitive(
			bool(self.treev.get_cursor()[0] or self.checkbEdit.get_active())
		)

	def update_list(self, s=""):
		s = s.lower()
		t = self.trees
		t.clear()
		d = self.cityData
		n = len(d)
		if s == "":
			for i in range(n):
				t.append((i, d[i][0]))
		else:  # here check also translations
			mr = self.maxResults
			r = 0
			for i in range(n):
				if s in (d[i][0] + "\n" + d[i][1]).lower():
					t.append((i, d[i][1]))
					r += 1
					if r >= mr:
						break
		self.treev.scroll_to_cell((0, 0))
		self.okB.set_sensitive(self.checkbEdit.get_active())

	def entry_changed(self, entry):
		self.update_list(entry.get_text())

	def run(self):
		ex = gtk.Dialog.run(self)
		self.hide()
		if ex == gtk.ResponseType.OK:
			if (
				self.checkbEdit.get_active() or
				self.treev.get_cursor()[0] is not None
			):  # FIXME
				return (
					self.entry_edit_name.get_text(),
					self.spin_lat.get_value(),
					self.spin_lng.get_value(),
				)
		return None


class LocationButton(gtk.Button):
	def __init__(self, plugin, locName, lat, lng, window=None):
		gtk.Button.__init__(self)
		self.setLocation(locName, lat, lng)
		self.plugin = plugin
		self.parentWindow = window
		self.dialog = None
		####
		self.connect("clicked", self.onClick)

	def setLocation(self, locName, lat, lng):
		self.locName = locName
		self.lat = lat
		self.lng = lng
		self.set_label(self.locName)

	def onClick(self, widget):
		if self.dialog is None:
			self.dialog = LocationDialog(
				self.plugin.getCityData(),
				parent=self.parentWindow,
			)
		res = self.dialog.run()
		if res:
			locName, lat, lng = res
			self.setLocation(locName, lat, lng)


class TextPluginUI:
	def makeWidget(self):
		self.confDialog = gtk.Dialog()
		self.confDialog.set_title(
			_("Pray Times") + " - " + _("Configuration")
		)
		self.confDialog.connect("delete-event", self.confDialogCancel)
		group = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		###
		hbox = gtk.HBox()
		label = newAlignLabel(sgroup=group, label=_("Location"))
		pack(hbox, label)
		self.locButton = LocationButton(
			self,
			self.locName,
			self.backend.lat,
			self.backend.lng,
			window=self.confDialog,
		)
		pack(hbox, self.locButton)
		pack(self.confDialog.vbox, hbox)
		###
		hbox = gtk.HBox()
		label = newAlignLabel(sgroup=group, label=_("Calculation Method"))
		pack(hbox, label)
		self.methodCombo = gtk.ComboBoxText()
		for methodObj in methodsList:
			self.methodCombo.append_text(_(methodObj.desc))
		pack(hbox, self.methodCombo)
		pack(self.confDialog.vbox, hbox)
		#######
		self.timeNamesButtons = []
		for name in timeNames:
			desc = _(name.capitalize())
			cb = gtk.CheckButton(label=desc)
			cb.name = name
			self.timeNamesButtons.append(cb)
		vbox = VBox()
		rowHbox = HBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		perRowCount = 3
		cbCount = len(self.timeNamesButtons)
		for index, cb in enumerate(self.timeNamesButtons):
			if index > 0 and index % perRowCount == 0:
				pack(vbox, rowHbox)
				rowHbox = HBox()
			pack(rowHbox, cb)
			if index < cbCount - 1:
				sgroup.add_widget(cb)
		pack(vbox, rowHbox)
		frame = gtk.Frame()
		frame.set_label(_("Shown Times"))
		frame.add(vbox)
		vbox.set_border_width(5)
		frame.set_border_width(5)
		pack(self.confDialog.vbox, frame)
		######
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(label=_("Imsak")))
		spin = gtk.SpinButton()
		spin.set_increments(1, 5)
		spin.set_range(0, 99)
		spin.set_digits(0)
		spin.set_direction(gtk.TextDirection.LTR)
		self.imsakSpin = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(label=_("minutes before fajr")))
		pack(self.confDialog.vbox, hbox)
		######
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(label=_("Separator")))
		textview = gtk.TextView()
		textview.set_wrap_mode(gtk.WrapMode.CHAR)
		if locale_man.rtl:
			textview.set_direction(gtk.TextDirection.RTL)
		self.sepView = textview
		self.sepBuff = textview.get_buffer()
		frame = gtk.Frame()
		frame.set_border_width(4)
		frame.add(textview)
		pack(hbox, frame, 1, 1)
		pack(self.confDialog.vbox, hbox)
		######
		frame = gtk.Frame()
		frame.set_label(_("Azan"))
		vboxFrame = gtk.VBox()
		vboxFrame.set_border_width(5)
		frame.set_border_width(5)
		#####
		####
		hbox1 = gtk.HBox()
		self.preAzanEnableCheck = gtk.CheckButton(label=_("Play Pre-Azan Sound"))
		hbox2 = gtk.HBox()
		self.preAzanEnableCheck.connect(
			"clicked",
			self.updateAzanSensitiveWidgets,
		)
		pack(hbox1, self.preAzanEnableCheck)
		pack(hbox2, gtk.Label(label=_("Pre-Azan Sound") + ":"), padding=20)
		self.preAzanFileButton = gtk.FileChooserButton(title=_("Pre-Azan Sound"))
		self.preAzanEnableCheck.sensitiveWidgets = [self.preAzanFileButton, hbox2]
		pack(hbox1, self.preAzanFileButton, 1, 1)
		##
		spin = gtk.SpinButton()
		spin.set_increments(1, 5)
		spin.set_range(0, 60)
		spin.set_digits(2)
		spin.set_direction(gtk.TextDirection.LTR)
		self.preAzanMinutesSpin = spin
		pack(hbox2, spin)
		##
		pack(hbox2, gtk.Label(label=_("minutes before azan")))
		pack(vboxFrame, hbox1)
		pack(vboxFrame, hbox2, 1, 1)
		#####
		hbox1 = gtk.HBox()
		self.azanEnableCheck = gtk.CheckButton(label=_("Play Azan Sound"))
		hbox2 = gtk.HBox()
		self.azanEnableCheck.connect(
			"clicked",
			self.updateAzanSensitiveWidgets,
		)
		pack(hbox1, self.azanEnableCheck)
		self.azanFileButton = gtk.FileChooserButton(title=_("Azan Sound"))
		self.azanEnableCheck.sensitiveWidgets = [self.azanFileButton]
		pack(hbox1, self.azanFileButton, 1, 1)
		##
		pack(vboxFrame, hbox1, padding=10)
		#####
		frame.add(vboxFrame)
		pack(self.confDialog.vbox, frame)
		######
		self.updateConfWidget()
		###
		cancelB = dialog_add_button(
			self.confDialog,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		okB = dialog_add_button(
			self.confDialog,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		cancelB.connect("clicked", self.confDialogCancel)
		okB.connect("clicked", self.confDialogOk)
		###
		self.confDialog.vbox.show_all()
		##############
		"""
		submenu = gtk.Menu()
		submenu.add(gtk.MenuItem("Item 1"))
		submenu.add(gtk.MenuItem("Item 2"))
		#self.submenu = submenu
		self.menuitem = gtk.MenuItem("Owghat")
		self.menuitem.set_submenu(submenu)
		self.menuitem.show_all()
		"""
		self.dialog = None

	def updateAzanSensitiveWidgets(self, w=None):
		for cb in (self.preAzanEnableCheck, self.azanEnableCheck):
			active = cb.get_active()
			for widget in cb.sensitiveWidgets:
				widget.set_sensitive(active)

	def updateConfWidget(self):
		self.locButton.setLocation(
			self.locName,
			self.backend.lat,
			self.backend.lng,
		)
		self.methodCombo.set_active(
			methodsList.index(self.backend.method)
		)
		###
		for cb in self.timeNamesButtons:
			cb.set_active(cb.name in self.shownTimeNames)
		###
		self.imsakSpin.set_value(self.imsak)
		self.sepBuff.set_text(self.sep)
		buffer_select_all(self.sepBuff)
		###
		self.preAzanEnableCheck.set_active(self.preAzanEnable)
		if self.preAzanFile:
			self.preAzanFileButton.set_filename(self.preAzanFile)
		self.preAzanMinutesSpin.set_value(self.preAzanMinutes)
		##
		self.azanEnableCheck.set_active(self.azanEnable)
		if self.azanFile:
			self.azanFileButton.set_filename(self.azanFile)
		##
		self.updateAzanSensitiveWidgets()

	def updateConfVars(self):
		self.locName = self.locButton.locName
		self.backend.lat = self.locButton.lat
		self.backend.lng = self.locButton.lng
		self.backend.method = methodsList[self.methodCombo.get_active()]
		self.shownTimeNames = [
			cb.name
			for cb in self.timeNamesButtons
			if cb.get_active()
		]
		self.imsak = int(self.imsakSpin.get_value())
		self.sep = buffer_get_text(self.sepBuff)
		self.backend.imsak = str(self.imsak) + " min"
		###
		self.preAzanEnable = self.preAzanEnableCheck.get_active()
		self.preAzanFile = self.preAzanFileButton.get_filename()
		self.preAzanMinutes = self.preAzanMinutesSpin.get_value()
		##
		self.azanEnable = self.azanEnableCheck.get_active()
		self.azanFile = self.azanFileButton.get_filename()

	def confDialogCancel(self, widget=None, gevent=None):
		self.confDialog.hide()
		self.updateConfWidget()

	def confDialogOk(self, widget):
		self.confDialog.hide()
		self.updateConfVars()
		self.saveConfig()

	def set_dialog(self, dialog):
		self.dialog = dialog

	def open_configure(self):
		self.confDialog.run()

	def open_about(self):
		about = AboutDialog(
			name=self.title,
			title=_("About") + " " + self.title,
			authors=self.authors,
			comments=self.about,
		)
		about.connect("delete-event", lambda w, e: about.destroy())
		#about.connect("response", lambda w: about.hide())
		#about.set_skip_taskbar_hint(True)
		about.run()
		about.destroy()
