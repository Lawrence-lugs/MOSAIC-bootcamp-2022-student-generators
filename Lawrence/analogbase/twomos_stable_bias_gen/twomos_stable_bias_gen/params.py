#! /usr/bin/env python3

from __future__ import annotations  # allow class type hints within same class
from dataclasses import dataclass
from typing import *

from sal.params_base import ParamsBase


@dataclass
class TGateParams(ParamsBase):
    """
    Parameter class for twomos_stable_bias_gen

    Args:
    ----
    ntap_w : Union[float, int]
        Width of the N substrate contact

    ptap_w : Union[float, int]
        Width of P substrate contact

    lch : float
        Channel length of the transistors

    th_dict : Dict[str, str]
        NMOS/PMOS threshold flavor dictionary

    ndum : int
        Number of fingers in NMOS transistor

    tr_spaces : Dict[str, int]
        Track spacing dictionary

    tr_widths : Dict[str, Dict[int, int]]
        Track width dictionary

    top_layer: int
        Top metal Layer used in Layout

    ndum_mid_stages : int
        number of dummy fingers/transistors between stages/columns of transistors

    w_dict : Dict[str, Union[float, int]]
        NMOS/PMOS width dictionary

    seg_dict : Dict[str, int]
        NMOS/PMOS number of segments dictionary

    guard_ring_nf : int
        Width of guard ring

    show_pins : bool
        True to create pin labels

    out_conn : str
        Enable Alternative structure for flipped well processes

    finfet : bool
        Enable finfet process
    """

    ntap_w: Union[float, int]
    ptap_w: Union[float, int]
    lch: float
    th_dict: Dict[str, str]
    ndum: int
    tr_spaces: Dict[Union[str, Tuple[str, str]], Dict[int, Union[float, int]]]
    tr_widths: Dict[str, Dict[int, int]]
    top_layer: int
    ndum_mid_stages: int
    w_dict: Dict[str, Union[float, int]]
    seg_dict: Dict[str, int]
    guard_ring_nf: int
    show_pins: bool
    out_conn: str
    finfet: bool

    @classmethod
    def finfet_defaults(cls, min_lch: float) -> TGateParams:
        return TGateParams(ntap_w=10,
                           ptap_w=10,
                           lch=min_lch,
                           th_dict={
                               'Dummy_NB': 'standard', 'Dummy_NT': 'standard',
                               'Dummy_PB': 'standard', 'Dummy_PT': 'standard',
                               'n': 'standard', 'p': 'standard'
                           },
                           ndum=4,
                           tr_spaces={},
                           tr_widths={'sig': {4: 1}},
                           top_layer=5,
                           ndum_mid_stages=2,
                           w_dict={
                               'Dummy_NB': 10, 'Dummy_NT': 10,
                               'Dummy_PB': 10, 'Dummy_PT': 10,
                               'n': 10, 'p': 10
                           },
                           seg_dict={'n': 20, 'p': 40},
                           guard_ring_nf=0,
                           show_pins=True,
                           out_conn='g',
                           finfet=True,
                           )

    @classmethod
    def planar_defaults(cls, min_lch: float) -> TGateParams:
        return TGateParams(ntap_w=10 * min_lch,
                           ptap_w=10 * min_lch,
                           lch=min_lch,
                           th_dict={
                               'Dummy_NB': 'lvt', 'Dummy_NT': 'lvt',
                               'Dummy_PB': 'lvt', 'Dummy_PT': 'lvt',
                               'n': 'lvt', 'p': 'lvt'
                           },
                           ndum=4,
                           tr_spaces={},
                           tr_widths={'sig': {4: 1}},
                           top_layer=5,
                           ndum_mid_stages=2,
                           w_dict={
                               'Dummy_NB': 10 * min_lch, 'Dummy_NT': 10 * min_lch,
                               'Dummy_PB': 10 * min_lch, 'Dummy_PT': 10 * min_lch,
                               'n': 10 * min_lch, 'p': 10 * min_lch
                           },
                           seg_dict={'n': 20, 'p': 40},
                           guard_ring_nf=2,
                           show_pins=True,
                           out_conn='g',
                           finfet=False,
                           )
