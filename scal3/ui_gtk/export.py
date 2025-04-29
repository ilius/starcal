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

from scal3 import logger

log = logger.get()

__all__ = ["ExportDialog", "ExportToIcsDialog"]

from scal3 import core, locale_man, ui
from scal3.cal_types import calTypes
from scal3.export import exportToHtml
from scal3.locale_man import tr as _
from scal3.monthcal import getCurrentMonthStatus, getMonthStatus
from scal3.path import homeDir
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.year_month import YearMonthButton
from scal3.ui_gtk.utils import dialog_add_button, openWindow


class ExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Export to {format}").format(format="HTML"))
		# parent=None FIXME
		# self.set_has_separator(False)
		# --------
		hbox = HBox(spacing=2)
		pack(hbox, gtk.Label(label=_("Month Range")))
		combo = gtk.ComboBoxText()
		for t in ("Current Month", "Whole Current Year", "Custom"):
			combo.append_text(_(t))
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		self.combo = combo
		# ---
		hbox2 = HBox(spacing=2)
		pack(hbox2, gtk.Label(label=_("from month")))
		self.ymBox0 = YearMonthButton()
		pack(hbox2, self.ymBox0)
		pack(hbox2, gtk.Label(), 1, 1)
		pack(hbox2, gtk.Label(label=_("to month")))
		self.ymBox1 = YearMonthButton()
		pack(hbox2, self.ymBox1)
		pack(hbox, hbox2, 1, 1)
		self.hbox2 = hbox2
		combo.set_active(0)
		pack(self.vbox, hbox)
		# --------
		hbox = HBox(spacing=2)
		pack(hbox, gtk.Label(label=_("Font size scale")))
		self.fontScaleSpin = FloatSpinButton(0.01, 100, 2)
		self.fontScaleSpin.set_value(1)
		pack(hbox, self.fontScaleSpin)
		pack(self.vbox, hbox)
		# --------
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		pack(self.vbox, self.fcw, 1, 1)
		self.vbox.set_focus_child(self.fcw)  # FIXME
		self.vbox.show_all()
		combo.connect("changed", self.comboChanged)
		# --
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
			onClick=self.onDelete,
		)
		dialog_add_button(
			self,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
			onClick=self.save,
		)
		# --
		self.connect("delete-event", self.onDelete)
		self.fcw.set_current_folder(homeDir)

	def comboChanged(self, _widget=None, ym=None):
		i = self.combo.get_active()
		if ym is None:
			ym = (ui.cells.current.year, ui.cells.current.month)
		if i == 0:
			self.fcw.set_current_name(f"calendar-{ym[0]:04d}-{ym[1]:02d}.html")
			self.hbox2.hide()
		elif i == 1:
			self.fcw.set_current_name(f"calendar-{ym[0]:04d}.html")
			self.hbox2.hide()
		else:  # elif i==2
			self.fcw.set_current_name("calendar.html")
			self.hbox2.show()
		# select_region(0, -4) # FIXME

	def onDelete(self, _widget=None, _event=None):
		# hide(close) File Chooser Dialog
		self.hide()
		return True

	def _save(self, path):
		comboItem = self.combo.get_active()
		months = []
		fontSizeScale = self.fontScaleSpin.get_value()
		if comboItem == 0:
			s = getCurrentMonthStatus()
			months = [s]
			title = (
				locale_man.getMonthName(
					calTypes.primary,
					s.month,
					s.year,
				)
				+ " "
				+ _(s.year)
			)
		elif comboItem == 1:
			for i in range(1, 13):
				months.append(getMonthStatus(ui.cells.current.year, i))
			title = _("Calendar {year}").format(year=_(ui.cells.current.year))
		elif comboItem == 2:
			y0, m0 = self.ymBox0.get_value()
			y1, m1 = self.ymBox1.get_value()
			for ym in range(y0 * 12 + m0 - 1, y1 * 12 + m1):
				y, m = divmod(ym, 12)
				m += 1
				months.append(getMonthStatus(y, m))
			title = _("Calendar")
		exportToHtml(
			path,
			months,
			title=title,
			fontSizeScale=fontSizeScale,
		)
		self.hide()

	def save(self, _widget=None):
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		path = self.fcw.get_filename()
		if path in {None, ""}:
			return
		log.info(f'Exporting to html file "{path}"')
		self.waitingDo(
			self._save,
			path,
		)

	def showDialog(self, year, month):
		self.comboChanged(ym=(year, month))
		self.ymBox0.set_value((year, month))
		self.ymBox1.set_value((year, month))
		self.resize(1, 1)
		openWindow(self)

	"""
	def exportSvg(self, path, monthList):-- FIXME
		# monthList is a list of tuples (year, month)
		#import cairo
		hspace = 20
		mcal = ui.mainWin.mcal
		aloc = mcal.get_allocation()
		n = len(monthList)
		w = aloc.width
		h = n * aloc.height + (n - 1) * hspace
		surface = cairo.SVGSurface(f"{path}.svg", w, h)
		cr = cairo.Context(surface)
		year = ui.cells.current.year
		month = ui.cells.current.month
		day = self.mcal.day
		ui.mainWin.show() # ??????????????
		for i in range(n):
			surface.set_device_offset(0, i*(h0+hspace))
			mcal.dateChange((monthList[i][0], monthList[i][1], 1))
			mcal.drawAll(cr=cr, cursor=False)
			mcal.queue_draw()
		ui.mainWin.dateChange((year, month, day))
		surface.flush()
		surface.finish()
	"""


class ExportToIcsDialog(gtk.Dialog, MyDialog):
	def __init__(self, saveIcsFunc, defaultFileName, **kwargs):
		self.saveIcsFunc = saveIcsFunc
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Export to {format}").format(format="iCalendar"))
		# parent=None FIXME
		# self.set_has_separator(False)
		# --------
		hbox = HBox(spacing=2)
		pack(hbox, gtk.Label(label=_("From", ctx="time range") + " "))
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		pack(hbox, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		pack(self.vbox, hbox)
		# ----
		year, _month, _day = ui.cells.today.dates[calTypes.primary]
		self.startDateInput.set_value((year, 1, 1))
		self.endDateInput.set_value((year + 1, 1, 1))
		# --------
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		pack(self.vbox, self.fcw, 1, 1)
		self.vbox.set_focus_child(self.fcw)  # FIXME
		self.vbox.show_all()
		# --
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
			onClick=self.onDelete,
		)
		dialog_add_button(
			self,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
			onClick=self.save,
		)
		# --
		self.connect("delete-event", self.onDelete)
		self.fcw.connect("file-activated", self.save)  # not working FIXME
		# --
		self.fcw.set_current_folder(homeDir)
		if not defaultFileName.endswith(".ics"):
			defaultFileName += ".ics"
		self.fcw.set_current_name(defaultFileName)

	def onDelete(self, _widget=None, _event=None):  # hide(close) File Chooser Dialog
		self.destroy()
		return True

	def _save(self, path, startJd, endJd):
		self.saveIcsFunc(path, startJd, endJd)
		self.destroy()

	def save(self, _widget=None):
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		path = self.fcw.get_filename()
		if path in {None, ""}:
			return
		log.info(f'Exporting to ics file "{path}"')
		self.waitingDo(
			self._save,
			path,
			core.primary_to_jd(*self.startDateInput.get_value()),
			core.primary_to_jd(*self.endDateInput.get_value()),
		)
