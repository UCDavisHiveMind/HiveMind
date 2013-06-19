#!/usr/bin/env python

#-
#- HiveMind - Target Creation tool
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 4 Dec 2010
#- Revised: v0.2 - 28 May 2011
#- Revised: v0.3 - 28 Sep 2012
#-

"""
Copyright (c) 2010,2011,2012,2013 Regents of the University of the California

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and/or hardware specification (the "Work"), to deal in the Work including
the rights to use, copy, modify, merge, publish, distribute, and sublicense, for
non-commercial use, copies of the Work, and to permit persons to whom the Work is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Work.

The Work can only be used in connection with the execution of a project
which is authorized by the GENI Project Office (whether or not funded
through the GENI Project Office).

THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
WORK OR THE USE OR OTHER DEALINGS IN THE WORK.
"""


# this program sets random targets in the mesh 
#- the default is every 15 seconds, but this can be changed via CL options.
#- this is the client; usage is:
#   python clnt.py server_address port_number

import random
from random import choice
import time
import re
import sys
import os
from optparse import OptionParser
import signal
import logging
import logging.handlers
import socket
import ConfigParser
import node_map
import sensors

#random.seed(1114581)

workdir = os.path.dirname(os.path.abspath(__file__))

parser = OptionParser()

parser.add_option("-l", action='store_true', dest="loop", default=False, help="loop creating targets until killed")
parser.add_option("-i", action='store', type="int", dest="interval", default=15, help="number of seconds to wait between setting targets")
parser.add_option("-r", action='store_true', dest="remove", default=False, help="remove target before creating next ")
parser.add_option("-f", action='store', type="string", dest="node_map_filespec", default=workdir+"/hm_node_map.txt", help="filespec to read node map from (default = "+workdir+"/node_map")
parser.add_option("-t", action='store', type="string", dest="target_name", default=None, help="specified target for the attack")
parser.add_option("-e", action='store', type="string", dest="experiment", default=os.getenv("EXPERIMENT"), help="name of experiment")
parser.add_option("--multiple", action='store_true', dest="multiple_targets", default=False, help="set targets on multiple hosts. Density control number of target hosts")
parser.add_option("--group", action='store_true', dest="group_targets", default=False, help="place attack targets in a group of nearby nodes. ")
parser.add_option("--density", action='store', type='int', dest="group_density", default=5, help="approximately how many targets to create in the group")
parser.add_option("--spread", action='store', type='int', dest="group_spread", default=5, help="approximate diameter to put group of targets in")
parser.add_option("--type", action='store', type='int', dest="target_type", default=None, help="set a specific attack type as the target")
parser.add_option("--onetype", action='store_true', dest="one_type", default=False, help="make grouped attack types all one type")
parser.add_option("--onezone", action='store_true', dest="one_zone", default=False, help="make grouped attacks only target one zone per group")

(options, args) = parser.parse_args()




#- open the config file
config = ConfigParser.RawConfigParser()
start_dir = os.path.dirname(os.path.abspath(__file__))
config.readfp(open(start_dir+'/../hivemind.conf/hivemind.cfg'))


#- get the fully qualified name of the host this process is running on
this_host = socket.gethostname()


#- using the local logging directory specified in the config file,
#- redirect stderr to a host specific log2 file
logdir = config.get('NodeMgr','logdir')
errlogfile = logdir+'/set_targets.log.'+this_host
log_stderr_f = open(errlogfile, "w")
original_stderr = sys.stderr  #- save reference to original stderr for laster restoratin
sys.stderr = log_stderr_f

node_mgr_port = config.getint('NodeMgr','node_mgr_port')

#- 
#- Initialize the logger
#-
try:
  project = 'GENIHiveMind'
  logger_node = 'hivemind'
  logger_base = 'isi.deterlab.net'
  logger_port = 514

  logger = logging.getLogger('MyLogger')
  logger.setLevel(logging.INFO)
  f = logging.Formatter("%(created)s %(levelname)-9s %(message)s")
  #- write to logger for log_local7 ( = 23)
  logger_address = logger_node
  #logger_address = logger_node+'.'+options.experiment+'.'+project+'.'+logger_base
  
  #- for TCP logging (requires rsyslogd and python 2.7
  #h = logging.handlers.SysLogHandler(address=(logger_address,logger_port), facility=23, socktype=socket.SOCK_STREAM)
  
  #- for UDP logging (syntax requires python 2.7
  #h = logging.handlers.SysLogHandler(address=(logger_address,logger_port), facility=23, socktype=socket.SOCK_DGRAM)
  
  #- for UDP logging 
  h = logging.handlers.SysLogHandler(address=(logger_address,logger_port), facility=23)
  
  #- for local logging
  #h = logging.handlers.SysLogHandler(address='/dev/log',facility=23)
  h.setFormatter(f)
  logger.addHandler(h)

except socket.error, (value,message):
    print "Error opening connection to log server ("+logger_address+", "+logger_port+")"
    sys.exit(0) 

 

