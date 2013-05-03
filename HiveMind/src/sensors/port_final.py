#! /usr/bin/env python
"""
Detect Unexpected open port
"""

from  sensor_spec import SensorSpec, return_values, sensor_list, NEW_BASELINE
import hashlib
import os
import re

sensor_name = "unexpected_port"

update_on_fail = False
enabled = True

class Unexpected_Port(SensorSpec):
#- default enable state on initialization
    def __init__(self, name, enabled=True):
        super(Unexpected_Port, self).__init__(name, enabled)
        print ">>> INITING UNEX_PORT"

    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define data collection function
    #-
    #- i.e. how to collect and parse/format the relevant data
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #def append_data( protocol, interface, pid, program_name )
        
    def append_data(self, protocol, interface, local_port, program_name):
        return (protocol + ' ' + interface + ' ' + local_port + ' ' + program_name)
    
    def collect(self, parms):
        collected = ''
        #- get the data
        try:
        #import os
        #import md5
            from subprocess import Popen, PIPE
            stdout = Popen('sudo netstat -l4np', shell=True, stdout=PIPE).stdout
            output = stdout.read()
        #output1=output.split("\n")
            for line in output.split("\n"):
        #- EXAMPLE INPUT
        #Active Internet connections (only servers)
        #Pro    to Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
                #tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN      1019/cupsd      
                #tcp        0      0 0.0.0.0:17500           0.0.0.0:*               LISTEN      1897/dropbox    
                #udp        0      0 0.0.0.0:47422           0.0.0.0:*                           737/avahi-daemon: r
        # See if it matches an IPv4 TCP entry
                protocol = 'tcp'
                m = re.match(r"^\s*%s\s+\d+\s+\d+\s+(.+?):(\d+)\s+\S+\s+\S+\s+(\d+)/(.*)$" % (protocol), line)
                if m:
                    interface = m.group(0)
                    local_port = m.group(1)
                    pid = m.group(2)
                    program_name = m.group(3)
                    collected += self.append_data(protocol, interface, local_port, program_name) + '\n'
                    self.cur_data['data']['parsed'][self.append_data(protocol, interface, local_port, program_name)] = pid #- << need to write this function 
                    continue

                # See if it matches an IPv4 UDP entry
                protocol = 'udp'
                m = re.match(r"^\s*%s\s+\d+\s+\d+\s+(.+?):(\d+)\s+/S+\s+(/d+)/(.*)$" % (protocol), line)
                if m:
                    interface = m.group(0)
                    local_port = m.group(1)
                    pid = m.group(2)
                    program_name = m.group(3)                
                    #collected+=protocol+' '+ interface+' '+ pid+' '+ program_name+'\n' #- << need to write this function 
                    collected += self.append_data(protocol, interface, local_port, program_name) + '\n'
                    
                    self.cur_data['data']['parsed'][self.append_data(protocol, interface, local_port, program_name)] = pid 
                    continue

                # See if it matches an IPv6 TCP entry
                # ???  

                # See if it matches an IPv6 UDP entry
                # ???  

                #- matched nothing, so just ignore
                continue
                # << add comment explaining the format you are building >>
                # >> formatted_entry = protocol+' '+interface+' '+pid+' '+program_name )
                #formatted_entry = ' '.join( (protocol, interface, pid, program_name) )
                #base.append( formatted_entry)
            #collected = '\n'.join( base )
            checkval = hashlib.md5(collected).hexdigest()

            self.cur_data['md5'] = checkval
            self.cur_data['data']['raw'] = collected
            return True

        #- if issues, handle them here
        except:
            self.cur_data['md5'] = ''
            self.cur_data['data'] = ''
            return False


    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define data compare function
    #-
    #- i.e. how to compare collected data to baseline for relevant differences
    #- returns True if differences were found
    #- sets class variable variable 'difference_data' to differences found and any other
    #-   information needed by the response functions.
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def compare(self, observed, reference):
        found = {}
        self.difference_data = {}

        #-- return True if changes were found
        #-- save difference information (e.g. to support response) in 'difference_data'
        if observed['md5'] == reference['md5']:
        #- checksums match, assume collected matches baseline
            return False
        else:
            #return True 

        #- checksums do not match, determine what has changed and save this for
        #- use in response.
        #- note: not all sensors will have a response

            #- get set of baseline open ports
            bas_names = {}
            for x in observed['data']['parsed']:
                if not x in reference['data']['parsed']:
                    found[x] = observed['data']['parsed'][x]
            self.message = "unexpected port found"
            self.difference_data = found
            return True


    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define 'undo' function
    #-
    #- i.e. how to undo the problem created by the 'target' function.
    #- its purpose is to support unit testing. Though not intended as a true response
    #-
    #- *** this should never be null ***
    #-
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def undo_target(self, parms=None):
        rv = 0 #- initialize to zero in case the response will be null (e.g. nothing to change)
        
        #- this section is to remove all the open ports found in the difference using
        #-     the 'pid' in the collected data
        if parms is None:
            print "IN UNDO, Ports=(None)"  #- << parms is list of ports to kill
            print "difference =(", self.difference_data, ")"
            
            for x in self.difference_data:
                print "----	>> ", self.difference_data

                pid = self.difference_data[x]
                cmd = "sudo kill -9 " + pid
                print "? ?    >>", cmd
                rv = os.system(cmd)
                
        else: 
        	#- alternative list of response items (??? do we need this ???)
            # this section is used to remove a list of explicit ports. It requires finding the 
            #-     correct pid for the port, then killing that pid
            print "IN UNDO, Ports=(", parms, ")" 
            for port in parms:
                #-- find process associated with the port
                # ? tbd ?
                print "----    >> ", self.difference_data
                pid = self.difference_data[port]

                cmd = "sudo kill -9 " + pid
                print "? ?	>>", cmd
                rv = os.system(cmd)
 
        return rv == 0 #- if rv is 0 all is well

    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define 'target' function --
    #-
    #- i.e. how to generate a test condition that the 'sensor' can detect
    #-
    #- when possible and feasible, the 'response' function should deal with this.
    #- the 'undo' function should be able to undo the changes to the
    #- system made by this function (relative to the baseline)
    #- this is to prevent repeated triggers on the target
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def set_target(self, parms):
        cmd = "sudo nc -l " + parms + ' &'
        print "? ?    >>", cmd
        return os.system(cmd)




