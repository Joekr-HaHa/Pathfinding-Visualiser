import pygame #for visualisation
from collections import deque #allows me to use stacks and queues
import json #to allow for operations to write and read json files
import heapq#allows for a priority queue
import math#allows for mathematical operations e.g. sqrt
import shelve#allows for data persistence
import datetime#allows for the program to get the exact date and time, for save slot formatting
import random


WIDTH=1344#for window size
HEIGHT=720
vec=pygame.math.Vector2#to make it easier to reference vectors
found=False
surf=pygame.display.set_mode((WIDTH,HEIGHT+50))#display surface
clock=pygame.time.Clock()

class Grid:#class for grid, to make it easier to reference nodes and save grids
    def __init__(self,w,h):
        self.w=w
        self.h=h
        self.obstacles=[]
        self.conns=[vec(1,0),vec(-1,0),vec(0,1),vec(0,-1)]#list of all adjacent nodes, not including diagonals
        self.weights={}
        self.userWeights={}
    def is_on_screen(self,node):
        return 0<=node.x<self.w and 0<=node.y<self.h#returns only nodes that are bigger than 0 and within the screens width and height maximum
    def obstacles_check(self,node):
        return node not in self.obstacles#returns nodes that are on screen and not obstacles, helper function
    def adjacent_nodes(self,node):
        neighbours=[node+conn for conn in self.conns]#adds the conn value to find vector value of all adjacent nodes
        neighbours=filter(self.is_on_screen,neighbours)
        neighbours=filter(self.obstacles_check,neighbours)#filters out obstacles
        return neighbours
    def draw(self):#draws all obstacles onto the grid
        settings=read_settings()
        for obs in self.obstacles:
            rect=pygame.Rect(obs*settings['tilesize'],(settings['tilesize'],settings['tilesize']))
            pygame.draw.rect(surf,(140,140,140),rect)
    def set_weights(self,rand=False):
        self.weights.clear()
        current=vec(0,0)
        frontier=deque()
        frontier.append(vec(0,0))
        if not rand:
            self.weights[vectint(vec(0,0))]=1
        else:
            self.weights[vectint(vec(0,0))]=random.randint(0,100)
        while len(frontier)>0:
            current=frontier.popleft()
            for i in (self.adjacent_nodes(current)):
                if vectint(i) not in self.weights:
                    frontier.append(i)
                    if rand:
                        self.weights[vectint(i)]=random.randint(0,100)
                    else:
                        self.weights[vectint(i)]=1
    def weight(self,start,end):
        return self.weights.get(start,0)+10
    def add_weight(self,node,weight):
        self.weights[node]=weight
    def user_add_weight(self,node,weight):
        self.userWeights[node]=weight

############ HELPER FUNCTIONS ###############
def vectint(vec):#converts vectors to integers
    x,y=vec
    x=int(x)
    y=int(y)
    return (x,y)
def intvec(i):#converts integers to vectors
    x,y=i
    return(vec(x,y))
def save_settings(settings):#function to save new settings to a json file
    with open('settings.json','w') as file:
        json.dump(settings,file)
def read_settings():#function to read the settings from the json file
    with open('settings.json') as file:
        settings=json.load(file)
    return settings
def save_config(obstacles,start,end,name,num=1,weights={}):#saves the user's settings to a json file
    shelfFile = shelve.open('savefile{}.json'.format(num))
    shelfFile['obstacles'] = obstacles
    shelfFile['start'] = start
    shelfFile['end'] = end
    shelfFile['name']=name
    shelfFile['weights']=weights
    shelfFile.close()
def read_config(num=1):#reads the user's settings from the selected json file
    shelfFile = shelve.open('savefile{}.json'.format(num))
    return shelfFile
    shelfFile.close()
def save_dist(multiplier,unit):#saves the user-selected distance unit and multiplier to a json file
    shelfFile=shelve.open('distances.json')
    shelfFile['multiplier']=multiplier
    shelfFile['unit']=unit
    shelfFile.close()
def read_dist():#reads the user-selected distance unit and multiplier from a json file
    shelfFile=shelve.open('distances.json')
    multiplier=shelfFile['multiplier']
    unit=shelfFile['unit']
    return shelfFile
    shelfFile.close()
