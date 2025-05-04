from __future__ import annotations

__all__ = [
	"ColorType",
	"colorizeSpan",
	"hslToRgb",
	"rgbToCSS",
	"rgbToHsl",
	"rgbToHtmlColor",
	"rgbToInt",
]


type ColorType = tuple[int, int, int] | tuple[int, int, int, int]


def rgbToInt(r, g, b):
	"""For example (170, 85, 52) or "#aa5534" becomes 0xaa5534."""
	return b + g * 256 + r * 256**2


def rgbToHsl(r, g, b):
	r /= 255.0
	g /= 255.0
	b /= 255.0
	# ---
	mx = max(r, g, b)
	mn = min(r, g, b)
	dm = float(mx - mn)
	# ---
	if dm == 0:
		h = None
	elif mx == r:
		h = 60.0 * (g - b) / dm
		if h < 0:
			h += 360
	elif mx == g:
		h = 60.0 * (b - r) / dm + 120
	else:  # mx == b:
		h = 60.0 * (r - g) / dm + 240
	# ---
	# ln means lightness
	ln = (mx + mn) / 2.0
	# ---
	if 0 in {ln, dm}:
		s = 0
	elif 0 < ln < 0.5:
		s = dm / (mx + mn)
	else:  # ln > 0.5
		s = dm / (2.0 - mx - mn)
	return (h, s, ln)


def hslToRgb(h, s, ln):
	# 0.0 <= h <= 360.0
	# 0.0 <= s <= 1.0
	# 0.0 <= ln <= 1.0
	if ln < 0.5:
		q = ln * (1.0 + s)
	else:
		q = ln + s - ln * s
	p = 2 * ln - q
	hk = h / 360.0
	tr = (hk + 1.0 / 3) % 1
	tg = hk % 1
	tb = (hk - 1.0 / 3) % 1
	rgb = []
	for tc in (tr, tg, tb):
		if tc < 1.0 / 6:
			c = p + (q - p) * 6 * tc
		elif 1.0 / 6 <= tc < 0.5:
			c = q
		elif 0.5 <= tc < 2.0 / 3:
			c = p + (q - p) * 6 * (2.0 / 3 - tc)
		else:
			c = p
		rgb.append(round(c * 255))
	return tuple(rgb)
	# rgb = rgb + (255,)


# def getRandomHueColor(s, l):
# 	import random
# 	h = random.uniform(0, 360)
# 	return hslToRgb(h, s, l)


def htmlColorToRgb(hc):
	return (
		int(hc[1:3], 16),
		int(hc[3:5], 16),
		int(hc[5:7], 16),
	)


def rgbToHtmlColor(color: ColorType):
	for x in color:
		assert isinstance(x, int)
	return "#" + "".join([f"{x:02x}" for x in color])


def rgbToCSS(color: ColorType) -> str:
	color = tuple(color)
	if len(color) == 3:
		return f"rgb{color}"
	if len(color) == 4:
		return f"rgba{color}"
	raise ValueError(f"invalid {color=}")


def colorizeSpan(text, color) -> str:
	return f'<span color="{rgbToHtmlColor(color)}">{text}</span>'