#----------------------------------------------------------------------------------------------------------------------
# If this is run as a stand-alone program, perform unit testing
#----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import shelve
    from time import sleep

    #- create an instance of this sensor
    ss = Unexpected_Port(sensor_name);

    if len(sys.argv) > 1 and sys.argv[1] == 'B':
    #- just compare current state to persistent baseline. If no baseline, report this and exit.
        db = shelve.open('sensor-baseline')
        if ss.name in db:
            rv = ss.sensor('')
            print "persist check: {%s}" % (ss.return_values[rv])
        else:
            print "ERROR: persistent baseline does not exist"
        db.close()

    else:
    #- run sequence of tests, first delete persistent baseline for this sensor if it exists

        print "Running unit tests for sensor '%s'" % (ss.name)

        step = 0
    
        #- if persistent baseline exists, remove it for this sensor and continue
        print "* >    reset baseline"
        ss.reset_baseline()
    
        print "* >    first check after reset"
        #- now that baseline has been created, check for changes
        sleep(1)
        rv = ss.sensor('')
        step += 1
    
        #- check again
        sleep(1)
        rv = ss.sensor('')
        print "* %d: stability check #1: {%s}" % (step, return_values[rv]),
        if rv != 0: 
            print "-- Fail --"
            print "!!!! Error: expected no change"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- check again
        sleep(1)
        rv = ss.sensor('')
        print "* %d: stability check #2: {%s}" % (step, return_values[rv]),
        if rv != 0: 
            print "-- Fail --"
            print "!!!! Error: expected no change"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- create a detectable situation
        sleep(1)
        rv = ss.set_target('2393')
        print "* %d: create detectable situation: {%s}" % (step, ('Ok', 'Error')[rv == True]),
        if rv != False: 
            print "-- Fail --"
            print "!!!! Error: set target failed"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- recheck to verify problem exists
        sleep(1)
        rv = ss.sensor('')
        print "* %d: verify target situation exists: {%s}" % (step, return_values[rv]),
        if rv != 1: 
            print "-- Fail --"
            print "!!!! Error: expected change to be observed"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- default response is to remove the problem
        sleep(1)
        rv = ss.response(None)
        print "* %d: test response: {%s}" % (step, ('Error', 'Ok')[rv]),
        if rv != True: 
            print "-- Fail --"
            print "!!!! Error: failed response"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- recheck to verify that the problem has been resolved
        sleep(1)
        rv = ss.sensor('')
        print "* %d: reverify target situation has been removed: {%s}" % (step, return_values[rv]),
        if rv != 0: 
            print "-- Fail --"
            print "!!!! Error: expected no change from baseline (after cleanup)"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
    
        #- call the undo function to clean-up (just in case the response was inadequate for this)
        sleep(1)
        rv = ss.undo_target(['2393'])
        print "* %d: verify cleanup did not fail: {%s}" % (step, rv),
        if rv == False: 
            print "-- Ok - nothing to do --"
        else: 
            print "-- OK - 'undo' removed lingering target --"
        step += 1
    
        #- check undo, just cuz...
        sleep(1)
        rv = ss.sensor('')
        print "* %d: reverify target situation has been removed: {%s}" % (step, return_values[rv]),
        if rv != 0: 
            print "-- Fail --"
            print "!!!! Error: expected no change from baseline (after verify undo)"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
        step += 1
        
        print "<< done >>"


else:
    #- if this module is imported, initialize an instance of it and add it to the master sensor list
    if sensor_name in sensor_list:
        print "Named sensor '%s' already defined" % (ss.name)
        False
    else:
        ss = Unexpected_Port(sensor_name);
        sensor_list[ss.name] = ss
        True
