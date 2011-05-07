# -*- coding: utf-8 -*-
#        
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from scal2.utils import toStr

from scal2.locale_man import rtl
from scal2.locale_man import tr as _
from scal2 import core
from scal2.core import numLocale

from scal2 import ui
from scal2.monthcal import getMonthDesc

rgbToHtml = lambda r, g, b, a=None: '#%.2x%.2x%.2x'%(r, g, b) ## What to do with alpha ??

def colorComposite(front, back):
    if len(back)==3:
        (r0, g0, b0) = back
        a0 = 1.0
    elif len(back)==4:
        (r0, g0, b0) = back[:3]
        a0 = back[3]/255.0
    else:
        raise ValueError
    if len(front)==3:
        (r1, g1, b1) = front
        a1 = 1.0
    elif len(front)==4:
        (r1, g1, b1) = front[:3]
        a1 = front[3]/255.0
    else:
        raise ValueError
    return (a1*r1 + (1-a1)*a0*r0,
                    a1*g1 + (1-a1)*a0*g0,
                    a1*b1 + (1-a1)*a0*b0)


def colorComposite3(front, middle, back):## FIXME
    c1 = colorComposite(colorComposite(front, middle), back)
    c2 = colorComposite(front, colorComposite(middle, back))
    assert c1 == c2
    return c1


def exportToHtml(fpath, monthsStatus, title=''):
    ##################### Options:
    format = ((2, 'SUB'), (0, None), (1, 'SUB')) ## (dateMode, htmlTag)
    sizeMap = lambda size: size*0.25 - 0.5 ## ???????????????
    sep = ' '
    extraSep = ' <B>ـ</B> '
    extraPerLine = True ## description of each day in one line
    #####################
    dates = ui.shownCals
    #####################
    bgColor = rgbToHtml(*ui.bgColor)
    grayColor = rgbToHtml(*colorComposite(ui.inactiveColor, ui.bgColor))
    borderColor= rgbToHtml(*colorComposite(ui.borderColor, ui.bgColor))
    borderTextColor = rgbToHtml(*ui.borderTextColor)
    holidayColor = rgbToHtml(*ui.holidayColor)
    colors = [rgbToHtml(*x['color']) for x in dates]
    if rtl:
        DIR = 'RTL'
    else:
        DIR = 'LRT'
    text = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>%s</TITLE>
</HEAD>
<BODY LANG="%s" DIR="%s" BGCOLOR="%s">\n'''%(title, core.langSh, DIR, bgColor)
    for status in monthsStatus:
        mDesc = getMonthDesc(status).split('\n')
        text += '    <P>\n'
        for i in xrange(len(dates)):
            if dates[i]['enable']:
                text += '        <FONT COLOR="%s">%s</FONT>\n        <BR>\n'%(colors[i], mDesc[i])
        text += '    </P>\n'
        text += '''    <TABLE WIDTH=100%% BGCOLOR="%s" BORDER=%s BORDERCOLOR="#000000"
CELLPADDING=4 CELLSPACING=0>
    <TR VALIGN=TOP>\n'''\
            %(bgColor, int(ui.calGrid))
        text += '''            <TD WIDTH=9%% BGCOLOR="%s">
            <P ALIGN=CENTER></P>
        </TD>\n'''%borderColor## what text????????
        for j in xrange(7):
            text += '''            <TD WIDTH=13%% BGCOLOR="%s">
            <P ALIGN=CENTER>
                <FONT COLOR="%s"><B>%s</B></FONT>
            </P>
        </TD>\n'''%(borderColor,borderTextColor,core.getWeekDayN(j))
        extra = '<P><FONT COLOR="%s">\n'%colors[0]
        text += '        </TR>\n'
        for i in xrange(6):
            text += '''        <TR VALIGN=TOP>
        <TD WIDTH=9%% BGCOLOR="%s">
            <P ALIGN=CENTER>
                <FONT COLOR="%s"><B>%s</B></FONT>
            </P>
        </TD>\n'''%(borderColor, borderTextColor, numLocale(status.weekNum[i]))
            for j in xrange(7):
                cell = status[i][j]
                text += '            <TD WIDTH=13%>\n                <P DIR="LTR" ALIGN=CENTER>\n'
                for (ind, tag) in format:
                    if not dates[ind]['enable']:
                        continue
                    mode = dates[ind]['mode']
                    day = numLocale(cell.dates[mode][2], mode)## , 2
                    font = dates[ind]['font']
                    face = font[0]
                    if font[1]:
                        face += ' Bold'
                    if font[2]:
                        face += ' Underline'
                    size = str(sizeMap(font[3]))
                    if cell.month != status.month:## cell.gray != 0
                        if ind==0:
                            text += '                    '
                            if tag:
                                text += '<%s>'%tag
                            text += '<FONT COLOR="%s" FACE="%s" SIZE="%s">%s</FONT>'\
                                %(grayColor, face, size, day)
                            if tag:
                                text += '</%s>'%tag
                            text += '\n'
                            break
                        else:
                            continue
                    text += '                    '
                    if tag:
                        text += '<%s>'%tag
                    if ind==0 and cell.holiday:
                        color = holidayColor
                    else:
                        color = colors[ind]
                    text += '<FONT COLOR="%s" FACE="%s" SIZE="%s">%s</FONT>'%(color, face, size, day)
                    if tag:
                        text += '</%s>'%tag
                    text += '\n'
                    #text += sep##???????????
                text += '                </P>\n            </TD>\n'
                if cell.month == status.month:## cell.gray == 0
                    if cell.holidayExtra:
                        color = holidayColor
                    else:
                        color = colors[0]
                    t = cell.extraday.replace('\n', extraSep)
                    if t!='':
                        extra+='<B><FONT COLOR="%s">%s</FONT>:</B>    <SMALL>%s</SMALL>'\
                            %(color, numLocale(cell.dates[core.primaryMode][2]), t)
                        if extraPerLine:
                            extra+='<BR>\n'
                        else:
                            extra+='    \n'
            text += '        </TR>\n'
        extra += '    </FONT></P>\n'
        text += '    </TABLE>\n'
        text = toStr(text) ## needed for windows
        text += extra
        text += '\n<P STYLE="border-bottom: 5pt double %s"></P>\n'%colors[0]
    text += '''    <P>
    <FONT COLOR="%s">%s <A HREF="%s">StarCalendar</A> %s %s</FONT>
</P>
</BODY>
</HTML>'''%(
        colors[0],
        toStr(_('Generated by')),
        core.homePage,
        toStr(_('version')),
        core.VERSION
    )
    open(fpath, 'w').write(text)



