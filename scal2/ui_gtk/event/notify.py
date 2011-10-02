# -*- coding: utf-8 -*-

import sys, os

eid = int(sys.argv[1])

if len(sys.argv)>2:
    os.setuid(int(sys.argv[2]))

from scal2 import core, event_man
import gtk
import scal2.ui_gtk.event.main

event = event_man.Event(eid)
event.loadConfig()
event.notify(gtk.main_quit)

gtk.main()

