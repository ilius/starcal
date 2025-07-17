#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import core, locale_man, ui
from scal3.app_info import APP_DESC, homePage
from scal3.cal_types import calTypes
from scal3.color_utils import RGB
from scal3.locale_man import tr as _
from scal3.monthcal import getMonthDesc
from scal3.ui import conf
from scal3.ui.font import getOptionsFont

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable

	from scal3.color_utils import ColorType
	from scal3.pytypes import CellType, MonthStatusType

__all__ = ["exportToHtml"]


def rgbToHtml(
	r: int,
	g: int,
	b: int,
	a: int | None = None,  # noqa: ARG001
) -> str:
	return f"#{r:02x}{g:02x}{b:02x}"
	# What to do with alpha?


def colorComposite(front: ColorType, back: ColorType) -> RGB:
	if len(back) == 3:
		r0, g0, b0 = back
		a0 = 1.0
	elif len(back) == 4:
		r0, g0, b0 = back[:3]
		a0 = back[3] / 255.0
	else:
		raise ValueError
	if len(front) == 3:
		r1, g1, b1 = front
		a1 = 1.0
	elif len(front) == 4:
		r1, g1, b1 = front[:3]
		a1 = front[3] / 255.0
	else:
		raise ValueError
	return RGB(
		int(a1 * r1 + (1 - a1) * a0 * r0),
		int(a1 * g1 + (1 - a1) * a0 * g0),
		int(a1 * b1 + (1 - a1) * a0 * b0),
	)
	# should return alpha? FIXME
	# is so, we return `a0` as alpha,
	# and don't multiply others by `a0`


def formatFont(font: ui.Font) -> tuple[str, float]:
	face = font.family
	assert face is not None
	if font.bold:
		face += " Bold"
	if font.italic:
		face += " Italic"
	return face, font.size


def _renderTableCellCalType(
	calTypeIndex: int,
	tag: str | None,
	cell: CellType,
	sizeMap: Callable[[float], float],
	status: MonthStatusType,
	inactiveColor: str,
	holidayColor: str,
	colors: list[str],
) -> tuple[bool, str]:
	try:
		calType = calTypes.active[calTypeIndex]
	except IndexError:
		return False, ""
	try:
		options = conf.mcalTypeParams.v[calTypeIndex]
	except IndexError:
		return False, ""
	day = _(cell.dates[calType][2], calType=calType)

	font = getOptionsFont(options)
	assert font is not None
	face, sizeOrig = formatFont(font)
	size = str(sizeMap(sizeOrig))
	text = ""
	if cell.month != status.month:
		if calTypeIndex == 0:
			text += "\t\t\t\t\t"
			if tag:
				text += f"<{tag}>"
			text += (
				f'<FONT COLOR="{inactiveColor}" '
				f'FACE="{face}" SIZE="{size}">{day}</FONT>'
			)
			if tag:
				text += f"</{tag}>"
			text += "\n"
			return True, text
		return False, text
	text += "\t\t\t\t\t"
	if tag:
		text += f"<{tag}>"
	if calTypeIndex == 0 and cell.holiday:
		color = holidayColor
	else:
		color = colors[calTypeIndex]
	text += f'<FONT COLOR="{color}" FACE="{face}" SIZE="{size}">{day}</FONT>'
	if tag:
		text += f"</{tag}>"
	text += "\n"
	# text += sep  # FIXME
	return False, text


def exportToHtml(
	fpath: str,
	monthsStatus: Iterable[MonthStatusType],
	title: str = "",
	fontSizeScale: float = 1.0,
	pluginsTextPerLine: bool = True,  # description of each day in one line
) -> None:
	def sizeMap(size: float) -> float:
		return fontSizeScale * (size * 0.25 - 0.5)

	# ------------------- Options:
	calTypesFormat = (
		(2, "SUB"),
		(0, None),
		(1, "SUB"),
	)  # a list of (calTypeIndex, htmlTag) tuples
	# sep = " "
	pluginsTextSep = " <B>–</B> "
	# ---------------------
	pluginSep = "<BR>\n" if pluginsTextPerLine else "\t\n"
	bgColor = rgbToHtml(*conf.bgColor.v)
	inactiveColor = rgbToHtml(*colorComposite(conf.inactiveColor.v, conf.bgColor.v))
	borderColor = rgbToHtml(*colorComposite(conf.borderColor.v, conf.bgColor.v))
	borderTextColor = rgbToHtml(*conf.borderTextColor.v)
	textColor = rgbToHtml(*conf.textColor.v)
	holidayColor = rgbToHtml(*conf.holidayColor.v)
	colors = [rgbToHtml(*x["color"]) for x in conf.mcalTypeParams.v]
	direction = "RTL" if locale_man.rtl else "LRT"
	borderFontSize = sizeMap(ui.getFont().size)
	gridSize = int(conf.mcalGrid.v)

	text = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>{title}</TITLE>
