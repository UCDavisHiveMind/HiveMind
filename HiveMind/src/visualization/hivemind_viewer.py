#!/usr/bin/python

#-
#- HiveMind Activity Viewer
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 21 Sept 2011
#- Revised: v0.2 - 11 Mar 2012
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

import time
import string
import random
import sys
import re
import math
import signal


from optparse import OptionParser

# PyGame Constants
import pygame
from pygame.locals import *
from pygame.color import THECOLORS

import cell

#- constants
#WINSIZE = 640,480
#WINSIZE = 1024,1024
WINSIZE = 1900,1024

IDLE = 0
FORAGING = 1
DROPPING = 2
FOLLOWING = 3
STATES = ['IDLE','FORAGING','DROPPING','FOLLOWING']
STATE_COLORS = { IDLE: THECOLORS['purple3'], FORAGING: THECOLORS['dodgerblue4'], DROPPING: THECOLORS['forestgreen'], FOLLOWING: THECOLORS['orangered2'] } 
ACTION_COLORS = {'recruited':THECOLORS['yellow']}
ENCLAVE_COLORS = {'A':THECOLORS['salmon1'],'B':THECOLORS['plum2'],'C':THECOLORS['mistyrose'],
                  'D':THECOLORS['darkslategray3'],'E':THECOLORS['cornflowerblue'],'F':[238, 204, 60, 255],
                  'G':THECOLORS['khaki3'],'H':THECOLORS['lightpink'],'I':THECOLORS['yellowgreen'],
                  'J':THECOLORS['tan'], 'K':THECOLORS['blue'], 'L':THECOLORS['red']}


INACTIVE_CELL_COLOR = THECOLORS["gray17"]
SHOW_PROJECT_LOGOS = True

REFRESH_RATE = 0.10


#- command line input
parser = OptionParser()
parser.add_option("-s", action='store', type="string", dest="tfile", default="test.trace", help="filename of trace to display")
parser.add_option("-m", action='store', type="string", dest="nmfilename", default=False, help="filename of node_map file.")
parser.add_option("-l", action='store_true', dest="loop_input", default=False, help="loop replay input file when at end")
parser.add_option("-w", action='store_true', dest="wait_at_end", default=False, help="wait for keypress when input exhausted")
parser.add_option("-d", action='store', type="int", dest="delay", default=100, help="number of milliseconds to pause between node updates")
parser.add_option("-i", action='store', type="int", dest="skip_lines", default=0, help="start delay after skipping this many lines")
parser.add_option("-q", action='store_true', dest="be_quiet", default=False, help="suppress most output")
parser.add_option("-E", action='store_true', dest="show_enclaves", default=False, help="show enclaves by color")

(options, args) = parser.parse_args()



#  signal.signal(signal.SIGINT, signal_handler)
def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    #sys.stderr = original_stderr
    #log_stderr_f.close()
    sys.exit(0)


# construct the empty matrix for the geography
#-   make it nearly square and as small as possible
def calc_grid(node_cnt = 32):
    d = int(math.sqrt(node_cnt))
    if node_cnt == d*d: #- square
        rows=cols=d
    else:
        cols = d+1
        (rows,x) = divmod(node_cnt,cols)
        if x != 0: rows += 1

    return( rows, cols )
#- end :: calc_grid()


#- define the node map buffer
nm_buff = [] 


ant_tasks = {}
task_counts = {1:0,2:0,3:0,4:0,5:0,6:0}
def update_task_counts(ant_id,task):
    global ant_tasks
    global task_counts
    #- adjust the task counts
    if ant_id in ant_tasks:
	old_task = ant_tasks[ant_id]
	if old_task != task:
	    if task_counts[old_task] > 0: task_counts[old_task] -= 1
	    if task is not None:
		ant_tasks[ant_id] = task
                try:
		    task_counts[task] += 1         
                except:
                    print "??? task=",task, "ant_id=",ant_id
                    time.sleep(30)
	    else:
		del ant_tasks[ant_id]
    else:
	if task is not None:
	    ant_tasks[ant_id] = task
	    task_counts[task] += 1         


