from scal2 import core
from scal2.locale_man import tr as _
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.customize import CustomizableCalObj

@registerSignals
class CalObj(gtk.ProgressBar, CustomizableCalObj):
    _name = 'seasonPBar'
    desc = _('Season Progress Bar')
    def __init__(self):
        gtk.ProgressBar.__init__(self)
        self.initVars()
    def onDateChange(self, *a, **kw):
        from scal2.season import getSeasonNamePercentFromJd
        CustomizableCalObj.onDateChange(self, *a, **kw)
        name, frac = getSeasonNamePercentFromJd(ui.cell.jd)
        if rtl:
            percent = '%d%%'%(frac*100)
        else:
            percent = '%%%d'%(frac*100)
        self.set_text(
            _(name) +
            ' - ' +
            locale_man.textNumEncode(
                percent,
                changeDot=True,
            )
        )
        self.set_fraction(frac)


