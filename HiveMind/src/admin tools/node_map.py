#!/usr/bin/python

#-
#- Generate a Node Map based on Hive nodes, neighbor assignments, and enclave
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

import re
import string
import sys
import random
from random import choice
 
class NodeMap:
    def __init__(self):

        self.rosette = {}
	self.cells = {}
        self.rcells = {}
        self.grid_rows = 0
        self.grid_cols = 0
        self.grid = []


    def load_map(self,map_file):
	#-
	#- read in the list of nodes to use from the config file
	#-
	try:
	    node_map_file = open( map_file )
	    try:
		nm_buff = node_map_file.readlines()
	    finally: 
		node_map_file.close() # close socket
	except IOError:
	    print "Error accessing the node map file (%s): %s" % (map_file, ErrorMessage)
	    sys.exit(0)

	#-
	#- get the node map dimensions
	#- 
	self.grid_rows = 0
	self.grid_cols = 0
	for line in nm_buff:

	    matchObj = re.match('^nm:\s+ROWS\s+(\w+)\s*',line)
	    if matchObj:
		self.grid_rows = int(matchObj.group(1))
		continue; 

	    matchObj = re.match('^nm:\s+COLS\s+(\w+)\s*',line)
	    if matchObj:
		self.grid_cols = int(matchObj.group(1))
		continue; 

	    #- if we have
	    if self.grid_rows > 0 and self.grid_cols > 0:
		break;

	    #- end :: get self.grid info loop    
	
	#- initialize node map self.grid
	self.grid = [[False for col in range(self.grid_cols)] for row in range(self.grid_rows)]

	self.cells = {}
	self.rcells = {}

	for line in nm_buff:
	    matchObj = re.match('^nm:\s+(False)\s+(\d+)\s+(\d+)',line)
	    if matchObj:
		row_idx = int(matchObj.group(2))
		col_idx = int(matchObj.group(3))
		node_id = 'null-'+str(row_idx)+'-'+str(col_idx)
		self.cells[node_id] = ( row_idx, col_idx ) 
		self.rcells[str(row_idx)+":"+str(col_idx)] = node_id
                self.grid[row_idx, col_idx] = node_id
		continue; 

	    matchObj = re.match('^nm:\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)',line)
	    if matchObj:
		node_id = matchObj.group(1)
		row_idx = int(matchObj.group(2))
		col_idx = int(matchObj.group(3))
		enclave = matchObj.group(4)
		self.cells[node_id] = ( row_idx, col_idx, enclave ) 
		self.rcells[str(row_idx)+":"+str(col_idx)] = node_id
                self.grid[row_idx][col_idx] = node_id
		continue; 

	    #- end :: initialze cells loop    



    #------------------------------------------------------------------------------
    #- For a 2-D arrangment of nodes, return the row,col of the neighbor node
    #-  from a particular row,col if moving in the specified direction 
    #-  
    #- This is valid for arrangments of 4,6,8 neighbors
    #------------------------------------------------------------------------------
    def get_neighbors(self,this_node,layout=6):

      maxr = self.grid_rows
      maxc = self.grid_cols

      def get_up(r,c):
	  r = (r-1+maxr) % maxr
	  return r,c

      def get_up_right(r,c):
	  if ( layout == 6 ):
	      if r%2 == 1: #- is odd 
		  c = (c+1) % maxc
	      else:
		  c = c % maxc
	  else:
	      c = (c+1) % maxc
	  r = (r-1+maxr) % maxr
	  return r,c

      def get_right(r,c):
	  c = (c+1) % maxc
	  return r,c

      def get_down_right(r,c):
	  if ( layout == 6 ):
	      if r%2 == 1: #- is odd 
		  c = (c+1) % maxc
	      else:
		  c = c % maxc
	  else:
	      c = (c+1) % maxc
	  r = (r+1) % maxr
	  return r,c

      def get_down(r,c):
	  r = (r+1) % maxr
	  return r,c

      def get_down_left(r,c):
	  if ( layout == 6 ):
	      if r%2 == 1: #- is odd 
		  c = c % maxc
	      else:
		  c = (c-1+maxc) % maxc
	  else:
	      c = (c-1+maxc) % maxc
	  r = (r+1) % maxr
	  return r,c

      def get_left(r,c):
	  c = (c-1+maxc) % maxc
	  return r,c

      def get_up_left(r,c):
	  if ( layout == 6 ):
	      if r%2 == 1: #- is odd 
		  c = c % maxc
	      else:
		  c = (c-1+maxc) % maxc
	  else:
	      c = (c-1+maxc) % maxc
	  r = (r-1+maxr) % maxr
	  return r,c

      if layout not in (4,6,8): 
	    #- logger.error("only self.grids of 4,6 or 8 neighbors are currently defined")
	    print "ERROR: only self.grids of 4,6 or 8 neighbors are currently defined"
	    sys.exit(1)      

      (row,col,enclave) = self.cells[this_node]
      #-
      #- for each direction used, get the
      #- coordinates of cell in specified direction
      #- skipping over any empty cells in that direction
      #-
      up_nbr_r,up_nbr_c = get_up(row,col)
      while not self.grid[up_nbr_r][col]:   
	  print "skipping (",up_nbr_r,",",up_nbr_c,")"
	  up_nbr_r,up_nbr_c = get_up(up_nbr_r,up_nbr_c)
	  
      ur_nbr_r,ur_nbr_c = get_up_right(row,col)
      while not self.grid[ur_nbr_r][ur_nbr_c]:   
	  print "skipping (",ur_nbr_r,",",col,")"
	  ur_nbr_r,ur_nbr_c = get_up_right(ur_nbr_r,ur_nbr_c)
	  
      rt_nbr_r,rt_nbr_c = get_right(row,col)
      while not self.grid[rt_nbr_r][rt_nbr_c]:
	  print "skipping (",row,",",rt_nbr_c,")"
	  rt_nbr_r,rt_nbr_c = get_right(rt_nbr_r,rt_nbr_c)
	  
      dr_nbr_r,dr_nbr_c = get_down_right(row,col)
      while not self.grid[dr_nbr_r][dr_nbr_c]:
	  print "skipping (",dr_nbr_r,",",dr_nbr_c,")"
	  dr_nbr_r,dr_nbr_c = get_down_right(dr_nbr_r,dr_nbr_c)
	  
      dn_nbr_r,dn_nbr_c = get_down(row,col)
      while not self.grid[dn_nbr_r][dn_nbr_c]:
	  print "skipping (",dn_nbr_r,",",dn_nbr_c,")"
	  dn_nbr_r,dn_nbr_c = get_down(dn_nbr_r,dn_nbr_c)
	  
      dl_nbr_r,dl_nbr_c = get_down_left(row,col)
      while not self.grid[dl_nbr_r][dl_nbr_c]:
	  print "skipping (",dl_nbr_r,",",dl_nbr_c,")"
	  dl_nbr_r,dl_nbr_c = get_down_left(dl_nbr_r,dl_nbr_c)
	  
      lt_nbr_r,lt_nbr_c = get_left(row,col)
      while not self.grid[lt_nbr_r][lt_nbr_c]:
	  print "skipping (",lt_nbr_r,",",lt_nbr_c,")"
	  lt_nbr_r,lt_nbr_c = get_left(lt_nbr_r,lt_nbr_c)
	  
      ul_nbr_r,ul_nbr_c = get_up_left(row,col)
      while not self.grid[ul_nbr_r][ul_nbr_c]:   
	  print "skipping (",ul_nbr_r,",",ul_nbr_c,")"
	  ul_nbr_r,ul_nbr_c = get_up_left(ul_nbr_r,ul_nbr_c)
      
      if layout == 4:
	  return ( self.grid[up_nbr_r][up_nbr_c], 
	       self.grid[rt_nbr_r][rt_nbr_c],
	       self.grid[dn_nbr_r][dn_nbr_c], 
	       self.grid[lt_nbr_r][lt_nbr_c] )

      '''
      # - for a hex w/ up and down sides
      if layout == 6:
	  return ( self.grid[up_nbr_r][up_nbr_c], 
	       self.grid[ur_nbr_r][ur_nbr_c],
	       self.grid[dr_nbr_r][dr_nbr_c], 
	       self.grid[dn_nbr_r][dn_nbr_c], 
	       self.grid[dl_nbr_r][dl_nbr_c],
	       self.grid[ul_nbr_r][ul_nbr_c] )
      '''
      # - for a hex w/ right and left sides
      if layout == 6:
	  return ( 
	       self.grid[ur_nbr_r][ur_nbr_c],
	       self.grid[rt_nbr_r][rt_nbr_c], 
	       self.grid[dr_nbr_r][dr_nbr_c], 
	       self.grid[dl_nbr_r][dl_nbr_c],
	       self.grid[lt_nbr_r][lt_nbr_c], 
	       self.grid[ul_nbr_r][ul_nbr_c] )

      if layout == 8:    
	  return ( self.grid[up_nbr_r][up_nbr_c], 
	       self.grid[ur_nbr_r][ur_nbr_c],
	       self.grid[rt_nbr_r][rt_nbr_c],
	       self.grid[dr_nbr_r][dr_nbr_c], 
	       self.grid[dn_nbr_r][dn_nbr_c], 
	       self.grid[dl_nbr_r][dl_nbr_c],
	       self.grid[lt_nbr_r][lt_nbr_c],
	       self.grid[ul_nbr_r][ul_nbr_c] )




