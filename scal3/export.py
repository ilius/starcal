#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3.cal_types import calTypes
from scal3 import locale_man
from scal3.locale_man import tr as _

from scal3 import core

from scal3 import ui
from scal3.monthcal import getMonthDesc


def rgbToHtml(r, g, b, a=None):
	return f"#{r:02x}{g:02x}{b:02x}"
	# What to do with alpha? FIXME


def colorComposite(front, back):
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
	return (
		int(a1 * r1 + (1 - a1) * a0 * r0),
		int(a1 * g1 + (1 - a1) * a0 * g0),
		int(a1 * b1 + (1 - a1) * a0 * b0),
	)
	# should return alpha? FIXME
	# is so, we return `a0` as alpha,
	# and don't multiply others by `a0`


def colorComposite3(front, middle, back):  # FIXME
	c1 = colorComposite(colorComposite(front, middle), back)
	c2 = colorComposite(front, colorComposite(middle, back))
	assert c1 == c2
	return c1


def exportToHtml(fpath, monthsStatus, title=""):
	def sizeMap(size):
		return size * 0.25 - 0.5  # FIXME

	# ################### Options:
	calTypesFormat = (
		(2, "SUB"),
		(0, None),
		(1, "SUB")
	)  # a list of (calTypeIndex, htmlTag) tuples
	sep = " "
	pluginsTextSep = " <B>ـ</B> "
	pluginsTextPerLine = True ## description of each day in one line
	#####################
	bgColor = rgbToHtml(*ui.bgColor)
	inactiveColor = rgbToHtml(*colorComposite(ui.inactiveColor, ui.bgColor))
	borderColor = rgbToHtml(*colorComposite(ui.borderColor, ui.bgColor))
	borderTextColor = rgbToHtml(*ui.borderTextColor)
	textColor = rgbToHtml(*ui.textColor)
	holidayColor = rgbToHtml(*ui.holidayColor)
	colors = [rgbToHtml(*x["color"]) for x in ui.mcalTypeParams]
	if locale_man.rtl:
		DIR = "RTL"
	else:
		DIR = "LRT"
	text = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>{title}</TITLE>
</HEAD>
<BODY LANG="{locale_man.langSh}" DIR="{DIR}" BGCOLOR="{bgColor}">\n"""
	for status in monthsStatus:
		text += "\t<P>\n"
		for i, line in enumerate(getMonthDesc(status).split("\n")):
			try:
				color = colors[i]
			except IndexError:
				color = textColor
			text += f"\t\t<FONT COLOR=\"{color}\">{line}</FONT>\n\t\t<BR>\n"
		text += "\t</P>\n"
		text += "\n".join([
			f'\t<TABLE WIDTH=100%% BGCOLOR="{bgColor}" BORDER={int(ui.mcalGrid)} BORDERCOLOR="#000000"',
			"\t\tCELLPADDING=4 CELLSPACING=0>",
			"\t\t<TR VALIGN=TOP>\n",
		])
		text += f"""\t\t\t<TD WIDTH=9%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER></P>
		</TD>\n"""  # what text? FIXME
		for j in range(7):
			text += f"""\t\t\t<TD WIDTH=13%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER>
				<FONT COLOR="{borderTextColor}"><B>{core.getWeekDayN(j)}</B></FONT>
			</P>
		</TD>\n"""
		pluginsText = f"\t<P><FONT COLOR=\"{colors[0]}\">\n"
		text += "\t\t</TR>\n"
		for i in range(6):
			text += f"""\t\t<TR VALIGN=TOP>
		<TD WIDTH=9%% BGCOLOR="{borderColor}">
			<P ALIGN=CENTER>
				<FONT COLOR="{borderTextColor}"><B>{_(status.weekNum[i])}</B></FONT>
			</P>
		</TD>\n"""
			for j in range(7):
				cell = status[i][j]
				text += "\t\t\t<TD WIDTH=13%>\n"
				text += "\t\t\t\t<P DIR=\"LTR\" ALIGN=CENTER>\n"
				for (calTypeIndex, calTypeTag) in calTypesFormat:
					try:
						calType = calTypes.active[calTypeIndex]
					except IndexError:
						continue
					try:
						params = ui.mcalTypeParams[calTypeIndex]
					except IndexError:
						continue
					day = _(cell.dates[calType][2], calType)## , 2
					font = params["font"]
					face = font[0]
					if font[1]:
						face += " Bold"
					if font[2]:
						face += " Underline"
					size = str(sizeMap(font[3]))
					if cell.month != status.month:
						if calTypeIndex == 0:
							text += "\t\t\t\t\t"
							if calTypeTag:
								text += f"<{calTypeTag}>"
							text += (
								f"<FONT COLOR=\"{inactiveColor}\" " +
								f"FACE=\"{face}\" SIZE=\"{size}\">{day}</FONT>"
							)
							if calTypeTag:
								text += f"</{calTypeTag}>"
							text += "\n"
							break
						else:
							continue
					text += "\t\t\t\t\t"
					if calTypeTag:
						text += f"<{calTypeTag}>"
					if calTypeIndex == 0 and cell.holiday:
						color = holidayColor
					else:
						color = colors[calTypeIndex]
					text += (
						f"<FONT COLOR=\"{color}\" FACE=\"{face}\" " +
						f"SIZE=\"{size}\">{day}</FONT>" 
					)
					if calTypeTag:
						text += f"</{calTypeTag}>"
					text += "\n"
					#text += sep##???????????
				text += "\t\t\t\t</P>\n\t\t\t</TD>\n"
				if cell.month == status.month:
					if cell.holiday:
						color = holidayColor
					else:
						color = colors[0]
					t = cell.pluginsText.replace("\n", pluginsTextSep)
					if t:
						pluginsText += (
							f"<B><FONT COLOR=\"{color}\">" +
							f"{_(cell.dates[calTypes.primary][2])}</FONT>:</B>"
						)
						pluginsText += f"\t<SMALL>{t}</SMALL>"
						if pluginsTextPerLine:
							pluginsText += "<BR>\n"
						else:
							pluginsText += "\t\n"
			text += "\t\t</TR>\n"
		pluginsText += "\t</FONT></P>\n"
		text += "\t</TABLE>\n"
		text += pluginsText
		text += f"\n\t<P STYLE=\"border-bottom: 5pt double {colors[0]}\"></P>\n"
	generatedBy = (
		f'{_("Generated by")} ' + 
		f'<A HREF="{core.homePage}">{core.APP_DESC}</A> ' +
		f'{_("version")} <code>{core.VERSION}</code>'
	)
	text += "\n".join([
		"\t<P>",
		f'\t\t<FONT COLOR="{colors[0]}">{generatedBy}</FONT>',
		"\t</P>",
		"</BODY>",
		"</HTML>",
	])
	open(fpath, "w").write(text)
