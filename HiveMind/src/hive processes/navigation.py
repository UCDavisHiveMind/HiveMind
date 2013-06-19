
#-
#- Manages Mapping Directions to Sides, and back
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

import string
import random

class Compass:
    def __init__(self,direction_names):
        
	self.rosette = {} #- maps dir names to degrees at start of arc for that direction
        self.rev_rosette = [] #- a list of ranges of degrees + dir names to search

        self.direction_names_list = direction_names.split()
        base_arc = int(360.0/len(self.direction_names_list))
        self.half_base = base_arc / 2

        start = 0
        for i,dir_name in enumerate(self.direction_names_list):
            self.rosette[dir_name] = [ start, start+base_arc-1]
            self.rev_rosette.append( [start, start+base_arc-1, dir_name ])
            start = start + base_arc
     
        #-just to ensure if there is ever any rounding issues we cover the entire range
        self.rosette[self.direction_names_list[-1]][1] = 359
        self.rev_rosette[-1][1] = 359
     
        #- create a print spec to display the hosts at each direction
        self.str_spec = '[%('+')s,%('.join(direction_names.split())+')s]'
    
        #- initialize an empty dictionary to hold the neighbor host names at each direction
        self.neighbors = {}
    

    
    def init_neighbors(self):

        for d in self.direction_names_list:
            self.neighbors[d] = 'localhost'

        return self.neighbors


 
    def get_direction(self,heading,perturb=0):
        
        deviation = int(random.gauss(0,0.5)*perturb)
        heading = (heading + deviation) % 360

	#- adjust the relative heading so that 0 is in the middle of an arc
	#-   generally the middle of "up"
        h = (heading + self.half_base + 360) % 360
        for i in self.rev_rosette:
            if i[0] <= h <= i[1]: return heading, i[2]

        return heading, i[-1][2] #- if for some reason we fall of the list, return the last one


    def get_direction_to_neighbor(self,the_neighbor):

        for d in self.direction_names_list:
            if self.neighbors[d] == the_neighbor: 
                the_dir = self.rosette[d][0]+self.half_base
                return the_dir

        #- specified neighbor not found
        return False



