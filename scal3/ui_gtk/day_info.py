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


from scal3 import core, ui
from scal3.cal_types import calTypes
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.event.occurrence_view import DayOccurrenceView
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.mywidgets.label import SLabel
from scal3.ui_gtk.utils import dialog_add_button

__all__ = ["DayInfoDialog"]


@registerSignals
class AllDateLabelsVBox(gtk.Box, ud.BaseCalObj):
	objName = "allDateLabels"
	desc = _("Dates")

	def __init__(self) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL, spacing=5)
		self.initVars()

	def onDateChange(self, *a, **ka) -> None:
		ud.BaseCalObj.onDateChange(self, *a, **ka)
		for child in self.get_children():
			child.destroy()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupDate = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for i, module in calTypes.iterIndexModule():
			hbox = HBox()
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
			pack(self, hbox)
		self.show_all()


@registerSignals
class PluginsTextView(gtk.TextView, ud.BaseCalObj):
	objName = "pluginsText"
	desc = _("Plugins Text")

	def __init__(self) -> None:
		gtk.TextView.__init__(self)
		self.initVars()
		# ---
		self.set_wrap_mode(gtk.WrapMode.WORD)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.set_justification(gtk.Justification.CENTER)

	def onDateChange(self, *a, **ka) -> None:
		ud.BaseCalObj.onDateChange(self, *a, **ka)
		self.get_buffer().set_text(ui.cells.current.getPluginsText())


@registerSignals
class DayInfoJulianDayHBox(gtk.Box, ud.BaseCalObj):
	objName = "jd"
	desc = _("Julian Day Number")

	def __init__(self) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		# ---
		pack(self, gtk.Label(label=_("Julian Day Number") + ":  "))
		self.jdLabel = SLabel()
		self.jdLabel.set_selectable(True)
		pack(self, self.jdLabel)
		pack(self, gtk.Label(), 1, 1)
		# ---
		self.show_all()

	def onDateChange(self, *a, **ka) -> None:
		ud.BaseCalObj.onDateChange(self, *a, **ka)
		self.jdLabel.set_label(str(ui.cells.current.jd))


@registerSignals
class DayInfoDialog(gtk.Dialog, ud.BaseCalObj):
	objName = "dayInfo"
	desc = _("Day Info")

	def __init__(self, **kwargs) -> None:
		gtk.Dialog.__init__(self, **kwargs)
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		self.set_title(_("Day Info"))
		self.connect("delete-event", self.onClose)
		self.vbox.set_spacing(15)
		# ---
		dialog_add_button(
			self,
			label=_("Close"),
			imageName="window-close.svg",
			res=0,
			onClick=self.onClose,
		)
		dialog_add_button(
			self,
			label=_("Previous"),
			imageName="go-previous.svg",
			res=1,
			onClick=self.goBack,
		)
		dialog_add_button(
			self,
			label=_("Today"),
			imageName="go-home.svg",
			res=2,
			onClick=self.goToday,
		)
		dialog_add_button(
			self,
			label=_("Next"),
			imageName="go-next.svg",
			res=3,
			onClick=self.goNext,
		)
		# ---
		self.appendDayInfoItem(AllDateLabelsVBox())
		self.appendDayInfoItem(DayInfoJulianDayHBox(), expander=False)
		self.appendDayInfoItem(PluginsTextView())
		self.appendDayInfoItem(DayOccurrenceView())
		# ---
		self.vbox.show_all()

	def appendDayInfoItem(self, item, expander=True) -> None:
		self.appendItem(item)
		# ---
		widget = item
		if expander:
			exp = ExpanderFrame(
				label=item.desc,
				# expanded=True,
			)
			exp.add(item)
			widget = exp
		pack(self.vbox, widget)

	def onClose(self, _obj=None, _gevent=None) -> bool:
		self.hide()
		return True

	def goBack(self, _obj=None) -> None:
		ui.cells.jdPlus(-1)
		self.onDateChange()

	def goToday(self, _obj=None) -> None:
		ui.cells.gotoJd(core.getCurrentJd())
		self.onDateChange()

	def goNext(self, _obj=None) -> None:
		ui.cells.jdPlus(1)
		self.onDateChange()
