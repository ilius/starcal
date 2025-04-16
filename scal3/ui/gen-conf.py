import io
import os
import sys
from os.path import dirname

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import params

all_names = sorted([p.v3Name for p in params.confParamsData])


output = io.StringIO()
output.write("from os.path import join\n\n")
output.write("from scal3.path import sourceDir\n\n")
output.write(f"__all__ = {all_names!r}\n\n")

for p in params.confParamsData:
	assert p.default is not params.NOT_SET
	value = p.default
	# if isinstance(value, str) and value.startswith(rootDir + os.sep):
	# value = value[len(rootDir) + 1 :]
	output.write(f"{p.v3Name} = {value!r}" + "\n")


output.write("\n")
output.write("statusIconImageDefault = statusIconImage\n")
output.write("wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon\n")
output.write("statusIconImageHoliDefault = statusIconImageHoli\n")
output.write("winControllerButtonsDefault = winControllerButtons.copy()\n")
output.write("mainWinItemsDefault = mainWinItems.copy()\n")
output.write("wcalItemsDefault = wcalItems.copy()\n")

with open("conf.py", "w", encoding="utf-8") as file:
	file.write(output.getvalue())
