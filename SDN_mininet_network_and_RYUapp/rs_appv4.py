from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, arp, ipv4
from ryu.lib.packet import ether_types
from ryu.lib.dpid import dpid_to_str, str_to_dpid
from ryu.lib import hub


class L2Switch(app_manager.RyuApp):  # creating a simple switch as a Ryu App
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    #============================HANDLING INCOMING PACKETS BASED ON THEIR TYPE===========================================#

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)  #L2switch is a child of Ryu App.
        self.mac_to_port = {} #{sid1:{port1:[(mac1,ip1),(),...],port2:[mac2,ip2]...},...},sid2:...} - to store the details of each switch and associated mac and IP of hosts connected on each port

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, event): #this method handles switch feature requests and we install initial flows to forward all the packets to the controller incase of a table miss
        print(" *** in feature handler *** ")
        self.sendto_controller(event) #send the packet to the controller

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER) #handling specific packet types like ARP an IP
    def _packet_in_handler(self, event): #event contains the event data.
        pkt = packet.Packet(data=event.msg.data) #creating a packet with message's data as payload
        eth = pkt.get_protocols(ethernet.ethernet)[0] #fetching ethernet dataframe
        if eth.ethertype == ether_types.ETH_TYPE_ARP: #handling ARP requests
            self.handle_ARP(event) #calling appropriate method to handle ARP packets
        elif eth.ethertype == ether_types.ETH_TYPE_IP: #handle IP packets
            self.handle_IP(event) #calling appropriate method to handle IP packet

    #====================================================================================================================#


    #=========================ADDING APPROPRIATE FLOW RULES BASED ON PACKET TYPE, SOURCE AND DESTINATION================================#

    #----------------------------------------------ARP Packet Handler--------------------------------------------#


    def handle_ARP(self, event):
        datapath = event.msg.datapath #extracting switch details from where the packet has been received
        ofproto = datapath.ofproto #extracting ofproto of the datapath - the openflow protocol version for the switch
        dpid = datapath.id #extracting the dpid which uniquely identifies a switch
        in_port = event.msg.match['in_port']  #port through which the respective switch recieved the packet
        parser = datapath.ofproto_parser #ofproto_parser module for encoding/decoding
        pkt = packet.Packet(data=event.msg.data) #extracting packet details
        eth = pkt.get_protocols(ethernet.ethernet)[0]  #fetching ethernet dataframe, 1st item (pkt and ethernet headers)
        arp_pkt = pkt.get_protocol(arp.arp)  #extract arp payload

        if (dpid in self.mac_to_port): #check if the switch's dpid exists in the mac_to_port dictionary
            if (in_port in self.mac_to_port[dpid]): #if switch's dpid exists check if respective port through which packet was recieved exists in mac_to_port dictionary
                if((arp_pkt.src_mac, arp_pkt.src_ip) in self.mac_to_port[dpid][in_port]): #if both switch and in port are present check if the mac and ip addresses are mapped against the respective port
                    pass #if the switch, in port as well as mac and ip address exist in mac_to_port, do not do anything
                else:
                    self.mac_to_port[dpid][in_port].append((arp_pkt.src_mac, arp_pkt.src_ip)) #if mac and ip address do not exist against specific switch's in port add the mac and ip against the 												      #respective switch's id against respective port number
            else:
                self.mac_to_port[dpid][in_port] = [(arp_pkt.src_mac, arp_pkt.src_ip)] #if the port does not exist against an existing switch add the port and appropriate mac and ip address

        else:
            self.mac_to_port[dpid] = {in_port: [(arp_pkt.src_mac, arp_pkt.src_ip)]} #if the switch does not exist add the switch, respective in port and corresponding mac an dip address

        out_port = self.check_mactable(ofproto, 'arp', dpid, arp_pkt.dst_mac)  #check the mac table to get the out port for destination mac address
        actions = [parser.OFPActionOutput(out_port)]  #as an action add flow rule to send the packet out on outport obtained from mac table
        match = self.simplematch(parser, eth.src, eth.dst, in_port)  #this is a match condition, the received arp is matched for the provided parameters
        self.add_flow_arp(datapath, 1, match, actions, buffer_id=None)  #add the flow entry, add datapath, match crieteria and no need to add buffer ID because we are not queing it


    #-------------------------------------------------------------------------------------------------------------------------#



    #---------------------------------------------------------------IP Packet Handler-------------------------------------------------------------------------#

    def handle_IP(self, event):  # handle IP packets
        datapath = event.msg.datapath
        ofproto = datapath.ofproto
        dpid = datapath.id
        in_port = event.msg.match['in_port']  #port through which the switch received this packet
        parser = datapath.ofproto_parser
        pkt = packet.Packet(data=event.msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]  #fetching ethernet dataframe, 1st item
        ip_pkt = pkt.get_protocol(ipv4.ipv4)  # extract IP payload

        backup = ['10.0.1.139', '10.0.1.140'] #IP addresses for backup servers
        research = ['10.0.1.' + str(i) for i in range(130, 134)] #IP addresses for research servers
        ipcamera = ['10.0.1.' + str(i) for i in range(100, 110)] #IP addresses for ip cameras
        ipsensors = ['10.0.1.' + str(i) for i in range(150,160)] #IP addresses for ip sensors
        host = '150.0.0.2' #IP addresses for remote host available on internet
        gate = '150.0.0.1' #IP addresses for gateway router

        students = ['10.0.1.' + str(i) for i in range(26, 66)] #IP addresses for student PCs
        researchers = ['10.0.1.' + str(i) for i in range(66, 77)] #IP addresses for researchers' PCs
        demo = '10.0.1.125' #IP address for demo PC (located in building 1 floor 2)
        so = ['10.0.1.119', '10.0.1.120'] #IP addresses for PCs in small office in building 2



        #execute only if destination IP address is anyone from remote host, backup or research server, ipcamera or ipsensor (checking addresses to establish appropriate rules for forward paths)
        if (ip_pkt.dst == host or ip_pkt.dst in backup or ip_pkt.dst in research or ip_pkt.dst in ipcamera or ip_pkt.dst in ipsensors):

            if (ip_pkt.dst in backup): #packet destined for backup server
                #check for source IP address and check if this address is allowed to access backup server 
                if (ip_pkt.src != host and ip_pkt.src not in research and ip_pkt.src not in students and ip_pkt.src != demo and ip_pkt.src not in ipsensors): #if source address is not among the mentioned 																				      #ones allow to forward 
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port for destination IP address
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if the source address is not allowed to access backup server clear actions and do not allow packet forwarding
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets

            if (ip_pkt.dst in research): #packet destined for research server
                #check for source IP address and check if it contains any address apart from allowed addresses 
                if (ip_pkt.src not in researchers and ip_pkt.src not in ipsensors): #if source adress is not among the mentioned addresses drop the packets
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets
                else: #if the source address is among the mentioned addresss, allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port for destination IP address
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port

            if (ip_pkt.dst in ipcamera): #packet destined for ip cameras
                #check for source IP address to check if it is allowed to access ip camera
                if (ip_pkt.src == demo or ip_pkt.src in so): #if source address is any of the mentioned addresses allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port for destination IP address
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if the source address is not among mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets

            if (ip_pkt.dst == host or ip_pkt.dst == gate): #packet destined for internet
                #check for source IP address and check if it is allowed to access internet; if address not in mentioned addresses allow to forward
                if (ip_pkt.src not in backup and ip_pkt.src not in research and ip_pkt.src != demo and ip_pkt.src not in ipcamera and ip_pkt.src not in so and ip_pkt.src not in ipsensors):
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port for destination IP address
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  # match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if the address is among the mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  # Drop the packets

            if(ip_pkt.dst in ipsensors): #packets destined for ipsensors
                #check the source IP address and check if it is allowed to access ip sensors
                if(ip_pkt.src in research or ip_pkt.src in so): #if the address is among the mentioned addresses allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port for destination IP address
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if the address is not among mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets


        #execute only if source IP address is anyone from remote host, backup or research server, ipcamera or ipsensor (checking addresses to establish appropriate rules for reverse paths)
        elif (ip_pkt.src == host or ip_pkt.src in backup or ip_pkt.src in research or ip_pkt.src in ipcamera or ip_pkt.src in ipsensors):

            if (ip_pkt.src in backup):  #reverse path from backup server
                #check destination addres and check if the backup server is supposed to reply to those addresses
                if (ip_pkt.dst != host and ip_pkt.dst not in research and ip_pkt.dst not in students and ip_pkt.dst != demo and ip_pkt.dst not in ipsensors): #if destination address is not among the 																				      #mentioned addresses allow to forward 
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port in IP packet.
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if destination address is among the mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets

            if (ip_pkt.src in research): #reverese path from research servers
                #check destination address and check if research server is supposed to reply to those addresses
                if (ip_pkt.dst not in researchers and ip_pkt.dst not in ipsensors): #if destination address is not among mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port) #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets
                else: #if the destination is among the mentioned addresses allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port in IP packet.
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port

            if (ip_pkt.src in ipcamera): #reverse path for ipcamera
                #check for destination address and if ip camera is supposed to reply to those addresses
                if (ip_pkt.dst == demo or ip_pkt.dst in so): #if destinaiton is among the mentioned addresses allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port in IP packet.
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if the destination is not among the mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets

            if (ip_pkt.src == host or ip_pkt.src == gate): #reverse path from ipcamera
                #check for destination address and check if these destinaitons are supposed to recieve reply from internet; if destinaiton is not among mentioned addresses allow to forward
                if (ip_pkt.dst not in backup and ip_pkt.dst not in research and ip_pkt.dst != demo and ip_pkt.dst not in ipcamera and ip_pkt.dst in so and ip_pkt.dst not in ipsensors):
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port in IP packet.
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  #allow to forward the pkt to appropriate out port
                else: #if destinaiton is among the mentioned addresses drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets


            if (ip_pkt.src in ipsensors): #reverse path from ipsensors
                #check for destinaiton address and check if they are supposed to get a reply form ip sensors
                if (ip_pkt.dst in research or ip_pkt.dst in so): #if destination address is among the menitioned addresses allow to forward
                    out_port = self.check_mactable(ofproto, 'ip', dpid, ip_pkt.dst)  #checking out port in IP packet.
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  # match the ethernet source address and in port
                    actions = [parser.OFPActionOutput(port=out_port)]  # specify to forward the pkt to out port no
                else: #if destination is not among mentioed address drop the packet
                    match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
                    actions = []  #no action to be performed
                    print('packet dropped')  #Drop the packets


        else: #covering any other case which is not a part of requirement and dropping the packet for maintaining security
            match = self.simplematch(parser, eth.src, eth.dst, in_port)  #match the ethernet source address and in port
            actions = []  #no action to be performed
            print('packet dropped')  #Drop the packets


        if event.msg.buffer_id != ofproto.OFP_NO_BUFFER: #if buffer id present
            if (actions == []): #send clear actions instruction, if action is null to drop the packet
                self.add_flow(datapath, 1, match, actions, ofproto.OFPIT_CLEAR_ACTIONS, event.msg.buffer_id) 

            else: #send apply actions instruction, if action is to forward 
                self.add_flow(datapath, 1, match, actions, ofproto.OFPIT_APPLY_ACTIONS, event.msg.buffer_id)

        else: #if buffer id absent
            if (actions == []): #send clear actions instruction, if action is null to drop the packet
                self.add_flow(datapath, 1, match, actions, ofproto.OFPIT_CLEAR_ACTIONS)

            else: #send apply actions instruction, if action is to forward 
                self.add_flow(datapath, 1, match, actions, ofproto.OFPIT_APPLY_ACTIONS)


    #-------------------------------------------------------------------------------------------------------------------------------------------------#


    #======================================================================================================================================================================#
 

    #===================================================Check MAC Table===================================================#
    
    def check_mactable(self, ofproto, caller, id, para):  #to check if an mac addr or IP addr exists in mac table for specific switch
        if caller == 'arp':  #if the calling function is arp, then check mac address
            for p in self.mac_to_port[id]: #for the switch id, check for the mac address in the mac ip tuple stored against each port
                for i in range(0,len(self.mac_to_port[id][p])): 
                    if self.mac_to_port[id][p][i][0] == para:
                        return p  #return p as outport port (returned if found)
        elif caller == 'ip':  # if calling function is ip , then check ip addr
            for p in self.mac_to_port[id]: #for the switch id, check for the ip address in the mac ip tuple stored against each port
                for i in range(0, len(self.mac_to_port[id][p])):
                    if self.mac_to_port[id][p][i][1] == para:
                        return p  #return p as outport port (returned if found)

        return ofproto.OFPP_FLOOD  # if no port is found, FLOOD the packet to all ports

    #=================================================================================================================#


    #=========================================Send To Controller======================================================#

    def sendto_controller(self, event):  #initial installation of table miss flow
        datapath = event.msg.datapath #indicates the switch from which packet is recieved 
        ofproto = datapath.ofproto  #tells which version of openflow protocol is being used and on that basis parser is decided.
        parser = datapath.ofproto_parser
        match = parser.OFPMatch() #creating match condition
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]  #install the table miss flow entry.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)  #sending message to the switch

    #==================================================================================================================#


    #============================================Add Flow==================================================================#

    def add_flow(self, datapath, priority, match, actions, res, buffer_id=None):  #add flow method for ip packets
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        idle_timeout = 45  # Idle time before discarding
        hard_timeout = 45  # Max time before discarding
        inst = [parser.OFPInstructionActions(res, actions)] #creating instruction for taking appropriate actions (drop packet or forward packet) for ip packet
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout, instructions=inst)
        self.logger.info("added flow for %s", mod)
        datapath.send_msg(mod)  #send message to the switch

    def add_flow_arp(self, datapath, priority, match, actions, buffer_id=None): #add flow method for arp packets
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        idle_timeout = 45  #Idle time before discarding
        hard_timeout = 45  #Max time before discarding

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)] #creating instruction for creating rule for enabling ARP
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout, instructions=inst)
        self.logger.info("added flow for %s", mod)
        datapath.send_msg(mod)  #send message to the switch

    #========================================================================================================================#




    #========================Request the packet to be forwarded onto a specific port from the switch==================================#

    def switchport_out(self, pkt, datapath, port):  #accept raw data , serialise it and packetout from a OF switch
        ofproto = datapath.ofproto  #ofproto of the datapath
        parser = datapath.ofproto_parser
        pkt.serialize()  #serialise packet (ie convert packet structs to raw data)
        self.logger.info("packet-out %s" % (pkt,))  #stores the info about pkt
        data = pkt.data  #taking all data out of packet
        actions = [parser.OFPActionOutput(port=port)]  #here this action is an out port action as we are sending the packet out
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions, data=data)
        datapath.send_msg(out)  #send message to the switch

    #=========================================================================================================================================


    #===========================================Simple match==================================================================

    def simplematch(self, parser, src, dst, in_port):
        match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)  # install a flow to avoid packet_in next time.
        return match
   
    #=========================================================================================================================

