##########################################
#                                        #
#   Current Mirror Layout Gernerator     #
#         Created by Kevin Pizarro       #
#                                        #
##########################################

import laygo2.interface
import laygo2_tech as tech
from laygo2_gds_view import setup_viewer

# Parameter definitions #############
# Variables
cell_type = ['current_mirror']
# nf_list = [2, 4, 6, 8, 10, 12, 16, 24, 32, 36, 40, 50, 64, 72, 100]
# nf_list = [2, 4, 6, 8, 10, 12, 16, 24, 32]
nf_list = [2, 4]
# Templates
tnmos_name = 'nmos_sky'
# Grids
pg_name = 'placement_basic'
r12_name = 'routing_12_cmos'
r23_name = 'routing_23_cmos'
# Design hierarchy
libname = 'logic_generated'
# cellname in for loop
ref_dir_template = './'  # './laygo2_generators_private/magic/logic/'
ref_dir_MAG_exported = './'  # './laygo2_generators_private/magic/logic/tcl/'
# End of parameter definitions ######

# Generation start ##################
# 1. Load templates and grids.
print("Load templates")
templates = tech.load_templates()
tnmos = templates[tnmos_name]
# tlib = laygo2.interface.yaml.import_template(filename=ref_dir_template+'logic_generated_templates.yaml')
print(templates[tnmos_name])

print("Load grids")
grids = tech.load_grids(templates=templates)
pg, r12, r23 = grids[pg_name], grids[r12_name], grids[r23_name]
print(grids[pg_name], grids[r12_name], grids[r23_name], sep="\n")

lib = laygo2.object.database.Library(name=libname)

for celltype in cell_type:
    for nf in nf_list:
        cellname = celltype + '_' + str(nf) + 'x'
        print('--------------------')
        print('Now Creating ' + cellname)

        # 2. Create a design hierarchy
        dsn = laygo2.object.database.Design(name=cellname, libname=libname)
        lib.append(dsn)

        # 3. Create instances.
        print("Create instances")
        in0 = tnmos.generate(name='MN0', params={'nf': nf, 'tie': 'S'})
        in1 = tnmos.generate(name='MN1', params={'nf': nf, 'tie': 'S'})

        # 4. Place instances.
        #   dsn.place(grid=pg, inst=[[in0], [ip0]], mn=[0,0])
        #   dsn.place(grid=pg, inst=[[in0 ,in1], [ip0, ip1]], mn=[0,0])
        dsn.place(grid=pg, inst=in0, mn=[0, 0])
        dsn.place(grid=pg, inst=in1, mn=pg.mn.bottom_left(in0) - pg.mn.width_vec(in0))

        # 5. Create and place wires.
        print("Create wires")

        # GATES
        _mn = [r23.mn(in0.pins['G'])[0], r23.mn(in1.pins['G'])[0]]
        _track = [r23.mn(in0.pins['G'])[0, 0] - 1, None]
        rgate = dsn.route_via_track(grid=r23, mn=_mn, track=_track)

        # IN
        # rin = dsn.route(grid=r12, mn=[r12.mn(in0.pins['D'])[0], r12.mn(in0.pins['D'])[1]])
        _mn = [r23.mn(in0.pins['D'])[0], r23.mn(in0.pins['G'])[0], r23.mn(in1.pins['G'])[0]]
        _track = [r23.mn(in0.pins['D'])[0, 0] - 1, None]
        rin = dsn.route_via_track(grid=r23, mn=_mn, track=_track)

        # OUT
        rout = dsn.route(grid=r12, mn=[r12.mn(in1.pins['D'])[0], r12.mn(in1.pins['D'])[1]])

        # VSS
        # _mn = [r12.mn(in0.pins['RAIL'])[0], r12.mn(in0.pins['RAIL'])[1],r12.mn(in1.pins['RAIL'])[0],  r12.mn(in1.pins['RAIL'])[1]]
        # rvss = dsn.route(grid=r12, mn=_mn, via_tag=[True, True, True, True])

        # rvss0 = dsn.route(grid=r12, mn=[r12.mn(in0.pins['RAIL'])[0], r12.mn(in0.pins['RAIL'])[1]])
        # rvss1 = dsn.route(grid=r12, mn=[r12.mn(in1.pins['RAIL'])[0], r12.mn(in1.pins['RAIL'])[1]])

        _mn = [r12.mn(in0.pins['RAIL'])[0], r12.mn(in1.pins['RAIL'])[0]]
        _track = [r12.mn(in0.pins['RAIL'])[0, 0] - 1, None]
        rvss = dsn.route_via_track(grid=r12, mn=_mn, track=_track)

        # 6. Create pins.
        # import pdb
        # pdb.set_trace()
        pin = dsn.pin(name='I', grid=r12, mn=r12.mn.bbox(rin[0][0]))
        pout = dsn.pin(name='O', grid=r12, mn=r12.mn.bbox(rout))
        pvss = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss[0][0]))
        # pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss0))
        # pvss1 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss1))

        # 7. Export to physical database.
        print("Export design")
        print("")

        # Uncomment for BAG export
        laygo2.interface.magic.export(lib, filename=ref_dir_MAG_exported + libname + '_' + cellname + '.tcl',
                                      cellname=None, libpath=ref_dir_template + 'magic_layout', scale=1,
                                      reset_library=False, tech_library='sky130A')
        # 8. Export to a template database file.
        nat_temp = dsn.export_to_template()
        laygo2.interface.yaml.export_template(nat_temp, filename=ref_dir_template + libname + '_templates.yaml',
                                              mode='append')
        setup_viewer.Laygo2GdsViewer.view(self=setup_viewer.Laygo2GdsViewer, dsn=dsn)