##############################################


########### DRAW FUNCTIONS ###################

def text_box(text,x,y,size=32,colour=(255,255,255)):#creates text and outputs it to screen
    font=pygame.font.Font((pygame.font.match_font("comicsans")),size)
    text_surface=font.render(text,True,colour)
    text_rect=text_surface.get_rect()
    text_rect.topleft=(x,y)
    surf.blit(text_surface,text_rect)


def draw_grid():#draws the grid lines
    settings=read_settings()
    for x in range(0,WIDTH,settings['tilesize']):#for loop with step width
        pygame.draw.line(surf,(140,140,140),(x,0),(x,HEIGHT))
    for y in range(0,HEIGHT,settings['tilesize']):
        pygame.draw.line(surf,(140,140,140),(0,y),(WIDTH,y))
        
def draw_algo_steps(visited):#goes through coordinates in an array and outputs them to corresponding grid squares in red
    settings=read_settings()
    for i in visited:
        rect=pygame.Rect(intvec(i)*settings['tilesize'],(settings['tilesize'],settings['tilesize']))
        pygame.draw.rect(surf,(255,0,0),rect)
    pygame.time.delay(settings['speed'])
    pygame.display.flip()
    pygame.event.pump()

def draw_start_end(end,start):#creates green boxes where the start and end points are
    settings=read_settings()
    rect=pygame.Rect((start)*settings['tilesize'],(settings['tilesize'],settings['tilesize']))
    pygame.draw.rect(surf,settings['colour'],rect)
    rect1=pygame.Rect((end)*settings['tilesize'],(settings['tilesize'],settings['tilesize']))
    pygame.draw.rect(surf,settings['colour'],rect1)
    
def draw_path(path,end,start,foundPath=True):#draws the optimal path
    settings=read_settings()
    try:
        current=start+path[vectint(start)]
        while current!=end:
            x=current.x*settings['tilesize']+settings['tilesize']/2
            y=current.y*settings['tilesize']+settings['tilesize']/2
            rect=pygame.Rect((x,y),(settings['tilesize'],settings['tilesize']))
            rect.centerx=x
            rect.centery=y
            pygame.draw.rect(surf,(0,0,255),rect)
            current=current+path[vectint(current)]
            if not foundPath:
                pygame.time.delay(20)
                pygame.display.update()
    except KeyError:
        print("l")

#########################################################

############### PATHFINDING FUNCTIONS ###################
        
def bfs(graph,start,end,show=False,speed=0):#breadth-first search
    frontier=deque()#makes a queue for the nodes
    frontier.append(start)
    path={}#creates a dictionary to store the optimal path in
    path[vectint(start)]=None#makes sure that the start must be in the path, and doesn't add bias
    while len(frontier)>0:
        current=frontier.popleft()#continuously pops elements from the unexplored queue until queue is empty
        if current==end:
            break
        for i in (graph.adjacent_nodes(current)):#finds adjacent nodes
            if vectint(i) not in path:
                frontier.append(i)#adds all unexplored adjacent nodes to unexplored frontier
                path[vectint(i)]=current-i#notes the relational distance from current node, so the path can be constructed
                if vectint(end) not in path and show:
                    draw_algo_steps(path)
    return path
def dijkstras(graph,start,end,show=False,speed=0):#dijkstras
    frontier=[]#makes a queue for the nodes
    heapq.heappush(frontier,(0,vectint(start)))#puts the start element in the queue with a weight of 0
    path={}#creates a dictionary to store the optimal path in
    weight={}
    path[vectint(start)]=None#makes sure that the start must be in the path, and doesn't add bias
    weight[vectint(start)]=0#sets the heuristic of the initial node to 0
    while len(frontier)>0:
        current=heapq.heappop(frontier)[1]#continuously pops lowest heuristic elements from the unexplored queue until queue is empty
        if current==end:
            break
        for i in (graph.adjacent_nodes(intvec(current))):#finds adjacent nodes
            i=vectint(i)
            calculatedWeight=weight[current]+graph.weight(current,i)#find the heuristic from the end node to a specific point
            if i not in weight or calculatedWeight < weight[i]:#if its a lower heuristic or if not already explored, then add/update to dictionary
                weight[i]=calculatedWeight
                priority=calculatedWeight
                heapq.heappush(frontier,(priority,i))#add to priority queue, ordering by weight
                path[i]=intvec(current)-intvec(i)#add whatever direction the node is from the current node
                if show:
                    draw_algo_steps(path)
    return path
