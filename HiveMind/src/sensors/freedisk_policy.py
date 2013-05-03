#! /usr/bin/env python
"""
Detect Unexpected User Account
"""

from  sensor_spec import SensorSpec, return_values, sensor_list, NEW_BASELINE
import hashlib
import os
from subprocess import call
import re
import string

sensor_name = "free_disk" 

update_on_fail = False
enabled = True
    
class Free_Disk(SensorSpec):
#- default enable state on initialization
    def __init__(self, name, enabled=True):
        super(Free_Disk, self).__init__(name, enabled)
        print ">>> INITING Free_Disk"
    
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define data collection function 
    #-
    #- i.e. how to collect and parse/format the relevant data
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def collect(self, parms):
        #- get the data
        try:
            collected = os.statvfs("/")
            self.cur_data['data'] = collected

        #- if issues, handle them here
        except:
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
        #- Example policy : Decrease in free blocks by 10,000 or something like 40 MB I believe since block size is 4K
        block_diff = abs(observed['data'].f_bfree - reference['data'].f_bfree) 
        if block_diff < 10000:
            return False
        else:
            found['difference'] = str(observed['data'].f_bfree - reference['data'].f_bfree)
            if long(found['difference'] < 0):
                self.message = "Something is missing. Change in #free_blocks found : "
            else:
                self.message = "Something entered. Change in #free_blocks found : "
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
        rv = 0 #- initialize to zero incase the response will be null (e.g. nothing to change)
        rv = os.system("sudo rm -f test_policy")    
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

        return os.system("sudo dd if=/dev/zero of=test_policy bs=4096 count=12000")
     
        
        

#----------------------------------------------------------------------------------------------------------------------
# If this is run as a stand-alone program, perform unit testing
#----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import shelve
    from time import sleep
    
    #- create an instance of this sensor
    ss = Free_Disk(sensor_name);

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
        rv = ss.set_target('BADUSER')
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
        rv = ss.response({})
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
        rv = ss.undo_target(None)
        print "* %d: verify cleanup did not fail: {%s}" % (step, rv),
        if rv != True: 
            print "-- Fail --"
            print "!!!! Error: failed cleanup (undo)"
            print "!!!! ** exiting early **"
            sys.exit()
        else:
            print "-- Ok --"
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
        ss = Free_Disk(sensor_name);
        sensor_list[ss.name] = ss
        True
    
            

