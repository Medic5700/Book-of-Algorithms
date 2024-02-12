"""
Author: Medic5700
A series a sorting algorithms, visualized
"""

import random
import copy # for deepcopying arrays
import time # for slowing animiation
    
animationDelay : float = 0.05 # in seconds

def visualize(A : list[int], newline : bool = True, dataComparisons : int = 0, dataSwaps: int = 0, highlight : list[int] = []):
    """
    Takes in an array of numbers, and displays an ANSI colour coded representation of array, with brighter red corrisponding to highest value

    Note: shade of colour is determined by how high the element is in the overall rank, not by it's value (IE: [1,2,3] will display the same as [0,5,500000000])
    newline = specifies whether to print a new line
    highlight = specifies 2 index positions to print a blue highlight character
    """
    assert type(A) is list
    assert all([type(i) is int for i in A])
    assert len(A) <= 64
    assert all([(0 <= i <= 255) for i in A])

    assert type(newline) is bool

    assert type(dataComparisons) is int
    assert dataComparisons >= 0

    assert type(dataSwaps) is int
    assert dataSwaps >= 0
    
    assert type(highlight) is list
    assert (len(highlight) == 0) or (len(highlight) == 2)
    assert all([type(i) is int for i in highlight])
    assert all([(0 <= i <= len(A)) for i in highlight]), highlight
    
    global animationDelay

    colourScaling : int = 255 // len(A)
    B : list[int] = copy.deepcopy(A)
    B.sort()

    line : list[str] = []
    i : int
    for i in range(len(A)):
        colour : int = B.index(A[i]) # colour is determined by final position in sorted array, not value
        backgroundColour : str = "\u001b[48;2;" + str(colour * colourScaling) + ";0;0m"
        forgroundColour : str = "\u001b[38;2;64;64;255m" # the 'highlight' colour
        value : str = " "
        if i in highlight:
            if i == highlight[0]: # lower value
                value = "\u2584"
            else: # upper value
                value = "\u2580"
        line.append(backgroundColour + forgroundColour + value)

    if newline == True:
        endline = "\n"
    else:
        endline = ""
    print("\u001b[0G" + "[" + ''.join(line) + "\u001b[0m" + "]" + \
            f"    DataComparisons = {str(dataComparisons).rjust(4, '0')};" + \
            f"    DataSwaps = {str(dataSwaps).rjust(4, '0')}", \
            end=endline, flush=True)
    time.sleep(animationDelay)

def _isSorted(A : list[int]) -> bool:
    """Takes an array of integrarts, A -> returns True iff array is sorted, False otherwise"""
    assert type(A) is list
    assert all([type(i) is int for i in A])
    assert len(A) >= 1

    result : bool = True
    i : int
    for i in range(len(A) - 1):
        if A[i] > A[i+1]:
            result = False
            break
    return result

