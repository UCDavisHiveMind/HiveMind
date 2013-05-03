#-
#- Sensor Parent Class Definition, test and initiaization template
#-

"""
Description of sensor
"""

import shelve
import _bsddb
import time



#- import sensor class spec and master sensor list 
#from sensor_specs import SensorSpec, sensor_list



sensor_list = {}

#- constant definitions
NO_CHANGE = 0
CHANGE = 1
NEW_BASELINE = 2
ERROR = -1
return_values = {NO_CHANGE:"NO_CHANGE", CHANGE:"CHANGE", NEW_BASELINE:"NEW_BASELINE", ERROR:"*** ERROR ***"}

#- baseline types
#- Create baseline from next data seen, then fix baseline
#- Create baseline by adding to existing baseline, do not fix baseline
#- Create baseline by adding next n observations, then fix baseline

#- note: changes compare to null baseline; can allow update or override existing baseline

class SensorSpec(object):
    """
    HiveMind Sensor Class
    """

    def __init__(self, name, enabled, blt=None):
        super(SensorSpec, self).__init__()
        self.name = name
        self.enabled = enabled
        self.update_on_fail = False # call for full baseline update if none exists
        
        print ">>> INITING PARENT", self.name
        
        self.dbname = self.name.split(':')[0]
        self.baseline_counter = 1;
        self.baseline_duration = 0;
        self.baseline_timestamp = None
        self.baseline_fixed = False #- only create baseline if missing or requested
        self.fix_when_stable = False
        self.baseline = {}
        self.cur_data = {}
        #- holds last observed difference between observed and baseline
        #- place holder for difference information to support 
        #- response and reporting functions
        self.difference_data = {}
        self.message = ""


    #------------------------------------------------------------------------------
    #-  Force a reset of the baseline for this sensor
    #------------------------------------------------------------------------------
    def reset_baseline(self):
        """
        Force a reset of existing baseline in memory and persistent store
        """ 
        self.baseline = {}
        db = shelve.open('sensor-baseline')
        try:
            del db[self.dbname]
        except _bsddb.DBNotFoundError: #- just ignore case where baseline does not exist
            pass
        db.close()       
        self.baseline_fixed = False
        self.baseline_counter = 1;
    
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define data collection function 
    #-
    #- i.e. how to collect and parse/format the relevant data
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def collect_data(self, parms):
        """
        Collect information from the system related to the sensor's "Activity-of-Interest".
        """ 
        return True

    def compare_data(self, parms):
        """
        Compare the collected data to the existing Baseline or the Policy statement.
        """ 
        return True

    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define response function
    #-
    #- i.e. how to correct the problem. in practice this can be null.
    #- information regarding difference found is in 'difference_data'
    #- 
    #- this function must use the provided information to figure out
    #- how to respond to this particular problem. E.g. to remove the
    #- new user(s) that appeared in the password file
    #-
    #- the default definition is to call the "undo" function
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    def response(self, parms):
        """
        Action to take as an automated response to the observed "Activity-of-Interest".
        """ 
        return self.undo_target(parms)

    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define baseline function 
    #- i.e. force creation of baseline for this Activity-of-Interest
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------        
    def update(self, parms):
        """
        Force an update of the persistent (and in-memory) baseline for this sensor
        """

        #- set baseline to collected data and shelve
        db = shelve.open('sensor-baseline')
        db[self.name] = dict(self.cur_data)
        self.baseline = db[self.name]
        db.close()
   
        return True


    def set_target(self, parms):
        """
        For Testing -- Create an Activity-of-Interest condition that the sensor can detect.
        """ 
        return True

    def undo_target(self, parms):
        """
        For Testing -- Undo the condition that was created by the set_target() function
        """
        return True
   
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #- define sensor function 
    #- i.e. how to detect the particular condition
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------        
    def sensor(self, parms):
        """
        Determine if the current state of the sensor's "Activity-of-Interest" has changed from the baseline value or violates the saved policy
        If no persistent baseline exists, this function will create it.
        """ 
        
        #- collect the data -- function writes data to class variable 'cur_data'
        if self.collect(parms) == ERROR:
            return False

         
        #- if no baseline in memory, update from persistent baseline. 
        #- If no persistent baseline exists make the current data the baseline 
        #-   and report that the baseline was updated.
        if self.baseline == {}:
   
            #- attempt to load the baseline for this sensor
            db = shelve.open('sensor-baseline')
            try:
                #- found a baseline for this function, so load it
                self.baseline = db[self.name]
                db.close()

                print "> >   using baseline from shelve"
                print "-------------------------------------------------------"
                print self.baseline
                print "-------------------------------------------------------"
                print

            except KeyError:
                #- no such baseline, so set flag to indicate a new one needs to be created
                print "- >    baseline not found on disk"
                self.baseline_fixed = False
                
        #- update the baseline as needed
        if self.baseline_fixed == False:
            #- update profile
            print "- >    updating profile"
            self.update(parms)

            #- decrement the counter for number of times the profile has been updated
            if self.baseline_counter > 0: self.baseline_counter -= 1
            
            #- if no prior initial timestamp set, do it now
            if self.baseline_timestamp is None: self.baseline_timestamp = time.time
            
            
            if self.baseline_counter <= 0 \
                or ((time.time - self.baseline_timestamp) >= self.baseline_duration) \
                or (self.fix_when_stable and "cur data is stable by compare"):

                #- we have reached the specified condition to fix the baseline
                self.baseline_fixed = True
                print "- >    baseline is now fixed"
        
        #- compare collected data to baseline
        #
        if self.compare(self.cur_data, self.baseline) is True:
            print "! >    difference found:", self.message
            for x in self.difference_data:
                print x, self.difference_data[x]
            return CHANGE
        else:
            return NO_CHANGE 

   


#----------------------------------------------------------------------------------------------------------------------
# If this is run as a stand-alone program, perform unit testing
#----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import unittest
    
    True
    
            

