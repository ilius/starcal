from __future__ import annotations

import io
import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import params


def genParamDict(names: list[str]) -> str:
	return "{" + "\n".join([f"\t{name!r}: {name}," for name in names]) + "\n}\n"


def genParamList(names: list[str]) -> str:
	return "[" + "\n".join([f"\t{name}," for name in names]) + "\n]\n"


all_names = sorted(
	[p.v3Name for p in params.confParamsData]
	+ [
		"confParams",
		"confParamsCustomize",
		"confParamsLive",
		"dayCalWinParamsLive",
		"needRestartList",
	],
)

output = io.StringIO()

output.write(
	"from __future__ import annotations\n\n"
	"import typing\n"
	"from scal3.color_utils import RGB, RGBA\n"
	"from scal3.property import DictProperty, ListProperty, Property\n\n"
	"if typing.TYPE_CHECKING:\n"
	"\tfrom typing import Any, Final\n\n"
	"\tfrom scal3.color_utils import ColorType\n"
	"\tfrom scal3.font import Font\n",
)
output.write("""\tfrom scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeParamsDict,
		CustomizableToolBoxDict,
		DayCalTypeWMParamsDict,
		DayCalTypeDayParamsDict,
		WeekCalDayNumParamsDict,
		PieGeoDict,
	)\n\n\n""")
output.write(f"__all__ = {all_names!r}\n\n")

for p in params.confParamsData:
	assert p.default is not params.NOT_SET
	value = p.default
	if p.type.startswith("list["):
		itemType = p.type[5:-1]
		output.write(
			f"{p.v3Name}: Final[ListProperty[{itemType}]] = ListProperty({value!r})\n"
		)
		continue
	# if p.type.endswith("Dict"):
	# 	output.write(
	# 		f"{p.v3Name}: Final[DictProperty[{p.type}]] = DictProperty({value!r})\n"
	# 	)
	# 	continue

	output.write(f"{p.v3Name}: Final[Property[{p.type}]] = Property({value!r})" + "\n")


output.write("\n\n")

confParams = params.getParamNamesWithFlag(params.MAIN_CONF)
confParamsLive = params.getParamNamesWithFlag(params.LIVE)
confParamsCustomize = params.getParamNamesWithFlag(params.CUSTOMIZE)
dayCalWinParamsLive = params.getParamNamesWithFlag(params.DAYCAL_WIN_LIVE)

output.write("confParams: dict[str, Property[Any]] = " + genParamDict(confParams))
output.write(
	"confParamsLive: dict[str, Property[Any]] = " + genParamDict(confParamsLive)
)
output.write(
	"confParamsCustomize: dict[str, Property[Any]] = "
	+ genParamDict(confParamsCustomize),
)
output.write(
	"dayCalWinParamsLive: dict[str, Property[Any]] = "
	+ genParamDict(dayCalWinParamsLive),
)

output.write("\n")

needRestart = params.getParamNamesWithFlag(params.NEED_RESTART)
output.write("needRestartList = " + genParamList(needRestart))
output.write("\n")


with open(join(rootDir, "scal3/ui/conf.py"), "w", encoding="utf-8") as file:
	file.write(output.getvalue())
