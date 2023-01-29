''' Game of Life in Python3
By: Medic5700 

An implimentation of Conway's Game of Life.
Generates a random map at start. Map uses 'pac-man physics' (wraps around). 
It is relatively simple, with no interface except printing to console.
Relative Stats Comparison = CPU 5/5; MEM 4/5; Readability 4/5; Security N/A; Interface 2/5; Scaleability 4/5; Robustness 5/5; Complexity 2/5;
Note:
    You can change the map height, width, and runtime via the "# global game settings"

Reference:
    https://en.wikipedia.org/wiki/Conway's_Game_of_Life
'''

# global game settings
mapY : int = 20 # map height
mapX : int = 80 # map width
timeout : int = 1024 # max runtime in interations, -1 for infinite runtime

import random # used for initial map generation
import time # used for limiting frames per second

def generateMap(height : int, width : int) -> list[list[bool]]:
    """Takes map dimensions, generates random map, returns a two dimensional array of Boolean
    
    Note: gamemap intentionally uses coordinates in YX configuration (instead of XY coordinates) for easier printing to screen
    Note: gamemap Y compoenent of coordinates is inverted [IE: coordinate (Y, X) -> (-Y, X)] if compaired to a proper graph
    """
    assert type(height) is int
    assert type(width) is int
    assert (width > 0) and (height > 0)

    gameMap : list[list[bool]] = [[(False) for _ in range(width)] for _ in range(height)]
    y : int
    for y in range(height):
        x : int
        for x in range(width): # nested array is always the x (horizontal) line
            if random.randint(0, 7) <= 3:
                gameMap[y][x] = True
    return gameMap

def strScreen(gameMap : list[list[bool]]) -> str:
    """Takes in gameMap, returns string representing gameMap for print()"""
    assert type(gameMap) is list
    assert all([(type(i) is list) for i in gameMap])
    assert all([(all([(type(j) is bool) for j in i])) for i in gameMap])

    result : str = ""
    y : int
    for y in range(len(gameMap)):
        result += "\n" # newline here because it meshes with previous 'frame' better
        x : int
        for x in range(len(gameMap[0])):
            result += ('-' if (gameMap[y][x] == False) else '0')
    return result

def iterate(gameMap : list[list[bool]]) -> list[list[bool]]:
    """Takes the gameMap, returns gameMap iterated one step following the rules of Conway's Game of Life"""
    assert type(gameMap) is list
    assert all([(type(i) is list) for i in gameMap])
    assert all([(all([(type(j) is bool) for j in i])) for i in gameMap])

    # generates adjacency field for gamemap
    neighbors : list[list[int]] = [[(0) for _ in range(len(gameMap[0]))] for _ in range(len(gameMap))]
    y : int
    for y in range(len(gameMap)):
        x : int
        for x in range(len(gameMap[0])):
            t : list[int] = [0, 1, 1, 1, 0, -1, -1, -1, 0, 1] # repeating pattern of period 8
            i : int
            for i in range(8): # checks 8 adjacent cells, including map wrap-around
                if gameMap[(t[i + 2] + y) % len(gameMap)][(t[i] + x) % len(gameMap[0])] == True:
                    neighbors[y][x] += 1
    
    # applies rules to generate next gamemap iteration
    newMap : list[list[bool]] = [[False for _ in range(len(gameMap[0]))] for _ in range(len(gameMap))]
    y : int
    for y in range(len(gameMap)):
        x : int
        for x in range(len(gameMap[0])): # applies game rules to gameMap for each cell
            if (gameMap[y][x] == False) and (neighbors[y][x] == 3):
                newMap[y][x] = True
            elif (gameMap[y][x] == True) and (neighbors[y][x] < 2 or neighbors[y][x] > 3):
                newMap[y][x] = False
            else:
                newMap[y][x] = gameMap[y][x]
    
    return newMap

if __name__ == "__main__":
    gameMap : list[list[bool]] = generateMap(mapY, mapX) # init
    while(timeout != 0): # uses '-1' for infinity on purpose
        print(f"{strScreen(gameMap)}\n{timeout}", end = '')
        gameMap = iterate(gameMap)
        time.sleep(0.1)
        timeout += -1
