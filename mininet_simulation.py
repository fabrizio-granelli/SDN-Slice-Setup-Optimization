from mininet.topo import Topo
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from comnetsemu.net import Containernet, VNFManager
from network.params import FAT_TREE_K
from network.topology import FatTreeTopo 


def main():
    topo = FatTreeTopo(FAT_TREE_K)
    net = Containernet(
        topo=topo,
        controller = RemoteController("c0", ip="127.0.0.1"),
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )

    mgr = VNFManager(net)

    net.build()
    net.start()

    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
    