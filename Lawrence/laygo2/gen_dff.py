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

class DFF(Laygo2):
    nf = TaskParameter(default=2, description="Number of fingers of pmos and nmos")
    cell_type = TaskParameter(default="typ", description="Cell type ('hs' or 'typ')")
    lib_name = TaskState(value="logic_generated")
    cell_name = TaskState(value="dff")

    #declare submodules
    inv_module = Inverter(task_params={"nf": Calculated})
    tinv_module = TriInverter(task_params={"nf": Calculated})
    tinv_small_module = TriInverterSmall(task_params={"nf": Calculated})

    def design(self, tlib, templates, grids):
        lib = self.lib
        dsn = self.dsn

        # Parameter definitions #############
        # Variables

        #append native template libraries from submodules
        #need to run with taskparams
        nf=self.nf.value
        invtlib = self.inv_module.run(task_params={"nf": nf})
        tinvlib = self.tinv_module.run(task_params={"nf":nf})
        tinv_slib = self.tinv_small_module.run(task_params={"nf":1})
        tlib.append(invtlib)
        tlib.append(tinvlib)
        tlib.append(tinv_slib)

        # import pdb
        # pdb.set_trace()

        # Templates
        # tpmos_name = 'pmos_sky'
        # tnmos_name = 'nmos_sky'
        # Grids
        # pg_name = 'placement_basic'
        # r12_name = 'routing_12_cmos'
        # r23_name = 'routing_23_cmos'
        # r34_name = 'routing_34_basic'
        # Design hierarchy
        # End of parameter definitions ######

        # Generation start ##################
        # 1. Load templates and grids.
        # print("Load templates")
        #templates = tech.load_templates()

        #tpmos, tnmos = templates[tpmos_name], templates[tnmos_name]
        tpmos, tnmos = templates[Laygo2.tpmos_name], templates[Laygo2.tnmos_name]

        # print("Load grids")
        pg, r12, r23, r34 = self.get_placement_grid(), self.get_metal(Laygo2.M12), self.get_metal(Laygo2.M23), self.get_metal(Laygo2.M34)

        # 2. Create a design hierarchy

        # 3. Create instances.

        print("Create instances")
        inv0 = tlib[invtlib.name].generate(name='inv0')
        inv1 = tlib[invtlib.name].generate(name='inv1')
        inv2 = tlib[invtlib.name].generate(name='inv2')
        inv3 = tlib[invtlib.name].generate(name='inv3')

        tinv0 = tlib[tinvlib.name].generate(name='tinv0')
        tinv1 = tlib[tinvlib.name].generate(name='tinv1')

        tinv_small0 = tlib[tinv_slib.name].generate(name='tinv_small0')
        tinv_small1 = tlib[tinv_slib.name].generate(name='tinv_small1')

        # 4. Place instances.
        dsn.place(grid=pg, inst=inv0, mn=[0, 0])
        dsn.place(grid=pg, inst=inv1, mn=pg.mn.bottom_right(inv0))
        dsn.place(grid=pg, inst=tinv0, mn=pg.mn.bottom_right(inv1))
        dsn.place(grid=pg, inst=tinv_small0, mn=pg.mn.bottom_right(tinv0))
        dsn.place(grid=pg, inst=inv2, mn=pg.mn.bottom_right(tinv_small0))
        dsn.place(grid=pg, inst=tinv1, mn=pg.mn.bottom_right(inv2))
        dsn.place(grid=pg, inst=tinv_small1, mn=pg.mn.bottom_right(tinv1))
        dsn.place(grid=pg, inst=inv3, mn=pg.mn.bottom_right(tinv_small1))

        # 5. Create and place wires.
        print("Create wires")

        # 1st M4

        _mn = [r34.mn(inv1.pins['O'])[0], r34.mn(tinv_small1.pins['ENB'])[0]]
        _track = [None, r34.mn(inv1.pins['O'])[0, 1] - 2]
        mn_list = []
        mn_list.append(r34.mn(inv1.pins['O'])[0])
        mn_list.append(r34.mn(tinv0.pins['ENB'])[0])
        mn_list.append(r34.mn(tinv1.pins['EN'])[0])
        mn_list.append(r34.mn(tinv_small0.pins['EN'])[0])
        mn_list.append(r34.mn(tinv_small1.pins['ENB'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        # 2nd M4
        _track[1] += 1
        mn_list = []
        mn_list.append(r34.mn(inv0.pins['O'])[0])
        mn_list.append(r34.mn(inv1.pins['I'])[0])
        mn_list.append(r34.mn(tinv0.pins['EN'])[0])
        mn_list.append(r34.mn(tinv1.pins['ENB'])[0])
        mn_list.append(r34.mn(tinv_small0.pins['ENB'])[0])
        mn_list.append(r34.mn(tinv_small1.pins['EN'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        # 3rd M4
        _track[1] += 1
        mn_list = []
        mn_list.append(r34.mn(inv2.pins['I'])[0])
        mn_list.append(r34.mn(tinv0.pins['O'])[0])
        mn_list.append(r34.mn(tinv_small0.pins['O'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        mn_list = []
        mn_list.append(r34.mn(inv3.pins['I'])[0])
        mn_list.append(r34.mn(tinv1.pins['O'])[0])
        mn_list.append(r34.mn(tinv_small1.pins['O'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        # 4th M4
        _track[1] += 1
        mn_list = []
        mn_list.append(r34.mn(inv2.pins['O'])[0])
        mn_list.append(r34.mn(tinv1.pins['I'])[0])
        mn_list.append(r34.mn(tinv_small0.pins['I'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        mn_list = []
        mn_list.append(r34.mn(inv3.pins['O'])[0])
        mn_list.append(r34.mn(tinv_small1.pins['I'])[0])
        dsn.route_via_track(grid=r34, mn=mn_list, track=_track)

        # VSS
        rvss0 = dsn.route(grid=r12, mn=[r12.mn.bottom_left(inv0), r12.mn.bottom_right(inv3)])

        # VDD
        rvdd0 = dsn.route(grid=r12, mn=[r12.mn.top_left(inv0), r12.mn.top_right(inv3)])

        # 6. Create pins.
        pin0 = dsn.pin(name='I', grid=r23, mn=r23.mn.bbox(tinv0.pins['I']))
        pclk0 = dsn.pin(name='CLK', grid=r23, mn=r23.mn.bbox(inv0.pins['I']))
        pout0 = dsn.pin(name='O', grid=r23, mn=r23.mn.bbox(inv3.pins['O']))
        pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss0))
        pvdd0 = dsn.pin(name='VDD', grid=r12, mn=r12.mn.bbox(rvdd0))