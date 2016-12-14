
invertColor = lambda r, g, b: (255-r, 255-g, 255-b)

def rgbToHsl(r, g, b):
	r /= 255.0
	g /= 255.0
	b /= 255.0
	###
	mx = max(r, g, b)
	mn = min(r, g, b)
	dm = float(mx - mn)
	###
	if dm == 0:
		h = None
	elif mx == r:
		h = 60.0*(g-b)/dm
		if h < 0:
			h += 360
	elif mx == g:
		h = 60.0*(b-r)/dm + 120
	else:## mx == b:
		h = 60.0*(r-g)/dm + 260
	###
	l = (mx+mn)/2.0
	###
	if l == 0 or dm == 0:
		s = 0
	elif 0 < l < 0.5:
		s = dm/(mx+mn)
	else:## l > 0.5
		s = dm/(2.0-mx-mn)
	return (h, s, l)


def hslToRgb(h, s, l):
	## 0.0 <= h <= 360.0
	## 0.0 <= s <= 1.0
	## 0.0 <= l <= 1.0
	if l < 0.5:
		q = l * (1.0+s)
	else:
		q = l + s - l*s
	p = 2*l - q
	hk = h/360.0
	tr = (hk+1.0/3) % 1
	tg = hk % 1
	tb = (hk-1.0/3) % 1
	rgb = []
	for tc in (tr, tg, tb):
		if tc < 1.0/6:
			c = p + (q-p)*6*tc
		elif 1.0/6 <= tc < 1.0/2:
			c = q
		elif 1.0/2 <= tc < 2.0/3:
			c = p + (q-p)*6*(2.0/3-tc)
		else:
			c = p
		rgb.append(int(c*255))
	rgb = tuple(rgb)
	#rgb = rgb + (255,)
	return rgb

#def getRandomHueColor(s, l):
#	import random
#	h = random.uniform(0, 360)
#	return hslToRgb(h, s, l)

htmlColorToRgb = lambda hc: (int(hc[1:3], 16), int(hc[3:5], 16), int(hc[5:7], 16))

def rgbToHtmlColor(r, g, b):
	return '#' + ''.join(['%.2x'%x for x in (r, g, b)])



