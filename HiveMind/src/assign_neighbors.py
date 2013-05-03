#!/usr/bin/env python

#-
#- HiveMind - Assign Neighbors to Hive Nodes Tool
#-
#- Author:  Steven Templeton
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


"""
*******************************************************************************

This version reads the list of nodes to use from a config file. All node_mgr
processes should be up and running prior to running this process.

*******************************************************************************
"""

import socket # networking module
import sys
import string
import re
import math
import random
import logging
import logging.handlers
from optparse import OptionParser
import os
import hilbert


random.seed(1114584)

#-
#- constant definitions -----
#-
hmadv_port = 50010 #- port for connect from hivemind Advocate
node_port = 50000 #- open port on nodes for node_manager
backlog = 1024    #- number of waiting messages on recv socket
layout = 6
hex_side_up = False

#COLOCATE_SIMILAR = None  #- 'hilbert', 'nearest-neighbor'
COLOCATE_SIMILAR = 'hilbert'  #- 'hilbert', 'nearest-neighbor'


workdir = os.path.dirname(os.path.abspath(__file__))

username = os.getenv('USER')

parser = OptionParser()
parser.add_option("--nodes", action='store', type="string", dest="nodes", default="", help="filename containing list of nodes to manage")
parser.add_option("--enclaves", action='store', type="int", dest="num_enclaves", default=1, help="number of distinct enclaves to create -- used for evaluation.")

(options, args) = parser.parse_args()

print "\n>>> [%s]\n" % (options.num_enclaves)

if options.nodes == "":
    print "ERROR: nust specify node list"
    sys.exit()
node_list_filespec = options.nodes

try:
    node_list = [line.strip() for line in open(node_list_filespec)]
except IOError, e:
    notes = sys.exc_info()[0]
    if e.errno == 2: #- file not found
	print "Error reading '%s': file not found" % (node_list_filespec)
        if node_list_filespec == '/tmp/hm_node_list':
            print ">>> Did you forget to specify the node list file?"
    else:   
	print "Error reading '%': %s" % (node_list_filespec, e)
    sys.exit(0)
    

