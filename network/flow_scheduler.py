from threading import Thread
from time import sleep
from switch import Switch
from globals import FAT_TREE_K
from ryu.ofproto.ofproto_v1_5_parser import OFPPortStats
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

    def __init__(self, switch, dst_pod):
        self.switch = switch
        self.dst_pod = dst_pod


class FlowScheduler(Thread):

    def __init__(self, datapaths) -> None:
        super().__init__()
        self.datapaths = datapaths
        self.switches: typing.Dict[int, Switch] = {}
        self.flows: typing.List[Flow] = []


    def run(self):
        """ Execute as a separate thread """
        self.running = True 
        self.__main_loop(30)

    
    def __main_loop(self, sleeptime: int = 5) -> None:
        """ Main scheduler execution loop, runs as a thread. 

        @param sleeptime: the time between the port stats requests 
        """
        while self.running:

            self.__update_detected_flows()
            self.__detect_flows()
            self.__schedule_paths(sleeptime)
            self.__send_port_status_req()

            self.print_flows_info()
            self.print_switches_info()

            sleep(sleeptime)   


    def __update_detected_flows(self) -> None:
        """ Update flows TTL and remove expired flows """
        for flow in self.flows:
            flow.update_ttl()
        self.flows = [ flow for flow in self.flows if flow.ttl > 0 ]


    def __detect_flows(self) -> None:
        """ Search for flows on core switches """
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
                    self.flows.append(Flow(switch.dpid64, in_port-1, out_port-1, 1))
                    tx = tx - rx


    def __schedule_paths(self, timeout: int):
        # Reset downlinks stats on switch objects
        for sw in self.switches.values():
            sw.reset_downlink_flows()

        # Update downlink flows counters 
        for flow in self.flows:
            self.switches[flow.switch.dpid64].port_stats[flow.out_pod+1].downlink_flows += 1

        # Find downlinks with more than one active flows
        congested_downlinks: typing.List[DownLink] = []
        for sw in self.switches.values():
            for port in range(1, FAT_TREE_K + 1):
                if sw.port_stats[port].downlink_flows > 1:
                    congested_downlinks.append(DownLink(Switch(sw.dpid64), port - 1))
                    print(f'Discovered congested downlink on {sw.name} to pod {port - 1}')

        # Load services
        services = {}
        with open('services.obj', 'rb') as file:
            services = pickle.load(file)

        # Search for services related to discovered congestion
        for downlink in congested_downlinks:
            for srv, ip in services.items():
                srv_pod = int(ip.split('.')[1])
                if srv_pod == downlink.dst_pod:
                    # Find pod with an available downlink and server
                    for pod in range(0, FAT_TREE_K):
                        
                        available_core_sw = { sw.dpid64: True for sw in self.switches.values() if sw.is_core }
                        for dl in congested_downlinks:
                            if pod == dl.dst_pod:
                                available_core_sw[dl.switch.dpid64] = False
                        
                        if not True in available_core_sw.values():
                            continue

                        host_available = ''
                        for s in range(0, int(FAT_TREE_K / 2)):
                            for h in range(2, int(FAT_TREE_K / 2) + 2):
                                host = f'10.{pod}.{s}.{h}'
                                if host not in services.values():
                                    host_available = host
                                    break
                            if host_available != '':
                                break

                        if host_available == '':
                            continue
                        
                        # Update services
                        services[srv] = host_available
                        with open('services.obj', 'wb') as file:
                            pickle.dump(services, file)

                        core_switch = None
                        for sw, is_available in available_core_sw.items():
                            if is_available:
                                core_switch = sw
                                break

                        self.__create_path(host_available, Switch(core_switch))
                        return  # Other congested downlinks could be still there,
                                # in case the services will be migrated on the next scheduler cycle 


    def __create_path(self, dst: str, via_switch: Switch):
        print(f'Create path to {dst} via {via_switch.name}')
        pass
                            

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


    def print_flows_info(self):
        """ Print the currently detected flows and their information """
        for flow in self.flows:
            print(f"Flow on switch {flow.switch.name} from pod {flow.in_pod} to pod {flow.out_pod}")


    def print_switches_info(self):
        """ Print the saved port statistics """
        for switch in self.switches.values():
            if switch.is_core:
                print(f'{switch.dpid} ->')
                for i in range(1, FAT_TREE_K + 1):
                    print(f'\t port {i} -- TX: {switch.port_stats[i].dtx_bytes}, RX: {switch.port_stats[i].drx_bytes}')

        