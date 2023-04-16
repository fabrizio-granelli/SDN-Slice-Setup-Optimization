from mininet.node import OVSKernelSwitch, RemoteController, Host
from mininet.cli import CLI
from mininet.link import TCLink
from comnetsemu.net import Containernet, VNFManager
from comnetsemu.node import DockerHost
from network.globals import FAT_TREE_K
from network.topology import FatTreeTopo 
import time


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


    server: DockerHost = net.getNodeByName('p0_s0_h2')
    client: DockerHost = net.getNodeByName('p1_s0_h2')

    mgr.addContainer(
        'Serverone', 'p0_s0_h2', 'service_migration',  'python3 /home/server.py'
    )

    print("Created server")
    time.sleep(3)

    clog1 = mgr.addContainer(
        'Clientone1', 'p1_s0_h2', 'service_migration',  'python3 /home/client.py'
    )
    print("Created client 1")

    clog2 = mgr.addContainer(
        'Clientone2', 'p2_s0_h2', 'service_migration',  'python3 /home/client.py'
    )
    print("Created client 2")
    
    time.sleep(10)

    print("Client 1", clog1.getLogs())
    print("Client 2", clog2.getLogs())


    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
    