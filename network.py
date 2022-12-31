#!/usr/bin/python3

from re import I
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class FatTreeTopo(Topo):
    
    def __init__(self, k: int) -> None:
        
        # Initialize topology
        Topo.__init__(self)
        self.k: int = k
        self.k_2: int = int(k / 2)

        # Create k pods
        for n in range(self.k):
            self.add_pod(n)

        # Create core switches and link to each pod
        for i in range(1, self.k_2 + 1):
            for j in range(1, self.k_2 + 1):
                switch = self.addSwitch(f"c{j}{i}", ip=f"10.{self.k}.{j}.{i}", dpid=self._compute_dpid(True, j, i))
                for n in range(self.k):
                    self.addLink(switch, f"p{n}_s{self.k_2 + j - 1}")


    def add_pod(self, n: int) -> None:
        """Add a pod to the FatTree topology. A pod is composed of two layers
        of k/2 switches. Each k-port switch in the lower layer is directly
        connected to k/2 hosts.
        
        @param n: The number of the pod
        @return: None
        """
        
        # Create k aggregation and edge switches
        for s in range(self.k):
            # Switch name: p{n}_s{s}   IP: 10.n.s.1 
            self.addSwitch(f"p{n}_s{s}", ip=f"10.{n}.{s}.1", dpid=self._compute_dpid(False, n, s))

        # Create (k/2)^2 hosts and links to edge switches
        for s in range(self.k_2):
            for h in range(2, self.k_2 + 2):
                # Host name: p{n}_s{s}_h{h}   IP: 10.n.s.h
                hostname = self.addHost(f"p{n}_s{s}_h{h}", ip=f"10.{n}.{s}.{h}")
                # Link host with lower-layer switch
                self.addLink(hostname, f"p{n}_s{s}")

        # Create Aggregation-Edge links
        for edge in range(self.k_2):
            for aggr in range(self.k_2, self.k):
                self.addLink(f"p{n}_s{edge}", f"p{n}_s{aggr}")


    def _compute_dpid(self, core: bool, x: int, y: int) -> str:
        """Create OpenFlow Datapath ID for the switch. It is used to identify the switch
        by the SDN controller. It is a 16-bit int composed as follows:
            is_core  | is_edge | pod_number | switch_number    
             1 bit   |  1 bit  |   6 bits   |    8 bits   
        
        @param core: If switch is a core switch
        @param x: X-Coordinate of the switch within the pod or the core grid
        @param y: Y-Coordinate of the switch within the pod or the core grid  
        @return: dpid
        """
        return bin(core << 15 | (y < self.k_2) << 14 | x << 8 | y)[2:] 


topos = {"fattree": (lambda: FatTreeTopo(4))}

if __name__ == "__main__":
    topo = FatTreeTopo(4)
    net = Mininet(
        topo=topo,
        controller = RemoteController("c0", ip="127.0.0.1"),
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    net.build()
    net.start()
    CLI(net)
    net.stop()