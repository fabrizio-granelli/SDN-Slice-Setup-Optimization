#!/usr/bin/python3

from mininet.topo import Topo
from network.switch import Switch
from network.params import FAT_TREE_K


class FatTreeTopo(Topo):
    
    def __init__(self, k: int) -> None:
        
        # Initialize topology
        Topo.__init__(self)
        self.k: int = k
        self.k_2: int = int(k / 2)

        # Create k pods
        for n in range(self.k):
            self._add_pod(n)

        # Create core switches and link to each pod
        for i in range(1, self.k_2 + 1):
            for j in range(1, self.k_2 + 1):
                sw = Switch()
                switch = self.addSwitch(f"c{j}{i}", ip=f"10.{self.k}.{j}.{i}", dpid=sw.set_dpid(True, j, i))
                for n in range(self.k):
                    self.addLink(switch, f"p{n}_s{self.k_2 + j - 1}")


    def _add_pod(self, n: int) -> None:
        """Add a pod to the FatTree topology. A pod is composed of two layers
        of k/2 switches. Each k-port switch in the lower layer is directly
        connected to k/2 hosts.
        
        @param n: The number of the pod
        @return: None
        """
        
        # Create k aggregation and edge switches
        for s in range(self.k):
            # Switch name: p{n}_s{s}   IP: 10.n.s.1 
            sw = Switch()
            self.addSwitch(f"p{n}_s{s}", ip=f"10.{n}.{s}.1", dpid=sw.set_dpid(False, n, s))

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


topos = {"fat-tree": (lambda: FatTreeTopo(FAT_TREE_K))}
