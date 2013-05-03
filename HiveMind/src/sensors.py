
#-
#- Repository of Sensor function groups
#-
#- Author: Steven J. Templeton
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

#------------------------------------------------------------------------------
#- predefined function definitions
#------------------------------------------------------------------------------
import os
import sys

#------------------------------------------------------------------------------
#-
#- Sensor function Definitions
#-
#- Included for testing and demo
#- -- replace with those for a particular task
#-
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#- Task #1 -- (test) Look for "bad data"
#------------------------------------------------------------------------------
def bad_data(parms):
    r = os.path.exists("/tmp/baddata")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_data_r(parms):
    r = None
    try:
        r = os.remove("/tmp/baddata")
    except OSError, err:
        print "I/O error(%s)" % (err)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    #- was an action taken ('Y','N', or None)
    action_taken = 'Y'

    #- if not zero, then generate an alert with this value
    alert = 1 

    #- any supporting inforation to report
    details = 'Bad data found'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_data_t(parms):
    open('/tmp/baddata','w').close() 
    r = os.path.exists("/tmp/baddata")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_data_u(parms):
    r = None
    try:
        r = os.remove("/tmp/baddata")
    except OSError, err:
        print "I/O error(%s) undoing baddata" % (err)
    except:
        print "Unexpected error undoing baddata:", sys.exc_info()[0]
        raise

    return (r)

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #2 -- (test) Look for "bad file"
#------------------------------------------------------------------------------
def bad_file(parms):
    r = os.path.exists("/tmp/badfile")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_file_r(parms):
    r = None
    try:
        r = os.remove("/tmp/badfile")
    except OSError, err:
        print "I/O error(%s)" % (err)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
    action_taken = 'Y'
    alert = 0
    details = 'no details'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_file_t(parms):
    open('/tmp/badfile','w').close() 
    r = os.path.exists("/tmp/badfile")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_file_u(parms):
    r = None
    try:
        r = os.remove("/tmp/badfile")
    except OSError, err:
        print "I/O error(%s) undoing badfile" % (err)
    except:
        print "Unexpected error undoing badfile:", sys.exc_info()[0]
        raise

    return (r)

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #3 -- (test) Look for "bad user"
#------------------------------------------------------------------------------
def bad_user(parms):
    r = os.path.exists("/tmp/baduser")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_user_r(parms):
    r = None
    try:
        r = os.remove("/tmp/baduser")
    except OSError, err:
        print "I/O error(%s)" % (err)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
    action_taken = 'Y'
    alert = 0
    details = 'no details'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_user_t(parms):
    open('/tmp/baduser','w').close() 
    r = os.path.exists("/tmp/baduser")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_user_u(parms):
    r = None
    try:
        r = os.remove("/tmp/baduser")
    except OSError, err:
        print "I/O error(%s) undoing baduser" % (err)
    except:
        print "Unexpected error undoing baduser:", sys.exc_info()[0]
        raise
    return True

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #4 -- (test) Look for "bad size"
#------------------------------------------------------------------------------
def bad_size(parms):
    r = os.path.exists("/tmp/badsize")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_size_r(parms):
    r = None
    try:
        r = os.remove("/tmp/badsize")
    except OSError, err:
        print "I/O error(%s)" % (err)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
    action_taken = 'Y'
    alert = 0
    details = 'no details'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_size_t(parms):
    open('/tmp/badsize','w').close() 
    r = os.path.exists("/tmp/badsize")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_size_u(parms):
    r = None
    try:
        r = os.remove("/tmp/badsize")
    except OSError, err:
        print "I/O error(%s) undoing badsize" % (err)
    except:
        print "Unexpected error undoing badsize:", sys.exc_info()[0]
        raise
    return True

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #5 -- (test) Look for "bad target"
#------------------------------------------------------------------------------
def bad_target(parms):
    r = os.path.exists("/tmp/badtarget")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_target_r(parms):
    r = None
    try:
        r = os.remove("/tmp/badtarget")
    except OSError, err:
        print "I/O error(%s)" % (err)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
    action_taken = 'Y'
    alert = 0
    details = 'no details'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_target_t(parms):
    open('/tmp/badtarget','w').close() 
    r = os.path.exists("/tmp/badtarget")
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_target_u(parms):
    r = None
    try:
        r = os.remove("/tmp/badtarget")
    except OSError, err:
        print "I/O error(%s) undoing badtarget" % (err)
    except:
        print "Unexpected error undoing badtarget:", sys.exc_info()[0]
        raise
    return True

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #6 -- (test) Look for "bad process"
#------------------------------------------------------------------------------
def bad_process(parms):
    parms = "junkboy"
    cmd = "ps -Af"
    #print "*** ",cmd," ***"
    tmp = os.popen(cmd).read()
    details = 'procs:' + ';'.join(parms in tmp)
    return (r,details)

#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_process_r(parms):
    #- code to remove bad process (e.g. identify process and kill it)

    #- return values
    action_taken = 'Y'
    alert = 0
    details = ';'.join(parms in tmp)
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_process_t(parms):
    r = True
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_process_u(parms):
    return True

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
#- Task #7 -- (test) Look for "bad port"
#------------------------------------------------------------------------------
def bad_port(parms):
    parms = 48888
    cmd = "netstat -ona | grep tcp | grep LISTEN | cut -b21-43 | cut -d: -f2 | grep "+str(parms)
    r = os.popen(cmd).read()
    #print "bad_port returned ("+r+")"
    details = "port="+parms
    return (r,details)



#------------------------------------------------------------------------------
#- response function
#------------------------------------------------------------------------------
def bad_port_r(parms):
    #- code to remove bad port (e.g. identify process and kill it)

    #- return values
    action_taken = 'Y'
    alert = 0
    details = 'no details'
    return (action_taken,alert,details)

#------------------------------------------------------------------------------
#- set target function
#------------------------------------------------------------------------------
def bad_port_t(parms):
    r = True
    details = "-"
    return (r,details)

#------------------------------------------------------------------------------
#- unset target function
#------------------------------------------------------------------------------
def bad_port_u(parms):
    return True

#------------------------------------------------------------------------------





#------------------------------------------------------------------------------
#- [mobile code] :: EXPERIMENTAL
#- -- allows for user to include Python code in Ant
#- -- may be dangerous (but fun)
#------------------------------------------------------------------------------
def user_code(pcode):
    msg = "Processing ant with mobile code: [%s]" % (pcode)
    logger.debug('[%s] %s',host_name, msg)
    r = False
    try:
        r = eval(pcode)
    except:
        msg = ">> user code failed to evaluate"
        logger.error('[%s] %s',host_name, msg)
        msg = sys.exc_info()[0] 
        logger.error('[%s] %s',host_name, msg)
    details = "-"
    return (r,details)



#-
#- add an entry here for each sensor you wish to include
#-
sensor       = {'1':bad_data,   '2':bad_file,   '3':bad_user,   '4':bad_size,   '5':bad_target,   '6':bad_process,   '7':bad_port}
response     = {'1':bad_data_r, '2':bad_file_r, '3':bad_user_r, '4':bad_size_r, '5':bad_target_r, '6':bad_process_r, '7':bad_port_r}
set_target   = {'1':bad_data_t, '2':bad_file_t, '3':bad_user_t, '4':bad_size_t, '5':bad_target_t, '6':bad_process_t, '7':bad_port_t}
unset_target = {'1':bad_data_u, '2':bad_file_u, '3':bad_user_u, '4':bad_size_u, '5':bad_target_u, '6':bad_process_u, '7':bad_port_u}

