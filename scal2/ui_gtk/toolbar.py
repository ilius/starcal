from time import time as now

from scal2 import core
from scal2.locale_man import tr as _
from scal2 import ui

import gobject

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import set_tooltip, myRaise
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import CustomizableCalObj



@registerSignals
class ToolbarItem(gtk.ToolButton, CustomizableCalObj):
    def __init__(self, name, stockName, method, desc='', shortDesc='', enableToolip=True):
        #print('ToolbarItem', name, stockName, method, desc, text)
        self.method = method
        ######
        if not desc:
            desc = name.capitalize()
        ##
        if not shortDesc:
            shortDesc = desc
        ##
        desc = _(desc)
        shortDesc = _(shortDesc)
        ######
        gtk.ToolButton.__init__(
            self,
            gtk.image_new_from_stock(
                getattr(gtk, 'STOCK_%s'%(stockName.upper())),
                gtk.ICON_SIZE_DIALOG,
            ) if stockName else None,
            shortDesc,
        )
        self._name = name
        self.desc = desc
        #self.shortDesc = shortDesc## FIXME
        self.initVars()
        if enableToolip:
            set_tooltip(self, desc)## FIXME
        self.set_is_important(True)## FIXME
    show = lambda self: self.show_all()


#@registerSignals
class CustomizableToolbar(gtk.Toolbar, CustomizableCalObj):
    _name = 'toolbar'
    desc = _('Toolbar')
    styleList = (
        ## Gnome's naming is not exactly the best here
        ## And Gnome's order of options is also different from Gtk's enum
        'Icon',## 'icons', 'Icons only'
        'Text',## 'text', 'Text only'
        'Text below Icon',## 'both', 'Text below items'
        'Text beside Icon',## 'both-horiz', 'Text beside items'
    )
    defaultItems = []
    defaultItemsDict = {}
    def __init__(self, funcOwner, vertical=False, onPressContinue=False):
        from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton
        gtk.Toolbar.__init__(self)
        self.funcOwner = funcOwner
        self.set_orientation(gtk.ORIENTATION_VERTICAL if vertical else gtk.ORIENTATION_HORIZONTAL)
        self.add_events(gdk.POINTER_MOTION_MASK)
        self.onPressContinue = onPressContinue
        ###
        optionsWidget = gtk.VBox()
        ##
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Style')))
        self.styleCombo = gtk.combo_box_new_text()
        for item in self.styleList:
            self.styleCombo.append_text(_(item))
        pack(hbox, self.styleCombo)
        pack(optionsWidget, hbox)
        ##
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Icon Size')))
        self.iconSizeCombo = gtk.combo_box_new_text()
        for (i, item) in enumerate(ud.iconSizeList):
            self.iconSizeCombo.append_text(_(item[0]))
        pack(hbox, self.iconSizeCombo)
        pack(optionsWidget, hbox)
        self.iconSizeHbox = hbox
        ##
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Buttons Border')))
        self.buttonsBorderSpin = IntSpinButton(0, 99)
        pack(hbox, self.buttonsBorderSpin)
        pack(optionsWidget, hbox)
        ##
        self.initVars(optionsWidget=optionsWidget)
        self.iconSizeCombo.connect('changed', self.iconSizeComboChanged)
        self.styleCombo.connect('changed', self.styleComboChanged)
        self.buttonsBorderSpin.connect('changed', self.buttonsBorderSpinChanged)
        #self.styleComboChanged()
        ##
        #print('toolbar state', self.get_state()## STATE_NORMAL)
        #self.set_state(gtk.STATE_ACTIVE)## FIXME
        #self.set_property('border-width', 0)
        #style = self.get_style()
        #style.border_width = 10
        #self.set_style(style)
    getIconSizeName = lambda self: ud.iconSizeList[self.iconSizeCombo.get_active()][0]
    setIconSizeName = lambda self, size_name: self.set_icon_size(ud.iconSizeDict[size_name])
    ## gtk.Toolbar.set_icon_size was previously Deprecated, but it's not Deprecated now!!
    def setButtonsBorder(self, bb):
        for item in self.items:
            item.set_border_width(bb)
    def iconSizeComboChanged(self, combo=None):
        self.setIconSizeName(self.getIconSizeName())
    def styleComboChanged(self, combo=None):
        style = self.styleCombo.get_active()
        self.set_style(style)
        #self.showHide()## FIXME
        self.iconSizeHbox.set_sensitive(style!=1)
    def buttonsBorderSpinChanged(self, spin=None):
        self.setButtonsBorder(self.buttonsBorderSpin.get_value())
    def moveItemUp(self, i):
        button = self.items[i]
        self.remove(button)
        self.insert(button, i-1)
        self.items.insert(i-1, self.items.pop(i))
    #def insertItem(self, item, pos):
    #    CustomizableCalObj.insertItem(self, pos, item)
    #    gtk.Toolbar.insert(self, item, pos)
    #    item.show()
    def appendItem(self, item):
        CustomizableCalObj.appendItem(self, item)
        gtk.Toolbar.insert(self, item, -1)
        if item.enable:
            item.show()
    getData = lambda self: {
        'items': self.getItemsData(),
        'iconSize': self.getIconSizeName(),
        'style': self.styleList[self.styleCombo.get_active()],
        'buttonsBorder': self.buttonsBorderSpin.get_value(),
    }
    def setupItemSignals(self, item):
        if item.method:
            if isinstance(item.method, str):
                func = getattr(self.funcOwner, item.method)
            else:
                func = item.method
            if self.onPressContinue:
                child = item.get_child()
                child.connect('button-press-event', lambda obj, ev: self.itemPress(func))
                child.connect('button-release-event', self.itemRelease)
            else:
                item.connect('clicked', func)
    def setData(self, data):
        for (name, enable) in data['items']:
            try:
                item = self.defaultItemsDict[name]
            except KeyError:
                myRaise()
            else:
                item.enable = enable
                self.setupItemSignals(item)
                self.appendItem(item)
        ###
        iconSize = data['iconSize']
        for (i, item) in enumerate(ud.iconSizeList):
            if item[0]==iconSize:
                self.iconSizeCombo.set_active(i)
        self.setIconSizeName(iconSize)
        ###
        styleNum = self.styleList.index(data['style'])
        self.styleCombo.set_active(styleNum)
        self.set_style(styleNum)
        ###
        bb = data.get('buttonsBorder', 0)
        self.buttonsBorderSpin.set_value(bb)
        self.setButtonsBorder(bb)
        ###
    def itemPress(self, func):
        self.lastPressTime = now()
        self.remain = True
        func()
        gobject.timeout_add(ui.timeout_initial, self.itemPressRemain, func)
    def itemPressRemain(self, func):
        if self.remain and now()-self.lastPressTime>=ui.timeout_repeat/1000.0:
            func()
            gobject.timeout_add(ui.timeout_repeat, self.itemPressRemain, func)
    def itemRelease(self, widget, event=None):
        self.remain = False