def main():
    the_map = NodeMap()
    the_map.load_map("logs/node_map")
    
    for k in the_map.cells:
         print k, the_map.cells[k]

    for k in the_map.rcells:
         print k, the_map.rcells[k]
    
    def get_nearby_node(the_node,diameter):

	d = int(random.random()*diameter)
	while d > 0:
	    neighbors = the_map.get_neighbors(the_node)
	    the_node = choice( neighbors ) #- select a random neighbor
	    d -= 1
	    
	return the_node


    _node = "node-40"
    x = the_map.get_neighbors(_node)
    print "(%s)  %s" % (_node,x)

    spread = 1
    density = 12
    print "--- %s ----------- %s" % (_node,spread)
    nbrs = {}
    for i in range(density):
        n = get_nearby_node(_node,spread)
        nbrs[n] = 1
        print ">> ",n
    print ">> set:",nbrs.keys()

    spread = 2
    density = 12
    print "--- %s ----------- %s" % (_node,spread)
    nbrs = {}
    for i in range(density):
        n = get_nearby_node(_node,spread)
        nbrs[n] = 1
        print ">> ",n
    print ">> set:",nbrs.keys()

    spread = 3
    density = 12
    print "--- %s ----------- %s" % (_node,spread)
    nbrs = {}
    for i in range(density):
        n = get_nearby_node(_node,spread)
        nbrs[n] = 1
        print ">> ",n
    print ">> set:",nbrs.keys()

    spread = 4
    density = 12
    print "--- %s ----------- %s" % (_node,spread)
    nbrs = {}
    for i in range(density):
        n = get_nearby_node(_node,spread)
        nbrs[n] = 1
        print ">> ",n
    print ">> set:",nbrs.keys()



if __name__=="__main__":
    main()
