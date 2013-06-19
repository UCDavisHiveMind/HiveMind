#!/usr/bin/env python

#-
#- HiveMind - Hive Node Manager Process
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 4 Dec 2010
#- Revised: v0.2 - 28 May 2011
#- Revised: v0.3 - 28 Sep 2012
#-
"""
Copyright (c) 2010,2011,2012,2013,2013 Regents of the University of the California

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

# this is the client; usage is:
#   python clnt.py server_address port_number

import socket # networking module
import sys
import os
import string
import re
import time
import random
from random import choice
import math
import thread
import threading
import logging
import logging.handlers
import signal
import ConfigParser
import smtplib

from rolling_totals import RollingTotal
from collections import deque
from navigation import Compass
from sensors import *


print "## starting %s" % ('now')

WAITING = 0
RUNNING = 1
KILLING = 2
node_state = WAITING
WAITING_ANT_LIMIT = 10
waiting_ants = deque([],WAITING_ANT_LIMIT)


#- open the config file
config = ConfigParser.RawConfigParser()
start_dir = os.path.dirname(os.path.abspath(__file__))
config.readfp(open(start_dir+'/../hivemind.conf/hivemind.cfg'))


#- get the fully qualified name of the host this process is running on
fq_host_name = socket.gethostname()


#- using the local logging directory specified in the config file,
#- redirect stderr to a host specific log2 file
logdir = config.get('NodeMgr','logdir')
errlogfile = logdir+'/log2.'+fq_host_name
log_stderr_f = open(errlogfile, "w")
original_stderr = sys.stderr  #- save reference to original stderr for laster restoratin
sys.stderr = log_stderr_f


#- communications parameters
#- port to listen on
#-
node_mgr_port = config.getint('NodeMgr','node_mgr_port')
port = node_mgr_port
hmadv_addr = config.get('NodeMgr','hmadv_addr')
hmadv_port = config.getint('NodeMgr','hmadv_port')

#- maximum number of waiting connections on the socket
backlog = config.getint('NodeMgr','backlog')
#- maximum size of socket receive buffer
size = config.getint('NodeMgr','size')


#-
#- the expected life of an ant will be about the linger_time * default_ant_age
#- also, the expected number of nodes the ant will touch will be that of the 
#-   default ant age.
#- -- note:
#-
DEFAULT_ANT_AGE = config.getint('NodeMgr','DEFAULT_ANT_AGE')
CROWDING_BIAS = config.getfloat('NodeMgr','CROWDING_BIAS')  #- determines how much crowding factor affects chance to die

#- allow the option to not create ants automatically, but by manual introduction
#-   this makes controlled experimentation easier.
CREATE_ANTS = config.getboolean('NodeMgr','CREATE_ANTS') 

#- get probability that a type 2 (swarming) ant will be created
PROB_TYPE_2_ANT = config.getfloat('NodeMgr','PROB_TYPE_2_ANT')

#- number of ants we want each node to see per observation period
#- -- this is number ants seen / size of obsrv. period in seconds
DESIRED_ANT_DENSITY = config.getfloat('NodeMgr','DESIRED_ANT_DENSITY')
OBSERVATION_PERIOD = config.getfloat('NodeMgr','OBSERVATION_PERIOD')

GRANULARITY = config.getint('NodeMgr','GRANULARITY')
NUM_BINS = config.getint('NodeMgr','NUM_BINS')
AVERAGE_OVER_k_SECS = NUM_BINS*GRANULARITY
ANT_COUNT_TARGET = (DESIRED_ANT_DENSITY * AVERAGE_OVER_k_SECS) / OBSERVATION_PERIOD

LINGER_TIME = config.getfloat('NodeMgr','LINGER_TIME')

death_chance = config.getfloat('NodeMgr','death_chance')

ACTIVE_RESPONSE = config.getboolean('NodeMgr','ACTIVE_RESPONSE')

forage_perturb = config.getfloat('NodeMgr','forage_perturb')
follow_perturb = config.getfloat('NodeMgr','follow_perturb')
drop_perturb = config.getfloat('NodeMgr','drop_perturb')
follow_chance = config.getfloat('NodeMgr','follow_chance')

max_pheromone_charge = config.getint('NodeMgr','max_pheromone_charge')
max_pheromone_strength = config.getfloat('NodeMgr','max_pheromone_strength')
type_2_strength_factor = config.getfloat('NodeMgr','type_2_strength_factor')

recruitment_probability = config.getfloat('NodeMgr','recruitment_probability')
recruitment_duration = config.getint('NodeMgr','recruitment_duration')
recruiting_focus = config.getint('NodeMgr','recruiting_focus')

default_focus = config.getint('NodeMgr','default_focus')
default_focus_change_prob = config.getfloat('NodeMgr','default_focus_change_prob')

rgenseed = config.getfloat('NodeMgr','rgenseed')


email_alerts = config.getboolean('NodeMgr','email_alerts')
email_server = config.get('NodeMgr','email_server')
sender = config.get('NodeMgr','sender')
receivers = '['+config.get('NodeMgr','receivers')+']'

node_pheromone={}
neighbors = {}
DIRECTIONS = config.get('NodeMgr','DIRECTIONS')

#- ant states
IDLE      = 0
FORAGING  = 1
DROPPING  = 2
FOLLOWING = 3



#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def create_ant():
    #- create additional ants for known tasks
    #- Whether or not an ant is created is based on the crowding factor. Lower
    #- values make it more likely an ant is creates. The specific ant task is
    #- also randomly selected, but biased towards ants of higher utility and
    #- secondarily towards those occurring less frequently.
    
    #- (1) should we create an ant at all?
    #- ***[test]*** if random.random() > crowding_factor(1): return False
    
    #- (2) what kind?
    #- *** weighting by utility not yet implemented
    #- *** also need to be able to track which parameters were used and valuable
    #- *** maybe add way to permute parameter value
    new_task = random.choice( sensor.keys() )
        
    #- select random neighbor and send ant on its way
    heading = int(random.uniform(0,360)) % 360
    new_heading,move_dir = compass.get_direction(heading)
    new_dest = neighbors[move_dir];
    
    new_id = get_unique_id()
    
    notes = "task:%s, heading:%s, dest:%s" % (new_task, new_heading, new_dest)
    msg = 'ant_id:%s %s:%s notes:%s' % (new_id,'event','created',notes)
    logger.info('[%s] %s',host_name, msg)

    if (random.random() < PROB_TYPE_2_ANT):
       ant_type = 2 #- swarming
    else:
       ant_type = 1 #- trail marking
    send_ant(new_dest, new_id, ant_type, new_heading, new_task)

    
    return new_task



#------------------------------------------------------------------------------
# generate an "unique" id for the ant.
# this is a combo of the node id it was created on plus a sequential number
# Currently these are only used for informational purposes
#------------------------------------------------------------------------------
next_local_id = 0
def get_unique_id():
    global next_local_id
    global node_mgr_id
    ant_id = '%04d%08d' % (node_mgr_id, next_local_id)
    next_local_id += 1;
    return int(ant_id)



#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def crowding_factor(task):
    global my_rt
    global ANT_COUNT_TARGET

    ants_seen = my_rt.rt_get_total(time.time())

    if ANT_COUNT_TARGET > 0.0:
        #- Initially the cf is zero, but as the number of ants observed increases, 
        #-   the cf will increase until when observed=desired where cf will be 1.0
        #-   if the number of ants continues to climb the cf will be greater than 1
        #-   -- note: because the desired number is "per second" we must adjust the
        #-            calculation by the time between checks (i.e. 'sleep_time)
        cf = ants_seen/float(ANT_COUNT_TARGET)
        #cf = math.log10((float(ants_seen)+0.000001)/ant_limit)
    else:
        cf = 0.0

    notes = ''
    stats = "(ants_seen=%d, max_desired:%d, cf:%.3f)" % (ants_seen,ANT_COUNT_TARGET,cf)
    msg = '%s:%s %s:%s notes:%s' % ('node_info', host_name, 'stats',stats, notes)
    logger.debug('[%s] %s',host_name, msg)

    return cf



#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def ant_genesis():
    import time
    
    logger = logging.getLogger('')
    msg = ">> starting genesis thread (%d)" % (thread.get_ident())
    logger.debug('[%s] %s',host_name, msg)

    while True:

        if node_state == RUNNING:
	    msg = ">> checking ant density"
	    logger.debug('[%s] %s',host_name, msg)

	    ant_density = crowding_factor('all_types')
	    
	    if ant_density < 1:
                if random.random() < 0.10: #!! to prevent all ants from comming up together
		    create_ant()
		
	    msg = ">> going back to sleep"
	    logger.debug('[%s] %s',host_name, msg)

	    #- sleep for a while, then check density 
	    time.sleep(OBSERVATION_PERIOD)
 


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def message_advocate(msgtype,msg):
    return False  #- disabled for now
#-    return "random.random() < 0.01" #- for testing, dummy value, just set the function to return true randomly

#    try:
#        # create Internet TCP socket to Advocate
#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        s.connect((hmadv_addr, hmadv_port))
#    except socket.error, (value,message):
#        if s: 
#            s.close()
#        print "Could not open socket: " + message
#        sys.exit(1)
#
#    fileobj = s.makefile('r',0)
#    fileobj.write(msgtype+':'+msg)
#
#    s.close() # close socket    
    
#    return





#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def get_new_function(task):
    msg = "looking for function task ", task, "\n"
    logger.debug('[%s] %s',host_name, msg)
    #-send function request message to Advocate
    new_func = message_advocate("sfreq",task)
    
    #- if request returned null, then no such function
    #- *** expand this to be able to handle comm errors ***    
    if (not new_func or new_func == ""):
        #- unresolved function
        msg = "Could not get code for function %s" % (task)
        logger.warning('[%s] %s',host_name, msg)
        rv = False
    else:
        #- update sensor function cache
        #- *** add in LRU policy ***
        sensor[task] = lambda parms : eval(new_func)
        rv = True
        
    return rv
    


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def sensor_check(task,parms,ant_id):
    
    result = False
    
    if task in sensor :  #- sensor function was defined
        #- execute the function
        (result,details) = sensor[task](parms)
    else:    
        #- see if this is a user defined function
        #- this code is not in the sensor task list, because we don't want it 
        #- (or any other special functions) to be assigned on ant creation
        if task == 'X':
            (result,details) = user_code(parms)
            
        #- ask Adbocate for function
        if get_new_function(task): 
            #- function was added to sensor list
            (result,details) = sensor[task](parms)
        else:
            #- unable to get function information
            msg = "Function %s not defined. Ignoring." % (task)
            logger.warning('[%s] %s',host_name, msg)
            return False
    
    if result: 
        notes = "task:%s details:%s" % (task,details)
        msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','found_something',notes)
        logger.info('[%s] %s',host_name, msg)

    return result


#------------------------------------------------------------------------------
#- simple coin flip
#------------------------------------------------------------------------------
def flip():
    return random.random()<0.5;


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def send_ant(dest, ant_id, ant_type, heading, task, parms='', focus=default_focus, flt_len=0, flt_cnt=0, age=DEFAULT_ANT_AGE, state=FORAGING, charge=0, came_from='', found_at=''):   

    #-
    #- Try sending the ant message, if it fails to connect to its neighbor, try a different direction,
    #- if this does not succeed after 'retry_count' tries, report to the master that the node has becom
    #- isolated.
    #-
    retry_count = 20
    ant_send_ok = False
    while retry_count > 0:

        retry_count -= 1
        try:
            # create Internet TCP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((dest, node_mgr_port))
            if s:
                ant_msg = 'ant:%(ant_id)d,%(ant_type)d,%(age)d,%(heading)d,%(state)d,%(task)s,%(parms)s,%(focus)s,%(flt_len)d,%(flt_cnt)d,%(charge)d,%(came_from)s,%(found_at)s' \
                    % {'ant_id':ant_id,'ant_type':ant_type,'age':age,'heading':heading,'state':state,'task':task,'parms':parms,'focus':focus,'flt_len':flt_len,'flt_cnt':flt_cnt,'charge':charge,'came_from':host_name,'found_at':found_at}
                notes = "dest:%s, age:%s, [%s]" % (dest,age,ant_msg)
                msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','sent',notes)
    
                #- log that an ant message was sent
                logger.debug('[%s] %s',host_name, msg)

                #- send the ant message
                fileobj = s.makefile('w',0)
                fileobj.write(ant_msg)

                #- close the socket (not to be used if proto is UDP)
                s.close()     

                ant_send_ok = True
                break; #- we were successful, so exit the loop and routine

        except socket.error, (value,message):
            if s: 
                s.close()
            msg = "Sending ant to "+dest+". Could not open socket: " + message
            logger.warning('[%s] %s',host_name, msg)
            
            #- no comm w/ neighbor, pick a new random direction, and send ant back to this node to be re-routed
            if flip():
                heading = (heading - 90 + 360) % 360
            else:
                heading = (heading + 90) % 360
         
            new_heading,move_dir = compass.get_direction(heading)
            dest = neighbors[move_dir];

            msg = "changing destination to %s on heading:%s" % (dest,new_heading)
            logger.debug('[%s] %s',host_name, msg)

            msg = '%s:%s notes:%s' % ('report-dead-node', dest, ant_id)
            logger.info('[%s] %s',host_name, msg)

    
    if ant_send_ok is False:
        #- send has failed, notify master program, kill ant, exit. A concern is that we don't want to
        #- become a black-hole for ants. Better to be removed from the system.
        notes = "Unable to send ants to any neighbors, ant %s has died, node shutting down" % (ant_id)
        msg = '%s:%s %s:%s notes:%s' % ('node_id', host_name,'event','node exiting',notes)
        logger.warning('[%s] %s',host_name, msg)
        sys.exit(1)
    

recruiting = 0
recruiting_task = None

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def handle_ant(ant_info):
    
    ant_id = ant_info['ant_id']
    ant_type = ant_info['ant_type']
    age = ant_info['age']
    heading = ant_info['heading']
    state = ant_info['state']
    task = ant_info['task']
    parms = ant_info['parms']
    focus = ant_info['focus']
    flt_len = ant_info['flt_len']
    flt_cnt = ant_info['flt_cnt']
    charge = ant_info['charge']
    came_from = ant_info['came_from']
    found_at = ant_info['found_at']

    global my_rt
    global recruiting
    global recruiting_task

    #- linger
    time.sleep(LINGER_TIME)

    #- update the ants age as needed, and take any age appropriate action
    #-
    #- ant ages:  > 1 normal aging
    #-         : == 1 dying, may be probabilistic, check for death roll
    #-         : == 0 immortal
    #-  
    if age > 1: #- a normal aging ant
        age -= 1
    elif age == 1: #- a dying ant
        #- see if the ant will die by luck. Chance is influenced by both base death prob. and one based on crowding
        if random.random() < (death_chance) + CROWDING_BIAS * crowding_factor(task):
            msg = 'ant_id:%s %s:%s' % (ant_id,'event','dies')
            logger.info('[%s] %s',host_name, msg)
            return None
    elif age == 0: #- an "immortal" ant
        pass
    else: #- if here, age must be < 0 -- Error: age must be positive
        msg = "ant_id:%s %s:%s" % (ant_id, 'error', "age was ("+age+"), must be > 0")
        logger.error('[%s] %s',host_name, msg)
        return None

    #- if ant is dropping pheromone, update node with this
    #-   as reverse heading of travel
    #- ALT: save "found_at" location
    #-       
    #- four states: forage, drop, follow, idle
    
    #- ant is dropping . if still charged, drop and move on, 
    #-   otherwise stop dropping and go back to foraging
    if state==DROPPING:

    #- decrease the charge of the ant's marker reserve
        charge -= 1

        #- if charge is exhausted, switch the ant back to foraging,
        #- otherwise mark this node with the marker information
        if charge <= 0:
            #state = IDLE
            #charge = 10
            state = FORAGING
            charge = 0

            #- pick a new direction
            heading = int(random.uniform(0,360)) % 360

            notes = 'state_was:%s' % ('DROPPING')
            msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','change_state(FORAGING)',notes)
            logger.debug('[%s] %s',host_name, msg)

        else:
        #- charge still good, mark the spot
            node_pheromone['time_set'] = time.time()             #- time marker set, will control how long it persits
            node_pheromone['strength'] = max_pheromone_strength  #- how long marker will last in msecs
            node_pheromone['heading'] = (heading+180) % 360      #- set pheromone heading to reverse direction
            node_pheromone['came_from'] = came_from              #- prior host so ant can follow node-path back to reward
            node_pheromone['found_at'] = found_at                #- record actual loc of reward (maybe use to teleport)
            node_pheromone['dropped_by'] = ant_id                #- which ant dropped this, to prevent following own trail

            #- have pheromone trail point back here
            came_from = host_name
            
        #- continue on (foraging or dropping)
        heading,move_dir = compass.get_direction(heading,drop_perturb)

    elif state==FORAGING or state==FOLLOWING:

    #- save the old state information for logging purposes
        if state == FORAGING:
            old_state_name = 'FORAGING'
        else:
            old_state_name = 'FOLLOWING'

#        #- only follow for so long. use the charge value as the interest value.
#        #- if the ant doesn't find something soon enought it will lose interest
#        if state == FOLLOWING: 
#            charge -= 1
#            if charge <= 0:
#                state = FORAGING
#                notes = 'state_was:%s, new_charge=%s' % ('FOLLOWING',charge)
#                msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','change_state(FORAGING)',notes)
#                logger.info('[%s] %s',host_name, msg)
                
        if sensor_check(task,parms,ant_id):
  
            #-
            #- take appropriate action to remediate discovered problem
            #-
            if ACTIVE_RESPONSE is True:
                (result, alert, details) = response[task](1)
                if result == 'Y':
                    notes = "task:%s, details:%s" % (task,details)
                    msg = '%s:%s %s:%s notes:%s' % ('node_id', host_name,'event','response_taken',notes)
                    logger.info('[%s] %s',host_name, msg)
                elif result == 'N': #- responder decided no action needed
                    notes = "task:%s, details:%s" % (task,details)
                    msg = '%s:%s %s:%s notes:%s' % ('node_id', host_name,'event','nevermind',notes)
                    logger.info('[%s] %s',host_name, msg)
                elif result == None: #- no response supplied, just ignore
		    pass
                else:
                    notes = "task:%s, response:%s, details:%s" % (task,response,details)
                    msg = '%s:%s %s:%s notes:%s' % ('node_id', host_name,'error','unknown response value',notes)
                    logger.error('[%s] %s',host_name, msg)
                    
            #-
            #- report finding to Adbocate if it meets significance test
            #-
	    if alert != 0:
                notes = "task:%s, details:%s" % (task,details)
		msg = '%s:%s %s:%s notes:%s' % ('node_id', host_name,'alert',alert,notes)
		logger.info('[%s] %s',host_name, msg)

		if email_alerts is True:
                    subj = "on node: %s, sensor: %s" % (host_name,task)
		    message = "From: Hivemind <%s>\nTo: Hivemind Recipients\nSubject: Alert: %s\n\n%s\n.\n" % (sender,subj,msg)

		    try:
		        smtpObj = smtplib.SMTP()
                        smtpObj.set_debuglevel(1)
                        smtpObj.connect(email_server)
                        smtpObj.ehlo()
		        smtpObj.sendmail(sender, receivers, message)         
                        smtpObj.quit()
		        msg = "Successfully sent email"
			logger.info('[%s] %s',host_name, msg)
		    except smtplib.SMTPException:
		        msg = "Error: unable to send email"
			logger.error('[%s] %s',host_name, msg)
		    except socket.error, (value,message):
		        msg = "Error: connecting to mail server"
			logger.error('[%s] %s',host_name, msg)
            else:
	        pass

            #-
            #- report finding to Adbocate if it meets significance test
            #- **** THIS IS AN EXPERIMENT, NOT CCRENTLY USED
            #if significance(task) > 0:
            if False: #- for now, do not execute this block
                # create Internet TCP socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    if s:
                        s.connect((hmadv_addr, hmadv_port))

                        #- send message to Adbocate
                        hmadv_msg = "found: loc=%s, what=%s, when=%s, parms=(%s)" % (host_name,task,time.time(),parms)
                        fileobj = s.makefile('w',0)
                        fileobj.write(hmadv_msg)

                        #- close the socket (not to be used if proto is UDP)
                        s.close()     
                except socket.error, (value,message):
                    if s: 
                        s.close()
                        msg = "Could not open socket to Advocate" 
                        logger.error('[%s] %s',host_name, msg)
   
            if (ant_type == 1): #- normal ants that leave a marker trail             
                state = DROPPING
                charge = max_pheromone_charge
                found_at = came_from = host_name

            elif (ant_type == 2): #- wasp type ants that send out a pheromone cloud
	   	propagate_marker_msg(3,host_name,host_name,host_name)

            else: 
               msg = "unknown ant type (%s)" % (ant_type)
               logger.error('[%s] %s',host_name, msg)

            #- something was found, start recruiting more to find the same thing.
            #-  -- that is, this node is recruiting for the task last found here.
            recruiting = recruitment_duration #- refresh recruitment period
            recruiting_task = task #- set to task to sensor target we just found

            #- after finding something, head out in a random direction
            heading = int(random.uniform(0,360)) % 360

            notes = 'state_was:%s, found_at:%s, new_charge=%s, new_heading:%s' % (old_state_name,found_at,charge,heading)
            msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','change_state(DROPPING)',notes)
            logger.info('[%s] %s',host_name, msg)
        
        else:
            #- nothing was found

            #- see if we need the ant to be recruited to look for a particular issue
            if state == FOLLOWING and recruiting > 0 and focus > 0:
                if random.random() < recruitment_probability:
                    task = recruiting_task
                    focus = recruiting_focus
                    msg = "recruiting ant %s to task %s" % (ant_id, task)
                    logger.info('[%s] %s',host_name, msg)
                
            #- see if ant gives up on what it is looking for and changes to a different task
            if focus == 1:
                if random.random() < default_focus_change_prob:
                    task = random.choice(sensor.keys())
                    focus = default_focus
                    msg = "recruiting ant %s to task %s -- FOCUS" % (ant_id, task)
                    logger.info('[%s] %s',host_name, msg)
            if focus < 1:
                pass
            else:
                focus -= 1 # decrement focus
            
            #- nothing was found, see if there is a marker here, if so
            #- maybe follow it, unless this ant dropped it
            if node_pheromone != {} and node_pheromone['dropped_by'] != ant_id:
                #-
                #- pheromone was found. See if ant follows (or continues to follow)
                #- the trail.
                #-
                if random.uniform(0,1) < follow_chance:
                    
                    #- follow pheromone path
                    heading = node_pheromone['heading']
                    move_dir = node_pheromone['came_from']
                    found_at = node_pheromone['found_at']

                    charge = 0  #- this was used to limit the range of a following ant

                    if state == FORAGING: #- we start following a trail
                        state = FOLLOWING

                        notes = 'state_was:%s, new_heading:%s' % ('FORAGING',heading)
                        msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','change_state(FOLLOWING)',notes)
                        logger.info('[%s] %s',host_name, msg)

            else:
                #- no pheromone on node

                #- ant decided to not follow trail or if it was following decided to stop following it
                if state == FOLLOWING:
                #- note: if for some reason the ant moves off the pheromone path,
                #-       it needs to leave following state. But  we'll keep it tracking in the 
                #-       same heading.
                    state = FORAGING
                      
                    notes = 'state_was:%s, new_heading:%s' % ('FOLLOWING',heading)
                    msg = '%s:%s %s:%s notes:%s' % ('ant_id', ant_id,'event','change_state(FORAGING)',notes)
                    logger.info('[%s] %s',host_name, msg)
                    
        #- continue foraging
        if state == FORAGING:
            heading,move_dir = compass.get_direction(heading,forage_perturb)
        else:
            heading,move_dir = compass.get_direction(heading,follow_perturb)

    elif state==IDLE:
        #- just keep moving don't do anything else
        heading,move_dir = compass.get_direction(heading,forage_perturb)
        charge =- 1
        if charge <=1:
            state = FORAGING
                      
    dest = neighbors[move_dir];

    send_ant(dest, ant_id, ant_type, heading, task, parms, focus, flt_len, flt_cnt, age, state, charge, host_name, found_at)   
    
    return dest




def propagate_marker_msg(count, direct_to, found_at, exclude_list):

    count = int(count)

    #- get list of neighbors
    neighbor_list = neighbors.values()

    excludes = dict([x,1] for x in exclude_list.split(';'))

    #- make new exclude list by add all neighbors to current exclude list
    new_exclude_list = {}
    for nbr in excludes:
        new_exclude_list[nbr] = 1
    for nbr in neighbor_list:
	new_exclude_list[nbr] = 1 
    new_excludes = ';'.join(new_exclude_list)     
 
    for next_dir in neighbors.keys():
        nbr = neighbors[next_dir]
        if nbr not in excludes.keys():

            #- calculate heading back to here from where message will be sent
            d = (int(compass.rosette[next_dir][0]) + int(compass.rosette[next_dir][1]) )/2
            heading_back = (d+180)%360

            #- send propagating marker message to neighbor
            prop_msg = "propmkr:%s,%s,%s,%s,%s" % (count, heading_back, host_name, found_at, new_excludes)
            logger.debug('[%s] %s',host_name, prop_msg)
    
	    # create Internet TCP socket
	    try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if s:
		    s.connect((nbr, node_mgr_port))

		    #- send message to Adbocate
		    fileobj = s.makefile('w',0)
		    fileobj.write(prop_msg)

		    #- close the socket (not to be used if proto is UDP)
		    s.close()     
	    except socket.error, (value,message):
		if s: 
		    s.close()
		    msg = "Could not open socket sending propagate messate to " + nbr 
		    logger.error('[%s] %s',host_name, msg)

	



def evaporate_marker(marker):
    #- determine current strength of marker and if it has disapated completely
    around_this_long = (time.time() - marker['time_set'])
    marker['strength'] = max_pheromone_strength - around_this_long
    if marker['strength'] <= 0: 
	return True
    else:
        return False

#- end :: evaporate_marker()                
           

#  signal.signal(signal.SIGINT, signal_handler)
def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    sys.stderr = original_stderr
    log_stderr_f.close() 
    sys.exit(0)


if __name__ == "__main__":    

  #- !!! NOTE: See about changing this to use the collections/deque methods
  my_rt = RollingTotal(NUM_BINS,GRANULARITY)
 
  #-
  #- initialize signal handler to catch ^C (aka SIGINT)
  #-
  signal.signal(signal.SIGINT, signal_handler)
 
  #-
  #- get the name of this host (aka node)
  #- this may return the fully qualified host name
  #-
  fq_host_name = socket.gethostname()

  #- 
  #- Initialize the logger
  #-
  logger_node = config.get('NodeMgr','logger_node')  # 'Advocate'
  logger_port = config.getint('NodeMgr','logger_port')  # 514 -- default syslog port

  logger = logging.getLogger('MyLogger')
  logger.setLevel(logging.INFO)
  f = logging.Formatter("%(created)s %(levelname)-9s %(message)s")
  #- write to logger for log_local7 ( = 23)
  logger_address = logger_node
  
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

  """
  #- define location of syslog server

  f = logging.Formatter("%(created)s %(levelname)-9s %(message)s")
  logger = logging.getLogger('')
  logger.setLevel(logging.DEBUG)
  h = logging.FileHandler(logdir+'/log.all', 'w')
  h.setFormatter(f)
  logger.addHandler(h)

  h = logging.handlers.SocketHandler('localhost', logging.handlers.DEFAULT_UDP_LOGGING_PORT)
  h.setFormatter(f)
  logger.addHandler(h)
  #h = logging.FileHandler(logdir+'/log.'+fq_host_name, 'w')
  #h = logging.handlers.DatagramHandler('localhost', logging.handlers.DEFAULT_UDP_LOGGING_PORT)
  
  h = logging.handlers.SysLogHandler(address=('localhost', SYSLOG_UDP_PORT), facility=LOG_USER, socktype=socket.SOCK_DGRAM) 
  h.setFormatter(f)
  logger.addHandler(h)
  """
  #-
  #- extract then 'node-#' part from the fully qualified host name
  #-
  matchObj = re.match('\s*(node-\d+).*',fq_host_name)
  if matchObj:
      host_name = matchObj.group(1)
  else:
      notes = sys.exc_info()[0]
      msg = "unable to extract node name"
      logger.error('[%s] <%s> notes:%s',fq_host_name, msg, notes)
      sys.exit(1)
  
  #-
  #- create an id for this node based on its node number
  #-
  node_mgr_id  = int(host_name[host_name.index('-')+1:]) 

  #- initialze the random numbers to a fixed (i.e. repeatable value)
  #- >> if it is zero, then don't bother just accept it as is (i.e. random!)
  if rgenseed != 0:
      random.seed(rgenseed+node_mgr_id)

  #- make a note in the log file when this node manager started
  msg = "starting node manager"
  logger.debug('[%s] %s',host_name, msg)
   
  #- 
  #- make a note in the log file of the port it is listening on for 
  #-   ant and control messages
  #_
  msg = "listening on port %d" % (node_mgr_port)
  logger.debug('[%s] %s',host_name, msg)

  #-
  #- initialize the navigation module  
  #-
  compass = Compass(DIRECTIONS)

  #-
  #- initialize the nodes neighbors based on the directions specified in the config
  #-
  neighbors = compass.init_neighbors()
  msg = "neighbors:"+compass.str_spec % neighbors
  logger.debug('[%s] %s',host_name, msg)


  #- start the thread to create ants when density is too low
  if CREATE_ANTS:
      thread.start_new_thread(ant_genesis,())
 
   
  #- MAIN LOOP
  #------------------------------------------------------------------------------
  #------------------------------------------------------------------------------

  # listen for connections
  try:
    # create Internet TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(backlog)
  except socket.error, (value,message):
    if s: 
        s.close()
    msg = "Could not open socket: " + message
    logger.error('[%s] %s',host_name, msg)
    sys.exit(1)


  Running = True

  while Running:
    msg = "waiting for data..."
    logger.debug('[%s] %s',host_name, msg)
    
    client, address = s.accept()
    data = client.recv(size)
    
    if data:
        notes = "data received:(from: %s, %d bytes) [%s]" % (address, len(data), data)
        msg = '%s:%s %s:%s notes:%s' % ('node_info', host_name, 'event','data-received', notes)
        logger.debug('[%s] %s',host_name, msg)

        while True:
            #-
            #- ant message: [ant_id, age, heading, state, pheromone] 
            #-
            matchObj = re.match('^ant:\s*(?P<ant_id>\d+),\s*(?P<ant_type>\d+),\s*(?P<age>\d+),\s*(?P<heading>\d+),\s*(?P<state>\d+),\s*(?P<task>\d+),\s*(?P<parms>.*),\s*(?P<focus>.*),\s*(?P<flt_len>\d+),\s*(?P<flt_cnt>\d+),\s*(?P<charge>\d+),\s*(?P<came_from>.+),\s*(?P<found_at>.*)',data)
            if matchObj:
                ant_info = {}
                ant_info['ant_id']     = int(matchObj.group('ant_id'))

                #- kill all ants if we're in that mood
                #- note: this will even kill the immortal ants
                if node_state == KILLING:
                    msg = 'ant_id:%s %s:%s' % (ant_info['ant_id'],'event','dies')
                    logger.info('[%s] %s',host_name, msg)
                    break

                #- ant not killed, so go ahead and parse out the rest of the ant info
                ant_info['ant_type']   = int(matchObj.group('ant_type'))
                ant_info['age']        = int(matchObj.group('age'))
                ant_info['heading']    = int(matchObj.group('heading'))
                ant_info['state']      = int(matchObj.group('state'))
                ant_info['task']       = matchObj.group('task')
                ant_info['parms']      = matchObj.group('parms')
                ant_info['focus']      = int(matchObj.group('focus'))
                ant_info['flt_len']    = int(matchObj.group('flt_len'))
                ant_info['flt_cnt']    = int(matchObj.group('flt_cnt'))
                ant_info['charge']     = int(matchObj.group('charge'))
                ant_info['came_from']  = matchObj.group('came_from')
                ant_info['found_at']   = matchObj.group('found_at')

                dir_back = compass.get_direction_to_neighbor(ant_info['came_from'])

                ant_msg = 'ant:%(ant_id)d,%(ant_type)d,%(age)d,%(heading)d,%(state)d,%(task)s,%(parms)s,%(focus)s,%(flt_len)d,%(flt_cnt)d,%(charge)d,%(dir_back)s,%(found_at)s' \
                    % {'ant_id':ant_info['ant_id'],'ant_type':ant_info['ant_type'],'age':ant_info['age'],'heading':ant_info['heading'],'state':ant_info['state'],'task':ant_info['task'],'parms':ant_info['parms'],'focus':ant_info['focus'],'flt_len':ant_info['flt_len'],'flt_cnt':ant_info['flt_cnt'],'charge':ant_info['charge'],'dir_back':dir_back,'found_at':ant_info['found_at']}

                notes = "ant_id:%s, from: %s, [%s]" % (ant_info['ant_id'], ant_info['came_from'], ant_msg)
                msg = '%s:%s %s:%s notes:%s' % ('node_info', host_name, 'event','ant-received', notes)
                logger.info('[%s] %s',host_name, msg)

                if recruiting > 0:
                    recruiting -= 1
    
                #- update the count of ants observed
                #- -- used to determine when to create more ants or increase likelihood of death
                #-
                #- update number of ants seen to infer ant density    
                #-
                t = my_rt.rt_inc_count(time.time())

                new_loc = handle_ant(ant_info)

                """
        if node_state is WAITING:
                    #- push the ant in a queue for later
                    waiting_ants.append(ant_info)
                    msg = '%s:%s %s' % ('ant_id',ant_info['ant_id'], 'added to waiting queue')
                    logger.info('[%s] %s',host_name, msg)
                else:
                    waiting_ants.append(ant_info)
                    while True:
                        try: 
                            ant_info=waiting_ants.popleft()
                            #- process the ant: 
                            #-   look for stuff, update state, and get next location                
                            new_loc = handle_ant(ant_info)
   
                            # *** THIS IS OLD. NOT SURE HOW IT WAS USED 
                            # this_ant = str(ant_info['ant_id'])
                            # if new_loc == None:
                            #     msg = "ant "+this_ant+" died on node "+host_name
                            # else:
                            #     msg = host_name+" sent ant "+this_ant+" to "+new_loc
                            #   
                            # #- reply to sender with response
                            # client.send(msg)
                        except IndexError:
                             #- queue is empty
                             break
                """

                #- this commnad is done, exit the parse loop and wait for more input
                break

            #-
            #- request to perform a specific sensor function 
            #- -- primarily used for "scatter/gather" testing and testing
            #-                
            matchObj = re.match('^check:\s*(\w+)\s*',data)
            if matchObj:
                sensor_name = matchObj.group(1)
                msg = ">>> checking sensor function: ", sensor_name
                logger.debug('[%s] %s',host_name, msg)
            
                result = sensor_check(sensor_name,'','???')
                if result:
                    msg = "+found"
                else:
                    msg = "+not_found"
        
                #- reply to sender with response
                client.send(msg)
                break;
        
 
            #-
            #- status request message
            #- -- returns list of neighbors, and marker information
            #- -- should be updated to return other status
            #-                
            matchObj = re.match('^status:',data)
            if matchObj:
                msg = "status: %(host_name)s " % { 'host_name':host_name }
                if neighbors:
                    msg += compass.str_spec % neighbors
                else:
                    msg += " [-,-,-,-] "
                
                if node_pheromone:
                    msg += "[%(strength)d,%(heading)d,%(came_from)s,%(found_at)s,%(dropped_by)s]" % node_pheromone
                else:
                    msg += "[-,-,-,-,-]"
                msg += "\n"

                #- reply to sender with response
                client.send(msg)
                logger.info('[%s] %s',host_name, msg)
                break
            
        
            #-
            #- "ping" just reply ok and the nodes name
            #-                
            matchObj = re.match('^ping:',data)
            if matchObj:
                msg = 'ok,'+host_name
                logger.info('[%s] %s',host_name, msg)
        
                #- reply to sender with response
                client.send(msg)
                break;
            
        
            #-
            #- "opt" change value of running parameters
            #-                
            matchObj = re.match('^opt:\s*(\w+)=(.*?)\s*',data)
            if matchObj:
                option_name = matchObj.group(1)
                option_value = matchObj.group(2)
                msg = "opt:%s  value:%s" % (option_name,option_value)
                logger.info('[%s] %s',host_name, msg)
        
                if option_name == "DESIRED_ANT_DENSITY":
                    DESIRED_ANT_DENSITY = option_name
                    ANT_COUNT_TARGET = (DESIRED_ANT_DENSITY * AVERAGE_OVER_k_SECS) / OBSERVATION_PERIOD
                else:
                    msg = "invalid option name:%s\n" % (option_name)
                    logger.error('[%s] %s',host_name, msg)
                    
                #- reply to sender with response
                client.send(msg)
                break;

        
            #-
            #- hello message
            #-                
            matchObj = re.match('^hello',data)
            if matchObj:
                msg = "hello from "+ host_name +"\n"
                logger.info('[%s] %s',host_name, msg)
        
                #- reply to sender with response
                client.send(msg)
                break
            
        
            #-
            #- new function definition ( from Adbocate ) 
            #-                
            matchObj = re.match('^fndef:\s*(.+)?,\s+(.+)\s*',data)
            if matchObj:
                sensor_task = matchObj.group(1)
                sfunc_def = matchObj.group(2)
                msg = "Got new sensor func definition: task=",sensor_task,"  [",sfunc_def,"]\n"
                logger.info('[%s] %s',host_name, msg)
                sensor[sensor_task] = lambda parms : eval(sfunc_def)
        
                #- reply to sender with response
                client.send(msg)
                break
            
        
            #-
            #- propagating marker message 
            #-                
            matchObj = re.match('^propmkr:\s*(.*?),\s*(.*?),\s*(.*?),\s*(.*?),\s*(.*?)\s*',data)
            if matchObj:
                prop_cnt = int(matchObj.group(1))
                heading_back = int(matchObj.group(2))
                came_from = matchObj.group(3)
                found_at = matchObj.group(4)
                exclude_list = matchObj.group(5)

                #- only set pheromone on the cells not already set or the target cell
                if found_at != host_name:
                    
                    if not ('strength' in node_pheromone) or node_pheromone['strength'] <= 0: #- marker not already set 
			#- mark the spot pointing back toward the sender
			node_pheromone['time_set'] = time.time()             #- time marker set, will control how long it persits
			node_pheromone['strength'] = int(max_pheromone_strength*type_2_strength_factor)  #- how long marker will last in msecs
			node_pheromone['heading'] = heading_back             #- set pheromone heading to reverse direction
			node_pheromone['came_from'] = came_from              #- prior host so ant can follow node-path back to reward
			node_pheromone['found_at'] = found_at                #- record actual loc of reward (maybe use to teleport)
			node_pheromone['dropped_by'] = '0000'                #- no ant involved, so use '0000' assume no ant will have that id
			notes = "came_from:%s, heading:%s, found_at:%s, cnt:%d, excludes:%s"% (came_from, heading_back, found_at, prop_cnt,exclude_list)
			msg = '%s:%s %s:%s notes:%s' % ('node_id',host_name,'event','marker_set',notes)
			logger.info('[%s] %s',host_name, msg)

	        if prop_cnt > 0:
	   	    propagate_marker_msg(prop_cnt-1,host_name,found_at,exclude_list)
                    
		break 


            #-
            #- got a neighbor assignment message
            #-    
            rgx_spec = '(?P<' + '>.+)?,\s*(?P<'.join(DIRECTIONS.split()) + '>.+)?\s*'

            matchObj = re.match('^dir:\s*'+rgx_spec,data)
            if matchObj:
                for d in neighbors:
                    neighbors[d] = matchObj.group(d)

                msg = "ack:%s " % host_name
                msg = msg + compass.str_spec+"\n" % neighbors
                logger.info('[%s] got-links, %s',host_name, msg)
        
                #- reply to sender with response
                client.send(msg)
                break
            
            #-
            #- got a shutdown message
            #-    
            matchObj = re.match('^quit\s*',data)
            if matchObj:
                msg = "ok: node %s shutting down\n" % (host_name)
                logger.info('[%s] %s',host_name, msg)
        
                #- reply to sender with response
                client.send(msg)
                
                #- do any clean up here
                Running = False
                break
            
            #-
            #- got a wait message
            #-    
            matchObj = re.match('^wait:',data)
            if matchObj:
                msg = "changing to wait state"
                logger.info('[%s] %s',host_name, msg)

                node_state = WAITING
                break

            #-
            #- got a run message
            #-    
            matchObj = re.match('^run:',data)
            if matchObj:
                msg = "changing to run state"
                logger.info('[%s] %s',host_name, msg)

                node_state = RUNNING
                break
            
            #-  
            #- got a kill message
            #-    
            matchObj = re.match('^kill:',data)
            if matchObj:
                msg = "changing to killing state"
                logger.info('[%s] %s',host_name, msg)

                node_state = KILLING
                break

            #-
            #- got a reset message
            #-    
            matchObj = re.match('^reset:\s*(\d*)\s*',data)
            if matchObj:
                pause_time = matchObj.group(1)
                msg = "pausing for [%s] seconds, then will restart" % (pause_time)
                logger.info('[%s] %s',host_name, msg)

                #- stop logging, wait, restart process
                time.sleep(pause_time)
                my_prog = sys.executable()
                os.execl(my_prog, my_prog, * sys.argv) #- this does not return
            
            #-
            #- got a set target message
            #-    
            matchObj = re.match('^set_t:\s*(\d*),\s*(\s*)$',data)
            if matchObj:
                sensor_func_id = matchObj.group(1)
                sensor_func_parms = matchObj.group(2)
                msg = "action: set attack target #%s on node %s" % (sensor_func_id,host_name)
                logger.info('[%s] %s',host_name, msg)

                #- call set target function for specifed sensor function
                (result, details) = set_target[sensor_func_id](1)

                break
            
            #-
            #- got a set target message
            #-    
            matchObj = re.match('^unset_t:\s*(\d*),\s*(\s*)$',data)
            if matchObj:
                sensor_func_id = matchObj.group(1)
                sensor_func_parms = matchObj.group(2)
                msg = "action: unset attack target #%s on node %s  *** NOT YET IMPLEMENTED" % (sensor_func_id,host_name)
                logger.info('[%s] %s',host_name, msg)

                #- call unset target function for specifed sensor function
		try:
                    (result, details) = unset_target[sensor_func_id](1)
                except: #- for now, just ignore errors
                    pass 

                break
            
            #-
            #- got a NAK message
            #-    
            matchObj = re.match('^NAK:\s*(.*)\s*',data)
            if matchObj:
                bad_msg = matchObj.group(1)
                msg = "message [%s] sent to %s was not understood" % (bad_msg,address)
                logger.info('[%s] %s',host_name, msg)
               
                #- do not ACK, just exit (to prevent ping/pong loops) 
                break
            
            #-
            #- unknown command
            #-
            msg = "NAK:("+ data +")"
            logger.warn('[%s] %s',host_name, msg)
        
            #- reply to sender with response
            client.send(msg)
        
            break
        #- end of command parsing block
    #- end :: if data
    

    #- either no data, or data was handled, close the connection to the sender, 
    if node_pheromone:                
	if evaporate_marker(node_pheromone):
	    #- log that the marker is gone
	    notes = 'was_leading_to:%s' % (node_pheromone['came_from'])
	    msg = '%s:%s %s:%s notes:%s' % ('node_id',host_name,'event','marker_fades_to_zero',notes)
	    logger.info('[%s] %s',host_name, msg)

	    #- delete it from the node
	    node_pheromone = {}
	
    #-   and return to top of loop to wait for new connnections
    time.sleep(0.01)
    client.close()


  #- we're done close the log file
  msg = "Exiting node manager"
  logger.info('[%s] %s',host_name, msg)
