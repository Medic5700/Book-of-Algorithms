import random
import time
animationDelay = 0.05 #in seconds

def visualize(registers, bitlength, operation="", endline=True, rh=[], sh=[]):
    """Takes array of registers, bitlength, and opertation, and prints the line

    boolean endline = if you want the line to end
    int array rh    = array of indexes for 'read highlight' (background grey)
    int array sh    = array of indexes for 'store highlight' (foreground teal)
    """
    line = []
    for i in range(len(registers)):
        bitstring = str(bin(registers[i])[2:]).rjust(bitlength*2, "0")
        forground = ""
        if i in sh:
            forground = "\u001b[31m" #red
        background = ""
        if i in rh:
            background = "\u001b[46m" #teal
        line.append("[" + forground + background + bitstring  + "\u001b[0m" + "]")
    line.append(operation.rjust(8," "))

    if endline == True:
        ending = "\n"
    else:
        ending = ""

    time.sleep(animationDelay)
    print("\u001b[0G" + ''.join(line) + "\u001b[0m", end=ending, flush=True) #moves curser to beginning of line, prints line

def multiply1(a, b, bitlength=8):
    '''Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits
    https://en.wikipedia.org/wiki/Binary_multiplier#Basics
    '''
    assert a < 2**bitlength
    assert b < 2**bitlength

    r = [0 for i in range(4)]

    r[0] = a #needs to be double the bit size of the number inputs
    r[1] = b
    r[3] = 0 #needs to be double the bit size of the number inputs

    visualize(r, bitlength, "no-op", True)

    for i in range(bitlength):
        r[2] = r[1] & 1
        visualize(r, bitlength, "and", False, rh=[1], sh=[2])
        visualize(r, bitlength, "compare", False, rh=[2])
        if r[2] == 1:
            r[3] = r[0] + r[3]
            visualize(r, bitlength, "add", False, rh=[0,3], sh=[3])
        r[0] = r[0] << 1
        visualize(r, bitlength, "shift", False, rh=[0], sh=[0])
        r[1] = r[1] >> 1
        visualize(r, bitlength, "shift", True, rh=[1], sh=[1])

    z = r[3]
    
    assert z == a * b #sanity check
    return z

if __name__ == "__main__":
    animationDelay = 0.5

    print("showing multiply1 =========================================================================")
    for i in range(10):
        a = random.randint(0,255)
        b = random.randint(0,255)
        z = multiply1(a,b)
        print("a = " + str(a), "b = " + str(b), "output = " + str(z), "\t", z == a*b)