def aStar(graph,start,end,show=False):
    frontier=[]#makes a queue for the nodes
    heapq.heappush(frontier,(0,vectint(start)))#puts the start element in the queue with a weight of 0
    path={}#creates a dictionary to store the optimal path in
    weight={}
    path[vectint(start)]=None#makes sure that the start must be in the path, and doesn't add bias
    weight[vectint(start)]=0#sets the heuristic of the initial node to 0
    while len(frontier)>0:
        current=heapq.heappop(frontier)[1]#continuously pops lowest heuristic elements from the unexplored queue until queue is empty
        if current==end:
            break
        for i in (graph.adjacent_nodes(intvec(current))):#finds adjacent nodes
            i=vectint(i)
            calculatedWeight=weight[current]+graph.weight(current,i)+heuristic(intvec(i),end)#find the heuristic from the end node to a specific point, adding to it the heuristic
            if i not in weight or calculatedWeight < weight[i]:#if its a lower heuristic or if not already explored, then add/update to dictionary
                weight[i]=calculatedWeight
                priority=calculatedWeight+heuristic(intvec(i),end)
                heapq.heappush(frontier,(priority,i))#add to priority queue, ordering by weight
                path[i]=intvec(current)-intvec(i)#add whatever direction the node is from the current node
                if show:
                    draw_algo_steps(path)
    return path
def heuristic(x,end):
    a=math.sqrt((x[1]-end[1])**2+(x[0]-end[0])**2)
    return a-10##################YOU CHANGED THIS TO -10 INSTEAD OF +10 DOCUMENT THIS!!!!!!!! @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#########################################################

################# MAINLOOP ##############################
def button(x,y,mx,my,click,func,text,param="",param1="",param2="",param3="",param4=""):#creates a button with width 200 and height 50 and calls a function when clicked
    settings=read_settings()
    button=pygame.Rect(x,y,200,50)
    size=32
    if len(text)>15:
        size=25
        x-=43
    elif len(text)>9:
        size=25
        x-=8
    if button.collidepoint(mx,my):
        pygame.draw.rect(surf,(255,255,255),button)
        text_box(text,x+50,y+12.5,size,(140,140,140))
        if click and param!="" and param1=="":
            if param in [(210,180,140),(0,255,0)]:
                settings['colour']=param
                save_settings(settings)
                options_loop()
            elif param in [0,20,40] and str(param)!="False":
                settings['speed']=param
                save_settings(settings)
                options_loop()
            elif param in ['bfs','aStar','dijk']:
                settings['algo']=param
                save_settings(settings)
                options_loop()
            elif param in [12,24,48]:
                settings['tilesize']=param
                save_settings(settings)
                options_loop()
            else:
                func(param)
        elif click and param!="" and param1!="" and param2=="":
            func(param,param1)
            options_loop()
        elif click and param!="" and param3!="":
            func(param,param1,param2,param3,param4)
        elif click:
            func()
    else:
        pygame.draw.rect(surf,(140,140,140),button)
        text_box(text,x+50,y+12.5,size)
def which_menu(options):
    if options:
        options_loop()
    else:
        main_menu()
