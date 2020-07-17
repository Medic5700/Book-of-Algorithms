"""
By: Medic5700
A binary search algorithm
"""

import random
import math

def binarySearch(A, T):
    """ Takes array of unique numbers A, and target number T -> returns index of T, None if not found
    https://en.wikipedia.org/wiki/Binary_search_algorithm#Alternative_procedure
    """    
    def visualize(A, L, R, T):
        line = [" " for i in range(len(A))]
        for i in range(len(A)):
            if i >= L and i <= R:
                line[i] = "-"
            else:
                line[i] = " "
        line[R] = "R"
        line[L] = "L"
        line[A.index(T)] = "T"
        print("[" + "".join(line) + "]")

    L = 0
    R = len(A) - 1
   
    while(L != R):
        visualize(A, L, R, T)
        m = math.ceil((L + R) / 2)
        if A[m] > T:
            R = m - 1
        else:
            L = m
    visualize(A, L, R, T)
    
    if A[L] == T:
        return L
    return None

if __name__ == "__main__":
    A = [None for i in range(16)]
    for i in range(len(A)):
        while(True):
            x = random.randint(0, 255)
            if not (x in A):
                A[i] = x
                break
    A.sort()
    #A is sorted, and has unique elements
    print(A)
        
    T = A[random.randint(0,16-1)]
    
    #print(T, binarySearch(A,T), A[binarySearch(A,T)])
    result = binarySearch(A,T)
    print("\nFind T = " + str(T))
    print("Index is = " + str(result))
    print("A[T] = " + str(A[result]))
