from scal2.mywidgets.multi_spin import FloatField
from scal2.ui_gtk.mywidgets.multi_spin import SingleSpinButton

class FloatSpinButton(SingleSpinButton):
    def __init__(self, _min, _max, digits, **kwargs):
        if digits < 1:
            raise ValueError('FloatSpinButton: invalid digits=%r'%digits)
        SingleSpinButton.__init__(
            self,
            FloatField(_min, _max, digits),
            **kwargs
        )