def read_node_map(nmfilename):
    try:
        nodemap_file = open(nmfilename)
        ncnt = 0
        while True:
            rec = nodemap_file.readline()
            ncnt += 1
            if rec.startswith("nm: <START>"):
                continue
            if rec.startswith("nm: <END>"):
                break
            else:
                nm_buff.append(rec.rstrip())
    
        nodemap_file.close() # close socket

    except IOError:
        exc_type, exc_value, exc_trbk = sys.exc_info()
        print "Error accessing the node map file (%s: %s)" % (nmfilename, exc_type, exc_value)
        sys.exit(0)



def main():
    SHOW_ENCLAVES = options.show_enclaves 
    UPDATE_DELAY = options.delay

    global task_counts


    print ">>------------------------------"
    print ">> options:",options
    print ">> colors:",STATE_COLORS
    print ""
     

    #-
    #- initialize signal handler to catch ^C (aka SIGINT)
    #-
    signal.signal(signal.SIGINT, signal_handler)

    #- if node map specified, read it in now.
    if options.nmfilename:
        print "using specified node map"
        read_node_map(options.nmfilename)
    else:
        print "using imbedded node map"
        read_node_map(options.tfile)

    if options.be_quiet is False:
        print "node map file read in"


    pygame.init()
    pygame.font.init()
    #screen = pygame.display.set_mode(WINSIZE,pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('HiveMind Demo')
    
    cell_bgcolor = THECOLORS["blue"]
    screen.fill(THECOLORS["black"])

    
    #- initialize the matrix of cells

    grid_rows = 0
    grid_cols = 0
    for line in nm_buff:

        matchObj = re.match('^nm:\s+ROWS\s+(\w+)\s*',line)
        if matchObj:
            grid_rows = int(matchObj.group(1))
            continue; 

        matchObj = re.match('^nm:\s+COLS\s+(\w+)\s*',line)
        if matchObj:
            grid_cols = int(matchObj.group(1))
            continue; 

        #- if we have
        if grid_rows > 0 and grid_cols > 0:
            break;
    #- end :: get grid info loop    

    if options.be_quiet is False:
        print ">>> grid_rows:",grid_rows
        print ">>> grid_cols:",grid_cols

    xoffset = 25
    yoffset = 15 
    border = 1

    box_size = (WINSIZE[1]-(xoffset*2))/(grid_rows-1)
    cell_size = box_size - border
    if options.be_quiet is False:
        print ">>> ",cell_size
 

    cells = {}
    for line in nm_buff:
        
        #- a placeholder cell (so we can render the grid as over a rectangular space
        matchObj = re.match('^nm:\s+(False)\s+(\d+)\s+(\d+)',line)
        if matchObj:
            row_idx = int(matchObj.group(2))
            col_idx = int(matchObj.group(3))
            ypos = row_idx*box_size + yoffset
            xpos = col_idx*box_size + xoffset
            node_id = 'null-'+str(row_idx)+'-'+str(col_idx)
            if options.be_quiet is False:
                print "*** (%d, %d) -> (%d, %d)" % (row_idx,col_idx,xpos,ypos)
            cell_color = INACTIVE_CELL_COLOR
            
            cells[node_id] = cell.Cell( node_id, screen, (col_idx,row_idx), cell_size, cell_bgcolor, cell_color )
            continue; 
        
        #- an active cell
        matchObj = re.match('^nm:\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)',line)
        if matchObj:
            node_id = matchObj.group(1)
            row_idx = int(matchObj.group(2))
            col_idx = int(matchObj.group(3))
            enclave = matchObj.group(4)
            ypos = row_idx*box_size + yoffset
            xpos = col_idx*box_size + xoffset
            if options.be_quiet is False:
                print "*** (%d, %d) -> (%d, %d)" % (row_idx,col_idx,xpos,ypos)

            if SHOW_ENCLAVES is True:
                cell_color = ENCLAVE_COLORS[enclave]
            else:
                cell_color = THECOLORS["white"]
            
            cells[node_id] = cell.Cell( node_id, screen, (col_idx,row_idx), cell_size, cell_bgcolor, cell_color )
            if options.be_quiet is False:
                print ">>> %s (%d,%d)" % (node_id, xpos, ypos)
            continue; 
    #- end :: initialze cells loop    
   

    #- draw the initial cells
    for node_id in cells.keys(): 
        pp = cells[node_id]
        cells[node_id].draw()

    if SHOW_PROJECT_LOGOS is True:
        hmlogo = pygame.image.load("HiveMind logo.png")
        hmrect = hmlogo.get_rect()

        ucdlogo = pygame.image.load("ucdavis logo.png")
        ucdrect = ucdlogo.get_rect()
        h = int(ucdrect.bottom *(float(hmrect.right)/ucdrect.right))
        ucdsmall = pygame.transform.scale(ucdlogo, (hmrect.right, h))
        screen.blit(ucdsmall, ( 1124, 20   ))
        screen.blit(hmlogo,   ( 1124, 40+h ))


	font = pygame.font.SysFont('Courier', 14)

	# Render the text
	text = font.render( ('%s' % options.tfile), True, THECOLORS['white'], THECOLORS['black'])

	# Create a rectangle
	textRect = text.get_rect()

	# Center the rectangle
	textRect.left = screen.get_rect().left + 20
	textRect.bottom = screen.get_rect().bottom - 60

	# Blit the text
	screen.blit(text, textRect)

