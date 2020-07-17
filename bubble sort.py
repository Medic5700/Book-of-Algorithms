"""
By: Medic5700
A series a bubble sort algorithms, visualized
"""

import random
import copy #for deepcopying arrays
import time
    
animationDelay = 0.05 #in seconds

def visualize(A, newline=True, highlight=[]):
    """
    Takes in an array of numbers, and displays an ANSI colour coded representation of array, with brighter red corrisponding to highest value

    Note: shade of colour is determined by how high the element is in the overall rank, not by it's value (IE: [1,2,3] will display the same as [0,5,500000000])
    newline = specifies whether to print a new line
    highlight = specifies 2 index positions to print a blue highlight character
    """
    assert len(A) <= 64
    assert highlight != None and len(highlight) <= len(A)

    colourScaling = 256//len(A)
    B = copy.deepcopy(A)
    B.sort()

    line = []
    for i in range(len(A)):
        colour = B.index(A[i])
        backgroundColour = "\u001b[48;2;" + str(colour*colourScaling) + ";0;0m"
        forgroundColour = "\u001b[38;2;0;0;255m"
        value = " "
        if i in highlight:
            if i == highlight[0]:
                value = "["
            else:
                value = "]"
        line.append(backgroundColour + forgroundColour + value)

    if newline == True:
        endline = "\n"
    else:
        endline = ""
    time.sleep(animationDelay)
    print("\u001b[0G" + "[" + ''.join(line) + "\u001b[0m" + "]", end=endline, flush=True)

def bubbleSort1(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    The simple dumb way"""
    for i in range(len(A)):
        for j in range(len(A) - 1):
            visualize(A, False, [j, j+1])
            if A[j] > A[j+1]:
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        visualize(A, True)
    return A

def bubbleSort2(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers"""
    for i in range(len(A)):
        for j in range(len(A) - 1 - i):
            visualize(A, False, [j,j+1])
            if A[j] > A[j+1]:
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        visualize(A, True)
    return A

def bubbleSort3(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    https://en.wikipedia.org/wiki/Bubble_sort
    """
    for i in range(len(A)):
        swapped = False
        for j in range(len(A) - 1 - i):
            visualize(A, False, [j,j+1])
            if A[j] > A[j+1]:
                swapped = True
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        visualize(A, True)
        if swapped == False:
            break
    return A

def cocktailShakerSort1(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    https://en.wikipedia.org/wiki/Cocktail_shaker_sort
    """
    for i in range(len(A)//2):
        for j in range(i, len(A) - 1 - i, 1): #goes forward through array
            visualize(A, False, [j,j+1])
            if A[j] > A[j+1]:
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        for j in range(len(A) - 2 - i, i -1, -1): #goes backwards through array
            visualize(A, False, [j,j-1])
            if A[j] > A[j+1]:
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        visualize(A, True)
    return A

def cocktailShakerSort2(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    https://en.wikipedia.org/wiki/Cocktail_shaker_sort
    """
    for i in range(len(A)//2):
        swapped = False
        for j in range(i, len(A) - 1 - i, 1): #goes forward through array
            visualize(A, False, [j,j+1])
            if A[j] > A[j+1]:
                swapped = True
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        for j in range(len(A) - 2 - i, i -1, -1): #goes backwards through array
            visualize(A, False, [j,j-1])
            if A[j] > A[j+1]:
                swapped = True
                temp = A[j+1]
                A[j+1] = A[j]
                A[j] = temp
        visualize(A, True)
        if swapped == False:
            break
    return A

def gnomeSort1(A : list) -> list:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    https://en.wikipedia.org/wiki/Gnome_sort
    """
    i = 1
    while i < (len(A)): #fails when at end of list, and thus everything is sorted
        visualize(A, False, [i-1,i])
        if (i == 0) or (A[i] >= A[i-1]): #when at beginning of list, or both elements are storted, move right
            i += 1
        else: #both elements aren't sorted, swap and move left
            temp = A[i]
            A[i] = A[i-1]
            A[i-1] = temp
            i += -1
    return A

if __name__ == "__main__":
    animationDelay = 0.05

    A = [None for i in range(16)]
    for i in range(len(A)):
        while(True):
            x = random.randint(0, 255)
            if not (x in A):
                A[i] = x
                break
    #A is unsorted list, can contain duplicats (but doesn't in this example)
    print(A)

    print("showing BubbleSort1  ===========================================================")
    print(bubbleSort1(copy.deepcopy(A)))

    print("showing BubbleSort2  ===========================================================")
    print(bubbleSort2(copy.deepcopy(A)))

    print("showing BubbleSort3  ===========================================================")
    print(bubbleSort3(copy.deepcopy(A)))

    print("showing CocktailShaker1 Sort  ==================================================")
    print(cocktailShakerSort1(copy.deepcopy(A)))

    print("showing CocktailShaker2 Sort  ==================================================")
    print(cocktailShakerSort2(copy.deepcopy(A)))

    print("showing GnomeSort1 Sort  =======================================================")
    print(gnomeSort1(copy.deepcopy(A)))
