from threading import Thread
from time import sleep
from switch import Switch
from params import FAT_TREE_K
import typing
import pprint


class FlowScheduler(Thread):

    def __init__(self, datapaths) -> None:
        super().__init__()
        self.datapaths = datapaths
        self.switches: typing.Dict[int, Switch] = {}


    def run(self):
        """ Execute as a separated thread """
        print('Flow Scheduler has started...')
        self.running = True 
        self._query_stats(5)

    
    def _query_stats(self, sleeptime=5):
        """ Continuously send port status requests to all the switches in the network 

        @param sleeptime: the time between the port stats requests 
        """
        while self.running:
            
            # Send a Port Status Request to every switch in the network
            for dpid, datapath in self.datapaths.items():
                
                ofp = datapath.ofproto
                ofp_parser = datapath.ofproto_parser
                req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
                datapath.send_msg(req)
                
            sleep(sleeptime)   # Sleep 10 seconds


    def save_port_stats(self, dpid, stats):
        """ Gets called by the Ryu controller. Save the retrieved port stats of a single switch

        @param dpid: The datapath id of the switch which sent the stats
        @param stats: The openflow port stats object that contains port statistics
        """
        if not dpid in self.switches.keys():
            self.switches[dpid] = Switch(dpid)

        for stat in stats:
            if stat.port_no < FAT_TREE_K:
                self.switches[dpid].port_stats[stat.port_no].update_stats(stat.tx_bytes, stat.rx_bytes)


    def print_switches_info(self):
        """ Print the saved port statistics """
        for switch in self.switches.values():
            print(f'{switch.dpid} ->')
            for i in range(1, FAT_TREE_K + 1):
                print(f'\t port {i} -- TX: {switch.port_stats[i].dtx_bytes}, RX: {switch.port_stats[i].drx_bytes}')

        