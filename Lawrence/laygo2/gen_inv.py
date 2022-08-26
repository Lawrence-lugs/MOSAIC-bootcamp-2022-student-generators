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

class Inverter(Laygo2):

    nf = TaskParameter(default=2, description="Number of fingers of pmos and nmos")
    cell_type = TaskParameter(default="typ", description="Cell type ('hs' or 'typ')")

    lib_name = TaskState(value="logic_generated")
    cell_name = TaskState(value="inv")
    
    def design(self, tlib, templates, grids):
        #Generator-specific code
        lib = self.lib
        dsn = self.dsn

        # Parameter definitions #############
        # Variables
        # Templates
        # tpmos_name = 'pmos_sky'
        # tnmos_name = 'nmos_sky'
        #
        # # Grids
        # pg_name = 'placement_basic'
        # r12_name = 'routing_12_cmos'
        # r23_name = 'routing_23_cmos'


        #tpmos, tnmos = templates[tpmos_name], templates[tnmos_name]
        tpmos, tnmos = templates[Laygo2.tpmos_name], templates[Laygo2.tnmos_name]

        # print("Load grids")
        pg, r12, r23, r34 = self.get_placement_grid(), self.get_metal(Laygo2.M12), self.get_metal(Laygo2.M23), self.get_metal(Laygo2.M34)

        # 2. Create a design hierarchy
        self.log.info("Creating hierarchy design")

        # 3. Create instances.
        #print("Create instances")
        self.log.info("Creating instances")
        in0 = self.get_mos(mos=tnmos, name='MN0', params={'nf': self.nf.value, 'tie': 'S'})
        ip0 = self.get_mos(mos=tpmos, transform='MX', params={'nf': self.nf.value, 'tie': 'S'})

        # 4. Place instances.
        dsn.place(grid=pg, inst=in0, mn=[0,0])
        dsn.place(grid=pg, inst=ip0, mn=pg.mn.top_left(in0) + pg.mn.height_vec(ip0))

        # 5. Create and place wires.
        self.log.info("Creating wires")
        # IN
        _mn = [r23.mn(in0.pins['G'])[0], r23.mn(ip0.pins['G'])[0]]
        _track = [r23.mn(in0.pins['G'])[0,0]-1, None]
        rin0 = dsn.route_via_track(grid=r23, mn=_mn, track=_track)

        # OUT
        if self.cell_type.value == 'typ':
            _mn = [r23.mn(in0.pins['D'])[1], r23.mn(ip0.pins['D'])[1]]
            vout0, rout0, vout1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
        elif self.cell_type.value == 'hs':
            for i in range(int(self.nf.value/2)):
                _mn = [r23.mn(in0.pins['D'])[0]+[2*i,0], r23.mn(ip0.pins['D'])[0]+[2*i,0]]
                vout0, rout0, vout1 = dsn.route(grid=r23, mn=_mn, via_tag=[True, True])
                pout0 = dsn.pin(name='O'+str(i), grid=r23, mn=r23.mn.bbox(rout0), netname='O:')

        # VSS
        rvss0 = dsn.route(grid=r12, mn=[r12.mn(in0.pins['RAIL'])[0], r12.mn(in0.pins['RAIL'])[1]])

        # VDD
        rvdd0 = dsn.route(grid=r12, mn=[r12.mn(ip0.pins['RAIL'])[0], r12.mn(ip0.pins['RAIL'])[1]])

        # 6. Create pins.
        pin0 = dsn.pin(name='I', grid=r23, mn=r23.mn.bbox(rin0[2]))
        if self.cell_type.value == 'typ':
            pout0 = dsn.pin(name='O', grid=r23, mn=r23.mn.bbox(rout0))
        pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss0))
        pvdd0 = dsn.pin(name='VDD', grid=r12, mn=r12.mn.bbox(rvdd0))