def help_menu(page=-1,options=True):#creates a menu where users can learn about the algorithms and controls
    run=True
    while run:
        click=False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    if page==-1:
                        which_menu(options)
                    else:
                        help_menu()
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    click=True
        mx,my=pygame.mouse.get_pos()
        surf.fill((0,0,0))
        if page==-1:
            text_box("Select below which pathfinding technique you would like to know more about",WIDTH/2-400,(HEIGHT/2)-250)
            text_box("Or select key to view the colour key for the visualisation",WIDTH/2-300,(HEIGHT/2)-150)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-50,mx,my,click,help_menu,"Dijkstra's",1)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+50,mx,my,click,help_menu,"A * Search",2)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,help_menu,"Breadth-First Search",3)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+250,mx,my,click,help_menu,"Key",4)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Controls",5)
            button(WIDTH/2-WIDTH/12-400,HEIGHT/2+350,mx,my,click,which_menu,"Return",options)
            pygame.display.flip()
        elif page==1:
            text_box("A generalised form of breadth-first search, where the order of traversed nodes is determined by the distance from the root",10,30)
            text_box("It searches all adjacent nodes, prioritising those with the smallest distance",10,80)
            text_box("This is mostly useful in weighted graphs, where nodes can have different costs/distances",10,140)
            text_box("Weighted graphs can be useful for representing traffic or altitude",10,200)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            pygame.display.flip()
        elif page==2:
            text_box("An alternative to Dijkstra's algorithm",10,30)
            text_box("Works much the same as Dijkstra's but uses a heuristic approach",10,80)
            text_box("A heuristic approach results in a 'good enough' outcome",10,140)
            text_box("This means it may not neccessarily calculate the shortest path",10,200)
            text_box("However, this approach means it takes much less time to calculate the optimal path than other algorithms",10,260)
            text_box("This is because it wastes less time searching nodes that may not be in the correct direction",10,320)
            text_box("In my implementation it uses the euclidean distance between a node and the end in the heuristic",10,380)
            text_box("This means the program will favour nodes that are closer to the end point",10,440)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            pygame.display.flip()
        elif page==3:
            text_box("This is the most basic algorithm",10,30)
            text_box("This simply searches every adjacent node of every node",10,80)
            text_box("This is a brute-force algorithm as it searches every available node until the end point is found",10,140)
            text_box("This presents itself as radiating out from the start point",10,200)
            text_box("This guarantees the shortest path",10,260)
            text_box("However, it is also the slowest due to its brute-force approach",10,320)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            pygame.display.flip()
        elif page==4:
            pygame.draw.rect(surf,(0,255,0),pygame.Rect(60,HEIGHT/2-330,48,48))
            pygame.draw.rect(surf,(210,180,140),pygame.Rect(60,HEIGHT/2-270,48,48))
            text_box("Start and end points",150,HEIGHT/2-330)
            text_box("These can be either green normally or tan with colour blind mode on",150,HEIGHT/2-300)
            text_box("These represent where the algorithm will search from and search to",150,HEIGHT/2-270)
            pygame.draw.rect(surf,(255,0,0),pygame.Rect(60,HEIGHT/2-30,48,48))
            text_box("Frontier area",150,HEIGHT/2-30)
            text_box("This is the area the algorithm is currently searching",150,HEIGHT/2)
            pygame.draw.rect(surf,(0,0,255),pygame.Rect(60,HEIGHT/2+230,48,48))
            text_box("Optimal Path",150,HEIGHT/2+230)
            text_box("This represents the shortest path as calculated by the selected algorithm, between the start and end points",150,HEIGHT/2+260)
            text_box("This will animate from the end point to the start point, due to it using backtracking",150,HEIGHT/2+290)
            text_box("This is because, once the algorithm has calulated the shortest path, it traces it back from the endpoint",150,HEIGHT/2+320)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            pygame.display.flip()
        elif page==5:
            text_box("Click using Mouse Key 1 (Left Click) on any square to add an obstacle, or click and drag to add multiple",10,30)
            text_box("Press 'D' to enter 'Delete Mode', the controls are the same as adding obstacles",10,80)
            text_box("But it now deletes obstacles, press 'D' again to toggle 'Delete Mode' off",10,140)
            text_box("Press 'S' to enter 'Show Mode'",10,200)
            text_box("This removes the instant calculation/visualisation of the path",10,260)
            text_box("Press the 'G' key whilst in show mode to show a visualisation of the algorithm and then see the optimal path",10,320)
            text_box("Use Mouse Key 2 (Right-Click) to change the position of the end point",10,380)
            text_box("Use Mouse Key 3 (Scroll Wheel In) to change the position of the start point",10,440)
            text_box("Press 'esc' at any time whilst in the program, to go to the options menu",10,500)
            text_box("Press 'esc' at any time in the menus to go to the last menu",10,560)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            button(WIDTH/2-WIDTH/12+400,HEIGHT/2+350,mx,my,click,help_menu,"More controls",6)
            pygame.display.flip()
        elif page==6:
            text_box("Start mode can be entered and exited by pressing p",10,30)
            text_box("Start mode allows the start to be changed with left click and the end with right click",10,80)
            text_box("This is useful for those without a mouse",10,140)
            text_box("r randomises the weights when using a star and dijkstra's",10,200)
            text_box("c can then reset the weights to their default value of 1",10,260)
            text_box("When using Dijkstra's and A* you can enter weights",10,320)
            text_box("To enter a weight, simply hover over the square you want to add it to",10,380)
            text_box("Then you can type in the number you want up to a maximum of three digits",10,440)
            text_box("Then press enter to confirm and render this choice",10,500)
            text_box("You can press and hold enter to add weights in bulk",10,560)
            text_box("If you want to change the number weight then simply press the delete key",10,620)
            text_box("Then type a new weight in",10,680)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            button(WIDTH/2-WIDTH/12-400,HEIGHT/2+350,mx,my,click,help_menu,"Previous controls",5)
            button(WIDTH/2-WIDTH/12+400,HEIGHT/2+350,mx,my,click,help_menu,"More controls",7)
            pygame.display.flip()
        else:
            text_box("When using random weights you can only see them in show mode",10,30)
            text_box("You can overwrite the weights with your own",10,80)
            text_box("If you overwrite a weight, your weight will be shown in both show and normal modes",10,140)
            text_box("It is reccomended you do not move the start and end points during/after setting the weights en masse",10,200)
            text_box("So be sure that your start and end points are in the correct position",10,260)
            text_box("Before either randomising weights or adding loads of weights",10,320)
            text_box("However, using the default tile size, this should not be a problem",10,380)
            text_box("This only really applies to the smaller tile sizes where lag/delay is more noticeable",10,440)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Return",-1)
            button(WIDTH/2-WIDTH/12-400,HEIGHT/2+350,mx,my,click,help_menu,"Previous controls",6)
            pygame.display.flip()
            
        
            
