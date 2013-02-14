from scal2.locale_man import tr as _
from scal2.vcs_modules import vcsModuleNames

import gtk

from scal2.ui_gtk.event.groups.group import GroupWidget as NormalGroupWidget
from scal2.ui_gtk.event import common


class GroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('VCS Type'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.vcsTypeCombo = gtk.combo_box_new_text()
        for name in vcsModuleNames:
            self.vcsTypeCombo.append_text(name)## descriptive name FIXME
        hbox.pack_start(self.vcsTypeCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Directory'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.dirEntry = gtk.Entry()
        hbox.pack_start(self.dirEntry, 0, 0)
        ##
        #self.dirBrowse = gtk.Button(_('Browse'))
        ##
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Commit Description'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        ##
        self.statCheck = gtk.CheckButton(_('Stat'))
        hbox.pack_start(self.statCheck, 0, 0)
        ##
        hbox.pack_start(gtk.Label('   '), 0, 0)
        ##
        self.authorCheck = gtk.CheckButton(_('Author'))
        hbox.pack_start(self.authorCheck, 0, 0)
        ##
        hbox.pack_start(gtk.Label('   '), 0, 0)
        ##
        self.shortHashCheck = gtk.CheckButton(_('Short Hash'))
        hbox.pack_start(self.shortHashCheck, 0, 0)
        ##
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        NormalGroupWidget.updateWidget(self)
        self.vcsTypeCombo.set_active(vcsModuleNames.index(self.group.vcsType))
        self.dirEntry.set_text(self.group.vcsDir)
        self.statCheck.set_active(self.group.showStat)
        self.authorCheck.set_active(self.group.showAuthor)
        self.shortHashCheck.set_active(self.group.showShortHash)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.vcsType = vcsModuleNames[self.vcsTypeCombo.get_active()]
        self.group.vcsDir = self.dirEntry.get_text()
        self.group.showStat = self.statCheck.get_active()
        self.group.showAuthor = self.authorCheck.get_active()
        self.group.showShortHash = self.shortHashCheck.get_active()


