#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk


class MultiValueRule(gtk.HBox):
    def __init__(self, rule, ValueWidgetClass):
        self.rule = rule
        self.ValueWidgetClass = ValueWidgetClass
        ##
        gtk.HBox.__init__(self)
        self.widgetsBox = gtk.HBox()
        self.pack_start(self.widgetsBox, 0, 0)
        ##
        self.removeButton = gtk.Button()
        self.removeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
        self.removeButton.connect('clicked', self.removeLastWidget)
        ##
        
        
        ##
        self.removeButton.hide()## FIXME

    def removeLastWidget(self, obj=None):
        
    def addWidget(self, obj=None):
        widget = self.ValueWidgetClass()
