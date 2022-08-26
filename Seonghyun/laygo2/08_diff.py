##########################################################
#                                                        #
#    Fifty Nifty Variations of Two-Transistor Circuits   #
#         08) Differential Pair Layout Generator         #
#          Contributors: T. Shin, S. Park, Y. Oh         #
#                 Last Update: 2022-08-11                #
#                                                        #
##########################################################

import numpy as np
import pprint
import laygo2
import laygo2.interface
import laygo2_tech as tech

# Parameter definitions #############
# Design Variables
cell_type = ['08_diff_pair']
nf_list = [2, 10]

# Templates
tpmos_name = 'pmos_sky'
tnmos_name = 'nmos_sky'

# Grids
pg_name = 'placement_basic'
r12_name = 'routing_12_cmos'
r23_name = 'routing_23_cmos'
r34_name = 'routing_34_basic'

# Design hierarchy
libname = 'fifty_nifty_generated'
export_path       = './fifty_nifty/' # Layout generation path: "export_path/libname/cellname"
export_path_tcl = export_path+'tcl/' # TCL file generation path: "export_path_skill/libname_cellname.tcl"
# End of parameter definitions ######

# Generation start ##################
# 1. Load templates and grids.
print("Load templates")
templates = tech.load_templates()
tpmos, tnmos = templates[tpmos_name], templates[tnmos_name]
# tlib = laygo2.interface.yaml.import_template(filename=export_path+'logic_generated_templates.yaml') # Uncomment if you use the logic templates
# print(templates[tpmos_name], templates[tnmos_name], sep="\n") # Uncomment if you want to print templates

print("Load grids")
grids = tech.load_grids(templates=templates)
pg, r12, r23, r34 = grids[pg_name], grids[r12_name], grids[r23_name], grids[r34_name]
# print(grids[pg_name], grids[r12_name], grids[r23_name], grids[r34_name], sep="\n") # Uncomment if you want to print grids

for celltype in cell_type:
   for nf in nf_list:
      cellname = celltype+'_'+str(nf)+'x'
      print('--------------------')
      print('Now Creating '+cellname)
      
# 2. Create a design hierarchy
      lib = laygo2.object.database.Library(name=libname)
      dsn = laygo2.object.database.Design(name=cellname, libname=libname)
      lib.append(dsn)
      
# 3. Create instances.
      print("Create instances")
      in0 = tnmos.generate(name='MN0', params={'nf': nf})
      in1 = tnmos.generate(name='MN1', params={'nf': nf})

# 4. Place instances.
      dsn.place(grid=pg, inst=in0, mn=[0,0])
      dsn.place(grid=pg, inst=in1, mn=pg.mn.bottom_right(in0))

# 5. Create and place wires.
      print("Create wires")
      
      # Bias
      _mn = [r12.mn(in0.pins['S'])[0], r12.mn(in1.pins['S'])[1]]
      rbias0 = dsn.route(grid=r12, mn=_mn)

      # VSS
      rvss0 = dsn.route(grid=r12, mn=[r12.mn(in0.pins['RAIL'])[0], r12.mn(in1.pins['RAIL'])[1]])

# 6. Create pins.
      pina0 = dsn.pin(name='In', grid=r23, mn=r23.mn.bbox(in0.pins['G']))
      pinb0 = dsn.pin(name='Ip', grid=r23, mn=r23.mn.bbox(in1.pins['G']))
      pout0 = dsn.pin(name='On', grid=r23, mn=r23.mn.bbox(in0.pins['D']))
      pout1 = dsn.pin(name='Op', grid=r23, mn=r23.mn.bbox(in1.pins['D']))
      pbias0 = dsn.pin(name='BIAS', grid=r12, mn=r12.mn.bbox(rbias0))
      pvss0 = dsn.pin(name='VSS', grid=r12, mn=r12.mn.bbox(rvss0))

# 7. Export to physical database.
      print("Export design")
      print("")
      laygo2.interface.magic.export(lib, filename=export_path_tcl+libname+'_'+cellname+'.tcl', cellname=None, scale=1, reset_library=False, libpath='./magic_layout', tech_library='sky130A')
      # Filename example: ./laygo2_generators_private/logic/skill/logic_generated_bcap_4x.il

# 8. Export to a template database file.
      nat_temp = dsn.export_to_template()
      laygo2.interface.yaml.export_template(nat_temp, filename=export_path+libname+'_templates.yaml', mode='append')
      # Filename example: ./laygo2_generators_private/logic/logic_generated_templates.yaml