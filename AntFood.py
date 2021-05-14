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
import sys
import os

#%%Setup

#Window Size
width=700
height=width

#Seed
seed=None

#Cell Size
numsquares=10
squareSize=width/numsquares
wallWidth=5

#Food Clusters
NumFoodClusters=round(numsquares**2/4)
FoodInCluster=round(squareSize*4)

#Ants
#Angles and Sight
randomWalk=math.radians(5)
seeAngs={math.radians(i*s):5/i for i in (60,40,30,10) for s in (-1,1)}
seeAngs[0]=2
seeDist=10
maxturn=math.radians(30)
#Speed
maxSpeed=1
acceleration=0.1
#Weights and Colors
foodweight=40
wallweight=-200
returnFood=200
BlueWeight=lambda a:a/2
BlueAvoidWeight=lambda a:-a/50
RedWeight=lambda a:a/5
AvoidFoodWeight=-60
distWeight=lambda d:0.8**d
#Number of Ants
numants=100
#FPS
fps=10
#Lasting Pheromones
LastLength=500
fadeRate=math.ceil(LastLength/50)
#%%Starting
global BP
global BPheromones

def ResetImgs():
    #Pheromones
    #Trail away from the nest
    global BPImg
    BPImg=Image.new("RGBA",(width,height),(0,0,255,0))
    global BPheromones
    BPheromones=BPImg.load()
    
    #Trail towards the nest
    global RPImg
    RPImg=Image.new("RGBA",(width,height),(255,0,0,0))
    global RPheromones
    RPheromones=RPImg.load()
    
    #Food and Maze
    global FoodMazeImg
    FoodMazeImg=Image.new("RGBA",(width,height),0)
    global FoodMaze
    FoodMaze=FoodMazeImg.load()
    global Mazedraw
    Mazedraw = ImageDraw.Draw(FoodMazeImg)
ResetImgs()

#Frames
frameNum=0
def resetFrames():
    global frameNum
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

#%%Ants
#Ant List
ants=[]
def OutOfBounds(x,y):
    return x>=width or x<0 or y>=height or y<0

#Ant Class
updateList=[]
def updatePixel(x,y):
    rect=pygame.Rect(x,y,1,1)
    updateList.append(rect)
    
