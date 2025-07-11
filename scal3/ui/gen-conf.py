from __future__ import annotations

import io
import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import options


def genParamDict(names: list[str]) -> str:
	return "{" + "\n".join([f"\t{name!r}: {name}," for name in names]) + "\n}\n"


def genParamList(names: list[str]) -> str:
	return "[" + "\n".join([f"\t{name}," for name in names]) + "\n]\n"


all_names = sorted(
	[p.v3Name for p in options.confOptionsData]
	+ [
		"confOptions",
		"confOptionsCustomize",
		"confOptionsLive",
		"dayCalWinOptionsLive",
		"needRestartList",
	],
)

output = io.StringIO()

output.write(
	"from __future__ import annotations\n\n"
	"import typing\n"
	"from scal3.color_utils import RGB, RGBA\n"
	"from scal3.option import DictOption, ListOption, Option\n\n"
	"if typing.TYPE_CHECKING:\n"
	"\tfrom typing import Any, Final\n\n"
	"\tfrom scal3.color_utils import ColorType\n"
	"\tfrom scal3.font import Font\n",
)
output.write("""\tfrom scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeOptionsDict,
		CustomizableToolBoxDict,
		DayCalTypeWMOptionsDict,
		DayCalTypeDayOptionsDict,
		WeekCalDayNumOptionsDict,
		PieGeoDict,
	)\n\n\n""")
output.write(f"__all__ = {all_names!r}\n\n")

for p in options.confOptionsData:
	assert p.default is not options.NOT_SET
	value = p.default
	if p.type.startswith("list["):
		itemType = p.type[5:-1]
		output.write(
			f"{p.v3Name}: Final[ListOption[{itemType}]] = ListOption({value!r})\n"
		)
		continue
	# if p.type.endswith("Dict"):
	# 	output.write(
	# 		f"{p.v3Name}: Final[DictOption[{p.type}]] = DictOption({value!r})\n"
	# 	)
	# 	continue

	output.write(f"{p.v3Name}: Final[Option[{p.type}]] = Option({value!r})" + "\n")


output.write("\n\n")

confOptions = options.getParamNamesWithFlag(options.MAIN_CONF)
confOptionsLive = options.getParamNamesWithFlag(options.LIVE)
confOptionsCustomize = options.getParamNamesWithFlag(options.CUSTOMIZE)
dayCalWinOptionsLive = options.getParamNamesWithFlag(options.DAYCAL_WIN_LIVE)

output.write("confOptions: dict[str, Option[Any]] = " + genParamDict(confOptions))
output.write(
	"confOptionsLive: dict[str, Option[Any]] = " + genParamDict(confOptionsLive)
)
output.write(
	"confOptionsCustomize: dict[str, Option[Any]] = "
	+ genParamDict(confOptionsCustomize),
)
output.write(
	"dayCalWinOptionsLive: dict[str, Option[Any]] = "
	+ genParamDict(dayCalWinOptionsLive),
)

output.write("\n")

needRestart = options.getParamNamesWithFlag(options.NEED_RESTART)
output.write("needRestartList = " + genParamList(needRestart))
output.write("\n")


with open(join(rootDir, "scal3/ui/conf.py"), "w", encoding="utf-8") as file:
	file.write(output.getvalue())
