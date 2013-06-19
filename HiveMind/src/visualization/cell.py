#!/usr/bin/env python

#-
#- HiveMind - Visualizer routines for the displayed Cells
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
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
from math import sin, cos, radians, ceil
import random
import string

pl2 = None

def roof(num):
    return int(ceil(num))

def make_nshex(side):
    """Given the length of a hexagon side, return the pointslist and
       bounding rectangle of hexagon"""
    global pl2
    s = side
    hexh = roof(sin(radians(30))*s)
    r    = roof(cos(radians(30))*s)
    rech = s + (2*hexh)
    recw = 2*r
    size = [roof(recw), roof(rech)]
    pl = [(0, hexh), (.5*recw,0), (recw,hexh), (recw, rech-hexh), (.5*recw, rech), (0, rech - hexh)]
    pl2 = [(1, 1+hexh), (.5*recw,2), (recw-2,hexh+1), (recw-2, rech-hexh-1), (.5*recw, rech-2), (2, rech - hexh-1)]
    return (pl, pl2, size)
    

class Cell:
    def __init__(self, cell_id, screen, position, width, background, cell_color):

        self.node_id = cell_id

        self.screen = screen
        screensize = self.screen.get_size()
        self.screenwidth = screensize[0]
        self.screenheight = screensize[1]

        # color of the box
        self.bgcolor = background
        self.cell_color = cell_color

        # Position of Box on the Screen
        self.col = position[0]
        self.row = position[1]

        # calculated dimenstions and positions for the cell based on width and x,y position
	side = roof(width / ( 2 * cos(radians(30))))

        pl, pl2, size = make_nshex(side)

        hex_rad_v = roof(sin(radians(30))*side)
        hex_rad_h = roof(cos(radians(30))*side)
        rech = side + (2*hex_rad_v)
        recw = 2 * hex_rad_h
        rowh = rech - hex_rad_v
        self.width = recw
        self.height = rech

        if self.row&1:
            hex_pos = (10+.5*size[0]+size[0]*self.col,10+rowh*self.row)
        else:
            hex_pos = (10+size[0]*self.col,10+rowh*self.row)
	self.x = int(hex_pos[0])
        self.y = int(hex_pos[1])

	hexa = pygame.Surface(size)
	hexa.fill([1,0,0])
	hexa.set_colorkey([1,0,0])
	pygame.draw.polygon(hexa, self.bgcolor, pl)
	pygame.draw.polygon(hexa, self.cell_color, pl2)
        self.surface = hexa

        self.antcolor = (128,128,128)

        self.action = ''
        self.count = 0
        self.ants = 0 
        self.anttask = 0
        self.attack = [False,False,False,False,False]
        self.marker = ""
        self.alert = 0

    def change_bg(self, new_bg):
        global pl2
	pygame.draw.polygon(self.surface, new_bg, pl2)

    def reset(self):

        self.action = ''
        self.count = 0
        self.ants = 0 
        self.anttask = 0
        self.attack = [False,False,False,False,False]
        self.marker = ""
        self.alert = 0
        self.alert_set = False

        
        
        
    def draw(self):


        # redraw the basic cell w/o markup
        self.screen.blit(self.surface,(self.x,self.y))
        
        # label the cell
        font = pygame.font.SysFont('Ariel',14)
        id_number  = string.replace(self.node_id,"node-","")
        label = '('+id_number+')'
        text = font.render(label, 1, THECOLORS['grey20'], self.cell_color )
        textRect = text.get_rect()
	textRect.centerx = self.surface.get_rect().centerx + self.x
	textRect.top = self.y + textRect.height + 5
        self.screen.blit(text,textRect)

        # If the cell has an alertable issue, change the box color to the alert color
        #self.rect = pygame.rect.Rect(self.x, self.y, self.width, self.height)
        #if self.alert > 0:
        #    self.alert -= 1
        #    cur_boxcolor = THECOLORS["black"]

        # Draw the new box
        #pygame.draw.rect( self.screen, cur_boxcolor, self.rect )

    #- label the box          
        #xxx = self.node_id.split('-')
        #print ">>"+self.node_id+"<<"
	#font = pygame.font.SysFont('Ariel',16)
        ##text = font.render('n-'+xxx[1], 1, THECOLORS['grey50'], cur_boxcolor)
        #text = font.render('n-???', 1, THECOLORS['grey50'], cur_boxcolor)
        #self.screen.blit(text,(self.x,self.y))

        if self.ants > 0:
            pygame.draw.circle(self.screen, self.antcolor, [self.x+self.width/2,self.y+self.height/2], self.width/4)
            #if self.ant_type == 2:
            #    pygame.draw.circle(self.screen, self.antcolor, [self.x+self.width/2,self.y+self.height/2], self.width/4)
            #else:
            #    pygame.draw.circle(self.screen, self.antcolor, [self.x+self.width/2,self.y+self.height/2], self.width/4)

            #- label the sensor with its task type          
            font = pygame.font.SysFont('Ariel',20)
            label = str(self.anttask)
            text = font.render(label, 1, THECOLORS['grey90'], self.antcolor)
            fw,fh = font.size(label)
            self.screen.blit(text,(self.x+self.width/2-fw/2,self.y+self.height/2-fh/2))

        if self.action == 'born':
            pygame.draw.circle(self.screen, THECOLORS["forestgreen"], [self.x+self.width/2,self.y+self.height/2], self.width/8)
            self.action = ''

        if self.action == 'died':
            pygame.draw.circle(self.screen, (0,0,0), [self.x+self.width/2,self.y+self.height/2], self.width/8)
            self.action = ''


        #-
        #- draw dots for each attack remaining on the node. Place them along the bottom between the possible marker dot locations"
        #-
        m = self.width * 0.25
        w = self.width - m
        h = self.height
        dotsize = roof(w/8)
        for i,attack in enumerate(self.attack):
            if attack is True:
                pygame.draw.circle(self.screen, THECOLORS["red"], [self.x + m/2 + w/5*i + dotsize, self.y + h * 0.85 - dotsize], dotsize)


        #-
        #- draw the trail marker in the location nearest where the dropping ant came from
        #-
        if self.marker is not "":
            marker_width = self.width/15
 
	    rev_dir = (self.marker) % 360
            #rev_dir = self.marker
            hex_dir = rev_dir

            """
            #- get the position along the cell edge to draw the marker
            if 0 <= rev_dir <  60:
                #- up right -
                hex_dir = 30
            elif  60 <= rev_dir < 120:
                #- right -
                hex_dir = 90
            elif 120 <= rev_dir < 180:
                #- down right -
                hex_dir = 150
            elif 180 <= rev_dir < 240:
                #- down left -
                hex_dir = 210
            elif 240 <= rev_dir < 300:
                #- left -
                hex_dir = 270
            elif 300 <= rev_dir < 360:
                #- up left -
                hex_dir = 330
            """


            marker_size = int(self.height/15)
            #px = 0 + (self.width/2 - marker_size-4) * sin(radians(self.marker-180))
            #py = 0 + (self.height/2 - marker_size-4) * -cos(radians(self.marker-180))
            px = 0 + (self.width/2 - marker_size-4) * sin(radians(hex_dir))
            py = 0 + (self.height/2 - marker_size-4) * -cos(radians(hex_dir))
                 
            #- draw the indicator that the pheromone marker is present                
            pygame.draw.circle(self.screen, THECOLORS["sienna4"], [self.x+self.width/2+px, self.y+self.height/2+py], marker_size)

        #if self.alert > 0:
        #    #- label the alert symbol on the cell          
        #    font = pygame.font.SysFont('Ariel',50)
        #    label = "!"
        #    text = font.render(label, 1, THECOLORS['red'], cur_boxcolor )
        #    fw,fh = font.size(label)
        #    self.screen.blit(text,(self.x+self.width/2-fw/2,self.y+self.width/2-fh/2))
        

        #pygame.display.update()


    def setBackgroundColor(self, color):
        self.bgcolor=color
        self.boxcolor=color