</HEAD>
<BODY LANG="{locale_man.langSh}" DIR="{direction}" BGCOLOR="{bgColor}">\n"""
	for status in monthsStatus:
		text += "\t<P>\n"
		for i, line in enumerate(getMonthDesc(status).split("\n")):
			try:
				color = colors[i]
			except IndexError:
				color = textColor
			text += f'\t\t<FONT COLOR="{color}">{line}</FONT>\n\t\t<BR>\n'
		text += "\t</P>\n"
		text += "\n".join(
			[
				f'\t<TABLE WIDTH="100%" BGCOLOR="{bgColor}" '
				f'BORDER={gridSize} BORDERCOLOR="#000000"',
				"\t\tCELLPADDING=4 CELLSPACING=0>",
				"\t\t<TR VALIGN=TOP>\n",
			],
		)
		text += f"""\t\t\t<TD WIDTH=9%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER></P>
		</TD>\n"""  # what text? FIXME
		for j in range(7):
			text += f"""\t\t\t<TD WIDTH=13%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER>
				<FONT COLOR="{borderTextColor}" SIZE="{borderFontSize}px">
					<B>{core.getWeekDayN(j)}</B>
				</FONT>
			</P>
		</TD>\n"""
		pluginsText = f'\t<P><FONT COLOR="{colors[0]}">\n'
		text += "\t\t</TR>\n"
		for i in range(6):
			text += f"""\t\t<TR VALIGN=TOP>
		<TD WIDTH=9%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER>
				<FONT COLOR="{borderTextColor}" SIZE="{borderFontSize}px">
					<B>{_(status.weekNum[i])}</B>
				</FONT>
			</P>
		</TD>\n"""
			for j in range(7):
				cell = status[i][j]
				text += "\t\t\t<TD WIDTH=13%>\n"
				text += '\t\t\t\t<P DIR="LTR" ALIGN=CENTER>\n'

				for calTypeIndex, calTypeTag in calTypesFormat:
					stop, cell_text = _renderTableCellCalType(
						calTypeIndex=calTypeIndex,
						tag=calTypeTag,
						cell=cell,
						sizeMap=sizeMap,
						status=status,
						inactiveColor=inactiveColor,
						holidayColor=holidayColor,
						colors=colors,
					)
					text += cell_text
					if stop:
						break

				text += "\t\t\t\t</P>\n\t\t\t</TD>\n"
				if cell.month == status.month:
					color = holidayColor if cell.holiday else colors[0]
					t = cell.getPluginsText().replace("\n", pluginsTextSep)
					if t:
						pluginsText += (
							f'<B><FONT COLOR="{color}">'
							f"{_(cell.dates[calTypes.primary][2])}</FONT>:</B>"
						)
						pluginsText += f"\t<SMALL>{t}</SMALL>"
						pluginsText += pluginSep

			text += "\t\t</TR>\n"
		pluginsText += "\t</FONT></P>\n"
		text += "\t</TABLE>\n"
		text += pluginsText
		text += f'\n\t<P STYLE="border-bottom: 5pt double {colors[0]}"></P>\n'
	generatedBy = (
		f"{_('Generated by')} "
		f'<A HREF="{homePage}">{APP_DESC}</A> '
		f"{_('version')} <code>{core.VERSION}</code>"
	)
	text += "\n".join(
		[
			"\t<P>",
			f'\t\t<FONT COLOR="{colors[0]}">{generatedBy}</FONT>',
			"\t</P>",
			"</BODY>",
			"</HTML>",
		],
	)
	with open(fpath, mode="w", encoding="utf-8") as _file:
		_file.write(text)
