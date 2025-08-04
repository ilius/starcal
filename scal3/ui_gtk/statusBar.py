from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.color_utils import colorizeSpan
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.mywidgets.label import SLabel
from scal3.ui_gtk.mywidgets.resize_button import ResizeButton

if TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI

__all__ = ["CalObj"]


class LabelWithCalType(SLabel):
	def __init__(self, calType: int, label: str = "") -> None:
		SLabel.__init__(self, label=label)
		self.calType = calType


class CalObj(CustomizableCalObj):
	objName = "statusBar"
	desc = _("Status Bar")
	itemListCustomizable = False
	hasOptions = True
	optionsPageSpacing = 15

	def __init__(self, win: gtk.Window) -> None:
		super().__init__()
		self.parentWin = win

		self.box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.w: gtk.Widget = self.box
		self.initVars()
		# ----
		self.labelBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(self.box, self.labelBox, 1, 1)
		resizeB = ResizeButton(win)
		pack(self.box, resizeB, 0, 0)
		if rtl:
			self.w.set_direction(gtk.TextDirection.LTR)
			self.labelBox.set_direction(gtk.TextDirection.LTR)
		# self.onConfigChange()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		# ---
		for label in self.labelBox.get_children():
			label.destroy()
		# ---
		activeCalTypes = calTypes.active
		if conf.statusBarDatesReverseOrder.v:
			# to not modify calTypes.active
			activeCalTypes = list(reversed(activeCalTypes))
		for calType in activeCalTypes:
			label = LabelWithCalType(calType=calType)
			label.set_direction(gtk.TextDirection.LTR)
			pack(self.labelBox, label, 1)
		self.w.show_all()
		# ---
		self.broadcastDateChange()

	def onDateChange(self) -> None:
		assert ud.dateFormatBin is not None
		super().onDateChange()
		labels = self.labelBox.get_children()
		for label in labels:
			assert isinstance(label, LabelWithCalType), f"{label=}"
			text = ui.cells.current.format(ud.dateFormatBin, label.calType)
			if label.calType == calTypes.primary:
				text = f"<b>{text}</b>"
			if conf.statusBarDatesColorEnable.v:
				text = colorizeSpan(text, conf.statusBarDatesColor.v)
			label.set_label(text)

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.check_mix import CheckColorOptionUI
		from scal3.ui_gtk.option_ui.color import ColorOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		option: OptionUI
		# ----
		option = CheckOptionUI(
			option=conf.statusBarDatesReverseOrder,
			label=_("Reverse the order of dates"),
			live=True,
			onChangeFunc=self.onConfigChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		option = CheckColorOptionUI(
			CheckOptionUI(
				option=conf.statusBarDatesColorEnable, label=_("Dates Color")
			),
			ColorOptionUI(option=conf.statusBarDatesColor, useAlpha=True),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return self.optionsWidget
