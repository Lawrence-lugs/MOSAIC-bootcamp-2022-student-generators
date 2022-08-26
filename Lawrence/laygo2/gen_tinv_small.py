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

class TriInverterSmall(Laygo2):

    nf = TaskParameter(default=2, description="Number of fingers of pmos and nmos")
    cell_type = TaskParameter(default="typ", description="Cell type ('hs' or 'typ')")

    lib_name = TaskState(value="logic_generated")
    cell_name = TaskState(value="tinv_small")


    def design(self, tlibs, templates, grids):
        lib = self.lib
        dsn = self.dsn

        # Design hierarchy
        # cellname in for loop
        # End of parameter definitions ######


        #tpmos, tnmos = templates[tpmos_name], templates[tnmos_name]
        tpmos, tnmos = templates[Laygo2.tpmos_name], templates[Laygo2.tnmos_name]

        # print("Load grids")
        pg, r12, r23, r34 = self.get_placement_grid(), self.get_metal(Laygo2.M12), self.get_metal(Laygo2.M23), self.get_metal(Laygo2.M34)

        # 2. Create a design hierarchy
        self.log.info("Creating hierarchy design")

        # 3. Create instances.
        #print("Create instances")
        self.log.info("Creating instances")
        nstack = templates['nmos13_fast_center_2stack'].generate(name='nstack')
        nbndl = templates['nmos13_fast_boundary'].generate(name='nbndl')
        nbndr = templates['nmos13_fast_boundary'].generate(name='nbndr')
        nspace0 = templates['nmos13_fast_space'].generate(name='nspace0')
        nspace1 = templates['nmos13_fast_space'].generate(name='nspace1')
        pstack = templates['pmos13_fast_center_2stack'].generate(name='pstack', transform='MX')
        pbndl = templates['pmos13_fast_boundary'].generate(name='pbndl', transform='MX')
        pbndr = templates['pmos13_fast_boundary'].generate(name='pbndr', transform='MX')
        pspace0 = templates['pmos13_fast_space'].generate(name='pspace0', transform='MX')
        pspace1 = templates['pmos13_fast_space'].generate(name='pspace1', transform='MX')

        # 4. Place instances.
        dsn.place(grid=pg, inst=nbndl, mn=[0, 0])
        dsn.place(grid=pg, inst=nstack, mn=pg.mn.bottom_right(nbndl))
        dsn.place(grid=pg, inst=nbndr, mn=pg.mn.bottom_right(nstack))
        dsn.place(grid=pg, inst=nspace0, mn=pg.mn.bottom_right(nbndr))
        dsn.place(grid=pg, inst=nspace1, mn=pg.mn.bottom_right(nspace0))
        dsn.place(grid=pg, inst=pbndl, mn=pg.mn.top_left(nbndl) + pg.mn.height_vec(pbndl))
        dsn.place(grid=pg, inst=pstack, mn=pg.mn.top_right(pbndl))
        dsn.place(grid=pg, inst=pbndr, mn=pg.mn.top_right(pstack))
        dsn.place(grid=pg, inst=pspace0, mn=pg.mn.top_right(pbndr))
        dsn.place(grid=pg, inst=pspace1, mn=pg.mn.top_right(pspace0))

        # 5. Create and place wires.
        self.log.info("Creating wires")
        # IN
        _mn = [r12.mn(nstack.pins['G0'])[0], r12.mn(pstack.pins['G0'])[0]]
        rin0 = dsn.route(grid=r23, mn=_mn)
        _mn = [r12.mn(nstack.pins['G0'])[0], r12.mn(pstack.pins['G0'])[0]]
        dsn.route(grid=r12, mn=_mn)
        _mn = [np.mean(r23.mn.bbox(rin0), axis=0, dtype=int),
               np.mean(r23.mn.bbox(rin0), axis=0, dtype=int) + [2, 0]]
        dsn.route(grid=r23, mn=_mn, via_tag=[True, False])
        dsn.via(grid=r12, mn=np.mean(r23.mn.bbox(rin0), axis=0, dtype=int))

        # OUT
        _mn = [r23.mn(nstack.pins['D0'])[0], r23.mn(pstack.pins['D0'])[1]]
        vout0, rout0, vout1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        vint0 = dsn.via(grid=r12, mn=r23.mn(nstack.pins['D0'])[0])
        vint1 = dsn.via(grid=r12, mn=r23.mn(pstack.pins['D0'])[1])

        # EN
        _mn = [r23.mn(nstack.pins['G1'])[0], r23.mn(nstack.pins['G1'])[0] + [1, 0]]
        ren0, ven0 = dsn.route(grid=r23, mn=_mn, via_tag=[False, True])
        ven1 = dsn.via(grid=r12, mn=r12.mn(nstack.pins['G1'])[0])
        _mn = [r23.mn(nstack.pins['G1'])[0] + [1, 0], r23.mn(pstack.pins['G1'])[0] + [1, 0]]
        ren1 = dsn.route(grid=r23, mn=_mn)

        # ENB
        _mn = [r23.mn(pstack.pins['G1'])[0], r23.mn(pstack.pins['G1'])[0] + [-1, 0]]
        renb0, venb0 = dsn.route(grid=r23, mn=_mn, via_tag=[False, True])
        venb1 = dsn.via(grid=r12, mn=r12.mn(pstack.pins['G1'])[0])
        _mn = [r23.mn(pstack.pins['G1'])[0] + [-1, 0], r23.mn(nstack.pins['G1'])[0] + [-1, 0]]
        renb1 = dsn.route(grid=r23, mn=_mn)

        # VSS
        # M2 Rect
        _mn = [r12.mn.bottom_left(nbndl), r12.mn.bottom_right(nspace1)]
        rvss0 = dsn.route(grid=r12, mn=_mn)

        # tie
        _mn = [r12.mn(nstack.pins['S0'])[0], r12.mn(nstack.pins['S0'])[0] + [0, -1]]
        rvss1, _ = dsn.route(grid=r12, mn=_mn, via_tag=[False, True])

        # VDD
        # M2 Rect
        _mn = [r12.mn.top_left(pbndl), r12.mn.top_right(pspace1)]
        rvdd0 = dsn.route(grid=r12, mn=_mn)

        # tie
        _mn = [r12.mn(pstack.pins['S0'])[1], r12.mn(rvdd0)[0] + [1, 0]]
        rvdd1 = dsn.route(grid=r12, mn=_mn, via_tag=[False, True])

        # 6. Create pins.
        pin0 = dsn.pin(name='I', grid=r23, mn=r23.mn.bbox(rin0))
        pout0 = dsn.pin(name='O', grid=r23, mn=r23.mn.bbox(rout0))
        pen0 = dsn.pin(name='EN', grid=r23, mn=r23.mn.bbox(ren1))
        penb0 = dsn.pin(name='ENB', grid=r23, mn=r23.mn.bbox(renb1))
        pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.bbox(rvss0))
        pvdd0 = dsn.pin(name='VDD', grid=r12, mn=r12.bbox(rvdd0))
