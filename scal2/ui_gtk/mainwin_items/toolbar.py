from scal2 import core
from scal2.locale_man import tr as _
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import *
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar

@registerSignals
class CalObj(CustomizableToolbar):
    params = (
        'ud.mainToolbarData',
    )
    defaultItems = [
        ToolbarItem('today', 'home', 'goToday', 'Select Today', 'Today'),
        ToolbarItem('date', 'index', 'selectDateShow', 'Select Date...', 'Date'),
        ToolbarItem('customize', 'edit', 'customizeShow'),
        ToolbarItem('preferences', 'preferences', 'prefShow'),
        ToolbarItem('add', 'add', 'eventManShow', 'Event Manager', 'Event'),
        ToolbarItem('export', 'convert', 'exportClicked', _('Export to %s')%'HTML', 'Export'),
        ToolbarItem('about', 'about', 'aboutShow', _('About ')+core.APP_DESC, 'About'),
        ToolbarItem('quit', 'quit', 'quit'),
    ]
    defaultItemsDict = dict([(item._name, item) for item in defaultItems])
    def __init__(self):
        CustomizableToolbar.__init__(self, ui.mainWin, vertical=False)
        if not ud.mainToolbarData['items']:
            ud.mainToolbarData['items'] = [(item._name, True) for item in self.defaultItems]
        self.setData(ud.mainToolbarData)
    def updateVars(self):
        CustomizableToolbar.updateVars(self)
        ud.mainToolbarData = self.getData()

