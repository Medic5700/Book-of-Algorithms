import random
import time
animationDelay = 0.05 #in seconds
try:
    import colorama
except:
    print("Warning: Colorama not installed")

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
            forground = "\u001b[96m" #teal
        background = ""
        if i in rh:
            background = "\u001b[40m" #grey?
        line.append("[" + forground + background + bitstring  + "\u001b[0m" + "]")
    line.append(operation.rjust(8," "))

    if endline == True:
        ending = "\n"
    else:
        ending = ""

    time.sleep(animationDelay)
    print("\u001b[0G" + ''.join(line) + "\u001b[0m", end=ending, flush=True) #moves curser to beginning of line, prints line

class MiddleSquare:
    """Implements the middle square random number generator. Generator state is stored internally
    
    https://en.wikipedia.org/wiki/Middle-square_method
    """
    
    def __init__(self, seed, bitlength=8):
        assert bitlength % 2 == 0
        assert bitlength != 0
        assert seed != 0
        
        self.m = [seed] #state memory
        self.bitlength = bitlength
    
    def random(self):
        r = [0 for i in range(1)]
        
        #gets current state
        r[0] = self.m[0]
        visualize(r, self.bitlength, "load", True, rh=[], sh=[0])
        
        #squares
        r[0] = r[0] * r[0]
        visualize(r, self.bitlength, "mult", True, rh=[0], sh=[0])
        
        #selects middle
        r[0] = r[0] >> (self.bitlength//2)
        visualize(r, self.bitlength, "shift", True, rh=[0], sh=[0])
        r[0] = r[0] & (2**self.bitlength-1)
        visualize(r, self.bitlength, "and", True, rh=[0], sh=[0])
        
        #store state
        self.m[0] = r[0]
        visualize(r, self.bitlength, "store", True, rh=[0], sh=[])
        
        assert r[0] < 2**self.bitlength #sanity check
        return r[0]

if __name__ == "__main__":
    animationDelay = 0.0
    bitlength = 16
    
    seed = random.randint(1,2**(bitlength)-1)
    generator = MiddleSquare(seed, (bitlength))
    
    print("random seed is = " + str(seed))
    for i in range(10):
        print(generator.random())
