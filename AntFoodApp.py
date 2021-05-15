# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:15:49 2021

@author: degog
"""

import tkinter as tk
import AntFood
from PIL import Image, ImageTk

class VarEntry():
    entries=[]
    exampleEnts={}
    def __init__(self,master,var,text=None,mode=int,preview=None):
        self.var=var
        self.mode=mode
        if text==None:
            text=tk.StringVar(value=var)
        else:
            text=tk.StringVar(value=text)
        
        #Add Label and Entry
        row = tk.Frame(master)
        lab = tk.Label(row, width=30, textvariable=text)
        self.entText=tk.StringVar(value=str(getattr(AntFood,var)))
        ent = tk.Entry(row, textvariable=self.entText)
        self.ent=ent
        #Last Value
        if self.entText.get()=="None":
            self.lastVal=None
        else:
            self.lastVal=self.mode()
        #Packing
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.LEFT, fill=tk.X)
        
        #List and Dict to use to update simulation and preview
        VarEntry.entries.append(self)
        if preview!=None:
            ent.bind("<KeyRelease>",(lambda x:VarEntry.update(self)))
            if preview in VarEntry.exampleEnts.keys():
                VarEntry.exampleEnts[preview].append(self)
            else:
                VarEntry.exampleEnts[preview]=[self]
    
    def update(self):
        lastval=self.lastVal
        self.setOtherVar()
        if self.ent.get() != lastval:
            updateExample(None)
        
    
    def setOtherVar(self,entSet=False):
        val=self.ent.get()
        try:
            val=self.mode(val)
        except:
            val=self.lastVal
        setattr(AntFood,self.var,val)
        self.lastVal=val
        if entSet:
            self.entText.set(self.lastVal)

def updateExample(event):
    if screen=="Home":
        updateMaze()

def updateMaze():
    for i in VarEntry.exampleEnts[HomeText]:
        i.setOtherVar()
    try:
        AntFood.drawMaze()
        AntFood.saveImgs()
    except:
        return
    
    #Draw the Maze
    global Maze
    Maze=Image.open("AntFoodMaze.png")
    Maze.convert("RGB")
    ImgWidth=Maze.width
    ImgHeight=Maze.height
    #Thinner Image Porportions
    if mazeWidth/mazeHeight>ImgWidth/ImgHeight:
        height_size=mazeHeight
        width_percent=(mazeHeight/ImgHeight)
        width_size = int((ImgWidth * width_percent))
    else:
        width_size=mazeWidth
        height_percent=(mazeWidth/ImgWidth)
        height_size = int((ImgHeight * height_percent))
    #Resize to fit
    Maze = Maze.resize((width_size, height_size),Image.NEAREST)
    #Drawing on Canvas
    global MazeTK
    MazeTK=ImageTk.PhotoImage(Maze)
    dx=int(mazeWidth/2)
    dy=int(mazeHeight/2)+1
    mazeImg.create_image(dx,dy,image=MazeTK)
    
def run():
    for i in VarEntry.entries:
        i.setOtherVar(entSet=True)
    AntFood.runSimulation()

app=tk.Tk()
app.title("Ant Simulator")

screen="Home"

Home=tk.Frame(app)

mazeWidth=500
mazeHeight=300
mazeImg=tk.Canvas(Home,width=mazeWidth,height=mazeHeight)
mazeImg.pack()

HomeVarsPreview={"width":"Simulation Width",
                 "height":"Simulation Height",
                 "seed":"Seed",
                 "numRectX":"Number of Rectangles X axis",
                 "numRectY":"Number of Rectangles Y axis",
                 "wallWidth":"Width of Walls"}
HomeText="Home"
for var,text in HomeVarsPreview.items():
    VarEntry(Home,var,text,preview=HomeText)
    
Home.pack()

run=tk.Button(app,text="Run Simulation",command=run)
run.pack()

updateExample(None)
app.mainloop()
