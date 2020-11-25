#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, textNumEncode
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.pbar import MyProgressBar
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(gtk.Frame, CustomizableCalObj):
	_name = "yearPBar"
	desc = _("Year Progress Bar")
	itemListCustomizable = False
	hasOptions = False

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

		year = ui.cell.year
		jd0 = core.primary_to_jd(year, 1, 1)
		jd1 = ui.cell.jd
		jd2 = core.primary_to_jd(year + 1, 1, 1)
		length = jd2 - jd0
		past = jd1 - jd0
		fraction = float(past) / length
		if rtl:
			percent = f"{int(fraction*100)}%"
		else:
			percent = f"%{int(fraction*100)}"
		self.pbar.set_text(
			_("Year") + ":  " +
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
