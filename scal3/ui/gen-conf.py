import io
import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import params

all_names = sorted([p.v3Name for p in params.confParamsData])


output = io.StringIO()

output.write("from __future__ import annotations\n\n")
output.write("from os.path import join\n")
output.write("import typing\n")
output.write("if typing.TYPE_CHECKING:\n\tfrom scal3.font import Font\n\n")
output.write("from scal3.path import sourceDir\n\n")
output.write(f"__all__ = {all_names!r}\n\n")

for p in params.confParamsData:
	assert p.default is not params.NOT_SET
	value = p.default
	if p.type.startswith("Color"):
		output.write(f"{p.v3Name} = {value!r}" + "\n")
		continue
	output.write(f"{p.v3Name}: {p.type} = {value!r}" + "\n")


output.write("\n")
output.write("statusIconImageDefault = statusIconImage\n")
output.write("wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon\n")
output.write("statusIconImageHoliDefault = statusIconImageHoli\n")
output.write("winControllerButtonsDefault = winControllerButtons.copy()\n")
output.write("mainWinItemsDefault = mainWinItems.copy()\n")
output.write("wcalItemsDefault = wcalItems.copy()\n")

with open(join(rootDir, "scal3/ui/conf.py"), "w", encoding="utf-8") as file:
	file.write(output.getvalue())
