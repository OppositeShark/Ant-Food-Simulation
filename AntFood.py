# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 15:24:21 2021

@author: degog
"""
#%% Importing
import pygame
#importing stuff
from PIL import Image, ImageDraw
import random
import math
import copy

#%%Setup
#Window Size
width=400
height=400

#Starting Pygame
pygame.init()
screen=pygame.display.set_mode((width,height))
pygame.display.set_caption("Ant Food Simulation")

#Pheromones
#Trail away from the nest
BPImg=Image.new("RGBA",(width,height),(0,0,255,0))
BPheromones=BPImg.load()

#Trail towards the nest
RPImg=Image.new("RGBA",(width,height),(255,0,0,0))
RPheromones=RPImg.load()

#Food and Maze
FoodMazeImg=Image.new("RGBA",(width,height),0)
FoodMaze=FoodMazeImg.load()
Mazedraw = ImageDraw.Draw(FoodMazeImg)

#Frames
frameNum=0

#%%Colors
BLUE=(0,0,255)
RED=(255,0,0)
GREEN=(0,255,0)
YELLOW=(255,255,0)
WHITE=(255,255,255)
PINK=(255,0,255)
ORANGE=(255,100,0)
PURPLE=(100,0,255)
BLACK=(0,0,0)
CLEAR=(0,0,0,0)
#Specific Colors
WALL=BLACK+(255,)
FOOD=GREEN+(255,)
NEST=YELLOW+(150,)
#%%Map Making

#Seed
random.seed(None)
numTiles=lambda length,tile:math.ceil(length/tile)-1

#Food
def food(img,x,y,dev,num):
    for i in range(num*5):
        gx=random.gauss(0,dev)+x
        gy=random.gauss(0,dev)+y
        if 0<gx<width and 0<gy<height:
            img[gx,gy]=FOOD
    
#Maze Making
def RecursionMaze(draw,tile,wallWidth,box,color=(0,0,0,255)):
    if box==None:
        box=[0,0]+list(draw.size())
    
    boxwidth=box[2]-box[0]
    boxheight=box[3]-box[1]
        
    if boxwidth<=tile[0] or boxheight<=tile[1]:
        return
    
    #Simplification for calculating walls
    halfWidth=round(wallWidth/2)
    
    #Vertical Wall
    x=random.randint(1,numTiles(boxwidth,tile[0]))*tile[0]+box[0]
    draw.rectangle([x-halfWidth,box[1],x+halfWidth,box[3]],fill=color)
    
    #Horizontal Wall
    y=(random.randint(1,numTiles(boxheight,tile[1])))*tile[1]+box[1]
    draw.rectangle([box[0],y-halfWidth,box[2],y+halfWidth],fill=color)
    
    #Holes
    patch=random.randint(0,3)
    for i in range(4):
        if i==patch:
            continue
        if i%2==0:
            if i==0:
                holey=random.randint(0,numTiles((y-box[1]),tile[1]))*tile[1]+box[1]
            else:
                holey=random.randint(0,numTiles((box[3]-y),tile[1]))*tile[1]+y
            x1=x-halfWidth
            y1=holey+halfWidth+1
            x2=x+halfWidth
            y2=holey+tile[1]-halfWidth-1
        else:
            if i==1:
                holex=random.randint(0,numTiles((x-box[0]),tile[0]))*tile[0]+box[0]
            else:
                holex=random.randint(0,numTiles((box[2]-x),tile[0]))*tile[0]+x
            x1=holex+halfWidth+1
            y1=y-halfWidth
            x2=holex+tile[0]-halfWidth-1
            y2=y+halfWidth
        clearColor=BLACK+(0,)
        draw.rectangle([x1,y1,x2,y2],fill=clearColor)

    #Recursion
    RecursionMaze(draw,tile,wallWidth,[box[0],box[1],x,y],color)
    RecursionMaze(draw,tile,wallWidth,[x,box[1],box[2],y],color)
    RecursionMaze(draw,tile,wallWidth,[box[0],y,x,box[3]],color)
    RecursionMaze(draw,tile,wallWidth,[x,y,box[2],box[3]],color)

#Cell Size
squareSize=100
wallWidth=10
#Food Distribution
for i in range(10):
    x=random.randint(0,numTiles(width,squareSize))*squareSize+(squareSize//2)
    y=random.randint(0,numTiles(height,squareSize))*squareSize+(squareSize//2)
    food(FoodMaze,x,y,squareSize/6,20)
    
#Walls
RecursionMaze(Mazedraw,(squareSize,squareSize),wallWidth,(0,0,width,height))
Mazedraw.rectangle([0,0,width,wallWidth/2],fill=(0,0,0,255))
Mazedraw.rectangle([0,0,wallWidth/2,height],fill=(0,0,0,255))
Mazedraw.rectangle([width-(wallWidth/2),0,width,height],fill=(0,0,0,255))
Mazedraw.rectangle([0,height-(wallWidth/2),width,height],fill=(0,0,0,255))

#%%Ants
#Ant List
ants=[]

#Angles and Speeds
randomWalk=math.radians(5)
maxSpeed=3
acceleration=0.1
seeAngs={math.radians(i*s):10/i for i in (30,10) for s in (-1,1)}
seeAngs[0]=2
seeDist=10
#Weights and Colors
foodweight=15
wallweight=-10
returnFood=20
BlueWeight=lambda a:a/255*20
RedWeight=lambda a:a/255*20
distWeight=lambda d:1

def OutOfBounds(x,y):
        return x>=width or x<0 or y>=height or y<0
#Ant Class
class ant():
    
    def __init__(self,x,y,ang):
        self.x=x
        self.y=y
        self.ang=ang
        self.food=False
        self.speed=2
        ants.append(self)
    
    def dropPheromone(self):
        #Sets image pixel to red or blue
        if self.x>width or self.x<0 or self.y>height or self.y<0:
            return
        if self.food==True:
            RPheromones[self.x,self.y]=tuple([RPheromones[self.x,self.y][i]+[0,0,0,100][i] for i in range(4)])
        else:
            BPheromones[self.x,self.y]=tuple([BPheromones[self.x,self.y][i]+[0,0,0,100][i] for i in range(4)])
    
    def pickFood(self,x,y):
        self.food=True
        FoodMaze[x,y]=CLEAR
    
    def turnAround(self):
        self.ang+=math.pi
        self.ang+=random.uniform(-randomWalk,randomWalk)
        
    def senses(self):
        #Creating Angle Choices
        choice={}
        for i in seeAngs.keys():
            choice[i]=1
        
        #Sight
        for ang,weight in seeAngs.items():
            direction=self.ang+ang
            cosDirection=math.cos(direction)
            sinDirection=math.sin(direction)
            for i in range(1,seeDist+1):
                #(x,y)
                x=round(i*cosDirection+self.x)
                y=round(i*sinDirection+self.y)
                #If the detection is out of bounds
                if OutOfBounds(x,y): 
                    break
                #Distance Weight
                iWeight=distWeight(i)
                #Checking if theres a wall
                PixVal=FoodMaze[x,y]
                if PixVal==WALL:
                    choice[ang]+=iWeight*wallweight
                    break
                #If they have food
                if self.food:
                    #Attraction to nest
                    if PixVal==NEST:
                        choice[ang]+=returnFood
                    #Blue Pheromones
                    PixVal=BPheromones[x,y]
                    if PixVal[:3]==BLUE:
                        choice[ang]+=iWeight*BlueWeight(PixVal[3])
                #If they don't have food
                else:
                    #Looking and picking up food
                    if PixVal==FOOD:
                        choice[ang]+=iWeight*foodweight
                        if self.speed>i:
                            self.pickFood(x,y)
                            self.turnAround()
                    #Red Pheromones
                    PixVal=RPheromones[x,y]
                    if PixVal[:3]==RED:
                        choice[ang]+=iWeight*RedWeight(PixVal[3])    
            #Angle Weight
            choice[ang]*=weight
            
        #Section of (0,1)
        choiceCopy=copy.deepcopy(choice)
        choice={k:v for k,v in choiceCopy.items() if v>=0}
        #If all values are bad
        if len(choice.keys())==0:
            self.turnAround()
            return {}
        
        #If all values are 0
        if list(choice.values()).count(0)==len(list(choice.keys())):
            return {}
        
        #Random choice with weights
        totalWeight=sum(choice.values())
        for i in choice.keys():
            choice[i]/=totalWeight
        return choice
    
    def move(self):
        #Move Forward
        self.x+=self.speed*math.cos(self.ang)
        self.y+=self.speed*math.sin(self.ang)
        
        #Random Walk
        self.ang+=random.gauss(0,randomWalk)
        
        #Sensing
        direction=random.random()
        sight=self.senses()
        section=0
        for ang,weight in sight.items():
            section+=weight
            if direction<=section:
                self.ang+=ang
                break
        
        #Collision Detection
        if 0<self.x<width and 0<self.y<height:
            #Reverse when in wall
            if FoodMaze[self.x,self.y]==WALL:
                self.turnAround()
            #Put Food
            elif self.food and FoodMaze[self.x,self.y]==NEST:
                self.food=False
                self.turnAround()
            
        #Accelerate
        if self.speed<maxSpeed:
            self.speed+=acceleration
        
        #Simplifying Angle
        self.ang=self.ang%(2*math.pi)

    def run(self):
        if OutOfBounds(self.x,self.y):
            self.kill()
            return
        self.move()
        self.dropPheromone()
        
    def kill(self):
        ants.remove(self)
        del self
        
    
    def draw(self, screen):
        screen.fill((0,0,0,255),rect=[self.x,self.y,1,1])
        if self.food==True:
            cosx=math.cos(self.ang)
            if cosx<0:
                x=self.x+math.floor(cosx)
            else:
                x=self.x+math.ceil(cosx)
            siny=math.sin(self.ang)
            if siny<0:
                y=self.y+math.floor(siny)
            else:
                y=self.y+math.ceil(siny)
            screen.fill((0,255,0,255),rect=[x,y,1,1])
            
#%% Fading Pheromones
def fade(PixelAccess):
    for x in range(width):
        for y in range(height):
            color=PixelAccess[x,y]
            if color[3]==0:
                continue
            PixelAccess[x,y]=color[:3]+(color[3]-1,)
            
#%%Nest
nestx=random.randint(0,numTiles(width,squareSize))*squareSize+(squareSize//2)
nesty=random.randint(0,numTiles(height,squareSize))*squareSize+(squareSize//2)
nestradius=(squareSize-2*wallWidth)/2
Mazedraw.ellipse((nestx-nestradius,nesty-nestradius,nestx+nestradius,nesty+nestradius),fill=YELLOW+(150,))

#%%Creating Ants
numants=10
for i in range(numants):
    ant(nestx,nesty,random.uniform(0,2*math.pi))

#%%Running
running=True
fps=10
delay=1000/fps
lastFrame=0
hold=False
while running:
    #Events
    for event in pygame.event.get():
        #Quitting
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.MOUSEBUTTONDOWN:
            hold=True
            FoodMaze[event.pos[0],event.pos[1]]=FOOD
        elif event.type==pygame.MOUSEBUTTONUP:
            hold=False
        #Mouse Motion
        elif event.type==4:
            if hold:
                FoodMaze[event.pos[0],event.pos[1]]=FOOD
            
    diffTime=pygame.time.get_ticks()-lastFrame
    if diffTime<delay:
        continue
    
    #Background
    screen.fill((255,255,255,255))
    
    #Calculations
    #Ant Movement
    for i in ants:
        i.run()
    #Pheromone Reduction
    if frameNum%5==0:
        for i in [BPheromones,RPheromones]:
            fade(i)
    
    #Drawing Pheromones, Food, and Walls
    BPImg.save("BluePheromones.png","PNG")
    RPImg.save("RedPheromones.png","PNG")
    FoodMazeImg.save("AntFoodMaze.png","PNG")
    pygBP=pygame.image.load("BluePheromones.png")
    pygRP=pygame.image.load("RedPheromones.png")
    pygFood=pygame.image.load("AntFoodMaze.png")
    for i in (pygBP,pygRP,pygFood):
        screen.blit(i, (0,0))
    
    #Drawing Ants
    for i in ants:
        i.draw(screen)

    #Update Screen
    pygame.display.update()
    frameNum+=1
    lastFrame=pygame.time.get_ticks()
    
pygame.quit()