from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from mininet.topo import Topo


class Design(Topo):
    def __init__(self):
        Topo.__init__(self)
        self.all_server = []  # list to store all the backup server names
        self.all_research = []  # list to store all the research server names
        self.all_reception = []  # list to store all the reception PC names
        self.all_grndoffice = []  # list to store all the PC names in the ground floor offices
        self.all_ff_switches = []  # list to store names of all the first floor switches
        self.all_lab = []  # list to store all the first floor software lab PC names 
        self.all_students = []  # list to store names of lal the student PCs
        self.all_lectern = []  # list to store the names of the lectern PCs
        self.all_sf_switches = []  # list to store names of all the second floor switches
        self.all_resPC = []  # list to store names of all the research PCs
        self.all_offPC = []  # list to store the names of all PCs in all the offices at second floor
        self.all_ipcam = []  # list to store nams of all the ip cameras in building 2
        self.all_ips = []  # list to store the names of all ip sensors in building 2
        self.create()

    def create(self):
        info("*** Creating nodes\n")

        '''==================================================BUIDLING 1 NETWORK======================================================='''

        # -----------------------------------------------Ground Floor---------------------------------------------------#
        g = self.addHost('g')  # gateway router located at bulding 1 server room
        rh = self.addHost('rh', ip='150.0.0.2', defaultRoute='via 150.0.0.1')  # Remote host at internet
        s1 = self.addSwitch('s1')  # Switch connecting the research and backup servers to s2 
        s2 = self.addSwitch(
            's2')  # aggregator swich for first and second floor switches also connects ground floor devices

        for i in range(1, 5):
            research = self.addHost('rs%d' % i, ip='10.0.1.' + str(i + 129),
                                    defaultRoute='via 10.0.1.1')  # Adding four research servers
            self.all_research.append(research)

        for i in range(1, 3):
            backup = self.addHost('bs%d' % i, ip='10.0.1.' + str(i + 138),
                                  defaultRoute='via 10.0.1.1')  # Adding two backup servers
            self.all_server.append(backup)

        for i in range(1, 3):
            reception = self.addHost('rc%d' % i, ip='10.0.1.' + str(i + 1),
                                     defaultRoute='via 10.0.1.1')  # Adding 2 reception PCs
            self.all_reception.append(reception)

        for i in range(1, 6):
            grndoffice = self.addHost('go%d' % i, ip='10.0.1.' + str(i + 3),
                                      defaultRoute='via 10.0.1.1')  # Adding PCs for 5 offices
            self.all_grndoffice.append(grndoffice)

        # ------------------------------------------Ground floor done-----------------------------------------------------------#

        # -----------------------------------------------First Floor-----------------------------------------------------------#

        for i in range(3, 7):
            sff = self.addSwitch(
                's%d' % i)  # Adding four switches at first floor (1 floor swich aggregating LAN switches on the floor and 3 LAN switches for devices)
            self.all_ff_switches.append(
                sff)  # index 0 of all_ff_switches stores the aggregator switch whereas as indexes 1-3 store LAN switches

        for i in range(10, 25):
            lab = self.addHost('lp%d' % (i - 9), ip='10.0.1.' + str(i),
                               defaultRoute='via 10.0.1.1')  # Adding 15 lab PCs
            self.all_lab.append(lab)

        for i in range(26, 66):
            stu = self.addHost('sp%d' % (i - 25), ip='10.0.1.' + str(i),
                               defaultRoute='via 10.0.1.1')  # Adding 40 student PCs
            self.all_students.append(stu)

        for i in range(82, 84):
            lectern = self.addHost('lc%d' % (i - 81), ip='10.0.1.' + str(i),
                                   defaultRoute='via 10.0.1.1')  # Adding 2 lectern PCs
            self.all_lectern.append(lectern)

        # --------------------------------------------------First Floor done-----------------------------------------------------#

        # ----------------------------------------------------Second Floor--------------------------------------------------------#

        for i in range(7, 10):
            ssf = self.addSwitch(
                's%d' % i)  # Adding 3 switches at second floor (1 floor swich aggregating LAN switches on the floor and 2 LAN switches for devices)
            self.all_sf_switches.append(
                ssf)  # index 0 of all_sf_switches stores the aggregator switch whereas as indexes 1-2 store LAN switches

        for i in range(66, 77):
            resPC = self.addHost('rpc%d' % (i - 65), ip='10.0.1.' + str(i),
                                 defaultRoute='via 10.0.1.1')  # Adding 11 research PCs on same switch including 1 PC which is also an office PC
            self.all_resPC.append(resPC)

        for i in range(77, 82):
            offPC = self.addHost('opc%d' % (i - 76), ip='10.0.1.' + str(i),
                                 defaultRoute='via 10.0.1.1')  # Adding 5 PCs for 5 offices
            self.all_offPC.append(offPC)

        demoPC = self.addHost('dpc', ip='10.0.1.125')  # Demo room PC

        # ---------------------------------------------------Second Floor done------------------------------------------------------------------#

        '''==========================================================BUIDLING 1 NETWORK DONE======================================================='''

        '''=============================================================BUIDLING 2 NETWORK======================================================='''

        so1 = self.addHost('so1', ip='10.0.1.119')  # PC1 in small office
        so2 = self.addHost('so2', ip='10.0.1.120')  # PC2 in small office

        for i in range(100, 110):
            ipcam = self.addHost('ic%d' % (i - 99), ip='10.0.1.' + str(i))  # Adding 10 IP cameras as 10 hosts
            self.all_ipcam.append(ipcam)

        s10 = self.addSwitch('s10')  # Switch connecting 10 ip cameras, 2 PCs and 10 wired IP sensors

        for i in range(150, 160):
            ips = self.addHost('ips%d' % (i - 149), ip='10.0.1.' + str(i))  # Adding 10 IP sensors as 10 hosts
            self.all_ips.append(ips)

        '''===========================================================BUIDLING 2 NETWORK DONE======================================================='''

        '''===================================================================ADDING LINKS=========================================================='''

    # ---------------------------------------------------Connecting server room ground floor building 1------------------------------------------------------------------#

        self.addLink(g, rh, 1, 1)  # connecting the gateway to remote host on internet
        self.addLink(g, s2, 2, 1)  # connecting the gateway with switch s2
        self.addLink(s1, s2, 1, 2)  # connecting the switches s1 and s2
        self.addLink(s10, s2, 1, 3)  # connecting switches s10 and s2

    # ---------------------------------------------------Server Room connection completed------------------------------------------------------------------#

    # ---------------------------------------------------Connecting ground floor building 1------------------------------------------------------------------#

        for i in range(2, 6):
            self.addLink(s1, self.all_research[i - 2], i, 1)  # connecting research servers to s1

        for i in range(6, 8):
            self.addLink(s1, self.all_server[i - 6], i, 1)  # connecting backup servers to s1

        for i in range(4, 6):
            self.addLink(s2, self.all_reception[i - 4], i, 1)  # connecting reception PCs to s2

        for i in range(6, 11):
            self.addLink(s2, self.all_grndoffice[i - 6], i, 1)  # connecting the PCs in ground offices to s2

    # ---------------------------------------------------Ground floor connection completed------------------------------------------------------------------#

    # ---------------------------------------------------Connecting first floor building 1------------------------------------------------------------------#

        self.addLink(s2, self.all_ff_switches[0], 11, 1)  # connecting the first floor main switch to s2

        for i in range(1, 4):
            self.addLink(self.all_ff_switches[0], self.all_ff_switches[i], i + 1, 1)  # connecting all the first floor LAN switches to main floor switch

        for i in range(2, 17):
            self.addLink(self.all_ff_switches[1], self.all_lab[i - 2], i, 1)  # connecting the PCs in the lab to s4

        self.addLink(self.all_ff_switches[1], self.all_lectern[0], 17, 1)  # Connecting first lectern PC to s4
        self.addLink(self.all_ff_switches[1], self.all_lectern[1], 18, 1)  # Connecting second lectern PC to s4

        for i in range(2, 4):
            for j in range(1, 21):
                if (i == 2):
                    self.addLink(self.all_ff_switches[i], self.all_students[j - 1], j + 1, 1)  # Connecting 20 student PCs to s5
                elif (i == 3):
                    self.addLink(self.all_ff_switches[i], self.all_students[j + 20 - 1], j + 1, 1)  # Connecting 20 student PCs to s6

    # ---------------------------------------------------First floor connection completed------------------------------------------------------------------#

    # ---------------------------------------------------Connecting second floor building 1------------------------------------------------------------------#

        self.addLink(s2, self.all_sf_switches[0], 12, 1)  # connecting the second floor main switch to s2

        for i in range(1, 3):
            self.addLink(self.all_sf_switches[0], self.all_sf_switches[i], i + 1, 1)  # connecting all the first floor LAN switches to main floor switch

        for i in range(1, 12):
            self.addLink(self.all_sf_switches[1], self.all_resPC[i - 1], i + 1, 1)  # connecting research PCs to s8

        for i in range(1, 6):
            self.addLink(self.all_sf_switches[2], self.all_offPC[i - 1], i + 1, 1)  # connecting second floor office PCs  to s9

        self.addLink(self.all_sf_switches[0], demoPC, 4, 1)  # connecting demoPC to s7 (main floor switch)

    # ---------------------------------------------------Second floor connection completed------------------------------------------------------------------#

    # ---------------------------------------------------Connecting building 2------------------------------------------------------------------#

        for i in range(1, 11):
            self.addLink(s10, self.all_ipcam[i - 1], i + 1, 1)  # connecting all ip cameras to s10

        self.addLink(s10, so1, 12, 1)  # connecting small office PC1 to s10
        self.addLink(s10, so2, 13, 1)  # connecting small office PC2 to s10

        for i in range(14, 24):
            self.addLink(s10, self.all_ips[i - 14], i, 1)  # connecting all io sensors to s10

    # ---------------------------------------------------Building 2 conneciton completed------------------------------------------------------------------#

    '''===========================================================DONE ADDING LINKS======================================================='''


topos = {'network': (lambda: Design())}  # Dictionary to trigger topology creation





