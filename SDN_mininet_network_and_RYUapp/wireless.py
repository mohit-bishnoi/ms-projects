#!/usr/bin/python

from mininet.node import Controller, Host, OVSKernelSwitch
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from subprocess import call


def myNetwork():

    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.1.0/24')

    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=Controller,
                           protocol='tcp',
                           port=6633)

    info( '*** Add switches/APs\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')#s1 is the switch to which our backup server is conencted to in building 1 server room

    #s2 is the switch connected to gateway in building 1 server room providing internet conenctivity
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
    #this is the switch to which AP1 is connected. AP1 is further connected to other APs hence providing connectivity to internet

    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid', channel='1', mode='g', position='270.0,0,0')#access point at ground floor, building 1
    ap2 = net.addAccessPoint('ap2', cls=OVSKernelAP, ssid='ap2-ssid', channel='1', mode='g', position='270.0,100,0')#access point at first floor, building 1
    ap3 = net.addAccessPoint('ap3', cls=OVSKernelAP, ssid='ap3-ssid', channel='1', mode='g', position='270.0,200.0,0')#access point at second floor, building 1
    ap4 = net.addAccessPoint('ap4', cls=OVSKernelAP, ssid='ap4-ssid', channel='1', mode='g', position='1300.0,0,0')#access point at building 2


    info( '*** Add hosts/stations\n')
    
    sta1 = net.addStation('sta1', ip='10.0.1.165', position='223.0,0,0', defaultRoute='via 10.0.1.1')#wireless station at ground floor, building 1
    sta2 = net.addStation('sta2', ip='10.0.1.166', position='312.0,100,0', defaultRoute='10.0.1.1')#wireless station at first floor, building 1
    sta3 = net.addStation('sta3', ip='10.0.1.167', position='191,200,0', defaultRoute='10.0.1.1')#wireless station at second floor, building 1
    sta4 = net.addStation('sta4', ip='10.0.1.168', position='1236.0,0,0', defaultRoute='10.0.1.1')#wireless station at building 2


    g = net.addHost('g', cls=Host)#gateway router in building 1 store room, connected to s2
    
    bs1 = net.addHost('bs1', cls=Host, ip='10.0.1.139', defaultRoute='via 10.0.1.1')#backup server 1 connected to s1 in building 1 server room
    bs2 = net.addHost('bs2', cls=Host, ip='10.0.1.140', defaultRoute='via 10.0.1.1')#backup server 2 connected to s1 in building 1 server room


    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()


    info( '*** Add links\n')

    net.addLink(ap1, s2, 3, 20)#connecting AP1 to s2
    net.addLink(ap1, ap2, 2, 3)#connecting AP1 to AP2
    net.addLink(ap1, sta1, 1, 1)#connecting AP1 to sta1

    net.addLink(ap2, ap3, 2, 3)#connecting AP2 to AP3
    net.addLink(ap2, sta2, 1, 1)#Connecting AP2 to sta2
    
    net.addLink(ap3, ap4, 2, 3)#Connecting AP3 to AP4
    net.addLink(ap3, sta3, 1, 1)#connecting AP3 to sta3

    net.addLink(ap4, sta4, 1, 1)#conencting AP4 to sta4
    

    
    net.addLink(g, s2, 2, 1)#conneciton between gateway and s2 in building 1 server room
    net.addLink(s1, s2, 1, 2)#conneciton between s1 and s2 in building 1 server room
    net.addLink(s1, bs1, 6, 1)#conneciton between s1 and backup server 1 in building 1 server room
    net.addLink(s1, bs2, 7, 1)#conneciton between s1 and backup server 2 in building 1 server room

    #net.plotGraph(max_x=1000, max_y=1000)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')
    net.get('ap3').start([c0])
    net.get('ap4').start([c0])
    net.get('ap1').start([c0])
    net.get('ap2').start([c0])
    net.get('s1').start([])
    net.get('s2').start([])


 

    info( '*** Post configure nodes\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

