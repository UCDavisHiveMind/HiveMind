#!/bin/csh

set h = `hostname`
echo "hostname", $h

set rundir = $1
echo
echo "---------------------------------------------------"
echo "rundir=" $rundir
set dr = `dirname $0`
echo "dr=" $dr
set wd = `pwd -P`
echo "wd=" $wd

echo
echo "IN START SCRIPT" >> /tmp/foo

#- assuming we are running as root

#- sync clocks via ntp now
sudo ntpdate -b boss

if ( $h =~ hivemind* || $h =~ Hivemind* ) then
    echo "configuring hivemind queen on $h"
    echo "updating rsyslogd"
    #- replace syslog config and restart syslogd on master hivemind node only
    set rundir = $wd/$dr
    echo ">>>> rundir="$rundir
    sudo cp $rundir/../hivemind.conf/50-default.conf /etc/rsyslog.d/
    sudo cp $rundir/../hivemind.conf/rsyslog.conf /etc/ 
    sudo rm -f /var/logs/hivemind.log
    sudo service rsyslog restart
    sudo chmod o+r /var/log/hivemind.log
    sudo rm /tmp/*
    sudo rm $rundir/../logs/*
    sudo chmod 755 $rundir/assign_neighbors.py
    sudo chmod 755 $rundir/node_mgr.py
    sudo chmod 755 $rundir/node_admin.py
    sudo apt-get -y install apache2
    sudo apache2ctl restart
    sudo cp $rundir/../html/*.html /var/www/.
    sudo cp $rundir/../html/*.pl /usr/lib/cgi-bin/.
else
    echo "STARTING node manager on $h" >> ~/hivemind/logs/foo-$h
    #- clear any existing "attacks" from the node
    #- !! this is from testing and refers to the test attacks
    #- either remove (i.e. don't clear attacks awaiting discovery, or call code to "undo" all test attacks
    rm -f /tmp/bad*

    #- start the node manager on all other nodes
    #- first wait a bit to hope syslog has been restarted w/ new config
    sleep 5
    mkdir $rundir/../logs
    rm -f $rundir/../logs/errlog.$h 2> /dev/null 
    touch $rundir/../logs/errlog.$h  
    echo "STARTING process" >> $rundir/../logs/foo
    python $rundir/node_mgr.py >& $rundir/../logs/errlog.$h  &
    sleep 2
echo "---------------------------------------------------"
endif

