from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from comnetsemu.net import Containernet, VNFManager
from network.params import FAT_TREE_K
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

    print("*** Deploy counter service on h2.\n")
    counter_server_h2 = mgr.addContainer(
        "counter_server_h2", "p0_s0_h2", "service_migration", "python /home/server.py p0_s0_h2"
    )
    time.sleep(3)

    
    print("*** Deploy client app on h1.\n")
    client_app = mgr.addContainer(
        "client", "p2_s1_h2", "service_migration", "python /home/client.py"
    )
    time.sleep(10)


    client_log = client_app.getLogs()
    print("\n*** Setup1: Current log of the client: \n{}".format(client_log))

    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
    