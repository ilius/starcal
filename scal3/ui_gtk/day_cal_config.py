from scal3.ui.params import ColorType


class ConfigHandlerBase:
	@property
	def backgroundColor(self) -> ColorType | None:
		return None

	@backgroundColor.setter
	def backgroundColor(self, value: ColorType):
		pass

	@property
	def dayParams(self) -> list[dict] | None:
		return None

	@dayParams.setter
	def dayParams(self, value: list[dict]):
		pass

	@property
	def monthParams(self) -> list[dict] | None:
		return None

	@monthParams.setter
	def monthParams(self, value: list[dict]):
		pass

	@property
	def weekdayParams(self) -> list[dict] | None:
		return None

	@weekdayParams.setter
	def weekdayParams(self, value: list[dict]) -> None:
		pass

	@property
	def weekdayLocalize(self) -> bool | None:
		return None

	@weekdayLocalize.setter
	def weekdayLocalize(self, value: bool) -> None:
		pass

	@property
	def weekdayAbbreviate(self) -> bool | None:
		return None

	@weekdayAbbreviate.setter
	def weekdayAbbreviate(self, value: bool) -> None:
		pass

	@property
	def weekdayUppercase(self) -> bool | None:
		return None

	@weekdayUppercase.setter
	def weekdayUppercase(self, value: bool) -> None:
		pass

	@property
	def widgetButtonsEnable(self) -> bool | None:
		return None

	@widgetButtonsEnable.setter
	def widgetButtonsEnable(self, value: bool) -> None:
		pass

	@property
	def widgetButtons(self) -> list[dict] | None:
		return None

	@widgetButtons.setter
	def widgetButtons(self, value: list[dict]) -> None:
		pass

	@property
	def widgetButtonsSize(self) -> float | None:
		return None

	@widgetButtonsSize.setter
	def widgetButtonsSize(self, value: float) -> None:
		pass

	@property
	def widgetButtonsOpacity(self) -> float | None:
		return None

	@widgetButtonsOpacity.setter
	def widgetButtonsOpacity(self, value: float) -> None:
		pass

	@property
	def navButtonsEnable(self) -> bool | None:
		return None

	@navButtonsEnable.setter
	def navButtonsEnable(self, value: bool) -> None:
		pass

	@property
	def navButtonsGeo(self) -> list[dict] | None:
		return None

	@navButtonsGeo.setter
	def navButtonsGeo(self, value: list[dict]) -> None:
		pass

	@property
	def navButtonsOpacity(self) -> float | None:
		return None

	@navButtonsOpacity.setter
	def navButtonsOpacity(self, value: bool) -> None:
		pass

	@property
	def eventIconSize(self) -> float | None:
		return None

	@eventIconSize.setter
	def eventIconSize(self, value: float) -> None:
		pass

	@property
	def eventTotalSizeRatio(self) -> float | None:
		return None

	@eventTotalSizeRatio.setter
	def eventTotalSizeRatio(self, value: float) -> None:
		pass

	@property
	def seasonPieEnable(self) -> bool | None:
		return None

	@seasonPieEnable.setter
	def seasonPieEnable(self, value: bool) -> None:
		pass

	@property
	def seasonPieGeo(self) -> list[dict] | None:
		return None

	@seasonPieGeo.setter
	def seasonPieGeo(self, value: list[dict]) -> None:
		pass

	@property
	def seasonPieSpringColor(self) -> ColorType | None:
		return None

	@seasonPieSpringColor.setter
	def seasonPieSpringColors(self, value: ColorType) -> None:
		pass

	@property
	def seasonPieSummerColor(self) -> ColorType | None:
		return None

	@seasonPieSummerColor.setter
	def seasonPieSummerColors(self, value: ColorType) -> None:
		pass

	@property
	def seasonPieAutumnColor(self) -> ColorType | None:
		return None

	@seasonPieAutumnColor.setter
	def seasonPieAutumnColors(self, value: ColorType) -> None:
		pass

	@property
	def seasonPieWinterColor(self) -> ColorType | None:
		return None

	@seasonPieWinterColor.setter
	def seasonPieWinterColors(self, value: ColorType) -> None:
		pass

	@property
	def seasonPieTextColor(self) -> ColorType | None:
		return None

	@seasonPieTextColor.setter
	def seasonPieTextColor(self, value: ColorType) -> None:
		pass
