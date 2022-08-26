from abs_templates_ec.analog_core import AnalogBase
from bag.layout.routing import TrackManager, TrackID
from .params import TGateParams

from sal.transistor import *


class layout(AnalogBase):
    """
    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
           the template database.
    lib_name : str
       the layout library name.
    params : dict[str, any]
       the parameter values.
    used_names : set[str]
       a set of already used cell names.
    **kwargs :
       dictionary of optional parameters.  See documentation of
       :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
        self._sch_params = None
    
    @classmethod
    def get_params_info(cls):
        """
        Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : dict[str, str]
           dictionary from parameter name to description.
        """
        return dict(
            params='TGateParams parameter object',
        )

    @classmethod
    def get_default_param_values(cls):
        """
        Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : dict[str, any]
           dictionary of default parameter values.
        """
        return dict(
        )

    @property
    def sch_params(self):
        # type: () -> Dict[str, Any]
        return self._sch_params

    def draw_layout(self):
        params: TGateParams = self.params['params']

        # horiz_conn_layer = self.mos_conn_layer + 1
        vert_conn_layer = self.mos_conn_layer + 2

        tr_manager = TrackManager(self.grid, params.tr_widths, params.tr_spaces)

        # Set up the row information
        row_Dummy_NB = Row(name='Dummy_NB',
                           orientation=RowOrientation.R0,
                           channel_type=ChannelType.N,
                           width=params.w_dict['Dummy_NB'],
                           threshold=params.th_dict['Dummy_NB'],
                           wire_names_g=['sig1', 'EN'],
                           wire_names_ds=['I']
                           )

        row_nmos_bot = Row(name='n',
                           orientation=RowOrientation.MX,
                           channel_type=ChannelType.N,
                           width=params.w_dict['n'],
                           threshold=params.th_dict['n'],
                           wire_names_g=['VREF'],
                           wire_names_ds=['VREF', 'VSS']
                           )

        row_Dummy_NT = Row(name='Dummy_NT',
                           orientation=RowOrientation.R0,
                           channel_type=ChannelType.N,
                           width=params.w_dict['Dummy_NT'],
                           threshold=params.th_dict['Dummy_NT'],
                           wire_names_g=['sig1'],
                           wire_names_ds=['I', 'O']
                           )

        row_Dummy_PB = Row(name='Dummy_PB',
                           orientation=RowOrientation.R0,
                           channel_type=ChannelType.N,
                           width=params.w_dict['Dummy_PB'],
                           threshold=params.th_dict['Dummy_PB'],
                           wire_names_g=['ENB'],
                           wire_names_ds=['I', 'O']
                           )

        row_nmos_top = Row(name='n',
                           orientation=RowOrientation.MX,
                           channel_type=ChannelType.N,
                           width=params.w_dict['n'],
                           threshold='hvt',
                           wire_names_g=['VSS'],
                           wire_names_ds=['VDD', 'VREF']
                           )

        row_Dummy_PT = Row(name='Dummy_PT',
                           orientation=RowOrientation.R0,
                           channel_type=ChannelType.P,
                           width=params.w_dict['Dummy_PT'],
                           threshold=params.th_dict['Dummy_PT'],
                           wire_names_g=['ENB'],
                           wire_names_ds=['I', 'O']
                           )

        # Define the order of the rows (bottom to top) for this analogBase cell
        rows = RowList([row_Dummy_NB, row_nmos_bot, row_Dummy_NT, row_Dummy_PB, row_nmos_top, row_Dummy_PT])

        # Initialize the transistors in the design
        divide = 1
        fg_n = params.seg_dict['n'] // divide

        nmos_top = Transistor(name='n1', row=row_nmos_top, fg=fg_n, seff_net='VREF', deff_net='VDD')
        nmos_bot = Transistor(name='n0', row=row_nmos_bot, fg=fg_n, seff_net='VSS', deff_net='VREF')

        # Compose a list of all the transistors so it can be iterated over later
        transistors = [nmos_top, nmos_bot]

        # 3:   Calculate transistor locations
        fg_single = max(nmos_top.fg, nmos_bot.fg)
        fg_total = fg_single + 2 * params.ndum
        fg_dum = params.ndum

        if (nmos_top.fg - nmos_bot.fg) % 4 != 0:
            raise ValueError('We assume seg_p and seg_n differ by multiples of 4.')

        # Calculate positions of transistors
        nmos_top.assign_column(offset=fg_dum, fg_col=fg_single, align=TransistorAlignment.CENTER)
        nmos_bot.assign_column(offset=fg_dum, fg_col=fg_single, align=TransistorAlignment.CENTER)

        # 4:  Assign the transistor directions (s/d up vs down)
        nmos_bot.set_directions(seff=EffectiveSource.S, seff_dir=TransistorDirection.UP)
        nmos_top.set_directions(seff=EffectiveSource.D, seff_dir=TransistorDirection.DOWN)

        n_rows = rows.n_rows
        p_rows = rows.p_rows

        # 5:  Draw the transistor rows, and the transistors
        # Draw the transistor row bases
        self.draw_base(params.lch, fg_total, params.ptap_w, params.ntap_w,
                       n_rows.attribute_values('width'), n_rows.attribute_values('threshold'),
                       p_rows.attribute_values('width'), p_rows.attribute_values('threshold'),
                       tr_manager=tr_manager, wire_names=rows.wire_names_dict(),
                       n_orientations=n_rows.attribute_values('orientation'),
                       p_orientations=p_rows.attribute_values('orientation'),
                       top_layer=params.top_layer,
                       half_blk_x=True, half_blk_y=True,
                       guard_ring_nf=params.guard_ring_nf
                       )

        # Draw the transistors
        for tx in transistors:
            ports = self.draw_mos_conn(mos_type=tx.row.channel_type.value,
                                       row_idx=rows.index_of_same_channel_type(tx.row),
                                       col_idx=tx.col,
                                       fg=tx.fg,
                                       sdir=tx.s_dir.value,
                                       ddir=tx.d_dir.value,
                                       s_net=tx.s_net,
                                       d_net=tx.d_net,
                                       gate_ext_mode=1,
                                       g_via_row=2,
                                       )
            tx.set_ports(g=ports['g'],
                         d=ports[tx.deff.value],
                         s=ports[tx.seff.value])

        # 6:  Define horizontal tracks on which connections will be made
        row_nmost_idx = rows.index_of_same_channel_type(row_nmos_top)
        row_nmosb_idx = rows.index_of_same_channel_type(row_nmos_bot)
        tid_nmos_G = self.get_wire_id('nch', row_nmosb_idx, 'g', wire_name='VREF')
        tid_pmos_G = self.get_wire_id('nch', row_nmost_idx, 'g', wire_name='VSS')
        tid_nmos_S = self.get_wire_id('nch', row_nmosb_idx, 'ds', wire_name='VSS')
        tid_pmos_S = self.get_wire_id('nch', row_nmost_idx, 'ds', wire_name='VREF')
        tid_pmos_D = self.get_wire_id('nch', row_nmost_idx, 'ds', wire_name='VDD')

        # 7:  Perform wiring
        warr_n_G = self.connect_to_tracks([nmos_bot.g], tid_nmos_G)
        warr_p_G = self.connect_to_tracks([nmos_top.g], tid_pmos_G)
        warr_p_D = self.connect_to_tracks([nmos_top.s, nmos_bot.d, nmos_bot.g], tid_nmos_G)
        warr_p_S = self.connect_to_tracks([nmos_top.s], tid_pmos_S)
        warr_n_S = self.connect_to_tracks([nmos_bot.s], tid_nmos_S)

        # Define vertical tracks for the connections, based on the location of the col
        tid_S_vert = TrackID(
            layer_id=vert_conn_layer,
            track_idx=self.grid.coord_to_nearest_track(
                layer_id=vert_conn_layer,
                coord=self.layout_info.col_to_coord(
                    col_idx=fg_dum-2,
                    unit_mode=True
                ),
                half_track=False,
                mode=1,
                unit_mode=True
            ),
            width=tr_manager.get_width(vert_conn_layer, 'sig1')
        )

        # Connection of transistors sources
        self.connect_to_tracks(
            [warr_n_S, warr_p_G],
            tid_S_vert,
            min_len_mode=0,
        )

        # Add Pin
        self.add_pin('VREF', warr_p_D, show=params.show_pins)

        #
        self.connect_to_substrate('ptap', [nmos_bot.s])
        self.connect_to_substrate('ntap', [nmos_top.d])

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy()
        # export supplies
        self.add_pin('VSS', ptap_wire_arrs)
        self.add_pin('VDD', ntap_wire_arrs)

        # Define transistor properties for schematic
        tx_info = {}
        for tx in transistors:
            tx_info[tx.name] = {
                'w': tx.row.width,
                'th': tx.row.threshold,
                'fg': tx.fg
            }

        self._sch_params = dict(
            lch=params.lch,
            dum_info=self.get_sch_dummy_info(),
            tx_info=tx_info,
        )


class twomos_stable_bias(layout):
    """
    Class to be used as template in higher level layouts
    """
    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
