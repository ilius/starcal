#!/usr/bin/env python3
# mypy: ignore-errors
# --
# --	Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# --
# --	This program is free software; you can redistribute it and/or modify
# --	it under the terms of the GNU Affero General Public License as published by
# --	the Free Software Foundation; either version 3 of the License, or
# --	(at your option) any later version.
# --
# --	This program is distributed in the hope that it will be useful,
# --	but WITHOUT ANY WARRANTY; without even the implied warranty of
# --	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# --	GNU Affero General Public License for more details.
# --
# --	You should have received a copy of the GNU Affero General Public License along
# --	If not, see <http://www.gnu.org/licenses/agpl.txt>.

APP_DESC = "StarCalendar"

from scal3 import logger

log = logger.get()

import os
import shutil
from os.path import isfile, join

from scal3.json_utils import dataToPrettyJson
from scal3.locale_man import langDefault, langDict
from scal3.path import (
	confDir,
	pixDir,
	sourceDir,
)
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.utils import dialog_add_button

_ = str

langConfDir = join(sourceDir, "conf", "defaults")

gtk.Window.set_default_icon_from_file(join(pixDir, "starcal.png"))

langNameList = []
langCodeList = []


win = gtk.Dialog(
	title=APP_DESC + " 3.x - First Run",
)
dialog_add_button(
	win,
	imageName="dialog-ok.svg",
	label=_("OK"),
	res=gtk.ResponseType.OK,
)
dialog_add_button(
	win,
	imageName="dialog-cancel.svg",
	label=_("Cancel"),
	res=gtk.ResponseType.CANCEL,
)
langHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
pack(langHbox, gtk.Label(label="Select Language:"))


langCombo = gtk.ComboBoxText()

for langObj in langDict.values():
	langNameList.append(langObj.name)
	langCodeList.append(langObj.code)
	langCombo.append_text(langObj.name)


if langDefault and (langDefault in langCodeList):
	langCombo.set_active(langCodeList.index(langDefault))
else:
	langCombo.set_active(0)

langHbox.pack_start(langCombo, expand=True, fill=True, padding=0)
win.vbox.pack_start(langHbox, expand=False, fill=False, padding=0)

pbarHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
pbar = gtk.ProgressBar()
pbarHbox.pack_start(pbar, expand=True, fill=True, padding=0)
win.vbox.pack_start(pbarHbox, expand=False, fill=False, padding=0)


win.vbox.show_all()

if win.run() == gtk.ResponseType.OK:
	i = langCombo.get_active()
	langCode = langCodeList[i]
	thisLangConfDir = join(langConfDir, langCode)
	# log.debug("Setting language", langCode)
	if not os.path.isdir(confDir):
		os.mkdir(confDir, 0o755)
	if os.path.isdir(thisLangConfDir):
		for fname in os.listdir(thisLangConfDir):
			src_path = join(thisLangConfDir, fname)
			if not isfile(src_path):
				continue
			dst_path = join(confDir, fname)
			# log.debug(src_path)
			shutil.copy(src_path, dst_path)
	else:
		with open(join(confDir, "locale.json"), "w", encoding="utf-8") as file:
			file.write(
				dataToPrettyJson(
					{
						"lang": langCode,
					},
				),
			)

win.destroy()

if not os.path.isdir(confDir):
	os.mkdir(confDir, 0o755)