#------------------------------------------------------------------------------
#- For a 2-D arrangment of nodes, return the row,col of the neighbor node
#-  from a particular row,col if moving in the specified direction 
#-  
#- This is valid for arrangments of 4,6,8 neighbors
#------------------------------------------------------------------------------
def get_neighbors(grid,row,col,maxr,maxc,layout=6):

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
	logger.error("only grids of 4,6 or 8 neighbors are currently defined")
        sys.exit(1)      

  #-
  #- for each direction used, get the
  #- coordinates of cell in specified direction
  #- skipping over any empty cells in that direction
  #-
  up_nbr_r,up_nbr_c = get_up(row,col)
  while not grid[up_nbr_r][col]:   
      print "skipping (",up_nbr_r,",",up_nbr_c,")"
      up_nbr_r,up_nbr_c = get_up(up_nbr_r,up_nbr_c)
      
  ur_nbr_r,ur_nbr_c = get_up_right(row,col)
  while not grid[ur_nbr_r][ur_nbr_c]:   
      print "skipping (",ur_nbr_r,",",col,")"
      ur_nbr_r,ur_nbr_c = get_up_right(ur_nbr_r,ur_nbr_c)
      
  rt_nbr_r,rt_nbr_c = get_right(row,col)
  while not grid[rt_nbr_r][rt_nbr_c]:
      print "skipping (",row,",",rt_nbr_c,")"
      rt_nbr_r,rt_nbr_c = get_right(rt_nbr_r,rt_nbr_c)
      
  dr_nbr_r,dr_nbr_c = get_down_right(row,col)
  while not grid[dr_nbr_r][dr_nbr_c]:
      print "skipping (",dr_nbr_r,",",dr_nbr_c,")"
      dr_nbr_r,dr_nbr_c = get_down_right(dr_nbr_r,dr_nbr_c)
      
  dn_nbr_r,dn_nbr_c = get_down(row,col)
  while not grid[dn_nbr_r][dn_nbr_c]:
      print "skipping (",dn_nbr_r,",",dn_nbr_c,")"
      dn_nbr_r,dn_nbr_c = get_down(dn_nbr_r,dn_nbr_c)
      
  dl_nbr_r,dl_nbr_c = get_down_left(row,col)
  while not grid[dl_nbr_r][dl_nbr_c]:
      print "skipping (",dl_nbr_r,",",dl_nbr_c,")"
      dl_nbr_r,dl_nbr_c = get_down_left(dl_nbr_r,dl_nbr_c)
      
  lt_nbr_r,lt_nbr_c = get_left(row,col)
  while not grid[lt_nbr_r][lt_nbr_c]:
      print "skipping (",lt_nbr_r,",",lt_nbr_c,")"
      lt_nbr_r,lt_nbr_c = get_left(lt_nbr_r,lt_nbr_c)
      
  ul_nbr_r,ul_nbr_c = get_up_left(row,col)
  while not grid[ul_nbr_r][ul_nbr_c]:   
      print "skipping (",ul_nbr_r,",",ul_nbr_c,")"
      ul_nbr_r,ul_nbr_c = get_up_left(ul_nbr_r,ul_nbr_c)
  
  if layout == 4:
      return ( grid[up_nbr_r][up_nbr_c], 
           grid[rt_nbr_r][rt_nbr_c],
           grid[dn_nbr_r][dn_nbr_c], 
           grid[lt_nbr_r][lt_nbr_c] )

  '''
  # - for a hex w/ up and down sides
  if layout == 6:
      return ( grid[up_nbr_r][up_nbr_c], 
           grid[ur_nbr_r][ur_nbr_c],
           grid[dr_nbr_r][dr_nbr_c], 
           grid[dn_nbr_r][dn_nbr_c], 
           grid[dl_nbr_r][dl_nbr_c],
           grid[ul_nbr_r][ul_nbr_c] )
  '''
  # - for a hex w/ right and left sides
  if layout == 6:
      return ( 
           grid[ur_nbr_r][ur_nbr_c],
           grid[rt_nbr_r][rt_nbr_c], 
           grid[dr_nbr_r][dr_nbr_c], 
           grid[dl_nbr_r][dl_nbr_c],
           grid[lt_nbr_r][lt_nbr_c], 
           grid[ul_nbr_r][ul_nbr_c] )

  if layout == 8:    
      return ( grid[up_nbr_r][up_nbr_c], 
           grid[ur_nbr_r][ur_nbr_c],
           grid[rt_nbr_r][rt_nbr_c],
           grid[dr_nbr_r][dr_nbr_c], 
           grid[dn_nbr_r][dn_nbr_c], 
           grid[dl_nbr_r][dl_nbr_c],
           grid[lt_nbr_r][lt_nbr_c],
           grid[ul_nbr_r][ul_nbr_c] )


#- 
#- Initialize the logger
#-
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.INFO)
f = logging.Formatter("%(created)s %(levelname)-9s %(message)s")
  
h = logging.handlers.SysLogHandler(address='/dev/log',facility=23)
h.setFormatter(f)
logger.addHandler(h)

#-
#- get name of host this process is running on
#-
my_name = socket.gethostname()


#-
#- open a log file for this process
#-
f = open("/tmp/log."+my_name,"w")
f.write("starting\n");

"""
#-
#- read in the list of nodes to use from the config file
#-
try:
    node_list_file = open("/tmp/hm_node_list")
    try:
        buff = node_list_file.readlines()
    finally: 
        node_list_file.close() # close socket
except IOError:
    exc_type, exc_value = sys.exc_info()[:2]
    print "Error writing '",node_list_file,"'",exc_type,"::",exc_value,"\n"
    sys.exit(0)

"""

#-
#- get information about hosts in file
#-
slice_info = {} 
for line in node_list : 
    print ">>> ",line
    host_name = line.rstrip()
    matchObj = re.match('\s*(?P<nm>node-\d+).*',host_name)
    try:
        node_name = matchObj.group('nm')
    except:
        print "Error getting node name from ",host_name
        print  sys.exc_info()[0]
        raise

    slice_info[node_name]={}
    slice_info[node_name]['host_name'] = host_name
    print ">>>",host_name
    node_ip = socket.gethostbyname(host_name)
    slice_info[node_name]['ip_addr'] = node_ip
    if options.num_enclaves: 
    	slice_info[node_name]['enclave'] = chr(int(random.random()*options.num_enclaves+65))
    else: #- take enclave name from node list
        #- to be implemented
    	slice_info[node_name]['enclave'] = 'X'


