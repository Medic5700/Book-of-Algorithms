''' Langton's Ant
By: Medic5700
https://en.wikipedia.org/wiki/Langton%27s_ant

note: The map is a pac-man map-space
'''

import time #used for limiting frames per second

#global game settings
MapX : int = 80 #map width
MapY : int = 20 #map height
timeout : int = 2**12 #max run time in steps, -1 for infinite runtime

def strScreen() -> str:
    """Takes the GameMap, returns string representing gameMap for print()"""
    global AntX, AntY, AntR
    global GameMap
    
    result = ""
    for y in range(len(GameMap[0]) - 1, -1, -1):
        result += "\n" #newline here because it meshes with previous 'frame' better
        for x in range(len(GameMap)):
            if (AntX == x) and (AntY == y):
                t1 = ['^', '>', 'v', '<']
                result += t1[AntR]
            else:
                result += ('-' if (GameMap[x][y] == False) else '0')
    return result

def iterate(steps = 1):
    """takes 'steps' number of algorithm interations, altering the GameMap, and the "ant's" position"""
    global MapX, MapY
    global AntX, AntY, AntR
    global GameMap
    
    t = [0, 1, 0, -1, 0, 1] #repeating pattern of period 4

    for i in range(steps):
        if GameMap[AntX][AntY] == False: #if white, flip colour, turn clockwise
            GameMap[AntX][AntY] = True
            AntR = (AntR + 1) % 4
        elif GameMap[AntX][AntY] == True: #if black, flip colour, turn counterclockwise
            GameMap[AntX][AntY] = False
            AntR = (AntR - 1) % 4
        
        #moves ant forward one, depending on the direction it's facing
        AntX = (AntX + t[AntR]) % MapX
        AntY = (AntY + t[AntR + 1]) % MapY #[AntR + 1] is a 90 degree offset

if __name__ == "__main__":
    #generates initial game map
    assert (MapX > 0) and (MapY > 0)
    assert type(timeout) == type(0)
    
    GameMap = [[(False) for y in range(MapY)] for x in range(MapX)]

    AntX = MapX // 2
    AntY = MapY // 2
    AntR = 3 #direction (0 = up, 1 = right, 2 = down, 3 = left)

    while(timeout != 0): #uses old '-1' for infinity trick on purpose
        print(strScreen() + "\n" + str(timeout), end='')
        iterate()
        time.sleep(0.05)
        timeout += -1
