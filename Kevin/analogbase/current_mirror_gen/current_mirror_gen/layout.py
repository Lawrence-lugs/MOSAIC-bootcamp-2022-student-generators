from abs_templates_ec.analog_core import AnalogBase
from bag.layout.routing import TrackManager, TrackID
from .params import CurrentMirrorParams

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
            params='CurrentMirrorParams parameter object',
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
        params: CurrentMirrorParams = self.params['params']

        # horiz_conn_layer = self.mos_conn_layer + 1
        vert_conn_layer = self.mos_conn_layer + 2

        tr_manager = TrackManager(self.grid, params.tr_widths, params.tr_spaces)

        # Set up the row information
        row_nmos = Row(name='n',
                       orientation=RowOrientation.MX,
                       channel_type=ChannelType.N,
                       width=params.w_dict['n'],
                       threshold=params.th_dict['n'],
                       wire_names_g=['I'],
                       wire_names_ds=['I', 'O', 'VSS']
                       )

        # Define the order of the rows (bottom to top) for this analogBase cell
        rows = RowList([row_nmos])

        # Initialize the transistors in the design
        divide = 1
        fg_n = params.seg_dict['n'] // divide

        nmos_in  = Transistor(name='n1', row=row_nmos, fg=fg_n, seff_net='VSS', deff_net='I')
        nmos_out = Transistor(name='n2', row=row_nmos, fg=fg_n, seff_net='VSS', deff_net='O')

        # Compose a list of all the transistors so it can be iterated over later
        transistors = [nmos_in, nmos_out]

        # 3:   Calculate transistor locations
        fg_single = nmos_in.fg
        fg_total = fg_single * 2 + 2 * params.ndum
        fg_dum = params.ndum

        # if (nmos_in.fg - nmos_out.fg) % 4 != 0:
        #     raise ValueError('We assume seg_n1 and seg_n2 differ by multiples of 4.')
        # import pdb
        # pdb.set_trace()
        # Calculate positions of transistors
        nmos_in.assign_column(offset=fg_dum, fg_col=fg_single, align=TransistorAlignment.CENTER)
        nmos_out.assign_column(offset=fg_dum, fg_col=fg_single*3, align=TransistorAlignment.CENTER)

        # 4:  Assign the transistor directions (s/d up vs down)
        nmos_in.set_directions(seff=EffectiveSource.S, seff_dir=TransistorDirection.DOWN)
        nmos_out.set_directions(seff=EffectiveSource.S, seff_dir=TransistorDirection.DOWN)

        n_rows = rows.n_rows

        # 5:  Draw the transistor rows, and the transistors
        # Draw the transistor row bases
        self.draw_base(params.lch, fg_total, params.ptap_w, params.ntap_w,
                       n_rows.attribute_values('width'), n_rows.attribute_values('threshold'),
                       [], [],
                       tr_manager=tr_manager, wire_names=rows.wire_names_dict(),
                       n_orientations=n_rows.attribute_values('orientation'),
                       # p_orientations=p_rows.attribute_values('orientation'),
                       top_layer=params.top_layer,
                       half_blk_x=True, half_blk_y=True,
                       guard_ring_nf=params.guard_ring_nf,
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

        # # 6:  Define horizontal tracks on which connections will be made
        row_nmos_idx = rows.index_of_same_channel_type(row_nmos)

        # IN
        tid_nmos_in_G = self.get_wire_id('nch', row_nmos_idx, 'g', wire_name='I')
        warr_n_in_out_G = self.connect_to_tracks([nmos_in.g, nmos_out.g], tid_nmos_in_G)
        warr_n_in_DG = self.connect_to_tracks([nmos_in.d, nmos_in.g], tid_nmos_in_G)
        self.add_pin('I', warr_n_in_DG)

        # OUT
        tid_nmos_out_D = self.get_wire_id('nch', row_nmos_idx, 'ds', wire_name='O')
        warr_n2_D = self.connect_to_tracks([nmos_out.d], tid_nmos_out_D)
        self.add_pin(self.get_pin_name('O'), warr_n2_D)

        # VSS
        self.connect_to_substrate('ptap', nmos_in.s)
        self.connect_to_substrate('ptap', nmos_out.s)
        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy()
        # export supplies
        self.add_pin('VSS', ptap_wire_arrs)

        # Define vertical tracks for the connections, based on the location of the col
        # tid_S_vert = TrackID(
        #     layer_id=vert_conn_layer,
        #     track_idx=self.grid.coord_to_nearest_track(
        #         layer_id=vert_conn_layer,
        #         coord=self.layout_info.col_to_coord(
        #             col_idx=fg_dum,
        #             unit_mode=True
        #         ),
        #         half_track=False,
        #         mode=1,
        #         unit_mode=True
        #     ),
        #     width=tr_manager.get_width(vert_conn_layer, 'sig1')
        # )

        # Connection of transistors sources
        # self.connect_to_tracks(
        #     [warr_n1_S, warr_n2_S],
        #     tid_S_vert,
        #     min_len_mode=0,
        # )


        #
        # # Define transistor properties for schematic
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


class current_mirror(layout):
    """
    Class to be used as template in higher level layouts
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
