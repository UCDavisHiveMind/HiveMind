#!/usr/bin/python

#-
#- Implements a Sliding Window over the data
#-
#- Author: Steven J. Templeton
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


# Provides a rolling total Class

import socket # networking module
import sys
import os
import string
import re
import time
import math
import thread
import threading
import logging
import logging.handlers
import signal



#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
class RollingTotal:
    def __init__(self, num_bins,bin_size):
        self.num_bins = num_bins
        self.bin_size = bin_size
        self.bins = [0]*num_bins
        self.total = 0
        self.last_bin_raw = 0-num_bins


    def rt_cleanup(self,now):

        #- calculate the absolute bin index (assume an infinite set of bins) 
        #-   based on the passed value (e.g. current time)
        cur_bin_raw = int(now/self.bin_size)
        #print "cur_bin_raw = ",cur_bin_raw
        #print "last_bin_raw",self.last_bin_raw
        #print "num_bins =",self.num_bins
 
        #- last been updated is the same bin, so just return the total
        #- we need to clear out any bins between last_bin_raw up to and including cur_bin_raw

        #- if the number of bins spanned is greater than or equal to the number of bins, the 
        #- entire table should be cleared
        if cur_bin_raw - self.last_bin_raw >= self.num_bins:
            #print "clearing all"
            self.bins = [0]*self.num_bins
            self.total = 0
        else:
        #- need to clear out just a range of bins, or none if last and cur bins are the same
            #print "clearing only",self.last_bin_raw+1,"to",cur_bin_raw
            for i0 in range(self.last_bin_raw+1,cur_bin_raw+1):
                i = i0 % self.num_bins
                #print "** clearing bin", i, "  (", self.bins[i], ")"
                self.total -= self.bins[i]
                self.bins[i] = 0

        #- adjust the location of the last used bin to be the current bin (raw)
        #-   this makes sense on a retrieve because we have already cleaned up
        #-   any earlier bins.
        self.last_bin_raw = cur_bin_raw
        #print "last_bin_raw updated to be",cur_bin_raw
        #- return the current total
        return( self.total )

    #-
    #-
    #-
    def rt_inc_count(self,now):

        #- clean-up the bins, in case we have changed bins and any intermediate
        #-   bins need to be cleared and the total adjusted
        self.rt_cleanup(now)
    
        #- increment the count in both actual bin and the running total
        cur_bin = self.last_bin_raw % self.num_bins
        #print ">> now increment bin",cur_bin

        self.bins[cur_bin] += 1
        self.total += 1
        #print ">> [cb=",cur_bin," tot=",self.total,"]"

        notes = 'ants_seen=%d, num_in_bin=%d, bin_id=%d' % (self.total,self.bins[cur_bin],cur_bin)
        msg = 'node_info::%s %s:%s notes:%s' % ('xxx','event','counting an ant',notes)
        #logger.debug('[%s] %s',host_name, msg)
        # print ('[%s] %s','xxx', msg)

        #- return the current total
        return( self.total )


    #-
    #-
    #-
    def rt_get_total(self,now):

        #- clean-up the bins, in case we have changed bins and any intermediate
        #-   bins need to be cleared and the total adjusted
        self.rt_cleanup(now)
    
        cur_bin = self.last_bin_raw % self.num_bins

        notes = 'ants_seen=%d, num_in_bin=%d, bin_id=%d' % (self.total,self.bins[cur_bin],cur_bin)
        msg = 'node_info::%s %s:%s notes:%s' % ('xxx','event','getting num ants seen',notes)
        #logger.debug('[%s] %s',host_name, msg)
        #  print('[%s] %s','xxx', msg)

        #- return the current total
        return( self.total )





def test():
    bin_size = 10               #- size of bins in seconds
    num_bins = 10               #- number of bin_size bins in ring buffer
    bins = [0]*num_bins

    last_bin_raw = 0-num_bins
    total = 0
    
    my_rt = RollingTotal(10,10)

    #events = range(1,200+11)
    events = (1,4,5,82,83,88,89,99, 189) 
    for now in events:
        t = my_rt.rt_inc_count(now)
        print ">> time: %s   total = %s" % (now,t)

    pass


if __name__ == "__main__":    
    test()


