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
import threading

#%%Setup

#Window Size
width=300
height=width

#Seed
seed=None

#Cell Size
numRectX=5
numRectY=numRectX
wallWidth=2

#Number of Food Clusters
NumFoodClusters=math.ceil(numRectX*numRectY/4)

#Ants
lifespan=width*height/20
#Angles and Sight
randomWalk=math.radians(3)
angs=(45,90)
seeAngs={math.radians(i*s):20/i for i in angs for s in (-1,1)}
seeAngs[0]=2
seeDist=10
maxturn=math.radians(30)
angChangeWeight = 0.05
maxInfluence = math.radians(10)
#Speed
maxSpeed=1
acceleration=0.1
#Weights and Colors
foodweight=2000
wallweight=-2000*seeDist/2
returnFood=2000
BlueWeight=lambda a:a*5
BlueAvoidWeight=lambda a:-a
RedWeight=lambda a:a*5
AvoidFoodWeight=wallweight
distWeight=lambda d:0.9**d
#Number of Ants
numants=200
#Threading
numThreads=4
#Lasting Pheromones
putAmount=math.ceil(500/numants)
LastLength=width*3
fadeRate=math.ceil(LastLength/putAmount)
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
ANTCOLOR=BLACK+(255,)
TONEST=BLUE
AWAYNEST=RED
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

def avgAng(ang1,ang2,ranges):
    if abs(ang1-ang2)>ranges/2:
        return (max(ang1,ang2)+min(ang1,ang2)+ranges)/2%ranges
    else:
        return (ang1+ang2)/2
class ant():
    def __init__(self,x,y,ang):
        self.x=x
        self.y=y
        self.ang=ang
        self.food=False
        self.speed=0
        self.lastFood=(0,0)
        self.placePheromone=True
        self.life = lifespan
        ants.append(self)
    
    toShade = 255/math.pi/2
    def dropPheromone(self):
        #Sets image pixel to red or blue
        if self.x>width or self.x<0 or self.y>height or self.y<0:
            return
        if self.food==True:
            pastVal = RPheromones[self.x,self.y]
            ang = avgAng(pastVal[2], self.ang*ant.toShade, 255)
            RPheromones[self.x,self.y]=(255,round(ang), 0, pastVal[3]+putAmount)
        else:
            pastVal = BPheromones[self.x,self.y]
            ang = avgAng(pastVal[2], self.ang*ant.toShade, 255)
            BPheromones[self.x,self.y]=(0,round(ang), 255, pastVal[3]+putAmount)
    
    def pickFood(self,x,y):
        self.food=True
        FoodMaze[x,y]=CLEAR
        
    def senses(self):
        #Creating Angle Choices
        choice={}
        for i in seeAngs.keys():
            choice[i]=0
        
        #Sight
        #If the ant with food gets lost, it will stop dropping red pheromones
        seeBlue=False
        
        #Turn towards common angle
        avgAng = 0
        numSight = 0
        
        #Seeing each angle
        hasFood=self.food
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
                elif not hasFood and PixVal==FOOD:
                    choice[ang]+=iWeight*foodweight
                    if self.speed>i:
                        self.pickFood(x,y)
                        self.ang+=math.pi
                #Attraction to nest
                elif hasFood and PixVal==NEST:
                    choice[ang]+=returnFood
                #Pheromone Sensing
                #Green is directional Value
                PixVal=BPheromones[x,y]
                if hasFood:
                    #Blue Pheromones
                    if PixVal[3]>0:
                        seeBlue=True
                        #Sees path back
                        choice[ang]+=iWeight*BlueWeight(PixVal[3])
                        avgAng += PixVal[2]
                        numSight += 1
                    #Avoid Food
                    PixVal=FoodMaze[x,y]
                    if PixVal==FOOD:
                        choice[ang]+=iWeight*AvoidFoodWeight
                #If they don't have food
                else:
                    #Blue Pheromones
                    if PixVal[3]>0:
                        choice[ang]+=iWeight*BlueAvoidWeight(PixVal[3])
                    #Red Pheromones
                    PixVal=RPheromones[x,y]
                    if PixVal[3]>0:
                        choice[ang]+=iWeight*RedWeight(PixVal[3])
                        avgAng += PixVal[2]
                        numSight += 1
                
            #Angle Weight
            if abs(choice[ang])>=1:
                choice[ang]*=weight
            else:
                choice[ang]/=weight
        
        #Changing angle to align against path
        if numSight!=0:
            avgAng/=ant.toShade
            avgAng/=numSight
            avgAng+=math.pi
            diff = (self.ang-avgAng)*angChangeWeight
            if abs(diff)>maxInfluence:
                if diff>0:
                    diff = maxInfluence
                else:
                    diff = -maxInfluence
            self.ang+=diff
            
        #Turn off pheromones
        if hasFood:
            if seeBlue:
                self.placePheromone=True
            else:
                self.placePheromone=False
        
        #Shift and Expand distances between Values
        minWeight = min(choice.values())
        if minWeight>0:
            minWeight=-minWeight
        for i in choice.keys():
            choice[i]+=minWeight
            choice[i]=choice[i]**5
        
        #Weights of each choice
        totalWeight=sum(choice.values())
        if totalWeight==0:
            return seeAngs
        return choice
    
    def move(self):
        #Move Forward
        self.x+=self.speed*math.cos(self.ang)
        self.y+=self.speed*math.sin(self.ang)
        
        goStraight=False
        
        #Collision Detection
        if 0<self.x<width and 0<self.y<height:
            #Put Food in nest
            if FoodMaze[self.x,self.y]==NEST:
                if self.food:
                    self.food=False
                    self.ang+=math.pi
                    self.placePheromone=True
                    
                goStraight=True
            #"Kill" if they hit a wall
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
            ang = random.choices(list(sight.keys()),weights = list(sight.values()))[0]
            if ang>maxturn:
                ang=maxturn
            elif ang<-maxturn:
                ang=-maxturn
            self.ang+=ang
                    
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
        if self.placePheromone:
            self.dropPheromone()
        self.life-=1
        if self.life<1:
            self.restart()
        updatePixel(self.x,self.y)
        
    def restart(self):
        self.food=False
        self.x=nestx
        self.y=nesty
        self.ang=random.uniform(0,2*math.pi)
        self.life = lifespan
    
    def draw(self, screen):
        screen.fill(ANTCOLOR,rect=[self.x,self.y,1,1])
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
            screen.fill(FOOD,rect=[x,y,1,1])
            self.lastFood=(x,y)
            updatePixel(x,y)
            
