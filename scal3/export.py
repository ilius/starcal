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
	return '#%.2x%.2x%.2x' % (r, g, b)
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
		a1 * r1 + (1 - a1) * a0 * r0,
		a1 * g1 + (1 - a1) * a0 * g0,
		a1 * b1 + (1 - a1) * a0 * b0,
	)
	# should return alpha? FIXME
	# is so, we return `a0` as alpha,
	# and don't multiply others by `a0`


def colorComposite3(front, middle, back):  # FIXME
	c1 = colorComposite(colorComposite(front, middle), back)
	c2 = colorComposite(front, colorComposite(middle, back))
	assert c1 == c2
	return c1


def exportToHtml(fpath, monthsStatus, title=''):
	##################### Options:
	calTypesFormat = (
		(2, 'SUB'),
		(0, None),
		(1, 'SUB')
	)  # a list of (calTypeIndex, htmlTag) tuples
	sizeMap = lambda size: size * 0.25 - 0.5  # FIXME
	sep = ' '
	pluginsTextSep = ' <B>ـ</B> '
	pluginsTextPerLine = True ## description of each day in one line
	#####################
	bgColor = rgbToHtml(*ui.bgColor)
	inactiveColor = rgbToHtml(*colorComposite(ui.inactiveColor, ui.bgColor))
	borderColor = rgbToHtml(*colorComposite(ui.borderColor, ui.bgColor))
	borderTextColor = rgbToHtml(*ui.borderTextColor)
	textColor = rgbToHtml(*ui.textColor)
	holidayColor = rgbToHtml(*ui.holidayColor)
	colors = [rgbToHtml(*x['color']) for x in ui.mcalTypeParams]
	if locale_man.rtl:
		DIR = 'RTL'
	else:
		DIR = 'LRT'
	text = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>%s</TITLE>
</HEAD>
<BODY LANG="%s" DIR="%s" BGCOLOR="%s">\n''' % (
		title,
		locale_man.langSh,
		DIR,
		bgColor,
	)
	for status in monthsStatus:
		text += '    <P>\n'
		for i, line in enumerate(getMonthDesc(status).split('\n')):
			try:
				color = colors[i]
			except IndexError:
				color = textColor
			text += '        <FONT COLOR="%s">%s</FONT>\n        <BR>\n' % (
				color,
				line,
			)
		text += '    </P>\n'
		text += '''    <TABLE WIDTH=100%% BGCOLOR="%s" BORDER=%s BORDERCOLOR="#000000"
CELLPADDING=4 CELLSPACING=0>
	<TR VALIGN=TOP>\n''' % (
			bgColor,
			int(ui.mcalGrid),
		)
		text += '''            <TD WIDTH=9%% BGCOLOR="%s">
			<P ALIGN=CENTER></P>
		</TD>\n''' % borderColor  # what text? FIXME
		for j in range(7):
			text += '''            <TD WIDTH=13%% BGCOLOR="%s">
			<P ALIGN=CENTER>
				<FONT COLOR="%s"><B>%s</B></FONT>
			</P>
		</TD>\n''' % (
				borderColor,
				borderTextColor,
				core.getWeekDayN(j),
			)
		pluginsText = '<P><FONT COLOR="%s">\n' % colors[0]
		text += '        </TR>\n'
		for i in range(6):
			text += '''        <TR VALIGN=TOP>
		<TD WIDTH=9%% BGCOLOR="%s">
			<P ALIGN=CENTER>
				<FONT COLOR="%s"><B>%s</B></FONT>
			</P>
		</TD>\n''' % (
				borderColor,
				borderTextColor,
				_(status.weekNum[i]),
			)
			for j in range(7):
				cell = status[i][j]
				text += '            <TD WIDTH=13%>\n'
				text += '                <P DIR="LTR" ALIGN=CENTER>\n'
				for (calTypeIndex, calTypeTag) in calTypesFormat:
					try:
						mode = calTypes.active[calTypeIndex]
					except IndexError:
						continue
					try:
						params = ui.mcalTypeParams[calTypeIndex]
					except IndexError:
						continue
					day = _(cell.dates[mode][2], mode)## , 2
					font = params['font']
					face = font[0]
					if font[1]:
						face += ' Bold'
					if font[2]:
						face += ' Underline'
					size = str(sizeMap(font[3]))
					if cell.month != status.month:
						if calTypeIndex == 0:
							text += '                    '
							if calTypeTag:
								text += '<%s>' % calTypeTag
							text += '<FONT COLOR="%s" FACE="%s" SIZE="%s">%s</FONT>' % (
								inactiveColor,
								face,
								size,
								day,
							)
							if calTypeTag:
								text += '</%s>' % calTypeTag
							text += '\n'
							break
						else:
							continue
					text += '                    '
					if calTypeTag:
						text += '<%s>' % calTypeTag
					if calTypeIndex == 0 and cell.holiday:
						color = holidayColor
					else:
						color = colors[calTypeIndex]
					text += '<FONT COLOR="%s" FACE="%s" SIZE="%s">%s</FONT>' % (
						color,
						face,
						size,
						day,
					)
					if calTypeTag:
						text += '</%s>' % calTypeTag
					text += '\n'
					#text += sep##???????????
				text += '                </P>\n            </TD>\n'
				if cell.month == status.month:
					if cell.holiday:
						color = holidayColor
					else:
						color = colors[0]
					t = cell.pluginsText.replace('\n', pluginsTextSep)
					if t:
						pluginsText += '<B><FONT COLOR="%s">%s</FONT>:</B>'
						pluginsText += '    <SMALL>%s</SMALL>' % (
							color,
							_(cell.dates[calTypes.primary][2]),
							t,
						)
						if pluginsTextPerLine:
							pluginsText += '<BR>\n'
						else:
							pluginsText += '    \n'
			text += '        </TR>\n'
		pluginsText += '    </FONT></P>\n'
		text += '    </TABLE>\n'
		text += pluginsText
		text += '\n<P STYLE="border-bottom: 5pt double %s"></P>\n' % colors[0]
	text += '''    <P>
	<FONT COLOR="%s">%s <A HREF="%s">%s</A> %s %s</FONT>
</P>
</BODY>
</HTML>''' % (
		colors[0],
		_('Generated by'),
		core.homePage,
		core.APP_DESC,
		_('version'),
		core.VERSION,
	)
	open(fpath, 'w').write(text)
