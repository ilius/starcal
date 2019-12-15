import unittest

# results are confirmed with
# https://www.w3schools.com/colors/colors_converter.asp
# except we don't round H, S or L (rgbToHsl returns 3 floats)


class TestColorUtils(unittest.TestCase):
	def test_rgbToInt(self):
		from scal3.color_utils import rgbToInt
		self.assertEqual(rgbToInt(170, 85, 52), 0xaa5534)
		self.assertEqual(rgbToInt(255, 0, 0), 0xff0000)
		self.assertEqual(rgbToInt(0, 255, 0), 0x00ff00)
		self.assertEqual(rgbToInt(0, 0, 255), 0x0000ff)

	def assertEqualHSL(self, first, second):
		self.assertEqual(len(first), 3)
		self.assertEqual(len(second), 3)
		self.assertAlmostEqual(first[0], second[0], places=1)  # hue
		self.assertAlmostEqual(first[1], second[1], places=3)  # saturation
		self.assertAlmostEqual(first[2], second[2], places=3)  # lightness

	def test_rgbToHsl(self):
		from scal3.color_utils import rgbToHsl
		self.assertEqualHSL(rgbToHsl(0, 0, 0), (None, 0, 0))  # OK
		self.assertEqualHSL(rgbToHsl(255, 0, 0), (0, 1, 0.5))  # OK
		self.assertEqualHSL(rgbToHsl(0, 255, 0), (120, 1, 0.5))  # OK
		self.assertEqualHSL(rgbToHsl(0, 0, 255), (240, 1, 0.5))  # OK
		self.assertEqualHSL(rgbToHsl(128, 64, 64), (0, 0.333, 0.376))  # OK
		self.assertEqualHSL(rgbToHsl(0, 64, 64), (180, 1, 0.125))  # OK
		self.assertEqualHSL(rgbToHsl(123, 64, 12), (28.1, 0.822, 0.265))  # OK
		self.assertEqualHSL(rgbToHsl(209, 238, 249), (196.5, 0.769, 0.898))  # OK
		self.assertEqualHSL(rgbToHsl(69, 185, 213), (191.7, 0.632, 0.553))  # OK
		self.assertEqualHSL(rgbToHsl(66, 151, 95), (140.5, 0.392, 0.425))  # OK
		self.assertEqualHSL(rgbToHsl(206, 13, 164), (313.1, 0.881, 0.429))  # OK
		self.assertEqualHSL(rgbToHsl(122, 210, 75), (99.1, 0.600, 0.559))  # OK
		self.assertEqualHSL(rgbToHsl(147, 27, 194), (283.1, 0.756, 0.433))  # OK
		self.assertEqualHSL(rgbToHsl(73, 24, 20), (4.5, 0.570, 0.182))  # OK
		self.assertEqualHSL(rgbToHsl(165, 119, 232), (264.4, 0.711, 0.688))  # OK
		self.assertEqualHSL(rgbToHsl(162, 90, 135), (322.5, 0.286, 0.494))  # OK
		self.assertEqualHSL(rgbToHsl(57, 125, 68), (129.7, 0.374, 0.357))  # OK

	def test_hslToRgb(self):
		from scal3.color_utils import hslToRgb
		self.assertEqual(hslToRgb(0, 0, 0), (0, 0, 0))  # OK
		self.assertEqual(hslToRgb(0, 1, 0.5), (255, 0, 0))  # OK
		self.assertEqual(hslToRgb(120, 1, 0.5), (0, 255, 0))  # OK
		self.assertEqual(hslToRgb(240, 1, 0.5), (0, 0, 255))  # OK
		self.assertEqual(hslToRgb(0, 0.33, 0.37), (125, 63, 63))  # OK
		self.assertEqual(hslToRgb(0, 0.34, 0.38), (130, 64, 64))  # OK
		self.assertEqual(hslToRgb(0.28, 0.82, 0.26), (121, 12, 12))  # OK
		self.assertEqual(hslToRgb(35.0, 0.277, 0.001), (0, 0, 0))  # OK
		self.assertEqual(hslToRgb(194.0, 0.378, 0.742), (164, 202, 214))  # OK
		self.assertEqual(hslToRgb(55.0, 0.382, 0.450), (159, 151, 71))  # OK
		self.assertEqual(hslToRgb(122.0, 0.222, 0.995), (253, 254, 253))  # OK
		self.assertEqual(hslToRgb(178.0, 0.157, 0.903), (226, 234, 234))  # OK
		self.assertEqual(hslToRgb(90.0, 0.475, 0.295), (75, 111, 39))  # OK
		self.assertEqual(hslToRgb(214.0, 0.317, 0.409), (71, 100, 137))  # OK
		self.assertEqual(hslToRgb(11.0, 0.866, 0.401), (191, 46, 14))  # OK
		self.assertEqual(hslToRgb(322.0, 0.775, 0.793), (243, 161, 213))  # OK
		self.assertEqual(hslToRgb(95.0, 0.978, 0.903), (226, 254, 206))  # OK


def genRandomTests_rgbToHsl():
	from scal3.color_utils import rgbToHsl
	from random import randint
	for i in range(10):
		r = randint(0, 255)
		g = randint(0, 255)
		b = randint(0, 255)
		h, s, ln = rgbToHsl(r, g, b)
		log.info(
			f"self.assertEqualHSL(rgbToHsl({r}, {g}, {b}), " +
			f"({h:.1f}, {s:.3f}, {ln:.3f}))"
		)


def genRandomTests_hslToRgb():
	from scal3.color_utils import hslToRgb
	from random import randint, random
	for i in range(10):
		h = randint(0, 360)
		s = random()
		ln = random()
		r, g, b = hslToRgb(h, s, ln)
		log.info(
			f"self.assertEqual(hslToRgb({h:.1f}, {s:.3f}, {ln:.3f}), " +
			f"({r}, {g}, {b}))"
		)


if __name__ == "__main__":
	unittest.main()
