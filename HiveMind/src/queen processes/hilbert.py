
#-
#- Generate Hilbert Curve
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

 
size = 10
pos = (0,0)
direction = 2

hilbert_series = []


def hilbert(level, angle):
    global direction
    global pos

    #print "\nhilbert (",level,angle,")"

    if level == 0:
        #print int(xcor()/10), int(ycor()/10),
        #print "<%d, %d>" % (pos[0], pos[1])
        hilbert_series.append(pos)
        #print ""
        return
    
    grid_angle = angle/90
    #print ">> grid_angle",grid_angle
    #print ">> initial heading:",heading()

    #right(angle)
    direction = (direction + grid_angle + 4) % 4
    #print ">> turning right to %s (%s)" % (direction, grid_angle)
    #print ">>     heading   ",heading()

    hilbert(level - 1, -angle)
    #forward(size)
    pos = grid_forward(direction,pos)

    #left(angle)
    direction = (direction - grid_angle + 4) % 4
    #print ">> turning left to %s (%s)" % (direction, grid_angle)
    #print ">>     heading   ",heading()

    hilbert(level - 1, angle)
    #forward(size)
    pos = grid_forward(direction,pos)

    hilbert(level - 1, angle)

    #left(angle)
    direction = (direction - grid_angle + 4) % 4
    #print ">> turning left to %s (%s)" % (direction, grid_angle)
    #print ">>     heading   ",heading()

    #forward(size)
    pos = grid_forward(direction,pos)

    hilbert(level - 1, -angle)

    #right(angle)
    direction = (direction + grid_angle + 4) % 4
    #print ">> turning right to %s (%s)" % (direction, grid_angle)
    #print ">>     heading   ",heading()
 



def grid_forward (direction,pos):
    
    x = pos[0]; y = pos[1]
    if direction == 0:
        x -= 1; y += 0
    elif direction == 1:
        x += 0; y += 1
    elif direction == 2:
        x += 1; y -= 0
    elif direction == 3:
        x -= 0; y -= 1
    else:
        print "ERROR: diection out of bounds"

    #print "moving: (%s,%s) dir=%d to  (%s,%s)" % (pos[0],pos[1],direction,x,y)
    return (x,y)


def get_series(level):
    hilbert(level,-90)
    return hilbert_series


def main():

    hilbert_series = get_series(5)

    print hilbert_series


if __name__=="__main__": main()
