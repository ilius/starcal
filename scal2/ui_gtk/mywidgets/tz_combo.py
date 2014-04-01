from os.path import join

from scal2.path import rootDir
from scal2.json_utils import jsonToOrderedData
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import ui

from scal2.ui_gtk import *

class TimeZoneComboBoxEntry(gtk.ComboBoxEntry):
    def __init__(self):
        model = gtk.TreeStore(str, bool)
        gtk.ComboBoxEntry.__init__(self)
        self.set_model(model)
        self.set_entry_text_column(0)
        self.add_attribute(self.get_cells()[0], 'sensitive', 1)
        self.connect('changed', self.onChanged)
        child = self.get_child()
        child.set_text(str(core.localTz))
        ###
        self.get_text = child.get_text
        self.set_text = child.set_text
        #####
        recentIter = model.append(None, [
            _('Recent...'),
            False,
        ])
        for tz_name in ui.localTzHist:
            model.append(recentIter, [tz_name, True])
        ###
        self.appendOrderedDict(
            None,
            jsonToOrderedData(
                open(join(rootDir, 'zoneinfo-tree.json')).read()
            ),
        )
    def appendOrderedDict(self, parentIter, dct):
        model = self.get_model()
        for key, value in dct.items():
            if isinstance(value, dict):
                itr = model.append(parentIter, [key, False])
                self.appendOrderedDict(itr, value)
            else:
                itr = model.append(parentIter, [key, True])
    def onChanged(self, widget):
        model = self.get_model()
        itr = self.get_active_iter()
        if itr is None:
            return
        path = model.get_path(itr)
        parts = []
        if path[0] == 0:
            text = model.get(itr, 0)[0]
        else:
            for i in range(len(path)):
                parts.append(
                    model.get(
                        model.get_iter(path[:i+1]),
                        0,
                    )[0]
                )
            text = '/'.join(parts)
        self.set_text(text)

