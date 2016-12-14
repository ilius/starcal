# -*- coding: utf-8 -*-

from scal3.color_utils import rgbToHtmlColor
from gi.repository import Gdk as gdk

## r, g, b in range(256)
rgbToGdkColor = lambda r, g, b, a=None: gdk.Color(int(r*257), int(g*257), int(b*257))

gdkColorToRgb = lambda gc: (gc.red//257, gc.green//257, gc.blue//257)

#htmlColorToGdk = lambda hc: gdk.color_parse(hc)

colorize = lambda text, color: '<span color="%s">%s</span>'%(
	rgbToHtmlColor(*color),
	text,
)

