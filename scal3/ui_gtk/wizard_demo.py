from __future__ import annotations

from scal3 import logger

log = logger.get()

from scal3.locale_man import tr as _
from scal3.path import deskDir
from scal3.ui_gtk import HBox, VBox, gdk, gtk, pack
from scal3.ui_gtk.wizard import WizardWindow


class DemoWizardWindow(WizardWindow):
	def __init__(self) -> None:
		WizardWindow.__init__(self, _("Demo for WizardWindow"))
		self.set_type_hint(gdk.WindowTypeHint.DIALOG)
		# self.set_property("skip-taskbar-hint", True)
		# self.set_modal(True)
		# self.set_transient_for(manager)
		# self.set_destroy_with_parent(True)
		self.resize(400, 400)

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

		def onCancelClick(self, _w: gtk.Widget) -> None:
			self.win.destroy()

		def onNextClick(self, _w: gtk.Widget) -> None:
			fpath = self.fcb.get_filename()
			format_ = None
			if self.radioJson.get_active():
				format_ = "json"
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

		def run(self, format_: str, fpath: str) -> None:
			self.win.waitingDo(self._runAndCleanup, format_, fpath)

		def _runAndCleanup(self, format_: str, fpath: str) -> None:
			if format_ == "json":
				self._runJson(fpath)
			else:
				raise ValueError(f"invalid format {format_!r}")

		def _runJson(self, fpath: str) -> None:  # noqa: PLR6301
			print(f"_runAndCleanup: {fpath=}")  # noqa: T201

		def onBackClick(self, _w: gtk.Widget) -> None:
			self.win.showStep(0)

		def onCloseClick(self, _w: gtk.Widget) -> None:
			self.win.destroy()

	stepClasses = [
		FirstStep,
		SecondStep,
	]


if __name__ == "__main__":
	DemoWizardWindow().present()
	gtk.main()
