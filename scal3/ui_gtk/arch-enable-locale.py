#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import sys
import os
import subprocess
from time import time as now

from gi.repository import Gtk as gtk


localeGen = "/etc/locale.gen"


def error(text, parent=None):
	d = gtk.MessageDialog(
		parent,
		gtk.DialogFlags.DESTROY_WITH_PARENT,
		gtk.MessageType.ERROR,
		gtk.ButtonsType.OK,
		text.strip(),
	)
	d.set_title("Error")
	d.run()


def errorExit(text, parent=None):
	error(text, parent)
	sys.exit(1)


if __name__ == "__main__":
	if os.getuid() != 0:
		errorExit("This program must be run as root")
	if not os.path.isfile(localeGen):
		errorExit(f"File \"{localeGen}\" does not exist!")
	localeName = sys.argv[1].lower().replace(".", " ")
	with open(localeGen) as fp:
		lines = fp.read().split("\n")
	for (i, line) in enumerate(lines):
		if line.lower().startswith(localeName):
			log.info(f"locale \"{localeName}\" is already enabled")
			break
		if line.lower().startswith("#" + localeName):
			lines[i] = line[1:]
			os.rename(localeGen, f"{localeGen}.{now()}")
			open(localeGen, "w").write("\n".join(lines))
			exit_code = subprocess.call("/usr/sbin/locale-gen")
			log.info(f"enabling locale \"{localeName}\" done")
			break
	else:
		errorExit(f"locale \"{localeName}\" not found!")
