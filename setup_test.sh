
mkdir -p  var/locconf/netif/ etc/sysconfig/network-scripts /tmp/locconf
touch etc/hosts
touch etc/redhat-release
echo GATEWAY=1.2.3.4 > etc/sysconfig/network
echo "bond0 www.vipmobile.rs" > ./var/locconf/netif/netinterfaces
echo "eth0 bond0" >> ./var/locconf/netif/netinterfaces
echo "eth1 bond0" >> ./var/locconf/netif/netinterfaces
echo "#bond1  none" >> ./var/locconf/netif/netinterfaces
echo "#bond1.26        bridge26" >> ./var/locconf/netif/netinterfaces
echo "#bond1.31       bridge31" >> ./var/locconf/netif/netinterfaces
echo "#eth3   bond1" >> ./var/locconf/netif/netinterfaces
echo "#eth6   bond1" >> ./var/locconf/netif/netinterfaces
echo "#bridge26        none" >> ./var/locconf/netif/netinterfaces
echo "#bridge31       none" >> ./var/locconf/netif/netinterfaces
echo "#eth7       " >> ./var/locconf/netif/netinterfaces
echo "#eth8       -bup" >> ./var/locconf/netif/netinterfaces
echo "212.15.182.0 212.15.182.255 255.255.255.0" > ./var/locconf/netif/netmasks

#export LOCCONF_ROOTDIR=`pwd`
#LOCCONF_DEBUG=2 ./post.py

