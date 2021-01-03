#!/usr/bin/python3

from os.path import isfile
from os import environ
from sys import argv
import netinterfaces

def main():
    #local vars: action, rootdir, temp, netints_list, netint, netints_list_old, tmp_list, debug
    if len(argv)>1 :
        if argv[1] in ["-h", "-help", "--help"] or len(argv)>3 :
            print(f"usage: {argv[0]} [ -verify|-info|-install|-fix|-upgrade|-remove [-prepare_pkg]]")
            return
        else:
            action=argv[1] 
        if len(argv) == 3:
            if argv[2] == "-prepare_pkg" :
                return
    else:
        action="-verify"

    if "LOCCONF_ROOTDIR" in environ:
        rootdir=environ['LOCCONF_ROOTDIR']
    else:
        rootdir="/"
    if "LOCCONF_TEMP" in environ:
        temp=environ['LOCCONF_TEMP']
    else:
        temp="/tmp/locconf"
    if "LOCCONF_DEBUG" in environ:
        debug=int(environ['LOCCONF_DEBUG'])
    else:
        debug=0
    if not isfile(f"{rootdir}/etc/redhat-release"):
        print("Only Redhat is supported")
        return
# 
#    eth3=netinterfaces.NetinterfaceRH("eth3","www.vipmobile.rs") 
#    eth3.config(action)
    netints_list=netinterfaces.read_netinterfaces_file(f"{rootdir}/var/locconf/netif/netinterfaces")
    for netint in netints_list:
        if debug :
            print(f"### checking {netint.interface}")
        netint.config(action)

    if isfile(f"{temp}/netinterfaces") :
        if action in ["-verify","-fix","-upgrade"]:
            netints_list_old=netinterfaces.read_netinterfaces_file(f"{temp}/netinterfaces")
            tmp_list=[]
            for netint in netints_list :
                tmp_list.append(netint.interface)
            for netint in netints_list_old :
                if netint.interface not in tmp_list :
                    if debug:
                        print(f"### remove {netint.interface}")
                    netint.remove(action)

if __name__ == "__main__":
    main()
