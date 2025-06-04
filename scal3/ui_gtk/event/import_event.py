from __future__ import annotations

from typing import Any

from scal3 import logger

log = logger.get()

import json
import sys

from gi.repository import Gtk as gtk

from scal3 import ui
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.path import deskDir
from scal3.ui_gtk import HBox, VBox, gdk, pack
from scal3.ui_gtk.wizard import WizardWindow

__all__ = ["EventsImportWindow"]

type EventManagerType = gtk.Dialog


class EventsImportWindow(WizardWindow):
	def __init__(self, manager: EventManagerType) -> None:
		self.manager = manager
		WizardWindow.__init__(self, _("Import Events", ctx="window title"))
		self.set_type_hint(gdk.WindowTypeHint.DIALOG)
		# self.set_property("skip-taskbar-hint", True)
		# self.set_modal(True)
		# self.set_transient_for(manager)
		# self.set_destroy_with_parent(True)
		self.resize(400, 200)

	class FirstStep(gtk.Box):
		desc = ""

		def getWidget(self) -> gtk.Widget:
			return self

		def __init__(self, win: gtk.Window) -> None:
			gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_("Cancel"), self.onCancelClick),
				(_("Next"), self.onNextClick),
			)
			# ----
			hbox = HBox(spacing=10)
			frame = gtk.Frame()
			frame.set_label(_("Format"))
			# frame.set_border_width(10)
			radioBox = VBox(spacing=10)
			radioBox.set_border_width(10)
			# --
			self.radioJson = gtk.RadioButton(label=_("JSON (StarCalendar)"))
			# self.radioIcs = gtk.RadioButton(label="iCalendar", group=self.radioJson)
			# --
			pack(radioBox, self.radioJson)
			# pack(radioBox, self.radioIcs)
			# --
			self.radioJson.set_active(True)
			# self.radioJson.connect("clicked", self.formatRadioChanged)
			# self.radioIcs.connect("clicked", self.formatRadioChanged)
			# --
			frame.add(radioBox)
			pack(hbox, frame, 0, 0, 10)
			pack(hbox, gtk.Label(), 1, 1)
			pack(self, hbox)
			# ----
			hbox = HBox()
			pack(hbox, gtk.Label(label=_("File") + ":"))
			self.fcb = gtk.FileChooserButton(title=_("Import: Select File"))
			self.fcb.set_local_only(True)
			self.fcb.set_current_folder(deskDir)
			pack(hbox, self.fcb, 1, 1)
			pack(self, hbox)
			# ----
			self.show_all()

		def run(self) -> None:
			pass

		def onCancelClick(self, _obj: Any) -> None:
			self.win.destroy()

		def onNextClick(self, _obj: Any) -> None:
			fpath = self.fcb.get_filename()
			if not fpath:
				return
			if self.radioJson.get_active():
				format_ = "json"
			# elif self.radioIcs.get_active():
			# 	format_ = "ics"
			else:
				return
			self.win.showStep(1, format_, fpath)

	class SecondStep(gtk.Box):
		desc = ""

		def getWidget(self) -> gtk.Widget:
			return self

		def __init__(self, win: gtk.Window) -> None:
			gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_("Back"), self.onBackClick),
				(_("Close"), self.onCloseClick),
			)
			# ----
			self.textview = gtk.TextView()
			pack(self, self.textview, 1, 1)
			# ----
			self.show_all()

		def redirectStdOutErr(self) -> None:
			from scal3.ui_gtk.buffer import GtkBufferFile

			t_table = gtk.TextTagTable()
			tag_out = gtk.TextTag(name="output")
			t_table.add(tag_out)
			tag_err = gtk.TextTag(name="error")
			t_table.add(tag_err)
			self.buffer: gtk.TextBuffer = self.textview.get_buffer()
			self.out_fp = GtkBufferFile(self.buffer, tag_out)
			sys.stdout = self.out_fp
			self.err_fp = GtkBufferFile(self.buffer, tag_err)
			sys.stderr = self.err_fp

		@staticmethod
		def restoreStdOutErr() -> None:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

		def run(self, format_: str, fpath: str) -> None:
			self.redirectStdOutErr()
			self.win.waitingDo(self._runAndCleanup, format_, fpath)

		def _runAndCleanup(self, format_: str, fpath: str) -> None:
			try:
				if format_ == "json":
					self._runJson(fpath)
				else:
					raise ValueError(f"invalid format {format_!r}")
			finally:
				self.restoreStdOutErr()

		@staticmethod
		def _runJson(fpath: str) -> None:
			try:
				with open(fpath, encoding="utf-8") as fp:
					text = fp.read()
			except Exception as e:
				sys.stderr.write(f"{_('Error in reading file')}\n{e}\n")
				return

			try:
				data = json.loads(text)
			except Exception as e:
				sys.stderr.write(f"{_('Error in loading JSON data')}\n{e}\n")
			else:
				try:
					res = ev.groups.importData(data)
				except Exception as e:
					sys.stderr.write(f"{_('Error in importing events')}\n{e}\n")
					log.exception("")
				else:
					for gid in res.newGroupIds:
						group = ev.groups[gid]
						ui.eventUpdateQueue.put("+g", group, None)
					# TODO: res.newEventIds
					# TODO: res.modifiedEventIds
					msg = _(
						"Imported successfuly: {newGroupCount} new groups"
						", {newEventCount} new events"
						", {modifiedEventCount} modified events",
					)
					print(  # noqa: T201
						msg.format(
							newGroupCount=_(len(res.newGroupIds)),
							newEventCount=_(len(res.newEventIds)),
							modifiedEventCount=_(len(res.modifiedEventIds)),
						),
					)

		def onBackClick(self, _obj: Any) -> None:
			self.win.showStep(0)

		def onCloseClick(self, _obj: Any) -> None:
			self.win.destroy()

	stepClasses = [
		FirstStep,
		SecondStep,
	]
