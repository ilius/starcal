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

from scal3 import core, ui
from scal3.cal_types import calTypes
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.event.occurrence_view import DayOccurrenceView
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.mywidgets.label import SLabel
from scal3.ui_gtk.utils import dialog_add_button

__all__ = ["DayInfoDialog"]


class AllDateLabelsVBox(CustomizableCalObj):
	objName = "allDateLabels"
	desc = _("Dates")

	def __init__(self) -> None:
		super().__init__()
		self.w: gtk.Box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
		self.initVars()

	def onDateChange(self) -> None:
		super().onDateChange()
		assert ud.dateFormatBin is not None
		for child in self.w.get_children():
			child.destroy()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupDate = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for i, module in calTypes.iterIndexModule():
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			label = gtk.Label(label=_(module.desc, ctx="calendar"))
			label.set_xalign(0)
			pack(hbox, label)
			sgroup.add_widget(label)
			pack(hbox, gtk.Label(label="  "))
			# ---
			dateLabel = SLabel(label=ui.cells.current.format(ud.dateFormatBin, i))
			dateLabel.set_selectable(True)
			dateLabel.set_xalign(1.0 if rtl else 0.0)
			pack(hbox, dateLabel)
			sgroupDate.add_widget(dateLabel)
			# ---
			pack(self.w, hbox)
		self.w.show_all()


class PluginsTextView(CustomizableCalObj):
	objName = "pluginsText"
	desc = _("Plugins Text")

	def __init__(self) -> None:
		super().__init__()
		self.w: gtk.TextView = gtk.TextView()
		self.initVars()
		# ---
		self.w.set_wrap_mode(gtk.WrapMode.WORD)
		self.w.set_editable(False)
		self.w.set_cursor_visible(False)
		self.w.set_justification(gtk.Justification.CENTER)

	def onDateChange(self) -> None:
		super().onDateChange()
		self.w.get_buffer().set_text(ui.cells.current.getPluginsText())


class DayInfoJulianDayHBox(CustomizableCalObj):
	objName = "jd"
	desc = _("Julian Day Number")

	def __init__(self) -> None:
		super().__init__()
		self.w: gtk.Box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		# ---
		pack(self.w, gtk.Label(label=_("Julian Day Number") + ":  "))
		self.jdLabel = SLabel()
		self.jdLabel.set_selectable(True)
		pack(self.w, self.jdLabel)
		pack(self.w, gtk.Label(), 1, 1)
		# ---
		self.w.show_all()

	def onDateChange(self) -> None:
		super().onDateChange()
		self.jdLabel.set_label(str(ui.cells.current.jd))


class DayInfoDialog(CustomizableCalObj):
	objName = "dayInfo"
	desc = _("Day Info")

	def __init__(self, transient_for: gtk.Window | None = None) -> None:
		self.w: Dialog = Dialog(transient_for=transient_for)
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		self.w.set_title(_("Day Info"))
		self.w.connect("delete-event", self.onDeleteEvent)
		self.w.vbox.set_spacing(15)
		# ---
		dialog_add_button(
			self.w,
			res=0,
			label=_("Close"),
			imageName="window-close.svg",
			onClick=self.onClose,
		)
		dialog_add_button(
			self.w,
			res=1,
			label=_("Previous"),
			imageName="go-previous.svg",
			onClick=self.goBack,
		)
		dialog_add_button(
			self.w,
			res=2,
			label=_("Today"),
			imageName="go-home.svg",
			onClick=self.goToday,
		)
		dialog_add_button(
			self.w,
			res=3,
			label=_("Next"),
			imageName="go-next.svg",
			onClick=self.goNext,
		)
		# ---
		self.appendDayInfoItem(AllDateLabelsVBox())
		self.appendDayInfoItem(DayInfoJulianDayHBox(), expander=False)
		self.appendDayInfoItem(PluginsTextView())
		self.appendDayInfoItem(DayOccurrenceView())
		# ---
		self.w.vbox.show_all()

	def appendDayInfoItem(
		self,
		item: CustomizableCalObj,
		expander: bool = True,
	) -> None:
		self.appendItem(item)
		# ---
		widget: gtk.Widget = item.w
		if expander:
			exp = ExpanderFrame(
				label=item.desc,
				# expanded=True,
			)
			exp.add(item.w)
			widget = exp
		pack(self.w.vbox, widget)

	def onDeleteEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> bool:
		self.hide()
		return True

	def onClose(self, _w: gtk.Widget) -> None:
		self.hide()

	def goBack(self, _w: gtk.Widget | None = None) -> None:
		ui.cells.jdPlus(-1)
		self.broadcastDateChange()

	def goToday(self, _w: gtk.Widget | None = None) -> None:
		ui.cells.gotoJd(core.getCurrentJd())
		self.broadcastDateChange()

	def goNext(self, _w: gtk.Widget | None = None) -> None:
		ui.cells.jdPlus(1)
		self.broadcastDateChange()
