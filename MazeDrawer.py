# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 11:04:52 2021

@author: degog
"""
import random
import math
numTiles=lambda length,tile:math.ceil(length/tile)-1
BLACK=(0,0,0)
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
