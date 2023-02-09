from params import FAT_TREE_K

class Switch():

    def __init__(self, dpid: int = 0) -> None:
        if len(bin(dpid)) > 18: 
            dpid = self._dpid64_to_dpid16(dpid)

        self.dpid: int = dpid
        # is a core switch
        self.is_core: bool = self.dpid >> 15

        if self.is_core:
            # Coordinates within core grid
            self.j: int = (self.dpid & 0x3F00) >> 8
            self.i: int = self.dpid & 0xFF
            self.name: str = f"c{self.j}{self.i}" 
            self.is_edge: bool = False
        else:
            # Pod number 
            self.pod: int = (self.dpid & 0x3F00) >> 8
            # Switch number inside pod 
            self.swn: int = self.dpid & 0xFF
            self.name: str = f"p{self.pod}_s{self.swn}"
            self.is_edge: bool = self.dpid >> 14


    def set_dpid(self, core: bool, x: int, y: int) -> str:
        """Create OpenFlow Datapath ID for the switch. It is used to identify the switch
        by the SDN controller. It is a 16-bit int composed as follows:
            is_core  | is_edge | pod_number | switch_number    
             1 bit   |  1 bit  |   6 bits   |    8 bits   
        
        @param core: If switch is a core switch
        @param x: X-Coordinate of the switch within the pod or the core grid
        @param y: Y-Coordinate of the switch within the pod or the core grid  
        @return: dpid
        """
        self.dpid = bin(core << 15 | (y < (int)(FAT_TREE_K / 2)) << 14 | x << 8 | y)[2:] 
        return self.dpid

    
    def _dpid64_to_dpid16(self, dpid_64: int) -> int:
        """ Convert a 64-bit format dpid to an OpenFlow-standard 16-bit format dpid
        
        @param dpid_64: The 64-bit dpid
        @return: The 16-bit dpid
        """
        dpid_16 = ''
        dpid_bin = bin(dpid_64)
        for i in range(2, len(dpid_bin), 4):
            dpid_16 += dpid_bin[i]
        return int(dpid_16, 2)