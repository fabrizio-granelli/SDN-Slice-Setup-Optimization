from threading import Thread
from time import sleep, time
from switch import Switch
from globals import FAT_TREE_K, slices
from ryu.ofproto.ofproto_v1_5_parser import OFPPortStats
from ryu.controller.controller import Datapath
import typing
import pickle


class Flow():

    def __init__(self, switch_id: int, in_pod: int, out_pod: int, ttl: int = 3):
        self.switch = Switch(switch_id)
        self.in_pod = in_pod
        self.out_pod = out_pod
        self.ttl = ttl  # Counter to be decremented at every scheduler loop cycle
    

    def update_ttl(self):
        """ Decrease flow Time To Live counter """
        self.ttl -= 1


class DownLink():

    def __init__(self, switch: Switch, dst_pod: int):
        self.switch: Switch = switch
        self.dst_pod: int = dst_pod


class FlowScheduler(Thread):

    def __init__(self, datapaths: typing.Dict[int, Datapath], add_flow_callback: typing.Callable) -> None:
        super().__init__()
        self.datapaths: typing.Dict[int, Datapath] = datapaths
        self.add_flow_callback: typing.Callable = add_flow_callback
        self.switches: typing.Dict[int, Switch] = {}
        self.flows: typing.List[Flow] = []
        self.congestions: typing.List[DownLink] = []


    def run(self):
        """ Execute as a separate thread """
        self.running = True 
        self.__main_loop(10)

    
    def __main_loop(self, sleeptime: int = 5) -> None:
        """ Main scheduler execution loop, runs as a thread. 

        @param sleeptime: the time between the port stats requests 
        """
        cont = 1
        while self.running:

            self.__detect_flows()
            self.__detect_congestions()

            if (cont % 4 == 0):
                self.__optimize_network()

            cont += 1
            self.print_switches_info()
            self.__send_port_status_req()
            sleep(sleeptime)   


    def __detect_flows(self) -> None:
        """ Update flows TTL and search for new flows on core switches """ 
        for flow in self.flows:
            flow.update_ttl()
        self.flows = [ flow for flow in self.flows if flow.ttl > 0 ]

        for switch in self.switches.values():
            if not switch.is_core:
                continue    # Not interested in flows on pod switches

            for out_port in range(1, FAT_TREE_K + 1):
                tx = switch.port_stats[out_port].dtx_bytes
                if tx < 1000:
                    continue    # Not enough data transmitted from this port
                for in_port in range(1, FAT_TREE_K + 1):
                    rx = switch.port_stats[in_port].drx_bytes
                    if in_port == out_port or rx < 1000 or tx < 1000:
                        continue
                    # Discovered flow
                    flow = Flow(switch.dpid64, in_port-1, out_port-1, 1)
                    self.flows.append(flow)
                    print(f"Flow on switch {flow.switch.name} from pod {flow.in_pod} to pod {flow.out_pod}")
                    tx = tx - rx


    def __detect_congestions(self) -> None:
        """ Discover downlinks with more than one running flows """
        # Reset downlinks stats on switch objects
        for sw in self.switches.values():
            sw.reset_downlink_flows()

        # Update downlink flows counters 
        for flow in self.flows:
            self.switches[flow.switch.dpid64].port_stats[flow.out_pod+1].downlink_flows += 1

        # Find downlinks with more than one active flows
        self.congestions = []
        for sw in self.switches.values():
            for port in range(1, FAT_TREE_K + 1):
                if sw.port_stats[port].downlink_flows > 1:
                    self.congestions.append(DownLink(Switch(sw.dpid64), port - 1))
                    print(f'Discovered congested downlink on {sw.name} to pod {port - 1}')

    
    def __optimize_network(self) -> None:
        """ Find new solutions for running services to eliminate congestions """
        # Load services
        services = {}
        with open('./services/services.obj', 'rb') as file:
            services = pickle.load(file)

        # Search for services related to discovered congestion
        for downlink in self.congestions:
            for srv, srv_ip in services.items():
                srv_pod = int(srv_ip.split('.')[1])
                if srv_pod == downlink.dst_pod:

                    if not self.__optimize_paths(srv_ip):
                        self.__optimize_services(srv, services)
                    break  


    def __optimize_paths(self, service_ip: str) -> bool:
        """ Schedule a new non-congested path to the service 
        
        @param service_ip: The destination service IP
        @return True if an available path was found and applied, False otherwise 
        """
        pod = int(service_ip.split('.')[1])
        available_core_sw = self.__search_available_core_sw(pod)
        if available_core_sw != None:
            self.__create_path(service_ip, available_core_sw) 
            return True
        return False


    def __optimize_services(self, service_id: str, services: dict) -> bool:
        """ Migrate service to a pod with an available downlink and server 
        
        @param service_id: The ID of the service to migrate
        @param services: The dictionary with the running services
        @return True if the service is successfully migrated and paths are updated, False otherwise
        """
        for pod in range(0, FAT_TREE_K):
            
            core_switch = self.__search_available_core_sw(pod)
            if core_switch == None:
                continue

            available_host = self.__search_available_host(pod, services)
            if available_host == None:
                continue
            
            # Update services
            print(f'Moved service {service_id} to host {available_host}')
            old_ip = services[service_id] 
            services[service_id] = available_host
            with open('./services/services.obj', 'wb') as file:
                pickle.dump(services, file)

            self.__update_slice(old_ip, available_host)
            self.__create_path(available_host, core_switch)
            return True 

        return False


    def __search_available_core_sw(self, pod: int) -> typing.Optional[Switch]:
        """ Return a core switch whose downlink to the specified pod is not congested 
        
        @param pod: Identifies the connection that must be available from the switch
        @param congested_downlinks: The list of currently congested downlinks
        @return Available core switch || None
        """
        available_core_sw = { sw.dpid64: True for sw in self.switches.values() if sw.is_core }
        for dl in self.congestions:
            if pod == dl.dst_pod:
                available_core_sw[dl.switch.dpid64] = False
        for dpid, is_available in available_core_sw.items():
            if is_available:
                sw = Switch(dpid)
                print(f'Found available core switch: {sw.name}')
                return sw


    def __search_available_host(self, pod: int, services: dict) -> typing.Optional[str]:
        """ Return host IP on requested pod with no running services 
        
        @param pod: Pod where to search for available host
        @param services: Dict of currently running services
        @return available host IP || None 
        """
        for s in range(0, int(FAT_TREE_K / 2)):
            for h in range(2, int(FAT_TREE_K / 2) + 2):
                host = f'10.{pod}.{s}.{h}'
                if host not in services.values():
                    print(f'Found available host: {host}')
                    return host


    def __update_slice(self, old_srv: str, new_srv: str) -> None:
        """ Update slices list to place new service in the same slice of old service

        @param old_srv: The old service to get its slice
        @param new_srv: The new service to add to the slice
        """
        # Check if new srv is already in the right slice
        new_slice, old_slice = -1, -1
        for slice_id, srvs in slices.items():
            if old_srv in srvs:
                if new_srv in srvs:
                    print('Slices are already correctly setup')
                    return
                new_slice = slice_id
            if new_srv in srvs:
                old_slice = slice_id

        # Add new srv to the slice 
        slices[new_slice].append(new_srv)
        print(f'Added host {new_srv} to slice {new_slice}')

        # Remove new srv from old slice
        if old_slice != -1:
            slices[old_slice].remove(new_srv)
        

    def __create_path(self, dst_ip: str, via_switch: Switch) -> None:
        """ Update FlowTables on edge and aggregation switches to create a path to dst through via_switch
        
        @param dst_ip: Destination host IP address 
        @param via_switch: Core switch to be used in the path
        """
        print(f'Create path to {dst_ip} via {via_switch.name}')
        
        for dpid, datapath in self.datapaths.items():
            sw = Switch(dpid)
            if sw.is_core or sw.pod == int(dst_ip.split('.')[1]): 
                continue    # Do not update core switches and switches in the same pod of the dst host
            
            port = -1
            if sw.is_edge:      # Edge
                port = int(FAT_TREE_K / 2) + via_switch.j
            if not sw.is_edge:  # Aggregate
                port = int(FAT_TREE_K / 2) + via_switch.i

            self.add_flow_callback(
                datapath=datapath, 
                ip=dst_ip, 
                mask=0xFFFFFFFF, 
                port=port, 
                timeout=30,
                priority=int(time()) & 0xFFFF
            )
                            

    def __send_port_status_req(self) -> None:
        """ Send a Port Status Request to core switches in the network """
        for dpid, datapath in self.datapaths.items():
            if Switch(dpid).is_core:
                ofp = datapath.ofproto
                ofp_parser = datapath.ofproto_parser
                req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
                datapath.send_msg(req)


    def save_port_stats(self, dpid: int, stats: typing.List[OFPPortStats]) -> None:
        """ Gets called by the Ryu controller. Save the retrieved port stats of a single switch

        @param dpid: The datapath id of the switch which sent the stats
        @param stats: List of openflow port stats objects that contain port statistics
        """
        if not dpid in self.switches.keys():
            self.switches[dpid] = Switch(dpid)

        for stat in stats:
            if stat.port_no < FAT_TREE_K + 1:
                self.switches[dpid].port_stats[stat.port_no].update_stats(stat.tx_bytes, stat.rx_bytes)


    def print_switches_info(self):
        """ Print the saved port statistics """
        if len(self.switches.values()) == 0:
            return
        print('\n=============== Core Switch Port Statistics ===============')
        for switch in self.switches.values():
            if switch.is_core:
                print(f'{switch.name} :')
                for i in range(1, FAT_TREE_K + 1):
                    print(f'\t Port {i}: [ TX: {switch.port_stats[i].dtx_bytes} \tRX: {switch.port_stats[i].drx_bytes} ]')
        print('=============== =========================== ===============\n')
