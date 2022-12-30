from ryu.base import app_manager
from ryu.controller import ofp_event, controller
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto.ofproto_v1_0_parser import OFPPacketIn


FAT_TREE_K = 4


class TwoLevelRouting(app_manager.RyuApp):
    
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TwoLevelRouting, self).__init__(*args, **kwargs)
        
        self.k = FAT_TREE_K
        self.K_2 = self.k / 2

        # # Generate aggregation switch routing tables
        # for pod in range(self.k):
        #     for switch in range(self.k_2, self.k):
        #         for subnet in range(self.k_2):
        #             # Add prefix (10.pod.switch.1 , 10.pod.subnet.0/24 , subnet)
        #             pass
        #         # Add prefix (10.pod.switch.1 , 0.0.0.0/0 , 0)
        #         for host in range(2, self.K_2):
        #             # Add suffix (10.pod.switch.1 , 0.0.0.subnet/8 , (subnet-2+switch) % k_2 + k_2)
        #             pass
        

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg: OFPPacketIn = ev.msg
        dp: controller.Datapath = msg.datapath
        dpid = self.dpid_to_16bit(dp.id)
        print(self.dpid_to_name(dpid))
        print(dpid)
        
    
    def _dpid64_to_dpid16(self, dpid_64: str) -> str:
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

    def __init__(self, dpid: str) -> None:
        # dpid string
        self.dpid_s: str = dpid
        # dpid int
        self.dpid_i: int = int(dpid, 2)
        # is a core switch
        self.is_core: bool = self.dpid_i >> 15

        if self.is_core:
            # Coordinates within core grid
            self.j = (dpid & 0x3F00) >> 8
            self.i = dpid & 0xFF
            self.name = f"c{self.j}{self.i}" 
        else:
            # Pod number 
            self.pod = (dpid & 0x3F00) >> 8
            # Switch number inside pod 
            self.swn = dpid & 0xFF
            self.name = f"p{self.pod}_s{self.swn}"
