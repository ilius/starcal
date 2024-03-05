
from scal3.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry


class WidgetClass(NumRangesEntry):
	def __init__(self, rule):
		self.rule = rule
		NumRangesEntry.__init__(self, 0, 9999, 10)

	def updateWidget(self):
		self.setValues(self.rule.values)

	def updateVars(self):
		self.rule.values = self.getValues()

	def changeCalType(self, calType):
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
