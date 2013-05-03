#! /usr/bin/env python
"""
Detect Unexpected User Account
"""

from  sensor_spec import SensorSpec, return_values, sensor_list, NEW_BASELINE
import hashlib
import os

sensor_name = "unexpected_user_args" 

#sensor_type : arguments hardcoded
# 0$<anything> - MD5 comparison only
# 1$<anything> - user list comparison
# 2$<username_to_check> - Check particular user

sensor_type = "2$BADDUDE"

#stripped as [type,username(in relevant modes)]
sensor_mode = sensor_type.split("$")
 
update_on_fail = False
enabled = True
    
class Unexpected_User(SensorSpec):
#- default enable state on initialization
    def __init__(self, name, enabled=True):
        super(Unexpected_User, self).__init__(name, enabled)
        print ">>> INITING UNEX_USER"
    
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
            collected = open("/etc/passwd").read()
            checkval = hashlib.md5(collected).hexdigest()
            self.cur_data['md5'] = checkval
            self.cur_data['data'] = collected

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

	#- Checks if username sensor is looking for already is in baseline
            if sensor_mode[0] == "2":
		    bas_names = {}
		    for x in reference['data'].splitlines():
		        y = x.split(':')
		        bas_names[y[0]] = None
		    uname = sensor_mode[1]
		    if uname in bas_names:
		        print "user '%s' is in baseline !!!" % (uname)
		   	return True
		    else:
			return False
        
	else:	
        #- checksums do not match, determine what has changed and save this for
        #- use in response.
        #- note: not all sensors will have a response
    
            #- get set of baseline usernames
	    self.message = "unexpected user account found" 		
	    
	#- Returns after MD5 failed    
	    if sensor_mode[0] == "0":		
		return True
	#- Returns after the user names that have been found new were stored    
            if sensor_mode[0] == "1":	
		    bas_names = {}
		    for x in reference['data'].splitlines():
		        y = x.split(':')
		        bas_names[y[0]] = None
	    
		    #- see if any observed user accounts are NOT in the baseline
		    for x in observed['data'].splitlines():
		        y = x.split(':')
		        uname = y[0]
		        if not uname in bas_names:
		            print "user '%s' not in baseline" % (uname)
		            found[uname] = y[1:]

		    self.message = "unexpected user account found"    
		    self.difference_data = found
		    return True

	#- Doesn't care about any other new users other than the one is argument
	    if sensor_mode[0] == "2":
			# user name in argument
		    uname = sensor_mode[1] 

		    bas_names = {}
		    for x in observed['data'].splitlines():
		        y = x.split(':')
		        if uname == y[0]:
				print "user '%s' is not in baseline but in observed list" % (uname)
			       	self.message = "unexpected user account found " + uname 
				found[uname] = y[1:]				
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
        if parms is None:
            print "IN UNDO, USER=(none)"
            print "difference =(", self.difference_data, ")"
            for user in self.difference_data:
                rv = os.system("sudo userdel " + user)
                print "undo 1: (%s) rv=%s" % (user, rv)
        else: #- alternative list of response items (??? do we need this ???)
            print "IN UNDO, USER=(", parms, ")"
            for user in parms:
                rv = os.system("sudo userdel " + user)
                print "undo 2: (%s) rv=%s" % (user, rv)
    
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
        return os.system("sudo useradd " + parms)
     
        
        

#----------------------------------------------------------------------------------------------------------------------
# If this is run as a stand-alone program, perform unit testing
#----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import shelve
    from time import sleep
    
    #- create an instance of this sensor
    ss = Unexpected_User(sensor_name);

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
        if sensor_mode[0] == "2":
            rv = ss.set_target('BADDUDE')
        else:
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
        if sensor_mode[0] == "2":
            rv = ss.undo_target(['BADDUDE'])
        else:
            rv = ss.undo_target(['BADUSER'])
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
        ss = Unexpected_User(sensor_name);
        sensor_list[ss.name] = ss
        True
    
            


 
