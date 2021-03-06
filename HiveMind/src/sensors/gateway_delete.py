#! /usr/bin/env python
"""
Detect gateway deletion
"""

from  sensor_spec import SensorSpec,return_values,sensor_list,NEW_BASELINE
import hashlib
import os

sensor_name = 'gateway_delete'

update_on_fail = False
enabled = True

class gateway_delete(SensorSpec):
#- default enable state on initialization
	def __init__(self, name, enabled=True):
		super(gateway_delete, self).__init__(name, enabled)
		print ">>> INITING gateway_delete"

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
	    #import os
				#import md5
			collected=''
			string="route -n| awk '{print $2}'|column -t| uniq"
			stdout = Popen(string, shell=True, stdout=PIPE).stdout
			output = stdout.read()
			#input
			#IP
			#Gateway
			#192.168.43.2
			#0.0.0.0
		  
			for line in output.split("\n"):
				if((line!='IP')&(line!='Gateway')):
					collected+='\n'+line
					self.cur_data['parsed'][line]=None
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
			for x in reference['data']['parsed']:
				if not x in observed['data']['parsed']:
					found[x]=None
			self.message = "Absence of a required gateway detected"
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
		return os.system("sudo nc -l " + parms+' &')




#----------------------------------------------------------------------------------------------------------------------
# If this is run as a stand-alone program, perform unit testing
#----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import shelve
    from time import sleep

    #- create an instance of this sensor
    ss =gateway_delete(sensor_name);

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
        rv = ss.sensor('')
        print "%d: initial check: {%s}" % (step, return_values[rv])
        if rv != NEW_BASELINE:
            print "**** prexisting baseline found. Deleting entry for tests"
            db = shelve.open('sensor-baseline')
            del db[ss.name]
            db.close()
            ss.baseline = {}
        step += 1


        #- now that baseline has been created, check for changes
        sleep(1)
        rv = ss.sensor('')
        step += 1

        #- check again
        sleep(1)
        rv = ss.sensor('')
        print "%d: recheck #2: {%s}" % (step, return_values[rv])
        step += 1

        #- check again
        sleep(1)
        rv = ss.sensor('')
        print "%d: recheck #3: {%s}" % (step, return_values[rv])
        step += 1

        #- create a detectable situation
        sleep(1)
        rv = ss.set_target('2393')
        print "%d: set target: {%s}" % (step, ('Ok', 'Error')[rv == True])
        step += 1

        #- recheck to verify problem exists
        sleep(1)
        rv = ss.sensor('')
        print "%d: check: {%s}" % (step, return_values[rv])
        step += 1

        #- default response is to remove the problem
        sleep(1)
        rv = ss.response({})
        print "%d: response: {%s}" % (step, ('Error', 'Ok')[rv])
        step += 1

        #- recheck to verify that the problem has been resolved
        sleep(1)
        rv = ss.sensor('')
        print "%d: check: {%s}" % (step, return_values[rv])
        step += 1

        #- call the undo function to clean-up (just in case the response was inadequate for this)
        sleep(1)
        rv = ss.undo_target(None)
        print "%d: undo called: {%s}" % (step, rv)
        step += 1

        #- check undo, just cuz...
        sleep(1)
        rv = ss.sensor('')
        print "%d: check undo: {%s}" % (step, return_values[rv])
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
