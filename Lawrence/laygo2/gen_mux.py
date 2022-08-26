from abc import abstractmethod
import pytest
import laygo2
from mosaic.mosaic import Task, Mosaic, CachableTask, TaskParameter, TaskState, Calculated
from skywater130 import PDK
from mosaic.wrappers import PythonViewWrapper
import numpy as np
import pprint
import laygo2
import laygo2.interface
import laygo2_tech as tech
from mosaic.tool import IPCtool
from mosaic.result import Validation, ValidationSuccess

from mosaic_laygo2.laygo2_task import Laygo2
from gen_inv import Inverter
from gen_tinv import TriInverter
from gen_tinv_small import TriInverterSmall

class MUX(Laygo2):
    nf = TaskParameter(default=2, description="Number of fingers of pmos and nmos")
    cell_type = TaskParameter(default="typ", description="Cell type ('hs' or 'typ')")

    lib_name = TaskState(value="logic_generated")
    cell_name = TaskState(value="mux")

    #declare submodules
    inv_module = Inverter(task_params={"nf": Calculated})

    def design(self, tlib, templates, grids):
        lib = self.lib
        dsn = self.dsn
        tpmos, tnmos = templates[Laygo2.tpmos_name], templates[Laygo2.tnmos_name]
        pg, r12, r23, r34 = self.get_placement_grid(), self.get_metal(Laygo2.M12), self.get_metal(Laygo2.M23), self.get_metal(Laygo2.M34)

        #append native template libraries from submodules
        #need to run with taskparams
        nf=self.nf.value
        invtlib = self.inv_module.run(task_params={"nf": nf})
        tlib.append(invtlib)
        inv0 = tlib[invtlib.name].generate(name='inv0')

        in0 = tnmos.generate(name='MN0', params={'nf': nf})
        ip0 = tpmos.generate(name='MP0', transform='MX', params={'nf': nf})
        in1 = tnmos.generate(name='MN1', params={'nf': nf})
        ip1 = tpmos.generate(name='MP1', transform='MX', params={'nf': nf})

        dsn.place(grid=pg, inst=in0, mn=[0, 0])
        dsn.place(grid=pg, inst=inv0, mn=pg.mn.bottom_right(in0))
        dsn.place(grid=pg, inst=in1, mn=pg.mn.bottom_right(inv0))
        dsn.place(grid=pg, inst=ip0, mn=pg.mn.top_left(in0) + pg.mn.height_vec(ip0))
        dsn.place(grid=pg, inst=ip1, mn=pg.mn.top_right(inv0))

        # connect in to gates
        _mn = [r23.mn(inv0.pins['I'])[0], r23.mn(in0.pins['G'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[False, True])
        _mn = [r23.mn(inv0.pins['I'])[1], r23.mn(ip1.pins['G'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[False, True])

        # connect out to gates
        _mn = [r23.mn(inv0.pins['O'])[0],r23.mn(inv0.pins['O'])[0] + [2, 1]]
        self.elbow_route(grid=r23,mn=_mn,shape='-|',via_tag=[True,True,True])
        # _mn = [r23.mn(inv0.pins['O'])[0], r23.mn(inv0.pins['O'])[0] + [2, 0]]
        # dsn.route(grid=r12, mn=_mn, via_tag=[True, True])
        # _mn = [r23.mn(inv0.pins['O'])[0] + [2, 1], r23.mn(inv0.pins['O'])[0] + [2, 0]]
        # dsn.route(grid=r12, mn=_mn, via_tag=[True, False])
        _mn = [r23.mn(inv0.pins['O'])[0] + [2, 1], r23.mn(in1.pins['G'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, True])
        _mn = [r23.mn(inv0.pins['O'])[1], r23.mn(inv0.pins['O'])[1] + [-2, 0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, True])
        _mn = [r23.mn(inv0.pins['O'])[1] + [-2, -1], r23.mn(inv0.pins['O'])[1] + [-2, 0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, False])
        _mn = [r23.mn(inv0.pins['O'])[1] + [-2, -1], r23.mn(ip0.pins['G'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, False])

        # connect sources through 2 and 1
        _mn = [r23.mn(in0.pins['S'])[0], r23.mn(in1.pins['S'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, True])
        _mn = [r23.mn(ip0.pins['S'])[0], r23.mn(ip1.pins['S'])[0]]
        dsn.route(grid=r12, mn=_mn, via_tag=[True, True])
        # this part makes more symmetric connections, but violates metal1 spacing DRC
        # _mn = [r23.mn(ip0.pins['S'])[0], r23.mn(in0.pins['S'])[0]]
        # dsn.route(grid=r12,mn=_mn,via_tag=[True,True])
        # _mn = [r23.mn(ip1.pins['S'])[0], r23.mn(in1.pins['S'])[0]]
        # dsn.route(grid=r12,mn=_mn,via_tag=[True,True])
        # _mn = [r23.mn(ip0.pins['S'])[1], r23.mn(in0.pins['S'])[1]]
        # dsn.route(grid=r12,mn=_mn,via_tag=[True,True])
        _mn = [r23.mn(ip1.pins['S'])[1], r23.mn(in1.pins['S'])[1]]
        dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        dsn.via(grid=r12, mn=_mn[0])
        dsn.pin(name='Q', grid=r23, mn=_mn)

        # connect drains through metal 3
        _mn = [r23.mn(in0.pins['D'])[0], r23.mn(ip0.pins['D'])[0]]
        dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        dsn.via(grid=r12, mn=_mn[0])
        dsn.via(grid=r12, mn=_mn[1])
        dsn.pin(name='A', grid=r23, mn=_mn)
        _mn = [r23.mn(in1.pins['D'])[0], r23.mn(ip1.pins['D'])[0]]
        dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        dsn.via(grid=r12, mn=_mn[0])
        dsn.via(grid=r12, mn=_mn[1])
        dsn.pin(name='B', grid=r23, mn=_mn)