class ant():
    def __init__(self,x,y,ang):
        self.x=x
        self.y=y
        self.ang=ang
        self.food=False
        self.speed=0
        self.lastFood=(0,0)
        ants.append(self)
    
    def dropPheromone(self):
        #Sets image pixel to red or blue
        if self.x>width or self.x<0 or self.y>height or self.y<0:
            return
        if self.food==True:
            RPheromones[self.x,self.y]=RED+(RPheromones[self.x,self.y][3]+50,)
        else:
            BPheromones[self.x,self.y]=BLUE+(BPheromones[self.x,self.y][3]+50,)
    
    def pickFood(self,x,y):
        self.food=True
        FoodMaze[x,y]=CLEAR
        
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
                #screen.fill(BLACK,rect=[x,y,1,1])
                #ant.updatePixel(x,y)
                
                #If the detection is out of bounds
                if OutOfBounds(x,y): 
                    break
                #Distance Weight
                iWeight=distWeight(i)
                #FoodMaze Pixel
                PixVal=FoodMaze[x,y]
                #Check if it's blank
                if PixVal==CLEAR:
                    pass
                #Checking if theres a wall
                elif PixVal==WALL:
                    choice[ang]+=iWeight*wallweight
                    break
                #Looking and picking up food
                elif not self.food and PixVal==FOOD:
                    choice[ang]+=iWeight*foodweight
                    if self.speed>i:
                        self.pickFood(x,y)
                        self.ang+=math.pi
                #Attraction to nest
                elif self.food and PixVal==NEST:
                    choice[ang]+=returnFood
                #If they have food
                PixVal=BPheromones[x,y]
                if self.food:
                    #Blue Pheromones
                    if PixVal[:3]==BLUE:
                        choice[ang]+=iWeight*BlueWeight(PixVal[3])
                    PixVal=FoodMaze[x,y]
                    if PixVal==FOOD:
                        choice[ang]+=iWeight*AvoidFoodWeight
                #If they don't have food
                else:
                    #Blue Pheromones
                    if PixVal[:3]==BLUE:
                        choice[ang]+=iWeight*BlueAvoidWeight(PixVal[3])
                    #Red Pheromones
                    PixVal=RPheromones[x,y]
                    if PixVal[:3]==RED:
                        choice[ang]+=iWeight*RedWeight(PixVal[3])    
            #Angle Weight
            if choice[ang]>=0:
                choice[ang]*=weight
            else:
                choice[ang]/=weight
        
        
        rangeVals=(max(choice.values())-min(choice.values()))/100
        for i in choice.keys():
            choice[i]/=rangeVals
            choice[i]=1.5**choice[i]
                
        #Random choice with weights
        totalWeight=sum(choice.values())
        if totalWeight==0:
            return seeAngs
        for i in choice.keys():
            choice[i]/=totalWeight
        return choice
    
    def move(self):
        #Move Forward
        self.x+=self.speed*math.cos(self.ang)
        self.y+=self.speed*math.sin(self.ang)
        
        goStraight=False
        
        #Collision Detection
        if 0<self.x<width and 0<self.y<height:
            #Put Food
            if FoodMaze[self.x,self.y]==NEST:
                if self.food:
                    self.food=False
                    self.ang+=math.pi
                goStraight=True
            elif FoodMaze[self.x,self.y]==WALL:
                self.restart()
        
        #Sensing & Turning
        direction=random.random()
        sight=self.senses()
        section=0
        if not goStraight:
            #Random Walk
            self.ang+=random.gauss(0,randomWalk)
            #Sensing
            for ang,weight in sight.items():
                section+=weight
                if direction<=section:
                    if ang>maxturn:
                        ang=maxturn
                    elif ang<-maxturn:
                        ang=-maxturn
                    self.ang+=ang
                    break
                    
        #Accelerate
        if self.speed<maxSpeed:
            self.speed+=acceleration
        
        #Simplifying Angle
        self.ang=self.ang%(2*math.pi)
            
    def run(self):
        if OutOfBounds(self.x,self.y):
            self.restart()
            return
        updatePixel(self.x,self.y)
        self.move()
        self.dropPheromone()
        updatePixel(self.x,self.y)
        
    def restart(self):
        self.food=False
        self.x=nestx
        self.y=nesty
        self.ang=random.uniform(0,2*math.pi)
    
    def draw(self, screen):
        screen.fill((0,0,0,255),rect=[self.x,self.y,1,1])
        updatePixel(self.lastFood[0],self.lastFood[1])
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
            self.lastFood=(x,y)
            updatePixel(x,y)
            
#%%Creating Ants
def makeAnts():
    ants=[]
    for i in range(numants):
        ant(nestx,nesty,random.uniform(0,2*math.pi))
        
#%%Map Making

#Seed
random.seed(seed)
numTiles=lambda length,tile:math.ceil(length/tile)-1

#Food
def food(img,x,y,dev,num):
    #Random Clusters
    for i in range(num):
        gx=random.gauss(0,dev)+x
        gy=random.gauss(0,dev)+y
        if 0<gx<width and 0<gy<height:
            img[gx,gy]=FOOD
    
#Maze Making
path="\\".join(os.path.abspath("AntFood.py").split("\\")[:-2])
if path not in sys.path:
    sys.path.insert(0,path)
from MazeDrawer import RecursionMaze