def main_menu():#Main Menu in which users can load a save, start the program, access help or exit
    pygame.init()
    run=True
    while run:
        click=False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    click=True
        mx,my=pygame.mouse.get_pos()
        surf.fill((0,0,0))
        button(WIDTH/2-WIDTH/12,HEIGHT/2-150,mx,my,click,main_loop,"Start")
        button(WIDTH/2-WIDTH/12,HEIGHT/2-50,mx,my,click,load_save_data,"Saved Paths",-1,False)
        button(WIDTH/2-WIDTH/12,HEIGHT/2+50,mx,my,click,help_menu,"Help",-1,False)
        button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,pygame.quit,"Quit")
        pygame.display.flip()

def options_loop(page=-1):#Renders the options menu, allowing the user to customise various aspects of the program
    run=True
    rect1Colour=(140,140,140)
    obstacles=read_config(6)['obstacles']
    start=read_config(6)['start']
    end=read_config(6)['end']
    weights=read_config(6)['weights']
    while run:
        click=False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    if page==-1:
                        main_loop(obstacles,start,end,weights)
                    else:
                        options_loop()
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    click=True

        mx,my=pygame.mouse.get_pos()
        if page==-1:
            surf.fill((0,0,0))
            button(WIDTH/2-WIDTH/12,HEIGHT/2-350,mx,my,click,options_loop,"Distance Settings",6)
            button(WIDTH/2-WIDTH/12-120,HEIGHT/2-250,mx,my,click,new_save_data,"Save",obstacles,start,end,weights,-1)
            button(WIDTH/2-WIDTH/12+120,HEIGHT/2-250,mx,my,click,load_save_data,"Load",-1)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-150,mx,my,click,options_loop,"Resume",1)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-50,mx,my,click,options_loop,"Pathfinding Algorithms",2)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+50,mx,my,click,options_loop,"Speed",3)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,options_loop,"Colours",4)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+250,mx,my,click,options_loop,"Grid Size",5)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,help_menu,"Help")
            button(WIDTH/2-WIDTH/12-400,HEIGHT/2+350,mx,my,click,pygame.quit,"Quit")
            pygame.display.flip()
        elif page==1:
            main_loop(obstacles,start,end,weights)
        elif page==2:
            surf.fill((0,0,0))
            button(WIDTH/2-WIDTH/12,HEIGHT/2,mx,my,click,options_loop,"A Star Search","aStar")
            button(WIDTH/2-WIDTH/12,HEIGHT/2+100,mx,my,click,options_loop,"Breadth-First Search","bfs")
            button(WIDTH/2-WIDTH/12,HEIGHT/2-100,mx,my,click,options_loop,"Dijkstras","dijk")
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
        elif page==3:
            surf.fill((0,0,0))
            button((WIDTH/2-WIDTH/12)-250,HEIGHT/2,mx,my,click,options_loop,"Slow",40)
            button(WIDTH/2-WIDTH/12,HEIGHT/2,mx,my,click,options_loop,"Medium",20)
            button((WIDTH/2-WIDTH/12)+250,HEIGHT/2,mx,my,click,options_loop,"Fast (default)",0)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
        elif page==4:
            surf.fill((0,0,0))
            button((WIDTH/2-WIDTH/12),HEIGHT/2,mx,my,click,options_loop,"Colour Blind Mode",(210,180,140))
            button(WIDTH/2-WIDTH/12,HEIGHT/2+100,mx,my,click,options_loop,"Normal",(0,255,0))
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
        elif page==5:
            surf.fill((0,0,0))
            button((WIDTH/2-WIDTH/12)-250,HEIGHT/2,mx,my,click,options_loop,"48 (default)",48)
            button(WIDTH/2-WIDTH/12,HEIGHT/2,mx,my,click,options_loop,"24 ",24)
            button((WIDTH/2-WIDTH/12)+250,HEIGHT/2,mx,my,click,options_loop,"12",12)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
        elif page==6:
            surf.fill((0,0,0))
            button(WIDTH/2-WIDTH/12,HEIGHT/2-250,mx,my,click,options_loop,"km",7)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-150,mx,my,click,options_loop,"m",8)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-50,mx,my,click,options_loop,"cm",9)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+50,mx,my,click,options_loop,"inches",10)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,options_loop,"miles",11)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,options_loop,"blocks",12)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
        elif page in [7,8,9,10,11,12]:
            surf.fill((0,0,0))
            if page==7:
                unit="km"
            elif page==8:
                unit="m"
            elif page==9:
                unit="cm"
            elif page==10:
                unit="inches"
            elif page==1:
                unit="miles"
            else:
                unit="blocks"
            button(WIDTH/2-WIDTH/12,HEIGHT/2-250,mx,my,click,save_dist,"10,000",10000,unit)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-150,mx,my,click,save_dist,"1,000",1000,unit)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-50,mx,my,click,save_dist,"100",100,unit)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+50,mx,my,click,save_dist,"10",10,unit)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+150,mx,my,click,save_dist,"1",1,unit)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,options_loop,"Return",-1)
            pygame.display.flip()
            
