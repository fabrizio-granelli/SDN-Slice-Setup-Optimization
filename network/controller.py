from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_5
from ryu.lib.packet import packet, ipv4
from switch import Switch
from globals import FAT_TREE_K, slices
from flow_scheduler import FlowScheduler
import typing


class TwoLevelRouting(app_manager.RyuApp):

    OFP_VERSIONS = [ ofproto_v1_5.OFP_VERSION ]

    def __init__(self, *args, **kwargs):
        super(TwoLevelRouting, self).__init__(*args, **kwargs)
        self.k: int = FAT_TREE_K
        self.k_2: int = int(FAT_TREE_K / 2)       
        self.switches = {}    # Contains all the datapaths connected to the controller
        
        self.scheduler = FlowScheduler(self.switches)
        self.scheduler.start()  


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def __switch_features_handler(self, ev) -> None:
        """ Configure switches the first time they connect to the ryu controller - Incoming traffic ONLY
        Implements the two-level routing mechanism described in the paper by Mohammad Al-Fares et al.
        Configuration of the pod switches for outgoing traffic is left to the MAIN_DISPATCHER to enable slicing.
        """
        datapath = ev.msg.datapath
        switch = Switch(datapath.id)
        self.switches[datapath.id] = datapath

        # Install two-levels routing rules
        if switch.is_core:
            # Config core switch routing
            for pod in range(self.k):
                self.__add_two_level_flow(datapath, ip=f"10.{pod}.0.0", mask=0xFFFF0000, port=pod+1)
        else:
            # Config pod switch routing
            if switch.is_edge:  # Config edge switch routing
                for hostid in range(2, self.k_2 + 2):
                    self.__add_two_level_flow(datapath, ip=f"10.{switch.pod}.{switch.swn}.{hostid}", mask=0xFFFFFFFF, port=hostid-1)
            else:   # Config aggregate switch routing
                for sub in range(self.k_2):
                    self.__add_two_level_flow(datapath, ip=f"10.{switch.pod}.{sub}.0", mask=0xFFFFFF00, port=sub+1)

        # Install table-miss flow entry
        match = datapath.ofproto_parser.OFPMatch(eth_type=0x0800)   # Install to IPv4 only 
        actions = [ datapath.ofproto_parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER, datapath.ofproto.OFPCML_NO_BUFFER) ]  
        inst = [ datapath.ofproto_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, actions) ]
        datapath.send_msg( datapath.ofproto_parser.OFPFlowMod( datapath=datapath, priority=0, match=match, instructions=inst ))


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def __packet_in_handler(self, ev) -> None:
        """ Switches send PacketIn after matching table-miss entry (installed by CONFIG_DISPATCHER).
        Get ip src and dst, check whether hosts can communicate based on slice policy, install flow if granted by policy.
        Only Pod switches are configured for slicing (not core switches), therefore pkts with wrong destination are dropped at the first stage.
        """
        msg = ev.msg
        switch = Switch(msg.datapath.id)
        ip_pkt = packet.Packet(msg.data).get_protocol(ipv4.ipv4)
        dst_hostid = int(ip_pkt.dst.split('.')[3])

        # Check that src is in the same slice of dst
        bool_slice = False
        for slice in slices.values():
            if ip_pkt.dst in slice and ip_pkt.src in slice:
                bool_slice = True
                break
        
        if not bool_slice:
            return

        port = (dst_hostid - 2 + switch.swn) % self.k_2 + self.k_2
        self.__add_two_level_flow(msg.datapath, ip=ip_pkt.dst, mask=0xFFFFFFFF, port=port+1, timeout=30)


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def __port_stats_reply_handler(self, ev) -> None:
        """ Forward port stats event to the scheduler """
        self.scheduler.save_port_stats(ev.msg.datapath.id, ev.msg.body)


    def __add_two_level_flow(self, datapath, ip: str, mask: int, port: int, timeout: int = 0) -> None:
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
        actions = [ 
            parser.OFPActionOutput(port),    # Forward packet to provided port
        ]  
        inst = [ parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions) ]   # Just a wrapper for actions list
        req = parser.OFPFlowMod(datapath, match=match, instructions=inst, idle_timeout=timeout)
        datapath.send_msg(req)
