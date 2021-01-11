#!/usr/bin/python3

import re
import socket
from os.path import isfile
from os import environ
from os import linesep
import subprocess

class Netinterface:
    _hostname=""
    def __init__(self, interface, address):
        self._interface=interface
        self._address=address
        #
        self._if_name=""
        self._if_ip=""
        self._rootdir="/"
        self._debug=0

    def __str__(self):
        return f"interface {self._interface} with name {self._address}"

    def config(self, action="-verify"):
        pass

    def _set_vars(self):
        #local: hostname_out
        if "LOCCONF_ROOTDIR" in environ:
            self._rootdir=environ['LOCCONF_ROOTDIR']
        else:
            self._rootdir="/"
        if "LOCCONF_DEBUG" in environ:
            self._debug=int(environ['LOCCONF_DEBUG'])
        else:
            self._debug=0
        if re.match("bond", self._address) or re.match("bridge", self._address) or re.match("none", self._address) :
            return
        if self._address=="" or self._address=="-bup" :
            if "LOCCONF_HOST" in environ:
                self._if_name=environ['LOCCONF_HOST']
            else:
                hostname_out=subprocess.run(['hostname'], stdout=subprocess.PIPE, universal_newlines=True)
                if hostname_out :
                    self._if_name=hostname_out.stdout
                else:
                    self._if_name=""
                #todo: if hostname has domain split .  
            self._if_name=self._if_name.rstrip()
            if self._address=="-bup" :
                self._if_name=self._if_name + "-bup"
            else:
                Netinterface._hostname=self._if_name
        else:
            self._if_name=self._address
        if self._debug == 2 :
            print("if_name:",self._if_name)

    def _config_hosts(self):
        #local: hosts_file, hosts_list, linija, dodati, hosts_changed, i, tmp
        if re.match("bond", self._address) or re.match("bridge", self._address) or re.match("none", self._address) :
            return
        hosts_list=[]
        if isfile(f"{self._rootdir}/etc/hosts"):
            try:
                hosts_file=open(f"{self._rootdir}/etc/hosts","r") 
            except:
                print(f"Could not open {self._rootdir}/etc/hosts for reading!")
                exit(1)
            while 1:
                linija=hosts_file.readline()
                if not linija:
                    break
                linija=linija.rstrip()
                hosts_list.append(linija)
            hosts_file.close()
        dodati=1
        hosts_changed=0
        if self._debug == 2 :
            print("hosts:", hosts_list)
        for i in hosts_list :
            if re.match("#",i):
                continue
            if re.match(f"( |\t)*{self._if_ip}( |\t)",i) or re.search(f"( |\t){self._if_name}( |\t|$)",i) :
                if self._if_name == Netinterface._hostname :
                    tmp=f"{self._if_ip}( |\t)+{self._if_name}( |\t)+loghost( |\t)*$"
                else:
                    tmp=f"{self._if_ip}( |\t)+{self._if_name}( |\t)*$"
                if re.match(tmp,i) :
                    dodati=0
                else:
                    if self._action == "-verify":
                        print(f"Need to remove {i} from etc/hosts")
                    else:
                        hosts_list.remove(i)
                        hosts_changed=1
                        print(f"Removed {i} from etc/hosts")
        if dodati :
            if self._action == "-verify" :
                if self._if_name == Netinterface._hostname :
                    print(f"Need to add {self._if_ip} {self._if_name} loghost to etc/hosts")
                    #todo: what with cnames ?
                else:
                    print(f"Need to add {self._if_ip} {self._if_name} to etc/hosts")
            else:
                if self._if_name == Netinterface._hostname :
                    hosts_list.append(f"{self._if_ip} {self._if_name} loghost")
                    print(f"Added {self._if_ip} {self._if_name} loghost to etc/hosts")
                else:
                    hosts_list.append(f"{self._if_ip} {self._if_name}")
                    print(f"Added {self._if_ip} {self._if_name} to etc/hosts")
                hosts_changed=1
        if self._action == "-verify" or not hosts_changed :
            return
        try:
            hosts_file=open(f"{self._rootdir}/etc/hosts","w") 
        except:
            print(f"Could not open {self._rootdir}/etc/hosts for write!")
            exit(1)
        for i in hosts_list :
            hosts_file.write(i+linesep)
        hosts_file.close()
        if self._debug == 2 :
            print("hosts:", hosts_list)

