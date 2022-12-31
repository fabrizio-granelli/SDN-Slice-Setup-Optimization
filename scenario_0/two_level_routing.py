from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


FAT_TREE_K = 4


class TwoLevelRouting(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TwoLevelRouting, self).__init__(*args, **kwargs)
        self.k: int = FAT_TREE_K
        self.k_2: int = int(FAT_TREE_K / 2)       


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        switch = Switch(int(self._dpid64_to_dpid16(datapath.id), 2))

        if switch.is_core:
            # Config core switch routing
            for pod in range(self.k):
                self._add_flow(datapath, ip=f"10.{pod}.0.0", mask=0xFFFF0000, port=pod+1)

        else:
            # Config pod switch routing
            if switch.is_edge:
                # Config edge switch routing
                for hostid in range(2, int(self.k_2) + 2):
                    self._add_flow(datapath, ip=f"10.{switch.pod}.{switch.swn}.{hostid}", mask=0xFFFFFFFF, port=hostid-1)
       
            else:
                # Config aggregate switch routing
                for sub in range(self.k_2):
                    self._add_flow(datapath, ip=f"10.{switch.pod}.{sub}.0", mask=0xFFFFFF00, port=sub+1)
            
            for hostid in range(2, self.k_2 + 2):
                port = (hostid - 2 + switch.swn) % self.k_2 + self.k_2
                self._add_flow(datapath, ip=f"0.0.0.{hostid}", mask=0x000000FF, port=port+1)


    def _add_flow(self, datapath, ip: str, mask: int, port: int) -> None:
        """ Send OFPFlowMod message to set a new entry to the flowtable of the switch identified by datapath.
        This flowtable configuration works as a routing table. 

        @param datapath: The 16-bit datapath of the switch to configure
        @param ip: Dest IP address to be matched
        @param mask: Address mask to match multiple IPs
        @param port: The output port of the switch (ports numbering starts from 1)
        @return: None
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch (       # Flow table match object
            eth_type_nxm = 0x0800,      # This is required according to the Ryu docs
            ipv4_dst_nxm = (ip, mask),  # Destination IP with mask 
        )
        actions = [ parser.OFPActionOutput(port) ]  # Forward packet to provided port
        inst = [ parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions) ]   # Just a wrapper for actions list
        req = parser.OFPFlowMod(datapath, match=match, instructions=inst)
        datapath.send_msg(req)


    def _dpid64_to_dpid16(self, dpid_64: int) -> str:
        """ Convert a 64-bit format dpid to an OpenFlow-standard 16-bit format dpid
        
        @param dpid_64: The 64-bit dpid
        @return: The 16-bit dpid
        """
        dpid_16 = ''
        dpid_bin = bin(dpid_64)
        for i in range(2, len(dpid_bin), 4):
            dpid_16 += dpid_bin[i]
        return dpid_16
    

class Switch():

    def __init__(self, dpid: int) -> None:
        # dpid int
        self.dpid: int = dpid
        # is a core switch
        self.is_core: bool = self.dpid >> 15

        if self.is_core:
            # Coordinates within core grid
            self.j: int = (dpid & 0x3F00) >> 8
            self.i: int = dpid & 0xFF
            self.name: str = f"c{self.j}{self.i}" 
            self.is_edge: bool = False
        else:
            # Pod number 
            self.pod: int = (dpid & 0x3F00) >> 8
            # Switch number inside pod 
            self.swn: int = dpid & 0xFF
            self.name: str = f"p{self.pod}_s{self.swn}"
            self.is_edge: bool = self.dpid >> 14
