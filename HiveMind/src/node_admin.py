#!/usr/bin/env python

#-
#- HiveMind - Hive Node Administration Tool
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 4 Dec 2010
#- Revised: v0.2 - 28 May 2011
#- Revised: v0.3 - 28 Sep 2012
#-

"""
Copyright (c) 2010,2011,2012 Regents of the University of the California

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

"""

node_admin.py:

Provides a collection of functions to manage nodes on the system.

"""

import multiprocessing
from optparse import OptionParser
import signal
import time
import logging
import socket
import os
import subprocess
import sys
import inspect
import ConfigParser

username = os.getenv('USER')

#print inspect.getfile(inspect.currentframe()) # script filename (usually with path)
#workdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
workdir = os.path.dirname(os.path.abspath(__file__))


#- open the config file
config = ConfigParser.RawConfigParser()
config.readfp(open(workdir+'/../hivemind.conf/hivemind.cfg'))
node_mgr_port = config.getint('NodeMgr','node_mgr_port')
use_NFS = config.getboolean('NodeMgr','use_NFS')
install_dir = config.get('NodeMgr','install_dir')

parser = OptionParser()
parser.add_option("--nodes", action='store', type="string", dest="nodes", default="", help="filename containing list of nodes to manage")
parser.add_option("-s", action='store_true', dest="restart_nodes", default=False, help="start node managers")
parser.add_option("-q", action='store_true', dest="shutdown_nodes", default=False, help="stop node managers")
parser.add_option("-k", action='store_true', dest="kill_nodes", default=False, help="forcibly kill node manager processes")
parser.add_option("--run", action='store_true', dest="create_ants", default=False, help="send command to allow ants to be automatically created")
parser.add_option("--wait", action='store_true', dest="wait_ants", default=False, help="send command to stop ants from being automatically created")
parser.add_option("--kill", action='store_true', dest="kill_ants", default=False, help="send command to kill all received ants")
parser.add_option("-n", action='store', type="int", dest="node_count", default=0, help="number of nodes, range 1 to this value to include in slice")
parser.add_option("--map", action='store_true', dest="save_map", default=False, help="save node map file, used to save list of node names discovered using -n")
parser.add_option("--ping", action='store_true', dest="do_ping", default=False, help="ping nodes to see if they are alive")
parser.add_option("--user", action='store', type="string", dest="username", default=os.getenv('USER'), help="Override user name to use when logging into nodes.")
parser.add_option("--opt", action='store', type="string", dest="opt", help="change adjustable value on all nodes. Format is OPTION_NAME=VALUE")

(options, args) = parser.parse_args()


if options.opt is not None:
    if options.opt.find("=") == -1: #- not found
        print
        print "option --opt must be of form OPTION_NAME=VALUE"
        print
        sys.exit()

# Initialization for package
HOSTNAME = socket.gethostname()
LOG_FILENAME = "log.node_admin." + HOSTNAME

# Creates a logger output to both a logfile and stdout
#logger = logging.getLogger("node_admin")
#logger.setLevel(logging.DEBUG)
#streamHandler = logging.StreamHandler()
#streamHandler.setLevel(logging.INFO)
#logger.addHandler(streamHandler)
#logger.addHandler(logging.FileHandler(LOG_FILENAME, "a"))


CONNECTION_RETRIES = 10
CLIENT_PORT = node_mgr_port
SENDING_TIMEOUT = 300030003000
INITIAL_WAIT = 1 #60 * 2
NORMAL_WAIT = 60 * 5
POOL_SIZE = 4

rbufsize = -1 
wbufsize = 0  

def run():

    # Create a handler to exit on signals or KeyboardInterrupt
    def stop(*args):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGHUP, stop)
    signal.signal(signal.SIGALRM, stop)


    #- 
    if options.shutdown_nodes:
        action = do_stop        
    
    elif options.restart_nodes:
        action = do_start        

    elif options.kill_nodes:
        action = do_kill         

    elif options.do_ping:
        action = do_ping         

    elif options.create_ants:
        action = do_send_create_ok         

    elif options.wait_ants:
        action = do_send_no_create     

    elif options.kill_ants:
        action = do_send_kill_ants     

    elif options.opt:
        action = do_opt         

    else:
        action = do_check        


    """Initialization A shared dictionary is set."""
    if options.nodes != "": #- read nodes from file
        node_list_filespec = options.nodes
    else:
        node_list_filespec = '/tmp/hm_node_list'

    if options.node_count == 0: #- no command to survey (old), so just use state file of nodes
        try:
            node_list = [line.strip() for line in open(node_list_filespec)]
        except IOError, e:
            notes = sys.exc_info()[0]
            if e.errno == 2: #- file not found
                print "Error reading '%s': file not found" % (node_list_filespec)
		if node_list_filespec == '/tmp/hm_node_list':
		    print ">>> Did you forget to specify the node list file?"
            else:   
                print "Error reading '%': %s" % (node_list_filespec, e)
            sys.exit(0)
            
    else: #- determine node list based on sequence of nodes named 'node-#'
        node_count = options.node_count
        node_list = []
        for node_num in range(1, node_count + 1):
            node_id = "node-" + str(node_num)
            node_list.append(node_id)


    #!!manager = multiprocessing.Manager()
    # process and thread-safe
    #!!nodes = manager.list(range(node_count))
    #nodes = manager.dict()

    # Create receiving process
    #receiver = Receiver(nodes)
    #listen_proc = multiprocessing.Process(target=receiver.run)
    #listen_proc.start()

    # Create sending process pool and wait
    print "[num cpus:", multiprocessing.cpu_count(), "]"
    pool = multiprocessing.Pool(32) #- arg. specifies # of processors to use, default is actual # of cores
    #time.sleep(INITIAL_WAIT)

    # check each listed node using pool
    result = pool.map_async(action, node_list)
    successes = result.get(timeout=SENDING_TIMEOUT)
    if len(successes) != len(node_list):
        print("Some nodes not updated: %d out of %d" % (len(successes), len(node_list)))

    #- display the result of the check
    alive_cnt = 0
    for x in successes:
        print "-->",x
        if x is not False: alive_cnt += 1

    print "number alive:", alive_cnt

    #- write out the node list file for all alive nodes
    if options.save_map is True:
        node_list_filespec = '/tmp/hm_node_list'
        try:
            fp = open(node_list_filespec, 'w')
            try:
                for x in successes:
                    if x:
                        node_id = x.split()[1] #- extract the node name from the status message
                        node_id = node_id.split('.')[0] #- extract the host from the fq node name
                        fp.write(node_id + "\n")
            finally: 
                fp.close() # close socket
        except IOError:
            notes = sys.exc_info()[0]
            exc_type, exc_value = sys.exc_info()[:2]
            print "Error writing '", node_list_filespec, "'", exc_type, "::", exc_value, "\n"
            sys.exit(0)


    print("done")


def do_send_create_ok(node):         
    # send message 'run:' to iniate creating ants
    response = query_node(node, 'run:')
    return response

def do_send_no_create(node):     
    # send message 'run:' to iniate creating ants
    response = query_node(node, 'wait:')
    return response

def do_send_kill_ants(node):     
    # send message 'run:' to iniate creating ants
    response = query_node(node, 'kill:')
    return response

def do_check(node):
    # send message 'status:', return status message
    response = query_node(node, 'status:')
    return response

def do_stop(node):
    # send message 'quit:'
    print ">>", node, "<<"
    response = do_check(node)
    if response is not False: #- if it is alive
        p = query_node(node, 'quit:')
        time.sleep(0.10)
        #- note: the check causes a "connection reset by peer" error. Thought is that we connect to
        #-       get the status, but the process quits midway through the handshake or something
        #-       seems we need to investigate a longer sleep above so the process actually completely quits first
        time.sleep(1.00)
        response = do_check(node)
    return response

def do_start(node):
    # use ssh to start node manager on host, return status message
    if username is None: # running from web
        msg = """<br />--------------------------------------------------------
                 <br />  This function not allowed for non privileged users 
                 <br />--------------------------------------------------------
                 <br /> """
        return msg

    response = do_check(node)

    if response is False:
        print ">> starting node_mgr on '" + node + "'"

        if use_NFS is True:
            print ">>> Using NFS: workdir =", workdir
		
            #- if we are using NFS, then just run file from user's NFS directory
	    #- execute the start script
	    cmd = "ssh %s@%s sudo %s/start_hivemind.sh %s" % (username, node, workdir, workdir)
            print ">>> CMD = [",cmd,"]"
	    os.system(cmd)
        else:
	    #- create user and directory on remote host for hivemind files
	    os.system("ssh -t "+ username + '@' + node + ' sudo useradd -m -g GENIHiveMind hivemind')

	    #- copy all needed files to the remote host
	    os.system("scp -r /opt/hivemind "+ username + '@' + node + ':/tmp')

	    #- copy them to the hivemind directory
	    os.system("ssh -t "+ username + '@' + node + ' sudo cp -r /tmp/hivemind/* ' + install_dir)

	    #- copy them to the hivemind directory
	    os.system("ssh -t "+ username + '@' + node + ' sudo chown -R hivemind ' + install_dir)

	    #- delete the original files
	    os.system("ssh -t "+ username + '@' + node + ' sudo rm -rf /tmp/hivemind')

	    #- execute the start script
            print "*** STARTING START_HIVEMIND ***"
	    os.system("ssh -t "+ username + '@' + node + ' ' + "sudo " + install_dir + "/start_hivemind.sh " + install_dir)
	    #p = subprocess.call(['ssh' , '-o StrictHostKeyChecking=no', username + '@' + node, ' sudo ' + workdir + '/opt/hivemind/start_hivemind.sh'])
	    
        time.sleep(1.00)
	response = do_check(node)

    return response

def do_kill(node):
    # use ssh to kill node manager process on host
    # because sometimes the nodes come up as root, we must sudo to ensure we have privs to kill them
    if username is None: # running from web
        msg = """<br />--------------------------------------------------------
                 <br />  This function not allowed for non privileged users 
                 <br />--------------------------------------------------------
                 <br /> """
        return msg

    p = subprocess.call(['ssh -t', '-o StrictHostKeyChecking=no', node, 'sudo pkill -f node_mgr.py'])
    response = do_check(node)    
    return response


def do_ping(node):
    p = subprocess.call(['ping', '-c 1', node])
    if p == 0:
        response = '%s is up' % node
    else:
        response = False
    return response 


def do_opt(node):
    response = query_node(node, 'opt:' + options.opt)
    return response


def query_node(node, request):

    #logger.info("checking node %s" % node)
    print "<br />checking node %s" % node

    for count in range(CONNECTION_RETRIES):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.sleep(0.001)
            sock.connect((node, CLIENT_PORT))
            break

        except socket.error as (_, message):
            if message == 'No route to host':
                sock = False
                break

            if message == 'Connection timed out':
                sock = False
                break

            if message == 'Connection refused':
                sock = False
                break

        except socket.timeout as (_, message):
            if message == 'timed out':
                message = '%s w TO=%s' % message, socket.getdefaulttimeout()
                sock = False
                break

        except:
            print ">>> socket.error: (" + message + ')'
            #logger.info("Couldn't open socket, %d tries left: %s" % \
            #            (CONNECTION_RETRIES - count - 1, message))
            sock = False

    if not sock:
        print("Was unable to connect to %s" % (node))
        return False

    """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.sleep(0.001)
            sock.connect((node, CLIENT_PORT))
            break
        except socket.error as (_, message):
            logger.info("Couldn't open socket, %d tries left: %s" % \
                    (CONNECTION_RETRIES - count - 1, message))
            sock = False

    if not sock:
        logger.error("Was unable to connect to %s" % (node))
        return False
    """

    rfile = sock.makefile('r', rbufsize)
    wfile = sock.makefile('w', wbufsize)

    """send a message and get a 1-line reply"""

    wfile.write(request + "\n")
    response = rfile.read()
    response = response.rstrip("\r\n")
    time.sleep(0.01)

    sock.close()

    msg = "%s: [%s]" % (node, response)
    #print(msg)

    return response

def get_host_spec_from_status(x):
    host_spec = x.split()[1] #- extract the node name from the status message
    return host_spec

def get_node_id_from_host_spec(x):
    node_id = x.split('.')[0] #- extract the host from the fq node name
    return node_id



if __name__ == "__main__":
    print("starting execution directly")
    run()