def new_save_data(obstacles,start,end,weights,page=-1):#allows the user to select a save slot and save their data
    run=True
    while run:
        click=False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    if page==-1:
                        options_loop()
                    else:
                        new_save_data(obstacles,start,end,weights)
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    click=True

        mx,my=pygame.mouse.get_pos()
        if page==-1:
            surf.fill((0,0,0))
            text_box("Select a Save File",WIDTH/2-110,80)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-100,mx,my,click,new_save_data,read_config(1)['name'],obstacles,start,end,weights,1)
            button(WIDTH/2-WIDTH/12,HEIGHT/2,mx,my,click,new_save_data,read_config(2)['name'],obstacles,start,end,weights,2)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+100,mx,my,click,new_save_data,read_config(3)['name'],obstacles,start,end,weights,3)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+200,mx,my,click,new_save_data,read_config(4)['name'],obstacles,start,end,weights,4)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+300,mx,my,click,new_save_data,read_config(5)['name'],obstacles,start,end,weights,5)
            pygame.display.flip()
        elif page in [1,2,3,4,5]:
            currentDateTime=datetime.datetime.now()
            currentDate="{}/{}/{}".format(currentDateTime.day, currentDateTime.month, currentDateTime.year)
            currentTime="{}:{}".format(currentDateTime.hour,currentDateTime.minute)
            name=settings['algo'] +" "+currentDate+" at "+currentTime
            save_config(obstacles,start,end,name,page,weights)
            page=6
        else:
            surf.fill((0,0,0))
            text_box("Saved!",WIDTH/2-10,HEIGHT/2)
            pygame.display.flip()
            pygame.time.delay(800)
            main_loop(obstacles,intvec(start),intvec(end),weights)
