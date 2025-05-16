import unittest

from scal3.date_utils import parseDroppedDate


class TestParseDroppedDate(unittest.TestCase):
	def case(self, text: str, date: tuple[int, int, int] | None) -> None:
		actualDate = parseDroppedDate(text)
		self.assertEqual(actualDate, date)

	def test_parseDroppedDate(self) -> None:
		self.case("", None)
		self.case("2020", None)
		self.case("2020/1", None)
		self.case("2020/1/a", None)
		self.case("2020/1/0", None)
		self.case("2020/0/1", None)
		self.case("1981/1/1", (1981, 1, 1))
		# self.case("1981/13/1", (1981, 1, 13))
		self.case("1981/1/13", (1981, 1, 13))
		self.case("2100/5/12", (2100, 5, 12))
		self.case("10/5/12", (2010, 5, 12))
		self.case("1/2/2012", (2012, 1, 2))  # American
		self.case("13/2/2012", (2012, 2, 13))  # European


if __name__ == "__main__":
	unittest.main()