class NetinterfaceRH(Netinterface):
        __bonding_flag=[]
        def __init__(self, interface, address=""):
            Netinterface.__init__(self, interface, address)
            #
            self.__netinterface_list=[]
            self.__file_changed=0

        def __str__(self):
            return Netinterface.__str__(self) 

        def config(self, action="-verify"):
            self._action=action
            if self._action not in ["-verify","-install","-fix","-upgrade"] :
                if self._action in ["-info","-remove"]:
                    return
                else:
                    print(f"{self._action} unknown action!")
                    exit(1)
            self._set_vars()
            self.__read_ifcfg_file()
            self.__config_general()
            self.__config_vlan()
            self.__config_bond()
            self.__config_bridge()
            self.__config_ip()
            self.__config_additional()
            self.__write_ifcfg_file()
            self._config_hosts()

        def __read_ifcfg_file(self):
            #local: netif_file, linija
            self.__netinterface_list=[]
            if not isfile(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._interface}"):
                return
            try:
                netif_file=open(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._interface}","r") 
            except:
                print(f"Could not open {self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._interface} for reading!")
                exit(1)
            while 1:
                linija=netif_file.readline()
                if not linija:
                    break
                linija=linija.rstrip()
                self.__netinterface_list.append(linija)
            netif_file.close()

        def __write_ifcfg_file(self):
            #local: netif_file, linija
            if self._action == "-verify" or not self.__file_changed :
                return
            try:
                netif_file=open(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._interface}","w") 
            except:
                print(f"Could not open {self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._interface} for write!")
                exit(1)
            for linija in self.__netinterface_list :
                netif_file.write(linija+linesep)
            netif_file.close()

        def __remove_line(self,i):
            #local: i
            if self._action == "-verify" :
                print(f"Need to remove {i} from ifcfg-{self._interface}")
            else:
                self.__netinterface_list.remove(i)
                self.__file_changed=1
                print(f"removed {i} from ifcfg-{self._interface}")

        def __add_line(self,j):
            if self._action == "-verify" :
                print(f"Need to add {j} to ifcfg-{self._interface}")
            else:
                self.__netinterface_list.append(j)
                self.__file_changed=1
                print(f"Added {j} to ifcfg-{self._interface}")

        def __config_general(self):
            #local:li, lm, j, k, dodati, i
            li=[f"DEVICE={self._interface}","ONBOOT=yes","BOOTPROTO=none"]
            lm=["^DEVICE=","^ONBOOT=","^BOOTPROTO="]
            for j,k in zip(li,lm):
                dodati=1
                for i in  self.__netinterface_list:
                    if re.match(k, i):
                        if not re.match(f"^{j}$", i):
                            self.__remove_line(i)
                        else:
                            dodati=0
                if dodati:
                    self.__add_line(j)

        def __config_vlan(self):
            #local: i 
            for i in  self.__netinterface_list:
                if re.match("VLAN=", i) and not re.match("VLAN=yes",i) :
                    self.__remove_line(i)
            if re.search("\.[0-9]+$" , self._interface) : 
                if not "VLAN=yes" in self.__netinterface_list :
                    if self._action == "-verify" :
                        print(f"Need to add VLAN=yes to ifcfg-{self._interface}")
                    else:
                        self.__netinterface_list.append("VLAN=yes")
                        self.__file_changed=1
                        print(f"Added VLAN=yes to ifcfg-{self._interface}")
            else:
                if "VLAN=yes" in self.__netinterface_list :
                    if self._action == "-verify" :
                        print(f"Need to remove VLAN=yes from ifcfg-{self._interface}")
                    else:
                        self.__netinterface_list.remove("VLAN=yes")
                        self.__file_changed=1
                        print(f"removed VLAN=yes from ifcfg-{self._interface}")

        def __config_bond(self):
            if re.match("bond", self._address):
                li=[f"MASTER={self._address}","SLAVE=yes"]
                lm=["^MASTER=","^SLAVE="]
                for j,k in zip(li,lm):
                    dodati=1
                    for i in self.__netinterface_list :
                        if re.match(k,i):
                            if not re.match(j,i):
                                self.__remove_line(i)
                            else:
                                dodati=0
                    if dodati :
                        self.__add_line(j)
                if self._address in NetinterfaceRH.__bonding_flag :
                    self.__conf_bond_opts()
            else :
                if len(NetinterfaceRH.__bonding_flag) and not re.match("bond.+\..+", self._interface) and not re.match("bond.+:.+", self._interface) :
                    print("interfaces should follow bond")
                for j in ["MASTER=","SLAVE="] :
                    for i in  self.__netinterface_list:
                        if re.match(j, i) :
                            self.__remove_line(i)
            if re.match("bond", self._interface) and not re.match("bond.+\..+", self._interface) and not re.match("bond.+:.+", self._interface) :
                NetinterfaceRH.__bonding_flag.append(self._interface)

        def __find_bond_opts(self):
            #local:bond_opt, mon
            if isfile(f"{self._rootdir}/var/locconf/netif/{self._address}_mode_4" ) :
                bond_opt="BONDING_OPTS=\"mode=4 miimon=100 lacp_rate=[1]\""
            else:
                if isfile(f"{self._rootdir}/var/locconf/netif/{self._address}_miimon"):
                    mon="miimon=100"
                else: 
                    if isfile(f"{self._rootdir}/var/locconf/netif/{self._address}_miimon_custom"):
                        mon="miimon=100 downdelay=300 updelay=300"
                    else:
                        if isfile(f"{self._rootdir}/var/locconf/netif/arptarget_{self._address}"):
                            bond_file=open(f"{self._rootdir}/var/locconf/netif/arptarget_{self._address}")
                            linija=bond_file.readline()
                            bond_file.close()
                            linija=linija.rstrip()
                        else:
                            if isfile(f"{self._rootdir}/etc/sysconfig/network"):
                                bond_file=open(f"{self._rootdir}/etc/sysconfig/network")
                                linija_list=[]
                                while 1:
                                    linija=bond_file.readline()
                                    linija=linija.rstrip()
                                    if not linija:
                                        break
                                    if re.match("GATEWAY",linija):
                                        linija_list=linija.split("=")
                                        break
                                bond_file.close()
                                if len(linija_list) == 2 :
                                    linija=linija_list[1]
                                else:
                                    linja=""
                        mon=f"arp_interval=1000 arp_ip_target={linija}"
                bond_opt=f"BONDING_OPTS=\"primary={self._interface} mode=1 {mon}\""
                return bond_opt

        def __conf_bond_opts(self):
            #local: bond_opt, bond_file, linija, linija_list, bond_list, i, bond_list_changed, dodati

            bond_opt=self.__find_bond_opts()
            if not isfile(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._address}"):
                print(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._address} does not exist")
                return
            try:
                bond_file=open(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._address}","r")
            except:
                print(f"could not open ifcfg-{self._address}")
                return
            bond_list=[]
            while 1:
                linija=bond_file.readline()
                if not linija:
                    break
                linija=linija.rstrip()
                bond_list.append(linija)
            bond_file.close()
            bond_list_changed=0
            dodati=1
            for i in bond_list:
                if re.match("BONDING_OPTS=",i):
                    if re.match(bond_opt,i):
                        dodati=0
                    else:
                        if self._action == "-verify" :
                            print(f"Need to remove {i} from ifcfg-{self._address}")
                        else:
                            bond_list.remove(i)
                            bond_list_changed=1
                            print(f"Removed {i} from ifcfg-{self._address}")
            if dodati :
                if self._action == "-verify" :
                    print(f"Need to add {bond_opt} to ifcfg-{self._address}")
                else:
                    bond_list.append(bond_opt)
                    bond_list_changed=1
                    print(f"Added {bond_opt} to ifcfg-{self._address}")
            if bond_list_changed :
                try:
                    bond_file=open(f"{self._rootdir}/etc/sysconfig/network-scripts/ifcfg-{self._address}","w")
                except:
                    print(f"could not open ifcfg-{self._address} for write")
                    return
                for i in bond_list:
                    bond_file.write(i+linesep)
                bond_file.close()
            NetinterfaceRH.__bonding_flag.remove(self._address)

        def __config_bridge(self):
            #local: i, dodati
            if re.match("bridge", self._interface) :
                if not "TYPE=Bridge" in self.__netinterface_list :
                    if self._action == "-verify" :
                        print(f"Need to add TYPE=Bridge to ifcfg-{self._interface}")
                    else:
                        self.__netinterface_list.append("TYPE=Bridge")
                        self.__file_changed=1
                        print(f"Added TYPE=Bridge to ifcfg-{self._interface}")
            else:
                if "TYPE=Bridge" in self.__netinterface_list :
                    if self._action == "-verify" :
                        print(f"Need to remove TYPE=Bridge from ifcfg-{self._interface}")
                    else:
                        self.__netinterface_list.remove("TYPE=Bridge" )
                        self.__file_changed=1
                        print(f"Removed TYPE=Bridge from ifcfg-{self._interface}")
            if re.match("bridge", self._address):
                dodati=1
                for i in  self.__netinterface_list:
                    if re.match("BRIDGE=", i) :
                        if not re.match(f"BRIDGE={self._address} *$",i):
                            self.__remove_line(i)
                        else:
                            dodati=0
                if dodati :
                    if self._action == "-verify" :
                        print(f"Need to add BRIDGE={self._address} to ifcfg-{self._interface}")
                    else:
                        self.__netinterface_list.append(f"BRIDGE={self._address}")
                        self.__file_changed=1
                        print(f"Added BRIDGE={self._address} to ifcfg-{self._interface}")
            else:
                for i in  self.__netinterface_list:
                    if re.match("BRIDGE=", i) :
                        self.__remove_line(i)

        def __config_ip(self):
            #local: i, host_ip, dodati, netmasks_file, netmask_found, linija, netmasks_list, ip_network, ip_broadcast, ip
            if re.match("bond", self._address) or re.match("bridge", self._address) or re.match("none", self._address) :
                for i in self.__netinterface_list:
                    if re.match("IPADDR=", i) or re.match("NETMASK=",i):
                        self.__remove_line(i)
                return
            host_ip=""
            if self._if_name == Netinterface._hostname and "LOCCONF_IP" in environ:
                host_ip=environ['LOCCONF_IP']
            else:            
                try:
                    host_ip = socket.gethostbyname(self._if_name)
                except:
                    print(f"could not resolve {self._if_name}")
                    return
            self._if_ip=host_ip
            dodati=1
            for i in self.__netinterface_list:
                if re.match("IPADDR=",i) :
                    if not re.match(f"IPADDR={host_ip}",i):
                        self.__remove_line(i)
                    else:
                        dodati=0
            if dodati :
                if self._action == "-verify" :
                    print(f"Need to add IPADDR={host_ip} to ifcfg-{self._interface}")
                else:
                    self.__netinterface_list.append(f"IPADDR={host_ip}")
                    print(f"Added IPADDR={host_ip} to ifcfg-{self._interface}")
                    self.__file_changed=1
            self.__conf_netmask()

        def __conf_netmask(self):
            #local: dodati, netmask_found, linija, netmasks_file, netmasks_list, ip_network, ip_broadcast, ip, i
            if not isfile(f"{self._rootdir}/var/locconf/netif/netmasks"):
                print("Could not find var/locconf/netif/netmasks file")
                return
            try:
                netmasks_file=open(f"{self._rootdir}/var/locconf/netif/netmasks","r") 
            except:
                print("Could not open var/locconf/netif/netmasks")
                return
            dodati=1
            netmask_found=0
            while 1:
                linija=netmasks_file.readline()
                if not linija:
                    break
                netmasks_list=linija.split()
                ip_network=netmasks_list[0].split(".")
                ip_broadcast=netmasks_list[1].split(".")
                ip=self._if_ip.split(".")
                if self._debug == 2 :
                    print("netmask:",ip_network, ip, ip_broadcast)
                if int(ip[0])>=int(ip_network[0]) and int(ip[1])>=int(ip_network[1]) and int(ip[2])>=int(ip_network[2]) and int(ip[3])>int(ip_network[3]) :
                   if int(ip[0])<=int(ip_broadcast[0]) and int(ip[1])<=int(ip_broadcast[1]) and int(ip[2])<=int(ip_broadcast[2]) and int(ip[3])<int(ip_broadcast[3]) :
                        netmask_found=1
                        for i in self.__netinterface_list:
                            if re.match("NETMASK=",i) :
                                if not re.match(f"NETMASK={netmasks_list[2]}",i):
                                    self.__remove_line(i)
                                else:
                                    dodati=0
                        if dodati :
                            if self._action == "-verify" :
                                print(f"Need to add NETMASK={netmasks_list[2]} to ifcfg-{self._interface}")
                            else:
                                self.__netinterface_list.append(f"NETMASK={netmasks_list[2]}")
                                self.__file_changed=1
                                print(f"Added NETMASK={netmasks_list[2]} to ifcfg-{self._interface}")
                        break
            netmasks_file.close()
            if not netmask_found :
                print("Did not find netmask in netmasks file")

        def __config_additional(self):
            pass

        def remove(self, action):
            #local: i, j
            self._action=action
            if self._action not in ["-verify", "-fix", "-install", "-upgrade", "-remove" ]:
                return
            self._set_vars()
            self.__read_ifcfg_file()
            for j in ["SLAVE=","MASTER=","IPADDR=","NETMASK=","VLAN=yes","BRIDGE=","ONBOOT=yes"]:
                for i in  self.__netinterface_list:
                    if re.match(j, i):
                        self.__remove_line(i)
                #todo: if bond, bridge maybe os.remove it, remove ONBOOT=<everthing except no>, remove ip from hosts
            if "ONBOOT=no" not in self.__netinterface_list:
                if self._action == "-verify" :
                    print(f"Need to add ONBOOT=no to ifcfg-{self._interface}")
                else:
                    self.__netinterface_list.append("ONBOOT=no")
                    self.__file_changed=1
                    print(f"Added ONBOOT=no to ifcfg-{self._interface}")
            self.__write_ifcfg_file()

