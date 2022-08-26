"""
twomos_bias
========

"""

from sal.design_base import DesignBase
from .params import TGateParams
from .layout import layout as twomos_bias_layout


class design(DesignBase):
    def __init__(self):
        DesignBase.__init__(self)
        self.params = self.parameter_class().defaults(min_lch=self.min_lch)

    @property
    def package(self):
        return "twomos_bias_gen"

    @classmethod
    def layout_generator_class(cls):
        """Return the layout generator class"""
        return twomos_bias_layout

    @classmethod
    def parameter_class(cls):
        """Return the parameter class"""
        return TGateParams

    # Define template draw and schematic parameters below using property decorators:
    @property
    def params(self) -> TGateParams:
        return self._params

    @params.setter
    def params(self, val: TGateParams):
        self._params = val