#- update the screen to reflect the initial state
    pygame.display.update()
    #raw_input("foo")


    #----------------------------------------
    lcnt = 0
    buff = []
    try:
        trace_file = open(options.tfile)
        try:
            while True:
                line = trace_file.readline()
                if not line:
                    break
                if options.skip_lines and lcnt < options.skip_lines:
                    lcnt += 1
                    continue;
                buff.append(line.rstrip())
        finally: 
            trace_file.close() # close socket
    except IOError:
        exc_type, exc_value, exc_trbk = sys.exc_info()
        print "Error accessing the trace file (%s: %s)" % (options.tfile, exc_type, exc_value)
        sys.exit(0)

    if options.be_quiet is False:
        print "trace file read in"

    #prompt = str(cnt)
    #raw_input(prompt)
    
 
    #-  main event loop
    cnt = 0
    stime = time.time()
    done = False
    last_update_time = 0.0
    skip_to_next_target = False

    #-used to record last observed positin of an ant
    last_loc = {}

    delay_on = True
    trace_iter = iter(buff)
    while not done:
        #- get info from input feed
        try:
            line = trace_iter.next()
            cnt = cnt + 1
        except StopIteration:
            if options.loop_input is True:
                trace_iter = iter(buff)
            else:
                done = True
            continue

        #- modify node image:
        parms = []
        parms = line.split()

        if skip_to_next_target is True:
            try:
                if parms[3] != 'T': 
                    continue
                else:
                    skip_to_next_target = False
            except IndexError:
                    continue
            
        if options.be_quiet is False:
            print "\n", " ".join(parms), "\n"

        if parms[0] == 'nm:': #- ignore node map information (it was previously obtained)
            continue

        if parms[1].startswith('>'):
        #- We have a viewer command
            command = parms[1]
            
            if command == '>RESET':
                #- command to reset all nodes, clearing all ants, markers, and other state
                last_loc = {}
                for node_id in cells:
                    cells[node_id].reset()
                    cells[node_id].draw()
                    pygame.display.update()  #- force an update
                
                print "****************** GRID RESET *****************"
    
                if options.be_quiet is False:
                    print "GRID RESET"
    
    
            if command == '>PAUSE':
                delay = float(parms[2])
                
                if delay > 0:
                    #- command to force replay to pause. generally to allow reviewing specific display state
                    time.sleep(delay)
                    print "****************** PAUSING %s SECONDS *****************" % (delay)
    
                    if options.be_quiet is False:
                        print "PAUSING: %s" % (delay)
                else:
                    #- delay until key pressed
                    raw_input('<paused>')

        else:
        #- something to display
    
        #- ACTION CODES
        #- M  - ant moves
        #- C  - ant created 
        #- D  - ant destroyed
        #- R  - ant recruited
        #-
        #- T  - target set
        #- t  - targete cleared
        #- x  - marker set
        #- X  - marker cleared
        #-


          #- 12.277828 node-20 5700000002 M node-47 245 1 5 152
    
          time_stamp = parms[0]
          node_id = parms[1]
          ant_id = parms[2]
          action = parms[3]


          if node_id in cells:

            if options.be_quiet is False:
                print ">> ",parms
         
            #- ant moved to new location, update from/to nodes and redraw
            if action == 'M':
                #- extract Ant-Moved specific fields
		from_node = parms[4]
		age = int(parms[5])
		state = int(parms[6])
		task = int(parms[7])
		heading = int(parms[8])
		#ant_type = int(parms[9])


		update_task_counts(ant_id,task)


                #- remove ant from 'prior' node and redraw
		if ant_id in last_loc:
                  ll = last_loc[ant_id]
                  if ll != node_id: #- need to delete from display at prior location
                      if cells[ll].ants > 0: cells[ll].ants -= 1
                      cells[ll].draw()



                #- mark cell that pheromone is present
                if state == DROPPING:
                    cells[node_id].marker = heading #(heading - 45/2.0)
    
                if options.be_quiet is False:
                    print "MOVING ("+str(state)+")"

                #- move ant to 'to' node and redraw
                cells[node_id].ants += 1
                cells[node_id].count += 1 #- count how many times an ant was here
                cells[node_id].anttask = task
                if options.be_quiet is False:
                    #print ">> %s: %d" % (node_id, cells[node_id].count)
                    print "STATE:("+str(state)+")"
                cells[node_id].antcolor = STATE_COLORS[state]
                #cells[node_id].ant_type = ant_type
                cells[node_id].draw()
  
                last_loc[ant_id] = node_id
            
            #- ant died, remove ant from node and redraw
            if action == 'D':
                #- extract Ant-Died specific fields
                #- N/A

		update_task_counts(ant_id,None)

                #- if for some reason the ant was still listed as being on another node, delete it before going of
		if ant_id in last_loc:
                  ll = last_loc[ant_id]
                  if ll != node_id: #- need to delete from display at prior location
                    
                    if cells[ll].ants > 0: cells[ll].ants -= 1
                    cells[ll].draw()


                if cells[node_id].ants > 0: cells[node_id].ants -= 1

                if options.be_quiet is False:
                    print "DIEING"
                    #print ">> %s: %d" % (node_id, cells[node_id].count)
                cells[node_id].action = 'died'
                cells[node_id].draw()
                 
                #- ant is gone, so delete its prior location
                if ant_id in last_loc:
                    del last_loc[ant_id]

            #- new ant born, add ant to node and redraw
            if action == 'C':
                #- extract Ant-Created specific fields
		task = int(parms[4])

		update_task_counts(ant_id,task)

                cells[node_id].ants += 1
                if options.be_quiet is False:
                    print "BIRTHING"
                cells[node_id].count += 1 #- count how many times an ant was here
                cells[node_id].action = 'born'
                cells[node_id].anttask = task
                #print ">> %s: %d" % (node_id, cells[node_id].count)
                cells[node_id].draw()
   
                last_loc[ant_id]=node_id
    
            #- ant was recruited or otherwise changed task
            if action == 'R':
                #- extract Ant-Recruited specific fields
		task = int(parms[4])

		update_task_counts(ant_id,task)

                cells[node_id].task = task  #- changed task
                cells[node_id].action = 'recruited'
                cells[node_id].antcolor = ACTION_COLORS['recruited']
                if options.be_quiet is False:
                    print "ANT RECRUITED"
                cells[node_id].draw()


            #-
            #- Node related actions, i.e. not ant specific    
            #-
    
            #- extract Node action specific fields
            task = int(parms[7])

            #- an event of interest was occurred on the Node
            if action == 'T':
                cells[node_id].attack[task-1] = True #- actually attack type
                if options.be_quiet is False:

                    print "ATTACk TARGET SET"
                cells[node_id].draw()
                delay_on = False
    
    
            #- an event of interest was cleared from the Node
            if action == 't':
                cells[node_id].attack[task-1] = False #- clear attack from node
                if options.be_quiet is False:
                    print "ATTACk TARGET CLEARED"
                cells[node_id].draw()
                delay_on = False
    
    
            #- pheromone has been set by a broadcast
            if action == 'x':
                heading = int(parms[8])
                cells[node_id].marker = heading #- clear marker from node
                if options.be_quiet is False:
                    print "MARKER SET"
                cells[node_id].draw()
                delay_on = False
    
    
            #- pheromone has faded to zero on the Node
            if action == 'X':
                cells[node_id].marker = "" #- clear marker from node
                if options.be_quiet is False:
                    print "MARKER CLEARED"
                cells[node_id].draw()
                delay_on = False
    
            ''' 
            #- node has been reported as dead
            if action == '!':
                cells[node_id].cell_color = INACTIVE_CELL_COLOR
                if options.be_quiet is False:
                    print "NODE MARKED INACTIVE"
                cells[node_id].draw()
            '''
    
    
            #- update screen
            now = time.time()
            if now > (last_update_time + REFRESH_RATE):
                if options.be_quiet is False:
                    print ">> screen update (now:%.3f, last:%.3f, rate:%.3f, delay:%.3f" % (now, last_update_time, REFRESH_RATE,options.delay)

                font = pygame.font.SysFont('Courier', 14)

		# Render the text
		text = font.render( ('%s' % line+"     "), True, THECOLORS['white'], cell_bgcolor)

		# Create a rectangle
		textRect = text.get_rect()

		# Center the rectangle
		textRect.left = screen.get_rect().left + 20
		textRect.bottom = screen.get_rect().bottom - 40

		# Blit the text
		screen.blit(text, textRect)

                hpos = 500
		for k in task_counts:
		    text = font.render( ('%2s:%s   ' % (k,task_counts[k])), True, THECOLORS['white'], cell_bgcolor)
		    textRect = text.get_rect()
		    textRect.left = screen.get_rect().left + 10 + hpos
		    textRect.bottom = screen.get_rect().bottom - 40
		    screen.blit(text, textRect)
                    hpos = textRect.right


                pygame.display.update()
                last_update_time = now
    
            if delay_on:
                time.sleep(UPDATE_DELAY/1000.0)
            delay_on = True

        # Event Handling:
        events = pygame.event.get( )
        for e in events:
            if( e.type == QUIT ):
                done = True
                break
            
            elif (e.type == KEYDOWN):
                
                #print pygame.key.name(e.key)
                mods = pygame.key.get_mods()

                if( e.key == K_p ):
                    print '<paused>'
                    time.sleep(0.5)
                    pause_done = False
                    while not pause_done:
                        #time.sleep(0.5) #- just so this loop doesn't spin and suck cycles
                        p_events = pygame.event.get( )
                        for p_e in p_events:
                            if (p_e.type == KEYDOWN):
                                if( p_e.key == K_p ):
                                    pause_done = True
                    break
                
                if( e.key == K_1 and mods & KMOD_LSHIFT ):
                #if( e.key == K_EXCLAIM ):
                    command = raw_input(">> ")
                    try:
                        UPDATE_DELAY = int(command)                        
                    except:
                        print ("Invalid Input")
                    break
                
                if( e.key == K_PERIOD ):
                    if UPDATE_DELAY > 50:
                        UPDATE_DELAY -= 25
                    else:
                        UPDATE_DELAY -= 10 
                    if UPDATE_DELAY < 0: UPDATE_DELAY = 0
                    print "DELAY:",UPDATE_DELAY
                    break
                
                if( e.key == K_COMMA ):
                    if UPDATE_DELAY > 50:
                        UPDATE_DELAY += 25
                    else:
                        UPDATE_DELAY += 10 
                    print "DELAY:",UPDATE_DELAY
                    break
                
                if( e.key == K_ESCAPE ):
                    done = True
                    break
                
                #- skip until next target set
                if( e.key == K_t ):
                    task_counts = {1:0,2:0,3:0,4:0,5:0,6:0}
                    skip_to_next_target = True
                    for node_id in cells:
                        cells[node_id].reset()
                        cells[node_id].draw()
                    pygame.display.update()  #- force an update
                    break
                
                if( e.key == K_f ):
                    pygame.display.toggle_fullscreen()

    if options.wait_at_end:
        raw_input('<done>')

    print "Exiting!"

    etime = time.time()
    print "num moves: %d, duration:%7.2f secs" % (cnt,etime-stime)

    return
#- end :: main()



if __name__=="__main__":
    main()