def read_netinterfaces_file(netinterface_file):
    #local: netif, linija, interface_lin, netinterfaces_list (return)
    # file format:   bond<x[.y]>|bridge<x[.y]>|<interface like ethX, enXY>  [-bup|bridge<x>|bond<x>|none|<host>]
    #                             if address not specified hostname is used, -bup is <hostname>-bup 
    if not isfile(netinterface_file):
        print(f"{netinterface_file} does not exist!")
        exit(1) 
    try:
        netif=open(netinterface_file,"r") 
    except:
        print(f"Could not open {netinterface_file} for reading!")
        exit(1)
    netinterfaces_list=[]
    while 1:
        linija=netif.readline()
        if not linija:
            break
        if re.match("^#", linija) :
            continue            
        if not re.search("[a-zA-Z]",linija):
            print(f"ignore {linija}")
            continue
        interface_lin=linija.split()
        if len(interface_lin)>2 :
            print(f"ignore more than 2 field in {linija}")
        if len(interface_lin) == 1:
            netinterfaces_list.append(NetinterfaceRH(interface_lin[0]))
        else:
            netinterfaces_list.append(NetinterfaceRH(interface_lin[0],interface_lin[1]))
    netif.close()
    return netinterfaces_list

def main():
       return 

if __name__ == "__main__":
    main()
