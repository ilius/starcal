from scal3 import core, ui
from scal3.locale_man import rtl, textNumEncode
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.pbar import MyProgressBar

__all__ = ["CalObj"]


@registerSignals
class CalObj(gtk.Frame, CustomizableCalObj):
	objName = "yearPBar"
	desc = _("Year Progress Bar")
	itemListCustomizable = False
	hasOptions = False

	def __init__(self, win: gtk.Window) -> None:
		self.win = win
		gtk.Frame.__init__(self)
		self.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.set_border_width(0)
		self.pbar = MyProgressBar()
		self.add(self.pbar)
		self.pbar.show()
		self.initVars()

	def onDateChange(self, *a, **kw) -> None:
		CustomizableCalObj.onDateChange(self, *a, **kw)

		year = ui.cells.current.year
		jd0 = core.primary_to_jd(year, 1, 1)
		jd1 = ui.cells.current.jd
		jd2 = core.primary_to_jd(year + 1, 1, 1)
		length = jd2 - jd0
		past = jd1 - jd0
		fraction = past / length
		if rtl:
			percent = f"{int(fraction * 100)}%"
		else:
			percent = f"%{int(fraction * 100)}"
		self.pbar.set_text(
			_("Year")
			+ ":  "
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
