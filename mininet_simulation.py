from mininet.node import OVSKernelSwitch, RemoteController, Host
from mininet.cli import CLI
from mininet.link import TCLink
from comnetsemu.net import Containernet, VNFManager, APPContainer
from comnetsemu.node import DockerHost
from network.globals import FAT_TREE_K, services
from network.topology import FatTreeTopo 
import pickle
import pathlib
import time


mgr: VNFManager = None
running_services = {}
abs_path = pathlib.Path(__file__).parent.resolve()

def spawn_service(name: str, ip: str) -> APPContainer:
    hostname = get_hostname(ip)
    running_services[name] = ip
    return mgr.addContainer( 
        name=f'srv{name}_{hostname}', 
        dhost=hostname, 
        dimage='service_migration', 
        dcmd='python3 /home/server.py ' + ip, 
        docker_args={
            'volumes': {f'{abs_path}/services/' : { 'bind': '/home', 'mode': 'ro' } } 
        }
    )


def migrate_service(name: str, old_ip: str, new_ip: str) -> APPContainer:
    old_hostname = get_hostname(old_ip)

    new_srv = spawn_service(name, new_ip)
    mgr.removeContainer( f'srv{name}_{old_hostname}' )
    
    running_services[name] = new_ip
    return new_srv


def spawn_client(name: str, host: str, target_srv: str) -> APPContainer:
    return mgr.addContainer(
        name=name,
        dhost=host,
        dimage='service_migration',
        dcmd='python3 /home/client.py ' + target_srv,
        docker_args={
            'volumes': {f'{abs_path}/services/' : { 'bind': '/home', 'mode': 'ro' } } 
        }
    )


def get_hostname(ip: str) -> str:
    """ Get mininet host name given its ip address
    
    @param ip: IP address of the host
    @return The host name related to the ip provided
    """
    split = ip.split('.')
    return f'p{split[1]}_s{split[2]}_h{split[3]}'


def main():

    # Dump services dict to make it globally available
    global services
    with open('./services/services.obj', 'wb') as file:
        pickle.dump(services, file)

    # Create topology and start network
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

    global mgr
    mgr = VNFManager(net)

    net.build()
    net.start()
    
    simulation_running = True

    spawn_client(name='c1', host='p1_s0_h2', target_srv='0')
    spawn_client(name='c2', host='p2_s0_h2', target_srv='1')

    while simulation_running:
        try:
            # Check if services were updated by scheduler
            for srv, ip in services.items():

                # Load services
                with open('./services/services.obj', 'rb') as file:
                    services = pickle.load(file)

                # Check for updates on services
                if srv not in running_services.keys():
                    # A new service was spawned
                    spawn_service(srv, ip)
                    print('Created service on host ' + ip)
                if running_services[srv] != ip:
                    # A service must be migrated
                    migrate_service(srv, running_services[srv], ip)
                    print('Migrated service to host ' + ip)

            time.sleep(2)
        except EOFError:
            print('Cannot access services.obj file')
        except KeyboardInterrupt:
            simulation_running = False

    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
    