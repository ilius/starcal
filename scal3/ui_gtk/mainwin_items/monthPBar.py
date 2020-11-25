#!/usr/bin/env python3

from scal3.date_utils import monthPlus
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, textNumEncode, getMonthName
from scal3.cal_types import calTypes, to_jd
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.pbar import MyProgressBar
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(gtk.Frame, CustomizableCalObj):
	_name = "monthPBar"
	desc = _("Month Progress Bar")
	itemListCustomizable = False
	hasOptions = True

	def __init__(self, win):
		self.win = win
		gtk.Frame.__init__(self)
		self.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.set_border_width(0)
		self.pbar = MyProgressBar()
		self.add(self.pbar)
		self.pbar.show()
		self.initVars()

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)

		calType = ui.monthPBarCalType
		if calType == -1:
			calType = calTypes.primary

		dates = ui.cell.dates[calType]
		year = dates[0]
		month = dates[1]
		jd0 = to_jd(year, month, 1, calType)
		jd1 = ui.cell.jd
		nyear, nmonth = monthPlus(year, month, 1)
		jd2 = to_jd(nyear, nmonth, 1, calType)
		length = jd2 - jd0
		past = jd1 - jd0
		fraction = float(past) / length
		if rtl:
			percent = f"{int(fraction * 100)}%"
		else:
			percent = f"%{int(fraction * 100)}"
		self.pbar.set_text(
			getMonthName(calType, month, year) +
			":   " +
			textNumEncode(
				percent,
				changeDot=True,
			) +
			"   =   " +
			_("{dayCount} days").format(dayCount=_(past)) +
			" / " +
			_("{dayCount} days").format(dayCount=_(length))
		)
		self.pbar.set_fraction(fraction)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils_extra import CalTypePrefItem
		if self.optionsWidget:
			return self.optionsWidget
		####
		self.optionsWidget = HBox()
		prefItem = CalTypePrefItem(
			ui,
			"monthPBarCalType",
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(self.optionsWidget, prefItem.getWidget())
		####
		self.optionsWidget.show_all()
		return self.optionsWidget
