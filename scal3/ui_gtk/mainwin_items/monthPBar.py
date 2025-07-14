from __future__ import annotations

from scal3 import ui
from scal3.cal_types import calTypes, to_jd
from scal3.date_utils import monthPlus
from scal3.locale_man import getMonthName, rtl, textNumEncode
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.pbar import MyProgressBar

__all__ = ["CalObj"]


class CalObj(CustomizableCalObj):
	objName = "monthPBar"
	desc = _("Month Progress Bar")
	itemListCustomizable = False
	hasOptions = True

	def __init__(self, win: gtk.Window) -> None:
		self.frame = gtk.Frame()
		self.w: gtk.Widget = self.frame
		self.parentWin = win
		self.frame.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.frame.set_border_width(0)
		self.pbar = MyProgressBar()
		self.frame.add(self.pbar.w)
		self.pbar.w.show()
		self.initVars()

	def onDateChange(self) -> None:
		super().onDateChange()

		calType = conf.monthPBarCalType.v
		if calType == -1:
			calType = calTypes.primary

		dates = ui.cells.current.dates[calType]
		year = dates[0]
		month = dates[1]
		jd0 = to_jd(year, month, 1, calType)
		jd1 = ui.cells.current.jd
		nyear, nmonth = monthPlus(year, month, 1)
		jd2 = to_jd(nyear, nmonth, 1, calType)
		length = jd2 - jd0
		past = jd1 - jd0
		fraction = past / length
		if rtl:
			percent = f"{int(fraction * 100)}%"
		else:
			percent = f"%{int(fraction * 100)}"
		self.pbar.set_text(
			getMonthName(calType, month, year)
			+ ":   "
			+ textNumEncode(
				percent,
				changeDot=True,
			)
			+ "   =   "
			+ _("{dayCount} days").format(dayCount=_(past))
			+ " / "
			+ _("{dayCount} days").format(dayCount=_(length)),
		)
		self.pbar.set_fraction(fraction)

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui_extra import CalTypeOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		option = CalTypeOptionUI(
			option=conf.monthPBarCalType,
			live=True,
			onChangeFunc=self.onCalTypeChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onCalTypeChange(self) -> None:
		self.onDateChange()