#%%Creating Ants
def makeAnts():
    global ants
    ants=[]
    for i in range(numants):
        ant(nestx,nesty,random.uniform(0,2*math.pi))
        
#%%Map Making
numTiles=lambda length,tile:math.ceil(length/tile)-1
    
#Maze Making
path="\\".join(os.path.abspath("AntFood.py").split("\\")[:-2])
if path not in sys.path:
    sys.path.insert(0,path)
from MazeDrawer import RecursionMaze

def RandomPoint(SquareSize,length):
    '''
    Returns
    -------
    Integer
        Random value between 0 and length, spaced SquareSize apart.

    '''
    return random.randint(0,numTiles(length,SquareSize))*SquareSize+(SquareSize//2)

#Food
def food(img,x,y,dev,num):
    #Draws Random Clusters
    for i in range(num):
        gx=random.gauss(0,dev)+x
        gy=random.gauss(0,dev)+y
        if 0<gx<width and 0<gy<height:
            img[gx,gy]=FOOD
            
#Draw Food
def drawFood(RectX,RectY,SquareSize):   
    #Food Distribution
    #Food Clusters
    numSquares=numRectX*numRectY
    FoodInCluster=math.ceil(SquareSize*4)
    #Drawing Food
    for i in range(NumFoodClusters):
        x=RandomPoint(RectX,width)
        y=RandomPoint(RectY,height)
        food(FoodMaze,x,y,SquareSize/6,FoodInCluster)

#Draw Walls using MazeDrawer
def drawWalls():
    #Walls
    RectX=width/numRectX
    RectY=height/numRectY
    RecursionMaze(Mazedraw,(RectX,RectY),wallWidth,(0,0,width,height))
    #4 Walls
    Mazedraw.rectangle([0,0,width,wallWidth/2],fill=(0,0,0,255))
    Mazedraw.rectangle([0,0,wallWidth/2,height],fill=(0,0,0,255))
    Mazedraw.rectangle([width-(wallWidth/2),0,width,height],fill=(0,0,0,255))
    Mazedraw.rectangle([0,height-(wallWidth/2),width,height],fill=(0,0,0,255))

#Creating the nest (yellow)
nestx=0
nesty=0
def setNest(RectX,RectY):
    global nestx
    nestx=RandomPoint(RectX,width)
    global nesty
    nesty=RandomPoint(RectY,height)
    
def drawNest(SquareSize):
    nestradius=(SquareSize-2*wallWidth)/5
    if nestradius<4:
        nestradius=4
    Mazedraw.ellipse((nestx-nestradius,nesty-nestradius,nestx+nestradius,nesty+nestradius),fill=YELLOW+(150,))

def drawMaze():
    random.seed(seed)
    #Length of Rectangle dimensions
    RectX=width/numRectX
    RectY=height/numRectY
    #Smaller of 2 numbers, squares
    SquareSize=min(RectX,RectY)
    #Drawing
    ResetImgs()
    drawFood(RectX,RectY,SquareSize)
    drawWalls()
    setNest(RectX,RectY)
    drawNest(SquareSize)
    
#%%Main Function
#Fading Pheromones
def fade(PixelAccess):
    for x in range(width):
        for y in range(height):
            color=PixelAccess[x,y]
            if color[3]==0:
                continue
            PixelAccess[x,y]=color[:3]+(color[3]-1,)
            updatePixel(x,y)
            
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
    
    def runAnts(ants):
        for i in ants:
            i.run()
    
    def drawAnts(ants):
        for i in ants:
            i.draw(screen)
    
    def threadAnts(func):
        threads=[]
        divisions=int(numants/numThreads)
        for i in range(numThreads):
            if i==numThreads-1:
                thread1=threading.Thread(target=func,args=(ants[i*divisions:],))
            else:
                thread1=threading.Thread(target=func,args=(ants[i*divisions:(i+1)*divisions],))
            threads.append(thread1)
            
        for i in threads:
            i.start()
        for i in threads:
            i.join()
            
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
            elif hold and event.type==4:
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
        threadAnts(runAnts)
        
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
        threadAnts(drawAnts)

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
    random.seed(seed)
    drawMaze()
    runSimulation()

if __name__=="__main__":
    run()