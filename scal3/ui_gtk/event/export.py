#!/usr/bin/env python3
from os.path import join, split, splitext

from scal3.path import deskDir
from scal3.json_utils import *
from scal3 import cal_types
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.event.common import GroupsTreeCheckList


class SingleGroupExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, group, **kwargs):
		self._group = group
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Export Group"))
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		self.connect("response", lambda w, e: self.hide())
		####
		hbox = HBox()
		frame = gtk.Frame()
		frame.set_label(_("Format"))
		radioBox = VBox()
		##
		self.radioIcs = gtk.RadioButton(label="iCalendar")
		self.radioJsonCompact = gtk.RadioButton(
			label=_("Compact JSON (StarCalendar)"),
			group=self.radioIcs,
		)
		self.radioJsonPretty = gtk.RadioButton(
			label=_("Pretty JSON (StarCalendar)"),
			group=self.radioIcs,
		)
		##
		pack(radioBox, self.radioJsonCompact)
		pack(radioBox, self.radioJsonPretty)
		pack(radioBox, self.radioIcs)
		##
		self.radioJsonCompact.set_active(True)
		self.radioIcs.connect("clicked", self.formatRadioChanged)
		self.radioJsonCompact.connect("clicked", self.formatRadioChanged)
		self.radioJsonPretty.connect("clicked", self.formatRadioChanged)
		##
		frame.add(radioBox)
		pack(hbox, frame)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		########
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		self.fcw.set_current_folder(deskDir)
		pack(self.vbox, self.fcw, 1, 1)
		####
		self.vbox.show_all()
		self.formatRadioChanged()

	def formatRadioChanged(self, widget=None):
		from scal3.os_utils import fixStrForFileName
		fpath = self.fcw.get_filename()
		if fpath:
			fname_nox, ext = splitext(split(fpath)[1])
		else:
			fname_nox, ext = "", ""
		if not fname_nox:
			fname_nox = fixStrForFileName(self._group.title)
		if self.radioIcs.get_active():
			if ext != ".ics":
				ext = ".ics"
		else:
			if ext != ".json":
				ext = ".json"
		self.fcw.set_current_name(fname_nox + ext)

	def save(self):
		fpath = self.fcw.get_filename()
		if self.radioJsonCompact.get_active():
			text = dataToCompactJson(
				ui.eventGroups.exportData([self._group.id]),
			)
			with open(fpath, "w", encoding="utf-8") as _file:
				_file.write(text)
		elif self.radioJsonPretty.get_active():
			text = dataToPrettyJson(
				ui.eventGroups.exportData([self._group.id]),
			)
			with open(fpath, "w", encoding="utf-8") as _file:
				_file.write(text)
		elif self.radioIcs.get_active():
			ui.eventGroups.exportToIcs(
				fpath,
				[self._group.id],
			)

	def run(self):
		if gtk.Dialog.run(self) == gtk.ResponseType.OK:
			self.waitingDo(self.save)
		self.destroy()


class MultiGroupExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Export"))
		self.vbox.set_spacing(10)
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		####
		hbox = HBox()
		frame = gtk.Frame()
		frame.set_label(_("Format"))
		radioBox = VBox()
		##
		self.radioIcs = gtk.RadioButton(
			label="iCalendar",
		)
		self.radioJsonCompact = gtk.RadioButton(
			label=_("Compact JSON (StarCalendar)"),
			group=self.radioIcs,
		)
		self.radioJsonPretty = gtk.RadioButton(
			label=_("Pretty JSON (StarCalendar)"),
			group=self.radioIcs,
		)
		##
		pack(radioBox, self.radioJsonCompact)
		pack(radioBox, self.radioJsonPretty)
		pack(radioBox, self.radioIcs)
		##
		self.radioJsonCompact.set_active(True)
		self.radioIcs.connect("clicked", self.formatRadioChanged)
		self.radioJsonCompact.connect("clicked", self.formatRadioChanged)
		self.radioJsonPretty.connect("clicked", self.formatRadioChanged)
		####
		frame.add(radioBox)
		pack(hbox, frame)
		pack(hbox, gtk.Label(), 1, 1)
		####
		hButtonBox = VBox()
		pack(hButtonBox, gtk.Label(), 1, 1)
		##
		button = gtk.Button(label=_("Disable All"))
		button.connect("clicked", self.disableAllClicked)
		pack(hButtonBox, button)
		##
		button = gtk.Button(label=_("Enable All"))
		button.connect("clicked", self.enableAllClicked)
		pack(hButtonBox, button)
		##
		hButtonBox.show_all()
		pack(hbox, hButtonBox)
		##
		pack(self.vbox, hbox)
		########
		hbox = HBox(spacing=2)
		pack(hbox, gtk.Label(label=_("File") + ":"))
		self.fpathEntry = gtk.Entry()
		y, m, d = cal_types.getSysDate(core.GREGORIAN)
		self.fpathEntry.set_text(join(
			deskDir,
			f"events-{y:04d}-{m:02d}-{d:02d}",
		))
		pack(hbox, self.fpathEntry, 1, 1)
		pack(self.vbox, hbox)
		####
		self.groupSelect = GroupsTreeCheckList()
		swin = gtk.ScrolledWindow()
		swin.add(self.groupSelect)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(self.vbox, swin, 1, 1)
		####
		self.vbox.show_all()
		self.formatRadioChanged()
		self.resize(600, 600)

	def disableAllClicked(self, widget=None):
		self.groupSelect.disableAll()

	def enableAllClicked(self, widget=None):
		self.groupSelect.enableAll()

	def formatRadioChanged(self, widget=None):
		#self.dateRangeBox.set_visible(self.radioIcs.get_active())
		###
		fpath = self.fpathEntry.get_text()
		if fpath:
			fpath_nox, ext = splitext(fpath)
			if fpath_nox:
				if self.radioIcs.get_active():
					if ext != ".ics":
						ext = ".ics"
				else:
					if ext != ".json":
						ext = ".json"
				self.fpathEntry.set_text(fpath_nox + ext)

	def save(self):
		fpath = self.fpathEntry.get_text()
		activeGroupIds = self.groupSelect.getValue()
		if self.radioIcs.get_active():
			ui.eventGroups.exportToIcs(fpath, activeGroupIds)
		else:
			data = ui.eventGroups.exportData(activeGroupIds)
			# FIXME: what to do with all groupData["info"] s?
			if self.radioJsonCompact.get_active():
				text = dataToCompactJson(data)
			elif self.radioJsonPretty.get_active():
				text = dataToPrettyJson(data)
			else:
				raise RuntimeError
			with open(fpath, "w", encoding="utf-8") as _file:
				_file.write(text)

	def run(self):
		if gtk.Dialog.run(self) == gtk.ResponseType.OK:
			self.waitingDo(self.save)
		self.destroy()


class EventListExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, idsList, defaultFileName="", groupTitle="", **kwargs):
		self._idsList = idsList
		self._defaultFileName = defaultFileName
		self._groupTitle = groupTitle
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Export Group"))
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		self.connect("response", lambda w, e: self.hide())
		####
		hbox = HBox()
		frame = gtk.Frame()
		frame.set_label(_("Format"))
		radioBox = VBox()
		##
		self.radioJsonCompact = gtk.RadioButton(
			label=_("Compact JSON (StarCalendar)"),
		)
		self.radioJsonPretty = gtk.RadioButton(
			label=_("Pretty JSON (StarCalendar)"),
			group=self.radioJsonCompact,
		)
		#self.radioIcs = gtk.RadioButton(label="iCalendar")
		##
		pack(radioBox, self.radioJsonCompact)
		pack(radioBox, self.radioJsonPretty)
		#pack(radioBox, self.radioIcs)
		##
		self.radioJsonCompact.set_active(True)
		#self.radioIcs.connect("clicked", self.formatRadioChanged)
		self.radioJsonCompact.connect("clicked", self.formatRadioChanged)
		self.radioJsonPretty.connect("clicked", self.formatRadioChanged)
		##
		frame.add(radioBox)
		pack(hbox, frame)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		########
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		self.fcw.set_current_folder(deskDir)
		pack(self.vbox, self.fcw, 1, 1)
		####
		self.vbox.show_all()
		self.formatRadioChanged()

	def formatRadioChanged(self, widget=None):
		from scal3.os_utils import fixStrForFileName
		fpath = self.fcw.get_filename()
		if fpath:
			fname_nox, ext = splitext(split(fpath)[1])
		else:
			fname_nox, ext = "", ""
		if not fname_nox:
			fname_nox = self._defaultFileName
		#if self.radioIcs.get_active():
		#	if ext != ".ics":
		#		ext = ".ics"
		#else:
		if ext != ".json":
			ext = ".json"
		self.fcw.set_current_name(fname_nox + ext)

	def save(self):
		fpath = self.fcw.get_filename()
		#if self.radioIcs.get_active():
		#	pass

		data = ui.eventGroups.eventListExportData(
			self._idsList,
			groupTitle=self._groupTitle,
		)

		if self.radioJsonCompact.get_active():
			text = dataToCompactJson(data)
		elif self.radioJsonPretty.get_active():
			text = dataToPrettyJson(data)
		else:
			RuntimeError("no format is selected")

		with open(fpath, "w", encoding="utf-8") as _file:
			_file.write(text)

	def run(self):
		if gtk.Dialog.run(self) == gtk.ResponseType.OK:
			self.waitingDo(self.save)
		self.destroy()
