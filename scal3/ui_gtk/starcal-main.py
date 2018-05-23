#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3.ui_gtk import gtk

def error_exit(resCode, text, parent=None):
	d = gtk.MessageDialog(
		parent,
		gtk.DialogFlags.DESTROY_WITH_PARENT,
		gtk.MessageType.ERROR,
		gtk.ButtonsType.OK,
		text.strip(),
	)
	d.set_title("Error")
	d.run()
	sys.exit(resCode)

if sys.version_info[0] != 3:
	error_exit(1, "Run this script with Python 3.x")

try:
	from scal3.ui_gtk.starcal import main
	sys.exit(main())
except Exception as e:
	error_exit(1, str(e))
