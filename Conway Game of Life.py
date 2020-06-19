''' Game of Life in Python3
By: Medic5700
https://github.com/Medic5700/Python3-Game-of-Life

Generates a random map, and iterates over that map. 
It is relatively simple, with no interface other then the map display.
note: The map is a pac-man map-space
'''

import random #used for initial map generation
import time #used for limiting frames per second

#global game settings
mapX = 80 #map width
mapY = 20 #map height
timeout = 1024 #max run time in steps, -1 for infinite runtime

def generateMap(width, height):
    """takes dimensions, Generates random map, returns a two dimensional array of True or False"""
    assert (width > 0) and (height > 0)
    gameMap = [[(False) for x in range(width)] for y in range(height)]
    for y in range(height):
        for x in range(width): #nested array is always the x (horizontal) line
            if random.randint(0,7) <= 3:
                gameMap[y][x] = True
    return gameMap

def strScreen(gameMap):
    """Takes the gameMap, returns string representing gameMap for print()"""
    result = ""
    for y in range(len(gameMap)):
        result += "\n" #newline here because it meshes with previous 'frame' better
        for x in range(len(gameMap[0])):
            result += ('-' if (gameMap[y][x] == False) else '0')
    return result

def iterate(gameMap):
    """Takes the gameMap, returns gameMap iterated one step"""
    neighbors = [[(0) for x in range(len(gameMap[0]))] for y in range(len(gameMap))]
    
    for y in range(len(gameMap)):
        for x in range(len(gameMap[0])):
            t = [0, 1, 1, 1, 0, -1, -1, -1, 0, 1] #repeating pattern of period 8
            for i in range(8): #checks 8 adjacent cells, including map wrap-around
                if gameMap[(t[i+2] + y) % len(gameMap)][(t[i] + x) % len(gameMap[0])] == True:
                    neighbors[y][x] += 1
    
    for y in range(len(gameMap)):
        for x in range(len(gameMap[0])): #applies game rules to gameMap for each cell
            if (gameMap[y][x] == False) and (neighbors[y][x] == 3):
                gameMap[y][x] = True
            elif (gameMap[y][x] == True) and (neighbors[y][x] < 2 or neighbors[y][x] > 3):
                gameMap[y][x] = False
    
    return gameMap

if __name__ == "__main__":
    gameMap = generateMap(mapX, mapY) #init
    while(timeout != 0): #uses old '-1' for infinity trick on purpose
        print(strScreen(gameMap) + "\n" + str(timeout), end='')
        gameMap = iterate(gameMap)
        time.sleep(0.1)
        timeout += -1