if __name__=="__main__":

    WINSIZE = [1024,768]
    #WINSIZE = [640,480]

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode(WINSIZE)
    #screen = pygame.display.set_mode(WINSIZE,0,8)
    pygame.display.set_caption('HiveMind Demo')

    cell_bgcolor = THECOLORS["black"]
    cell_color = THECOLORS["white"]
    screen.fill(THECOLORS["black"])

    dz = "ur r dr dl l ul".split()


    font = pygame.font.SysFont('Ariel',14)

    #myrect = pygame.rect.Rect(15,15,40,20)
    #mybox = pygame.Surface((40,20))
    #pygame.draw.rect( screen, [0,255,0], myrect)

    hive = {}

    col_cnt  = 15 
    row_cnt  = 15


    shz = (WINSIZE[0]/(col_cnt))
    svr = (WINSIZE[1]/(row_cnt))
    
    size = min(shz,svr)

    for x in range(col_cnt):
        for y in range(row_cnt):

            name = str(x)+","+str(y)            

            cell_color = [random.randint(0,127)+128,random.randint(0,127)+128,random.randint(0,127)+128]


	    cell = Cell( name, screen, (x,y), size, cell_bgcolor, cell_color )
 
            if (2*x+y) % 7 == 0: 
                cell.ants = 1
                cell.anttask = (3*x+y) % 4
            
            cell_index = (x*5+y)
            if cell_index < 7:
                cell.marker = cell_index * 60 + 30
            #cell.attack = [i%2==0, i%3==0, i%4==0, i%5 == 0]

            hive[name] = cell


    col_cnt  = 15 
    row_cnt  = 15
    for x in range(col_cnt):
        for y in range(row_cnt):
            name = str(x)+","+str(y)            

            hive[name].draw()

    pygame.display.update()

    raw_input("done")
