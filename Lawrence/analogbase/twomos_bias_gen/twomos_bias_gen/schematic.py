import os
from typing import *
from bag.design import Module

yaml_file = os.path.join(f'{os.environ["BAG_GENERATOR_ROOT"]}/BagModules/twomos_bias_templates', 'netlist_info', 'twomos_bias.yaml')


# noinspection PyPep8Naming
class schematic(Module):
    """Module for library twomos_bias_templates cell twomos_bias.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)
       
    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            lch='inverter/switch channel length, in meters.',
            tx_info='List of dictionaries of transistor information',
            dum_info='Dummy information data structure.', 
            )

    def design(self, **kwargs):
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.

        To modify schematic structure, call:

        rename_pin()
        delete_instance()
        replace_instance_master()
        reconnect_instance_terminal()
        restore_instance()
        array_instance()
        """
        # design main transistors
        tran_info_list = [('XP0', 'p'), ('XN0', 'n')]
        lch = kwargs.get('lch')
        tx_info = kwargs.get('tx_info')
        dum_info = kwargs.get('dum_info')

        for sch_name, layout_name in tran_info_list:
            w = tx_info[layout_name]['w']
            th = tx_info[layout_name]['th']
            nf = tx_info[layout_name]['fg']
            self.instances[sch_name].design(w=w, l=lch, nf=nf, intent=th, multi=1)

        # design dummies
        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')
