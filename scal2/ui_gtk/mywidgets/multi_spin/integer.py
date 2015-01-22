from scal2.mywidgets.multi_spin import IntField
from scal2.ui_gtk.mywidgets.multi_spin import SingleSpinButton

class IntSpinButton(SingleSpinButton):
    def __init__(self, _min, _max, **kwargs):
        SingleSpinButton.__init__(
            self,
            IntField(_min, _max),
            **kwargs
        )
    def set_range(self, _min, _max):
        self.field.children[0].setRange(_min, _max)
        self.set_text(self.field.getText())

