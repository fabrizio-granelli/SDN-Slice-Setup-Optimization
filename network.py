#!/usr/bin/python3

from re import I
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class FatTreeTopo(Topo):
    
    def __init__(self, k):
        
        # Initialize topology
        Topo.__init__(self)
        self.k = k
        self.k_2 = int(k / 2)

        # Create k pods
        for n in range(self.k):
            self.add_pod(n)

        # Create core switches and link to each pod
        for i in range(1, self.k_2 + 1):
            for j in range(1, self.k_2 + 1):
                switch = self.addSwitch(f"c{j}{i}", ip=f"10.{self.k}.{j}.{i}")
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
            self.addSwitch(f"p{n}_s{s}", ip=f"10.{n}.{s}.1")

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