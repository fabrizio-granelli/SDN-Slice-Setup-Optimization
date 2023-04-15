from threading import Thread
from time import sleep
from switch import Switch
from params import FAT_TREE_K
from ryu.ofproto.ofproto_v1_5_parser import OFPPortStats
import typing


class Flow():

    def __init__(self, switch_id: int, in_pod: int, out_pod: int, ttl: int = 3):
        self.switch = Switch(switch_id)
        self.in_pod = in_pod
        self.out_pod = out_pod
        self.ttl = ttl  # Counter to be decremented at every scheduler loop cycle
    

    def update_ttl(self):
        """ Decrease flow Time To Live counter """
        self.ttl -= 1


class FlowScheduler(Thread):

    def __init__(self, datapaths) -> None:
        super().__init__()
        self.datapaths = datapaths
        self.switches: typing.Dict[int, Switch] = {}
        self.flows: typing.List[Flow] = []


    def run(self):
        """ Execute as a separated thread """
        print('Flow Scheduler has started...')
        self.running = True 
        self.__main_loop(5)

    
    def __main_loop(self, sleeptime: int = 5) -> None:
        """ Main scheduler execution loop, runs as a thread. 

        @param sleeptime: the time between the port stats requests 
        """
        while self.running:

            self.__update_detected_flows()
            self.__detect_flows()
            self.__send_port_status_req()

            self.print_switches_info()
            self.print_flows_info()

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
            discovered_out_ports = []
            for in_port in range(1, FAT_TREE_K + 1):
                if switch.port_stats[in_port].drx_bytes > 1000:
                    for out_port in range(1, FAT_TREE_K + 1):
                        if switch.port_stats[out_port].dtx_bytes > 1000 and not out_port in discovered_out_ports and in_port != out_port:
                            discovered_out_ports.append(out_port)
                            self.flows.append(Flow(switch.dpid, in_port, out_port, 2))
                            break


    def __send_port_status_req(self) -> None:
        """ Send a Port Status Request to every switch in the network """
        for dpid, datapath in self.datapaths.items():
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
            print(f'{switch.dpid} ->')
            for i in range(1, FAT_TREE_K + 1):
                print(f'\t port {i} -- TX: {switch.port_stats[i].dtx_bytes}, RX: {switch.port_stats[i].drx_bytes}')

        