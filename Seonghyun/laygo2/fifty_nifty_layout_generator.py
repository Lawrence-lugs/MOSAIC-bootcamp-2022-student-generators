def execfile(filepath, globals=None, locals=None):
   if globals is None:
      globals = {}
   globals.update({
      "__file__": filepath,
      "__name__": "__main__",
   })
   import os
   with open(filepath, 'rb') as file:
      exec(compile(file.read(), filepath, 'exec'), globals, locals)

ref_dir = './seonghyun-code/fify_nifty_generators/'
files = [
   ref_dir+'01_inv.py',
   ref_dir+'03_esd_tie.py',
   ref_dir+'05_nand.py',
   ref_dir+'06_nor.py',
   ref_dir+'07_current_mirror.py',
   ref_dir+'08_diff.py',
   ref_dir+'09_source_follower.py',
   ref_dir+'10_cs_amp.py',
   ref_dir+'11_cascode_cs_amp.py',
   ref_dir+'12_cascode_cg_amp.py',
   ref_dir+'13_cg_amp.py',
   ref_dir+'14_tgate.py',
   ref_dir+'15_2to1mux.py',
   ref_dir+'17_diode_cs_amp.py',
   ref_dir+'18_diode_cs_amp_folded.py',
   ref_dir+'19_classB_pushpull.py',
   ref_dir+'20_degenerated_cs_amp.py',
   ref_dir+'21_cs_amp_variation.py',
   ref_dir+'24_bias_voltage_gen.py'
   ]
idx=0
for f in files:
   execfile(f)
   idx += 1
   print(str(round(idx/len(files)*100,2))+'% done')