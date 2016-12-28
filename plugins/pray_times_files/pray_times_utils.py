import math
from math import pi

earthR = 6370


def sind(x):
	return math.sin(pi / 180 * x)


def cosd(x):
	return math.cos(pi / 180 * x)


#def loc2hor(z, delta, lat):
#	return acosd(
#		(cosd(z) - sind(delta) * sind(lat)) / cosd(delta) / cosd(lat)
#	) / 15


def earthDistance(lat1, lng1, lat2, lng2):
	#if lat1==lat2 and lng1==lng2:
	#	return 0
	dx = lng2 - lng1
	if dx < 0:
		dx += 360
	if dx > 180:
		dx = 360 - dx
	####
	dy = lat2 - lat1
	if dy < 0:
		dy += 360
	if dy > 180:
		dy = 360 - dy
	####
	deg = math.acos(cosd(dx) * cosd(dy))
	if deg > pi:
		deg = 2 * pi - deg
	return deg * earthR
	#return ang * 180 / pi