def load_save_data(page=-1,options=True):#allows the user to load their data from their selected save slot
    run=True
    while run:
        click=False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    which_menu(options)
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    click=True

        mx,my=pygame.mouse.get_pos()
        if page==-1:
            surf.fill((0,0,0))
            text_box("Select a Save File",WIDTH/2-110,80)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-200,mx,my,click,load_save_data,read_config(1)['name'],1)
            button(WIDTH/2-WIDTH/12,HEIGHT/2-100,mx,my,click,load_save_data,read_config(2)['name'],2)
            button(WIDTH/2-WIDTH/12,HEIGHT/2,mx,my,click,load_save_data,read_config(3)['name'],3)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+100,mx,my,click,load_save_data,read_config(4)['name'],4)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+200,mx,my,click,load_save_data,read_config(5)['name'],5)
            button(WIDTH/2-WIDTH/12,HEIGHT/2+350,mx,my,click,which_menu,"Return",options)
            pygame.display.flip()
        elif page in [1,2,3,4,5]:
            obstacles=read_config(page)['obstacles']
            start=read_config(page)['start']
            end=read_config(page)['end']
            weights=read_config(page)['weights']
            main_loop(obstacles,start,end,weights)
        
def random_or_normal(rand,grid):#either sets weights to default or randomises them
    if rand==True:
        text="Randomised"
    else:
        text="Reset Weights"
    print(rand)
    grid.set_weights(rand)
    text_box(text,WIDTH//2-200,HEIGHT//2,70)
    pygame.display.update()
    pygame.time.delay(500)
    
def main_loop(obstacles="",start="",end="",weights={}):#the main loop in which the grid is rendered and can be drawn onto/ manipulated by the user
    weight=""
    multi=True
    pygame.init()
    settings=read_settings()
    GRIDWIDTH=WIDTH//settings['tilesize']
    GRIDHEIGHT=HEIGHT//settings['tilesize']#for size of grid boxes
    FPS=60#to factor in delta time
     
    grid=Grid(GRIDWIDTH,GRIDHEIGHT)
    run=True
    show=False
    found=False
    foundPath=False
    delete=False
    startMode=False
    mode=lambda a: 'On' if a else 'Off'
    if start=="" and end=="":
        start=vec(0,0)
        end=vec(20,6)
        grid.set_weights()
    else:
        start=start
        end=end
        grid.obstacles=obstacles
        grid.weights=weights
    save_config(grid.obstacles,start,end,"temp",6,grid.weights)
    codes=[x for x in range(5)]
    
    while run:
        f=0
        click=False
        if pygame.key.get_pressed()[pygame.K_RETURN]:
            if weight!="":
                grid.add_weight(vectint(mousepos),int(weight))
                grid.user_add_weight(vectint(mousepos),int(weight))
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
            mousepos=intvec(pygame.mouse.get_pos())//settings['tilesize']
            if pygame.mouse.get_pressed()[0]:#if left click is pressed
                if not startMode:
                    found=False
                    if mousepos not in grid.obstacles and not delete and mousepos not in [start,end] and grid.is_on_screen(mousepos):#get the mouse position and add to obstacles
                        grid.obstacles.append(mousepos)
                    elif delete and mousepos in grid.obstacles:
                        grid.obstacles.remove(mousepos)
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_s:
                    show=not show
                if event.key==pygame.K_g:
                    if settings['algo']=='dijk':
                        path=(dijkstras(grid,start,end,show))
                    elif settings['algo']=='aStar':
                        path=(aStar(grid,start,end,show))
                    else:
                        path=(bfs(grid,start,end,show))
                    found=True
                    foundPath=False
                if event.key==pygame.K_d:
                    delete=not delete
                if event.key==pygame.K_ESCAPE:
                    save_config(grid.obstacles,start,end,"temp",6,grid.weights)
                    options_loop()
                if event.key==pygame.K_h:
                    help_menu()
                if event.key==pygame.K_b:
                    new_save_data(grid.obstacles,start,end,weights)
                if event.key==pygame.K_DELETE:
                    weight=""
                if event.key==pygame.K_r:
                    random_or_normal(True,grid)
                if event.key==pygame.K_c:
                    random_or_normal(False,grid)
                if event.key==pygame.K_p:
                    startMode=not startMode
                if len(weight)<3:
                    if event.key==pygame.K_1:
                        weight+="1"
                    if event.key==pygame.K_2:
                        weight+="2"
                    if event.key==pygame.K_3:
                        weight+="3"
                    if event.key==pygame.K_4:
                        weight+="4"
                    if event.key==pygame.K_5:
                        weight+="5"
                    if event.key==pygame.K_6:
                        weight+="6"
                    if event.key==pygame.K_7:
                        weight+="7"
                    if event.key==pygame.K_8:
                        weight+="8"
                    if event.key==pygame.K_9:
                        weight+="9"
                
            if event.type==pygame.MOUSEBUTTONDOWN:
                found=False
                mousepos=intvec(pygame.mouse.get_pos())//settings['tilesize']
                if event.button==1:
                    if not startMode:
                        click=True
                    else:
                        start=mousepos
                if event.button==2:
                    if mousepos not in grid.obstacles:
                        end=mousepos
                    draw_start_end(start,end)
                if event.button==3:
                    if mousepos not in grid.obstacles:
                        if not startMode:
                            start =mousepos
                        else:
                            end=mousepos
                    draw_start_end(start,end)
        mx,my=pygame.mouse.get_pos()
                    
        surf.fill((40,40,40))
        draw_grid()
        
        if settings['algo']=='dijk' or settings['algo']=='aStar':
            if show:
                for node in grid.weights:
                    if grid.weights[node]!=1:
                        text_box(str(grid.weights[node]),node[0]*settings['tilesize'],node[1]*settings['tilesize'])
            else:
                for node in grid.userWeights:
                    text_box(str(grid.weights[node]),node[0]*settings['tilesize'],node[1]*settings['tilesize'])
            text_box(('Selected Weight: '+str(weight)),WIDTH-650,HEIGHT+10)
            
        draw_start_end(start,end)
        show_text=("Show Mode: "+mode(show))
        text_box(show_text,10,HEIGHT+10)
        text_box(("Delete Mode: "+mode(delete)),WIDTH-1100,HEIGHT+10)
        optionsButton=button(WIDTH-300,HEIGHT-2,mx,my,click,options_loop,"Options",-1)
        
 
        if not show:
            if settings['algo']=='dijk':
                path=(dijkstras(grid,start,end,show))
            elif settings['algo']=='aStar':
                path=(aStar(grid,start,end,show))
            else:
                path=(bfs(grid,start,end,show))
            draw_path(path,start,end)
        if found:
            grid.draw()
            draw_path(path,start,end,foundPath)
            text_box("End",((end.x+0.1)*settings['tilesize']),((end.y+0.3)*settings['tilesize']),25)
            text_box("Start",((start.x+0.1)*settings['tilesize']),((start.y+0.3)*settings['tilesize']),25)
            foundPath=True

        if not startMode:
            text_box(str(read_config(7)['obstacles']*read_dist()['multiplier'])+" "+str(read_dist()['unit']),WIDTH-850,HEIGHT+10)
        else:
            text_box("Start Mode On",WIDTH-850,HEIGHT+10)
        text_box("End",((end.x+0.1)*settings['tilesize']),((end.y+0.3)*settings['tilesize']),25)
        text_box("Start",((start.x+0.1)*settings['tilesize']),((start.y+0.3)*settings['tilesize']),25)
        grid.draw()
        
        
        pygame.display.flip()#allows buffering, so is quicker than .update

######################################################################
settings={'colour':(0,255,0),
          'speed':0,
          'algo':'bfs',
          'tilesize':48}#default settings
save_dist(1,"blocks")#sets the default units for measurement
save_settings(settings)#sets the settings to their default values
main_menu()