#- display the slice_info
print "----------\nnodes to include in mesh\n----------"
cnt = 0
for (k,v) in slice_info.items():
    cnt += 1
    print cnt,") ",k,":"
    for (a,b) in v.items():
        print "    -> ",a,":",b
print "----------"


#- create the empty matrix for the geography
#-   make it nearly square and as small as possible
node_cnt = len(slice_info)
d = int(math.sqrt(node_cnt))
if node_cnt == d*d: #- square
    rows=cols=d
else:
    cols = d+1
    (rows,x) = divmod(node_cnt,cols)
    if x != 0: rows += 1

print "\nmap size:",rows,"x",cols
node_map = [[False for col in range(cols)] for row in range(rows)]
print node_map


#-
#- assign the nodes to a region in the geography
#-
if COLOCATE_SIMILAR == 'hilbert':

   gsize = rows*cols
   series_scale = 6

   #- get hilbert series for grid of this size
   hilbert_series = hilbert.get_series(series_scale)
   hlen = len(hilbert_series)

   print ">>>>> gsize:",gsize, ", hlen:",hlen
   while gsize > hlen :
     print "SERIES NOT LONG ENOUGH, try again"

     #increase the size of the series
     series_scale += 1

     #- get hilbert series for grid of this size
     hilbert_series = hilbert.get_series(series_scale)

     #- make sure series is long enough
     hlen = len(hilbert_series)
     print ">> grid size: %s, series len: %s" % (gsize, hlen)


   #- sort nodes by defined criteria...
   nodes_sorted = sorted(slice_info.items(),key=lambda e: e[1]['enclave'])
   print "------------------------"
   #print nodes_sorted
   print "------------------------"
   #- assign nodes based on hilbert ordering.
   skip = 0
   for i,k in enumerate(nodes_sorted):
       print ">>> ",i,k,skip
       while True:
           (x,y) = hilbert_series[i+skip]
           print "<%s,%s> <%s,%s>" % (x,y,rows,cols)
           
           #- if the coordinates of the next in the hibert series are in the range of the grid
           #-   continue, otherwise skip this element, and try the next. This will work as lon
           #-   as the series is larger than the number of cells in the grid.
           if x < cols and y < rows: 
	       break
           
           skip += 1
           print "----",skip
       
       print "**** %s: (%s,%s) [%s] >> %s" % (i,x,y,nodes_sorted[i],k[0])
       name = nodes_sorted[i][0]
       node_map[int(y)][int(x)] = name

elif COLOCATE_SIMILAR == 'nearest-neighbor':
   True

else:
    i=0; j=0
    for h in slice_info.keys():
	node_map[i][j] = h
	j += 1
	if j == cols:
	    j=0
	    i+=1



#- print out the node map
#----------------
nmf = open(workdir+"/hm_node_map.txt","w") 

msg = "nm: <START>"
logger.info(msg);  nmf.write(msg+"\n")

msg = "nm: ROWS %d" % (rows)
logger.info(msg);  nmf.write(msg+"\n")

msg ="nm: COLS %d" % (cols)
logger.info(msg);  nmf.write(msg+"\n")

for i in range(rows):
  for j in range(cols):
    try:
      name = node_map[i][j]
      print ">>> name",name
      print ">>> si",slice_info[name]
      msg =  "nm: %s %d %d %s %s %s" % (name, i, j, slice_info[name]['enclave'], slice_info[name]['host_name'], slice_info[name]['ip_addr'])
      logger.info(msg);  nmf.write(msg+"\n")
    except (KeyError):
      msg = "nm: -"
      logger.info(msg);  nmf.write(msg+"\n")

msg = "nm: <END>"
logger.info(msg);  nmf.write(msg+"\n")

nmf.close()