def bubbleSort1(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    The simple dumb way"""
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    
    for _ in range(len(B)):
        j : int
        for j in range(len(B) - 1):
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO

    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

def bubbleSort2(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers"""
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    i : int
    for i in range(len(B)):
        j : int
        for j in range(len(B) - 1 - i):
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO

    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

def bubbleSort3(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    Reference({
        'Number': None,
        'Accessed': '2024-02-12',
        'Author': [
        ],
        'Title': 'Bubble sort - Wikipedia',
        'Host': 'Wikipedia',
        'URL': [
            'https://en.wikipedia.org/wiki/Bubble_sort'
        ],
        'Revised': '2024-01-29',
        'Note': None
    })
    """
    
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    i : int
    for i in range(len(B)):
        swapped : bool = False
        j : int
        for j in range(len(B) - 1 - i):
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                swapped = True

                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO
        if not swapped:
            break

    visualize(B, True, dataComparisons, dataSwaps)
    return B

def cocktailShakerSort1(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    Reference({
        'Number': None,
        'Accessed': '2024-02-12',
        'Author': [
        ],
        'Title': 'Cocktail shaker sort - Wikipedia',
        'Host': 'Wikipedia',
        'URL': [
            'https://en.wikipedia.org/wiki/Cocktail_shaker_sort'
        ],
        'Revised': '2023-11-25',
        'Note': None
    })
    """
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    i : int
    for i in range(len(B) // 2):
        j : int
        for j in range(i, len(B) - 1 - i, 1): # goes forward through array
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        j : int
        for j in range(len(B) - 2 - i, i -1, -1): # goes backwards through array
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO

    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

def cocktailShakerSort2(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    Reference({
        'Number': None,
        'Accessed': '2024-02-12',
        'Author': [
        ],
        'Title': 'Cocktail shaker sort - Wikipedia',
        'Host': 'Wikipedia',
        'URL': [
            'https://en.wikipedia.org/wiki/Cocktail_shaker_sort'
        ],
        'Revised': '2023-11-25',
        'Note': None
    })
    """
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    i : int
    for i in range(len(B) // 2):
        swapped : bool = False
        j : int
        for j in range(i, len(B) - 1 - i, 1): # goes forward through array
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                swapped = True

                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        j : int
        for j in range(len(B) - 2 - i, i - 1, -1): # goes backwards through array
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [j, j+1])           #DEMO
            if B[j] > B[j+1]:
                swapped = True

                temp : int = B[j+1]
                B[j+1] = B[j]
                B[j] = temp

                dataSwaps += 1                                                  #DEMO
        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO
        if not swapped:
            break

    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

def gnomeSort1(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    Reference({
        'Number': None,
        'Accessed': '2024-02-12',
        'Author': [
        ],
        'Title': 'Gnome sort - Wikipedia',
        'Host': 'Wikipedia',
        'URL': [
            'https://en.wikipedia.org/wiki/Gnome_sort'
        ],
        'Revised': '2023-11-01',
        'Note': None
    })
    """
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    i : int = 0
    while i < (len(B)): # fails when at end of list, and thus everything is sorted
        if (i == 0): # when at beginning of list, move right
            visualize(B, False, dataComparisons, dataSwaps, [i, i])             #DEMO
            i += 1
        elif (B[i] >= B[i-1]): # when both elements are storted, move right
            dataComparisons += 1                                                #DEMO
            visualize(B, False, dataComparisons, dataSwaps, [i-1, i])           #DEMO
            i += 1
        else: # both elements aren't sorted, swap and move left
            visualize(B, False, dataComparisons, dataSwaps, [i-1, i])           #DEMO
            dataSwaps += 1                                                      #DEMO

            temp : int = B[i]
            B[i] = B[i-1]
            B[i-1] = temp
            
            i += -1
    
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

def combSort1(A : list[int]) -> list[int]:
    """Takes an unsorted array of integers, A -> returns an array of sorted integers

    Reference({
        'Number': None,
        'Accessed': '2024-02-12',
        'Author': [
        ],
        'Title': 'Comb sort - Wikipedia',
        'Host': 'Wikipedia',
        'URL': [
            'https://en.wikipedia.org/wiki/Comb_sort'
        ],
        'Revised': '2023-11-11',
        'Note': None
    })
    """
    assert type(A) is list
    assert all([type(i) is int for i in A])

    B : list[int] = copy.deepcopy(A)

    dataComparisons : int = 0                                                   #DEMO
    dataSwaps : int = 0                                                         #DEMO
    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO

    gap : int = len(B)
    shrink : float = 1.3
    isSorted : bool = False

    while not isSorted:
        visualize(B, False, dataComparisons, dataSwaps)                         #DEMO

        gap = int(gap // shrink)
        if gap <= 1:
            gap = 1
            isSorted = True

        for i in range(len(B) - gap):
            visualize(B, False, dataComparisons, dataSwaps, [i, i+gap])         #DEMO
            dataComparisons += 1                                                #DEMO

            if B[i] > B[i+gap]:
                temp : int = B[i]
                B[i] = B[i+gap]
                B[i+gap] = temp

                isSorted = False

                dataSwaps += 1                                                  #DEMO

        visualize(B, True, dataComparisons, dataSwaps)                          #DEMO

    visualize(B, True, dataComparisons, dataSwaps)                              #DEMO
    return B

if __name__ == "__main__":
    A : list[int] = [None for _ in range(16)]
    B : list[int] = None
    i : int
    for i in range(len(A)):
        while(True):
            x : int = random.randint(0, 255)
            if not (x in A):
                A[i] = x
                break
    # A is unsorted list, will not contain duplicats for demonstration purposes
    print("Generated unsorted list ".ljust(80, '-'))
    print(A)

    print("showing BubbleSort1 ".ljust(80, '-'))
    B = bubbleSort1(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing BubbleSort2 ".ljust(80, '-'))
    B = bubbleSort2(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing BubbleSort3 ".ljust(80, '-'))
    B = bubbleSort3(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing CocktailShaker1 Sort ".ljust(80, '-'))
    B = cocktailShakerSort1(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing CocktailShaker2 Sort ".ljust(80, '-'))
    B = cocktailShakerSort2(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing GnomeSort1 Sort ".ljust(80, '-'))
    B = gnomeSort1(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)

    print("showing CombSort1 Sort ".ljust(80, '-'))
    B = combSort1(copy.deepcopy(A))
    assert _isSorted(B)
    print(B)
