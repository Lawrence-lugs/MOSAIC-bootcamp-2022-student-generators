from abc import abstractmethod
import pytest
import laygo2
from mosaic.mosaic import Task, Mosaic, CachableTask, TaskParameter, TaskState
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

class TriInverter(Laygo2):

    nf = TaskParameter(default=2, description="Number of fingers of pmos and nmos")
    cell_type = TaskParameter(default="typ", description="Cell type ('hs' or 'typ')")

    lib_name = TaskState(value="logic_generated")
    cell_name = TaskState(value="tinv")

    def design(self, tlib, templates, grids):
        lib = self.lib
        dsn = self.dsn

        # Parameter definitions #############
        # Variable
        # Design hierarchy
        # cellname in for loop
        # End of parameter definitions ######

        # Generation start ##################

        #tpmos, tnmos = templates[tpmos_name], templates[tnmos_name]
        tpmos, tnmos = templates[Laygo2.tpmos_name], templates[Laygo2.tnmos_name]

        # print("Load grids")
        pg, r12, r23, r34 = self.get_placement_grid(), self.get_metal(Laygo2.M12), self.get_metal(Laygo2.M23), self.get_metal(Laygo2.M34)

        # 2. Create a design hierarchy
        self.log.info("Creating hierarchy design")

        # 3. Create instances.
        #print("Create instances")
        self.log.info("Creating instances")
        in0 = tnmos.generate(name='MN0', params={'nf': self.nf.value, 'tie': 'S'})
        ip0 = tpmos.generate(name='MP0', transform='MX', params={'nf': self.nf.value,'tie': 'S'})
        in1 = tnmos.generate(name='MN1', params={'nf': self.nf.value, 'trackswap': True})
        ip1 = tpmos.generate(name='MP1', transform='MX', params={'nf': self.nf.value, 'trackswap': True})

        # 4. Place instances.
        dsn.place(grid=pg, inst=in0, mn=[0,0])
        dsn.place(grid=pg, inst=ip0, mn=pg.mn.top_left(in0) + pg.mn.height_vec(ip0))
        dsn.place(grid=pg, inst=in1, mn=pg.mn.bottom_right(in0))
        dsn.place(grid=pg, inst=ip1, mn=pg.mn.top_right(ip0))

        # 5. Create and place wires.
        self.log.info("Creating wires")
        # IN
        _mn = [r23.mn(in0.pins['G'])[0], r23.mn(ip0.pins['G'])[0]]
        v0, rin0, v1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])

        # OUT
        if self.cell_type.value == 'typ':
            _mn = [r23.mn(in1.pins['D'])[1], r23.mn(ip1.pins['D'])[1]]
            vout0, rout0, vout1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        elif self.cell_type.value == 'hs':
            for i in range(int(self.nf.value/2)):
                _mn = [r23.mn(in1.pins['D'])[0] + [2*i, 0], r23.mn(ip1.pins['D'])[0] + [2*i, 0]]
                vout0, rout0, vout1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
                pout0 = dsn.pin(name='O'+str(i), grid=r23, mn=r23.mn.bbox(rout0), netname='O:')

        # EN
        _mn = [r23.mn(in1.pins['G'])[1] + [1, 0], r23.mn(ip1.pins['G'])[1] + [1, 0]]
        ven0, ren0 = dsn.route(grid=r23, mn=_mn, via_tag=[True, False])
        _mn = [r23.mn(in1.pins['G'])[1], r23.mn(in1.pins['G'])[1] + [1, 0]]
        renint = dsn.route(grid=r23, mn=_mn)

        # ENB
        _mn = [r23.mn(in1.pins['G'])[1] + [-1, 0], r23.mn(ip1.pins['G'])[1] + [-1, 0]]
        renb0, venb0 = dsn.route(grid=r23, mn=_mn, via_tag=[False, True])

        # Internal
        _mn = [r23.mn(ip0.pins['D'])[0], r23.mn(ip1.pins['S'])[0]]
        rintp0 = dsn.route(grid=r23, mn=_mn)
        _mn = [r23.mn(in0.pins['D'])[0], r23.mn(in1.pins['S'])[0]]
        rintn0 = dsn.route(grid=r23, mn=_mn)

        # VSS
        rvss0 = dsn.route(grid=r12, mn=[r12.mn(in0.pins['RAIL'])[0], r12.mn(in1.pins['RAIL'])[1]])

        # VDD
        rvdd0 = dsn.route(grid=r12, mn=[r12.mn(ip0.pins['RAIL'])[0], r12.mn(ip1.pins['RAIL'])[1]])

        # 6. Create pins.
        pin0 = dsn.pin(name='I', grid=r23, mn=r23.mn.bbox(rin0))
        pen0 = dsn.pin(name='EN', grid=r23, mn=r23.mn.bbox(ren0))
        penb0 = dsn.pin(name='ENB', grid=r23, mn=r23.mn.bbox(renb0))
        if self.cell_type.value == 'typ':
            pout0 = dsn.pin(name='O', grid=r23, mn=r23.mn.bbox(rout0))
        pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss0))
        pvdd0 = dsn.pin(name='VDD', grid=r12, mn=r12.mn.bbox(rvdd0))
