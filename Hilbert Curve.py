''' 
Hilbert Curve
Author: Medic5700

Reference({
    'Number': None,
    'Accessed': '2024-02-12',
    'Author': [
    ],
    'Title': 'Hilbert curve - Wikipedia',
    'Host': 'Wikipedia',
    'URL': [
        'https://en.wikipedia.org/wiki/Hilbert_curve'
    ],
    'Revised': '2024-01-08',
    'Note': None
})
Reference({
    'Number': None,
    'Accessed': '2024-02-12',
    'Author': [
        '3Blue1Brown'
    ],
    'Title': 'Hilbert's Curve_ Is infinite math useful_ - YouTube',
    'Host': 'Youtube',
    'URL': [
        'https://www.youtube.com/watch?v=3s7h2MHQtxc'
    ],
    'Revised': '2017-07-21',
    'Note': None
})
Reference({
    'Number': None,
    'Accessed': '2024-02-13',
    'Author': [
        'kartikeysm2001'
    ],
    'Title': 'Python - Hilbert Curve using turtle - GeeksforGeeks',
    'Host': None,
    'URL': [
        'https://www.geeksforgeeks.org/python-hilbert-curve-using-turtle/'
    ],
    'Revised': '2023-04-04',
    'Note': 'Python reference uses Python Turtles for generating the Hilbert Curve'
})
Reference({ #TODO
    'Number': None,
    'Accessed': '2024-02-14',
    'Author': [
    ],
    'Title': 'Moore curve - Wikipedia',
    'Host': None,
    'URL': [
        'https://en.wikipedia.org/wiki/Moore_curve'
    ],
    'Revised': '2022-10-13',
    'Note': None
})
'''

from typing import Literal
from dataclasses import dataclass
import copy

import time # used to slow down animation
import os # used to find the size of the terminal
import math # used to figure out size of Hilbert curve to generate based on terminal size

animationDelay : float = 0.05

@dataclass
class Turtle:
    x : int
    y : int
    r : Literal[0, 1, 2, 3] # 0 = north, 1 = east, 2 = south, 3 = west; +1 = rotate clockwise 90 degrees, -1 = rotate counterclockwise 90 degrees

    _count : int = 0
    _rotation : tuple[Literal[-1, 0, 1]] = (0, 1, 0, -1, 0) # north=0x,1y; east=1x,0y; south=0x,-1y; west=-1x,0y

def strScreen(cellSpace : list[list[list[int, int, int]]], turtle : Turtle) -> str:
    #TODO assert cellSpace
    assert type(turtle) is Turtle
    
    global cellSpaceSideLength

    output : str = ''
    # constructs screen line by line, but from line y=0 upwards
    y : int
    for y in range(len(cellSpace[0])):
        line : str = ''
        x : int
        for x in range(len(cellSpace)):
            if (x == turtle.x) and (y == turtle.y): # turtle gets drawn over everything
                match turtle.r:
                    case 0:
                        line += 'A'
                    case 1:
                        line += '>'
                    case 2:
                        line += 'V'
                    case 3:
                        line += '<'
            elif cellSpace[x][y][0] == None: # empty map space
                line += ' '
            elif cellSpace[x][y][1] != None and cellSpace[x][y][2] != None: # draws line if there is valid start and end points
                box : dict[list[int, int], str]
                box = {(0,2):'\u2503', # |
                       (1,3):'\u2501', # -
                       (0,1):'\u2517', # up to right
                       (0,3):'\u251B', # up to left
                       (2,1):'\u250F', # down to right
                       (2,3):'\u2513'  # down to left
                       }
                i : int
                j : int
                for i,j in list(box.keys()):
                    box[j, i] = box[i, j]

                if (cellSpace[x][y][1], cellSpace[x][y][2]) in box.keys():
                    line += f"\u001b[38;2;{int(255 - 255*cellSpace[x][y][0]/cellSpaceSideLength**2)};{int(255*cellSpace[x][y][0]/cellSpaceSideLength**2)};0m" # adds ANSI colour gradiant
                    line += box[cellSpace[x][y][1], cellSpace[x][y][2]]
                    line += '\u001b[0m' # ANSI end character
                else: #debug only activated iff invalid map state (with Hilbert Curve algorithm)
                    line += '='
        output = line + "\n" + output
    return output[:-1] # removes trailing newline

def updateTurtle(turtle : Turtle) -> Turtle:
    assert type(turtle) is Turtle

    global curveTape

    turtleNew : Turtle = copy.deepcopy(turtle)

    turtleNew.r = (turtle.r + curveTape[turtleNew._count]) % 4
    turtleNew.x += turtleNew._rotation[turtleNew.r]
    turtleNew.y += turtleNew._rotation[turtleNew.r + 1]
    turtleNew._count += 1

    return turtleNew

def generateCurve(level : int) -> list[Literal[-1, 0, 1]]:
    assert type(level) is int
    assert level >= 1

    commandTape : Literal['A', 'B', 'F', '+', '-'] = 'A'
    for _ in range(level):
        t : str = ''
        i : str
        for i in commandTape:
            if i == 'A': # Note: 'A' and 'B' is eqivilent to each other except the 'turtle' is roated 180 degrees
                t += "+BF-AFA-FB+"
            elif i == 'B':
                t += "-AF+BFB+FA-"
            else:
                t += i
        commandTape = t

    result : list[int] = []
    rotation : int = 0
    i : str
    for i in commandTape:
        if i == '+':
            rotation += -1 # turn counter-clockwise
        elif i == '-':
            rotation += 1 # turn clockwise
        elif i == 'F':
            result.append(rotation)
            rotation = 0

    assert all([True if (-1 <= i <= 1) else False for i in result])
    return result

if __name__ == "__main__":
    sizeX : int = os.get_terminal_size()[0]
    sizeY : int = os.get_terminal_size()[1]
    assert sizeX >= 2, "Why?"
    assert sizeY >= 2, "Why?"

    # generate a map that is only as large as needed to fit the Hilbert Curve generated
    cellSpaceSideLength : int = 2 ** int(math.floor(math.log(min(sizeX, sizeY), 2))) # the length of the side of the square generated by the Hilbert Curve
    cellSpace : list[list[int, int, int]] = [[[None, None, None] for _ in range(cellSpaceSideLength)] for _ in range(cellSpaceSideLength)]

    turtle1 : Turtle = Turtle(0, 0, 1) # turtle starts at origin, facing east
    cellSpace[0][0][1] = 3 # initializes origin line segment to start from west
    print(strScreen(cellSpace, turtle1))

    curveTape : list[Literal[-1, 0, 1]] = generateCurve(int(math.floor(math.log(min(sizeX, sizeY), 2)))) # log_2(terminalSize)

    # update loop
    i : int
    for i in range(cellSpaceSideLength**2 - 1):
        turtle2 : Turtle = updateTurtle(turtle1)
        cellSpace[turtle1.x][turtle1.y][0] = turtle1._count
        j : int
        for j in range(4):
            x : int = turtle2.x + Turtle._rotation[j]
            y : int = turtle2.y + Turtle._rotation[j + 1]
            if turtle1.x == x and turtle1.y == y:
                cellSpace[turtle2.x][turtle2.y][1] = j
                cellSpace[turtle1.x][turtle1.y][2] = (j + 2) % 4
                break

        turtle1 = turtle2
        turtle2 = None

        print(strScreen(cellSpace, turtle1) + f"\nIteration: {i + 1}/{cellSpaceSideLength**2 - 1}")
        time.sleep(animationDelay)
