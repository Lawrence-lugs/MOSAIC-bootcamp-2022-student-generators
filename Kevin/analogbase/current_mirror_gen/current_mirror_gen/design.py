"""
current_mirror
========

"""

from sal.design_base import DesignBase
from .params import CurrentMirrorParams
from .layout import layout as current_mirror_layout


class design(DesignBase):
    def __init__(self):
        DesignBase.__init__(self)
        self.params = self.parameter_class().defaults(min_lch=self.min_lch)

    @property
    def package(self):
        return "current_mirror_gen"

    @classmethod
    def layout_generator_class(cls):
        """Return the layout generator class"""
        return current_mirror_layout

    @classmethod
    def parameter_class(cls):
        """Return the parameter class"""
        return CurrentMirrorParams

    # Define template draw and schematic parameters below using property decorators:
    @property
    def params(self) -> CurrentMirrorParams:
        return self._params

    @params.setter
    def params(self, val: CurrentMirrorParams):
        self._params = val