def drawFood():
    #Food Distribution
    for i in range(NumFoodClusters):
        x=random.randint(0,numTiles(width,squareSize))*squareSize+(squareSize//2)
        y=random.randint(0,numTiles(height,squareSize))*squareSize+(squareSize//2)
        food(FoodMaze,x,y,squareSize/6,FoodInCluster)
    
def drawWalls():
    #Walls
    RecursionMaze(Mazedraw,(squareSize,squareSize),wallWidth,(0,0,width,height))
    #4 Walls
    Mazedraw.rectangle([0,0,width,wallWidth/2],fill=(0,0,0,255))
    Mazedraw.rectangle([0,0,wallWidth/2,height],fill=(0,0,0,255))
    Mazedraw.rectangle([width-(wallWidth/2),0,width,height],fill=(0,0,0,255))
    Mazedraw.rectangle([0,height-(wallWidth/2),width,height],fill=(0,0,0,255))

nestx=0
nesty=0
def setNest():
    global nestx
    nestx=random.randint(0,numTiles(width,squareSize))*squareSize+(squareSize//2)
    global nesty
    nesty=random.randint(0,numTiles(height,squareSize))*squareSize+(squareSize//2)

def drawNest():
    nestradius=(squareSize-2*wallWidth)/3
    Mazedraw.ellipse((nestx-nestradius,nesty-nestradius,nestx+nestradius,nesty+nestradius),fill=YELLOW+(150,))

def drawMaze():
    ResetImgs()
    drawFood()
    drawWalls()
    setNest()
    drawNest()
    
#%%Main Function
#%% Fading Pheromones
def fade(PixelAccess):
    for x in range(width):
        for y in range(height):
            color=PixelAccess[x,y]
            if color[3]==0:
                continue
            PixelAccess[x,y]=color[:3]+(color[3]-1,)
            
def saveImgs():
    BPImg.save("BluePheromones.png","PNG")
    RPImg.save("RedPheromones.png","PNG")
    FoodMazeImg.save("AntFoodMaze.png","PNG")
    Img=BPImg.copy()
    Img.alpha_composite(RPImg)
    Img.save("RedBlue.png","PNG")
    Img.alpha_composite(FoodMazeImg)
    Img.save("FullImg.png","PNG")

def runSimulation():
    '''
    Runs the simulation
    '''
    running=True
    makeAnts()
    
    #Starting Pygame
    pygame.init()
    screen=pygame.display.set_mode((width,height))
    pygame.display.set_caption("Ant Food Simulation")

    #Drawing Pheromones/Food
    hold=False
    modeTypes=["Food","Red","Blue","Ant"]
    mode=0
    
    #Initial Map
    screen.fill((255,255,255,255))
    FoodMazeImg.save("AntFoodMaze.png","PNG")
    pygFood=pygame.image.load("AntFoodMaze.png")
    for i in (pygFood,):
        screen.blit(i, (0,0))
    pygame.display.update()
    
    #Running
    while running:
        #Events
        for event in pygame.event.get():
            #Quitting
            if event.type==pygame.QUIT:
                running=False
            elif event.type==pygame.MOUSEBUTTONDOWN:
                hold=True
                #Placing Pixels
                if modeTypes[mode]=="Food":
                    FoodMaze[event.pos[0],event.pos[1]]=FOOD
                elif modeTypes[mode]=="Red":
                    RPheromones[event.pos[0],event.pos[1]]=RED+(255,)
                updatePixel(event.pos[0],event.pos[1])
                
            elif event.type==pygame.MOUSEBUTTONUP:
                hold=False
            #Mouse Motion
            elif event.type==4:
                if hold:
                    FoodMaze[event.pos[0],event.pos[1]]=FOOD
                    updatePixel(event.pos[0],event.pos[1])
            #Key Down
            elif event.type==2:
                #Down Button
                if event.key==274:
                    saveImgs()
                
        #Background
        screen.fill((255,255,255,255))
    
        #Calculations
        #Ant Movement
        for inum,i in enumerate(ants):
            i.run()
            #Pheromone Reduction
        global frameNum
        if frameNum%fadeRate==0:
            for i in [BPheromones,RPheromones]:
                fade(i)
    
        #Drawing Pheromones, Food, and Walls
        pygBP=pygame.image.fromstring(BPImg.tobytes(), BPImg.size, BPImg.mode)
        pygRP=pygame.image.fromstring(RPImg.tobytes(), RPImg.size, RPImg.mode)
        pygFood=pygame.image.fromstring(FoodMazeImg.tobytes(), FoodMazeImg.size, FoodMazeImg.mode)
        pygame.image
        for i in (pygBP,pygRP,pygFood):
            screen.blit(i, (0,0))
    
        #Drawing Ants
        for i in ants:
            i.draw(screen)

        #Update Screen
        global updateList
        pygame.display.update(updateList)
        updateList=[]
        frameNum+=1
    pygame.quit()
    saveImgs()

def run():
    '''
    Sets up the simulation and runs it
    '''
    drawMaze()
    runSimulation()

if __name__=="__main__":
    run()