#-
#- ****
#-
def set_targets(node_set, one_type_only_q):

    manifest = {}
    #attacks_available = [ '/tmp/baddata','/tmp/badfile','/tmp/baduser','/tmp/badtarget','/tmp/badsize' ]
    attacks_available = sensors.sensor

    if one_type_only_q is True:
	#- select a number of attacks (1-5) at random
        if options.target_type is None: 
            the_attack = choice( attacks_available.keys() )
        else:
            the_attack = attacks_available[options.target_type-1]
     
    #- for each target node
    for this_node in node_set:

        attack_set = {}
        manifest[this_node] = []

        if one_type_only_q:
            attack_set[the_attack] = True     
        else:
	    #- generate a set of attacks
	    for s in range(1,len(attacks_available)):
		#- select a random "attack"
		this_attack = choice( attacks_available.keys() )

		#- record it for removal
		attack_set[this_attack]=True


	#- set the attacks for this node
	for this_attack in attack_set:

            manifest[this_node].append(this_attack)

	    notes = "attack:%s" % (this_attack)
	    msg = 'node_id:%s %s:%s notes:%s' % (this_node,'event','attack_set',notes)
	    logger.info('[%s] %s', this_host, msg)

	    print "\n>> USING ATTACK #", this_attack, "\n"
	    count = 10
	    while count > 0:
		try:
		    print ".",
		    # create tcp socket to Hive node
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect((this_node, node_mgr_port))
		    break
		except socket.error, (value,message):
		    if s: 
			s.close()
		    print "Could not open socket: " + message
		    count -= 1
	    
	    if count <= 0:
		print "ERROR: was unable to connect to ",name," at ",ip 
		sys.exit()

            #- send request to node manager 
            parms = ""
            msg = 'set_t:%s,%s' % (this_attack,parms)
            print ">>",msg
	    fileobj = s.makefile('r',0)
	    fileobj.write(msg)
	    print "set target #%s request sent to node manager on %s" % (this_attack,this_node)
		   

    return( manifest )



def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    sys.exit(0)


def get_nearby_node(the_node,diameter):

    d = int(random.random()*diameter)
    while d > 0:
        neighbors = the_map.get_neighbors(the_node)
        the_node = choice( neighbors ) #- select a random neighbor
	d -= 1
        
    return the_node


signal.signal(signal.SIGINT, signal_handler)

the_map = node_map.NodeMap()
the_map.load_map(options.node_map_filespec)
print "all is cool with the map"

for k in the_map.cells:
    print k, the_map.cells[k]

for k in the_map.rcells:
    print k, the_map.rcells[k]

a=0; b=0
the_node = the_map.rcells["%s:%s" % (a,b)]
x = the_map.get_neighbors(the_node)
#print "(%d,%d)  %s" % (a,b,x)


while True:

    target_group = {}
    attack_set = {}
    the_enclave = None

    one_type_only_q = options.one_type
   
    #- if a specific target type was selected, (since we only allow 1 for now)
    #-   force the one-type option to be true
    if options.target_type is not None: one_type_only_q = True

    one_zone_only_q = options.one_zone
    print ">> one zone:",one_zone_only_q
    
    if options.multiple_targets is True:
        if options.target_name is None: 
	    first_node = choice( the_map.cells.keys())
        else:
            first_node = options.target_name
	the_enclave = the_map.cells[first_node][2]
	print ">> setting enclave to",the_enclave

    #- generate a list of hosts to target
	for i in range(options.group_density):	
            #- select a random node
            while True:
                target_node = choice( the_map.cells.keys() )
                #- if we are targeting a single enclave, then retry until we get one
                if not one_zone_only_q or the_map.cells[target_node][2] == the_enclave:
	            target_group[target_node] = True
                    break #-exit retry loop

    elif options.group_targets is True:
    #- generate attacks on a related group of nodes (i.e. nearby in grid)

        #- first select the group of nearby nodes to target
        if options.target_name is None: 
	    first_node = choice( the_map.cells.keys())
        else:
            first_node = options.target_name

        the_enclave = the_map.cells[first_node][2]

	for i in range(options.group_density):	
            while True:
	        target_node = get_nearby_node(first_node,options.group_density) #- old method, spread = density
	        #target_node = get_nearby_node(first_node,options.group_spread)
                print "** %d >> %s -> %s [spread:%s]" % (i,first_node,target_node,options.group_spread)
                #- if we are targeting a single enclave, then retry until we get one
                if not one_zone_only_q or the_map.cells[target_node][2] == the_enclave:
	            target_group[target_node] = True
                    break #-exit retry loop
        print "**--->> [%s]" % ( target_group.keys() )        
    else:
    #- generate attacks on a single node
        if options.target_name is None: 
            target_node = choice( the_map.cells.keys() )
        else:
            target_node = options.target_name

	target_group[target_node] = True


    manifest = set_targets(target_group, one_type_only_q)
   
    print "\n--- MANIFEST -----" 
    for the_node in manifest:
        print ">> %s:  " % the_node,
        for the_attack in sorted(manifest[the_node]):
            print the_attack+"  ",
        print ""

    #- sleep for a while
    if options.loop: time.sleep(options.interval)

    if options.remove is True:
    #- remove all attacks that were just set
	for the_node in manifest:
            for the_attack in manifest[the_node]:
                #- clear the attack from the target node
		print "\n>> CLEARING ATTACK #", this_attack, "\n"
		count = 10
		while count > 0:
		    try:
			print ".",
			# create tcp socket to Hive node
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((this_node, node_mgr_port))
			break
		    except socket.error, (value,message):
			if s: 
			    s.close()
			print "Could not open socket: " + message
			count -= 1
		
		if count <= 0:
		    print "ERROR: was unable to connect to ",name," at ",ip 
		    sys.exit()

		#- send request to node manager 
		parms = ""
		msg = 'unset_t:%s,%s' % (the_attack,parms)
		print ">>",msg
		fileobj = s.makefile('r',0)
		fileobj.write(msg)
		print "unset target #%s request sent to node manager on %s" % (the_attack,this_node)
    
    if not options.loop: break 