print "\n================================"
#- assign neighbors to each node
for i in range(rows):
  for j in range(cols):
    try:
      name = node_map[i][j]
      print "***** (",i,",",j,"): ",name
      if not name: continue
      
      if layout == 4:
          (up,rt,dn,lt) = get_neighbors(node_map,i,j,rows,cols,layout)   
          print "     up:",up
          print "     rt:",rt
          print "     dn:",dn
          print "     lt:",lt
          slice_info[name]['u'] = up
          slice_info[name]['r'] = rt
          slice_info[name]['d'] = dn
          slice_info[name]['l'] = lt

      elif layout == 6:
          if ( hex_side_up ):
              (up,ur,dr,dn,dl,ul) = get_neighbors(node_map,i,j,rows,cols,layout)   
              print ">    up:",up
              print ">    ur:",ur
              print ">    dr:",dr
              print ">    dn:",dn
              print ">    dl:",dl
              print ">    ul:",ul
              slice_info[name]['u'] = up
              slice_info[name]['ur'] = ur
              slice_info[name]['dr'] = dr
              slice_info[name]['d'] = dn
              slice_info[name]['dl'] = dl
              slice_info[name]['ul'] = ul
          else:
              (ur,rt,dr,dl,lt,ul) = get_neighbors(node_map,i,j,rows,cols,layout)   
              print "     ur:",ur
              print "     rt:",rt
              print "     dr:",dr
              print "     dl:",dl
              print "     lt:",lt
              print "     ul:",ul
              slice_info[name]['ur'] = ur
              slice_info[name]['rt'] = rt
              slice_info[name]['dr'] = dr
              slice_info[name]['dl'] = dl
              slice_info[name]['lt'] = lt
              slice_info[name]['ul'] = ul


      elif layout == 8:
          (up,ur,rt,dr,dn,dl,lt,ul) = get_neighbors(node_map,i,j,rows,cols,layout)   
          print "     up:",up
          print "     ur:",ur
          print "     rt:",rt
          print "     dr:",dr
          print "     dn:",dn
          print "     dl:",dl
          print "     lt:",lt
          print "     ul:",ul
          slice_info[name]['u'] = up
          slice_info[name]['ur'] = ur
          slice_info[name]['r'] = rt
          slice_info[name]['dr'] = dr
          slice_info[name]['d'] = dn
          slice_info[name]['dl'] = dl
          slice_info[name]['l'] = lt
          slice_info[name]['ul'] = ul

      else:
          print "ERROR: layout must be either 4, 6 or 8"
          sys.exit(1)

    except KeyError: # (IndexError, KeyError):
      raise #pass      

print "\n================================"
print "\n\n\n"





# listen for connections
#try:
#    # create Internet TCP socket
#    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    s.bind(('', port))
#    s.listen(backlog)
#except socket.error, (value,message):
#    if s: 
#        s.close()
#    print "Could not open socket: " + message
#    sys.exit(1)

#max_count = 100
#connection_id = 0
#counter = 0



#- send neighbor assignments to all nodes in slice
for (name,h) in sorted(slice_info.items()):
    # connect to server
    print "sending neighbor info to ",name
    ip = h['ip_addr']
    print "> name:%s" % (name),
    print "  ip:%(ip_addr)s  [%(ur)s,%(rt)s,%(dr)s,%(dl)s,%(lt)s,%(ul)s]" % h  #- for hex w/ sides right/left
    #print "  ip:%(ip_addr)s  [%(u)s,%(r)s,%(d)s,%(l)s]" % h
    count = 10
    while count > 0:
        try:
            print ".",
            # create Internet TCP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, node_port))
            break
        except socket.error, (value,message):
            if s: 
                s.close()
            print "Could not open socket: " + message
            count -= 1
    
    if count <= 0:
        print "ERROR: was unable to connect to ",name," at ",ip 
        sys.exit()

    if layout == 4:
        msg = "dir:%(u)s,%(r)s,%(d)s,%(l)s" % h

    if layout == 6:
        #msg = "dir:%(u)s,%(ur)s,%(dr)s,%(d)s,%(dl)s,%(ul)s" % h  #- for hex w/ sides up/down
        msg = "dir:%(ur)s,%(rt)s,%(dr)s,%(dl)s,%(lt)s,%(ul)s" % h  #- for hex w/ sides right/left
   
    if layout == 8:
        msg = "dir:%(u)s,%(ur)s,%(r)s,%(dr)s,%(d)s,%(dl)s,%(l)s,%(ul)s" % h
    
    fileobj = s.makefile('r',0)
    fileobj.write(msg)
    print "    message sent"
           
    
    buff = fileobj.readlines()
    for line in buff : print line
    
    s.close() # close socket


sys.exit()
    
#while 1: #- main event looop
#    pass

f.close()            

#- get slice info: node names, ip addresses, ...
#- * by message sent from create_secure_slice.py


#- send message to each of the nodes about who its neighbors are, and an ok to start.
#- !! note: Sentinels need to handle neighbors not responding, for initial start-up and
#-    in case their are network and/or host problems. 

#- go into wait loop for messages from Sentinels, and to update/respond to UI.

