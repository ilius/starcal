#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger
from scal3.ui_gtk import gtk

log = logger.get()

def error_exit(resCode, text, parent=None):
	d = gtk.MessageDialog(
		parent=parent,
		destroy_with_parent=True,
		message_type=gtk.MessageType.ERROR,
		buttons=gtk.ButtonsType.OK,
		text=text.strip(),
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
	log.error(str(e))
	error_exit(1, str(e))
