#!/usr/bin/env python

#-
#- HiveMind Ant Movement Heatmap Viewer
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 21 Sept 2011
#- Revised: v0.2 - 11 Mar 2012
#- Revised: v0.3 - 28 Sep 2012
#-

"""
Copyright (c) 2012 Regents of the University of the California

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

import cell_map

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
parser.add_option("-b", action='store_true', dest="batch", default=False, help="batch mode, no animation, just show final map")

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
    
    cell_bgcolor = THECOLORS["white"]
    screen.fill(THECOLORS["black"])

    
    total_count = 0

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
            
            cells[node_id] = cell_map.Cell( node_id, screen, (col_idx,row_idx), cell_size, cell_bgcolor, cell_color )
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

            cell_color = THECOLORS["white"]
            
            cells[node_id] = cell_map.Cell( node_id, screen, (col_idx,row_idx), cell_size, cell_bgcolor, cell_color )
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
                for node_id in cells.keys():
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
                if node_id in cells.keys():
                    cells[node_id].count += 1
                else:
                    cells[node_id].count = 1
             

                if options.batch is False and UPDATE_DELAY == 1:
                    foo = [cells[i].count for i in cells.keys()]
                    mxc = max( foo )
                    mnc = min( foo )
                    cells[node_id].draw(mxc,mnc)
                    pygame.display.update()
                       
                total_count += 1

            #- update screen
            now = time.time()
            if options.batch is False and UPDATE_DELAY > 1 and total_count % UPDATE_DELAY == 0:
                
                foo = [cells[i].count for i in cells.keys()]
                mxc = max( foo )
                mnc = min( foo )

                for n in cells:
                    cells[n].draw(mxc,mnc)

                font = pygame.font.SysFont('Courier', 14)

		# Render the text
		#text = font.render( ('%s' % line+"     "), True, THECOLORS['white'], cell_bgcolor)

		# Create a rectangle
		#textRect = text.get_rect()

		# Center the rectangle
		#textRect.left = screen.get_rect().left + 20
		#textRect.bottom = screen.get_rect().bottom - 40

		# Blit the text
		#screen.blit(text, textRect)

                pygame.display.update()
                last_update_time = now
    
        # Event Handling:
        events = pygame.event.get( )
        for e in events:
            if( e.type == QUIT ):
                done = True
                break
            
            elif (e.type == KEYDOWN):
                
                #print pygame.key.name(e.key)
                mods = pygame.key.get_mods()

                if(e.key == K_p):
                    print '<paused>'
                    print 'at movement', total_count
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
                    if UPDATE_DELAY < 1: UPDATE_DELAY = 1
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

    if options.batch is True: #- batch update of heat map on all data
        foo = [cells[i].count for i in cells.keys()]
	mxc = max( foo )
	mnc = min( foo )
        print "\nCell Counts --\n",foo,"\n"
        for n in cells:
            cells[n].draw(mxc,mnc)
        pygame.display.update()

    if options.wait_at_end:
        raw_input('<done>')

    print "Exiting!"

    etime = time.time()
    print "num moves: %d, duration:%7.2f secs" % (cnt,etime-stime)

    return
#- end :: main()



if __name__=="__main__":
    main()
