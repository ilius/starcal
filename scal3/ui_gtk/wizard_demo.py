#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import sys

from scal3.path import deskDir
from scal3.json_utils import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.wizard import WizardWindow
from scal3.ui_gtk.mywidgets.dialog import MyDialog


class DemoWizardWindow(WizardWindow):
	def __init__(self):
		WizardWindow.__init__(self, _("Demo for WizardWindow"))
		self.set_type_hint(gdk.WindowTypeHint.DIALOG)
		#self.set_property("skip-taskbar-hint", True)
		#self.set_modal(True)
		#self.set_transient_for(manager)
		#self.set_destroy_with_parent(True)
		self.resize(400, 400)

	class FirstStep(gtk.Box):
		desc = ""
		def __init__(self, win):
			gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_("Cancel"), self.onCancelClick),
				(_("Next"), self.onNextClick),
			)
			####
			hbox = HBox(spacing=10)
			frame = gtk.Frame()
			frame.set_label(_("Format"))
			#frame.set_border_width(10)
			radioBox = VBox(spacing=10)
			radioBox.set_border_width(10)
			##
			self.radioJson = gtk.RadioButton(label=_("JSON (StarCalendar)"))
			#self.radioIcs = gtk.RadioButton(label="iCalendar", group=self.radioJson)
			##
			pack(radioBox, self.radioJson)
			#pack(radioBox, self.radioIcs)
			##
			self.radioJson.set_active(True)
			#self.radioJson.connect("clicked", self.formatRadioChanged)
			##self.radioIcs.connect("clicked", self.formatRadioChanged)
			##
			frame.add(radioBox)
			pack(hbox, frame, 0, 0, 10)
			pack(hbox, gtk.Label(), 1, 1)
			pack(self, hbox)
			####
			hbox = HBox()
			pack(hbox, gtk.Label(label=_("File") + ":"))
			self.fcb = gtk.FileChooserButton(title=_("Import: Select File"))
			self.fcb.set_local_only(True)
			self.fcb.set_current_folder(deskDir)
			pack(hbox, self.fcb, 1, 1)
			pack(self, hbox)
			####
			self.show_all()

		def run(self):
			pass

		def onCancelClick(self, obj):
			self.win.destroy()

		def onNextClick(self, obj):
			fpath = self.fcb.get_filename()
			format = None
			if self.radioJson.get_active():
				format = "json"
			self.win.showStep(1, format, fpath)

	class SecondStep(gtk.Box):
		desc = ""
		def __init__(self, win):
			gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_("Back"), self.onBackClick),
				(_("Close"), self.onCloseClick),
			)
			####
			self.textview = gtk.TextView()
			pack(self, self.textview, 1, 1)
			####
			self.show_all()

		def run(self, format, fpath):
			self.win.waitingDo(self._runAndCleanup, format, fpath)

		def _runAndCleanup(self, format, fpath):
			if format == "json":
				self._runJson(fpath)
			else:
				raise ValueError(f"invalid format {format!r}")

		def _runJson(self, fpath):
			print(f"_runAndCleanup: fpath={fpath}")

		def onBackClick(self, obj):
			self.win.showStep(0)

		def onCloseClick(self, obj):
			self.win.destroy()

	stepClasses = [
		FirstStep,
		SecondStep,
	]


if __name__ == "__main__":
	DemoWizardWindow().present()
	gtk.main()
