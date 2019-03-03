from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, textNumEncode
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(gtk.ProgressBar, CustomizableCalObj):
	_name = "yearPBar"
	desc = _("Year Progress Bar")

	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)
		self.initVars()

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)

		year = ui.cell.year
		jd0 = core.primary_to_jd(year, 1, 1)
		jd1 = ui.cell.jd
		jd2 = core.primary_to_jd(year+1, 1, 1)
		length = jd2 - jd0
		past = jd1 - jd0
		fraction = float(past) / length
		percent = "%%%d" % (fraction * 100)
		self.set_text(
			textNumEncode(
				percent,
				changeDot=True,
			) +
			"   =   " +
			"%s%s / %s%s" %(_(past), _(" days"), _(length), _(" days"))
		)
		self.set_fraction(fraction)
