from network.params import FAT_TREE_K
import typing

class Switch():

    def __init__(self, dpid: int = 0) -> None:
        if len(bin(dpid)) > 18: 
            dpid = self.__dpid64_to_dpid16(dpid)

        self.dpid: int = dpid
        # is a core switch
        self.is_core: bool = self.dpid >> 15

        # Initialize port stats for the switch, knowing that the number of ports = FAT_TREE_K
        self.port_stats: typing.Dict[int, PortStats] = { i : PortStats(0, 0) for i in range(1, FAT_TREE_K + 1) }

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

    
    def __dpid64_to_dpid16(self, dpid_64: int) -> int:
        """ Convert a 64-bit format dpid to an OpenFlow-standard 16-bit format dpid
        
        @param dpid_64: The 64-bit dpid
        @return: The 16-bit dpid
        """
        dpid_16 = ''
        dpid_bin = bin(dpid_64)
        for i in range(2, len(dpid_bin), 4):
            dpid_16 += dpid_bin[i]
        return int(dpid_16, 2)


class PortStats():

    def __init__(self, tx_bytes: int = 0, rx_bytes: int = 0) -> None:
        self.tx_bytes: int = tx_bytes    # Total amount of transmitted bytes (from the beginning of the simulation)
        self.rx_bytes: int = rx_bytes    # Total amount of received bytes (from the beginning of the simulation)
        self.dtx_bytes: int = tx_bytes   # Difference between the transmitted bytes now and before the update  
        self.drx_bytes: int = rx_bytes   # Difference between the received bytes now and before the update


    def update_stats(self, tx_bytes: int, rx_bytes: int) -> None:
        """ Update the current transmitted and received bytes counters along with the delta counters
        @param tx_bytes: The new tx_bytes value
        @param rx_bytes: The new rx_bytes value
        """
        self.dtx_bytes = tx_bytes - self.tx_bytes
        self.drx_bytes = rx_bytes - self.rx_bytes
        self.tx_bytes = tx_bytes
        self.rx_bytes = rx_bytes