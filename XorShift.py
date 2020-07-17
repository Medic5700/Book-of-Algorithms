"""
By: Medic5700
An implementation of the xorShift random number generatore
"""

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
            forground = "\u001b[96m" #teal
        background = ""
        if i in rh:
            background = "\u001b[40m" #grey?
        line.append("[" + forground + background + bitstring  + "\u001b[0m" + "]")
    line.append(operation.rjust(12," "))

    if endline == True:
        ending = "\n"
    else:
        ending = ""

    time.sleep(animationDelay)
    print("\u001b[0G" + ''.join(line) + "\u001b[0m", end=ending, flush=True) #moves curser to beginning of line, prints line
    
class XorShift:
    """Implements an XorShift Random Number Generator (32-bit, 64-bit, 128-bit only)
    
    https://en.wikipedia.org/wiki/Xorshift
    """
    
    def __init__(self, seed, bitlength=32):
        assert seed != 0
        assert seed < 2**bitlength
        assert bitlength in [32, 64, 128]
        
        self.m = [0 for i in range(4)]
        self.m[0] = seed
        self.bitlength = bitlength
        
        if bitlength == 32:
            self.random = self.random32
        
    def random32(self):
        """Returns a random number with each successuve call, stores state internally
        
        Implements example implementation from wikipedia        
        https://en.wikipedia.org/wiki/Xorshift#Example_implementation
        """
        assert self.bitlength == 32
        
        r = [self.m[0], 0]
        visualize(r, self.bitlength, "load", True, rh=[], sh=[0])
        
        r[1] = r[0] << 13
        visualize(r, self.bitlength, "shift", True, rh=[1], sh=[0])
        #because python can deal with arbitrarily large numbers, you have to select the lower section of the number to simulate 'cutting off' the number during a left shift
        r[1] = r[1] & (2**self.bitlength-1)
        visualize(r, self.bitlength, "python quirk", False, rh=[1], sh=[1])
        r[0] = r[0]^r[1]
        visualize(r, self.bitlength, "xor", True, rh=[0,1], sh=[0])
        
        r[1] = r[0] >> 17
        visualize(r, self.bitlength, "shift", True, rh=[1], sh=[0])
        r[0] = r[0]^r[1]
        visualize(r, self.bitlength, "xor", True, rh=[0,1], sh=[0])        
        
        r[1] = r[0] << 5
        visualize(r, self.bitlength, "shift", True, rh=[1], sh=[0])
        #because python can deal with arbitrarily large numbers, you have to select the lower section of the number to simulate 'cutting off' the number during a left shift
        r[1] = r[1] & (2**self.bitlength-1)        
        visualize(r, self.bitlength, "python quirk", False, rh=[1], sh=[1])
        r[0] = r[0]^r[1]
        visualize(r, self.bitlength, "xor", True, rh=[0,1], sh=[0])
        
        self.m[0] = r[0]
        visualize(r, self.bitlength, "store", True, rh=[0], sh=[])
        
        return r[0]
    
    def random32_Deep(self):
        """Showing more options for shift values and etc directly from the white paper?
        The Florida State University - George Marsaglia - Xorshift RNGs
        """
        assert self.bitlength == 32
        
        #initializes to pick a random shift value and shift pattern
        try:
            x = self.x
            y = self.y
        except:
            self.x = random.randint(0,81-1)
            self.y = random.randint(0,7)
            #yes, I am aware of the irony =P
            
            x = self.x
            y = self.y
        
        shiftValues = [
            ( 1, 3,10),( 1, 5,16),( 1, 5,19),( 1, 9,29),( 1,11, 6),( 1,11,16),( 1,19, 3),( 1,21,20),( 1,27,27),
            ( 2, 5,15),( 2, 5,21),( 2, 7, 7),( 2, 7, 9),( 2, 7,25),( 2, 9,15),( 2,15,17),( 2,15,25),( 2,21, 9),
            ( 3, 1,14),( 3, 3,26),( 3, 3,28),( 3, 3,29),( 3, 5,20),( 3, 5,22),( 3, 5,25),( 3, 7,29),( 3,13, 7),
            ( 3,23,25),( 3,25,24),( 3,27,11),( 4, 3,17),( 4, 3,27),( 4, 5,15),( 5, 3,21),( 5, 7,22),( 5, 9, 7),
            ( 5, 9,28),( 5, 9,31),( 5,13, 6),( 5,15,17),( 5,17,13),( 5,21,12),( 5,27, 8),( 5,27,21),( 5,27,25),
            ( 5,27,28),( 6, 1,11),( 6, 3,17),( 6,17, 9),( 6,21, 7),( 6,21,13),( 7, 1, 9),( 7, 1,18),( 7, 1,25),
            ( 7,13,25),( 7,17,21),( 7,25,12),( 7,25,20),( 8, 7,23),( 8,9, 23),( 9, 5, 1),( 9, 5,25),( 9,11,19),
            ( 9,21,16),(10, 9,21),(10, 9,25),(11, 7,12),(11, 7,16),(11,17,13),(11,21,13),(12, 9,23),(13, 3,17),
            (13, 3,27),(13, 5,19),(13,17,15),(14, 1,15),(14,13,15),(15, 1,29),(17,15,20),(17,15,23),(17,15,26)
            ]
        #is shiftValues[60] a typo? it's ( 9, 5, 1), but it looks like it 'should' be ( 9, 5, 10) because (a < c) fails? or is ( 9, 5, 1) valid because it can be rearranged?
        
        a,b,c = shiftValues[x]
        
        r = [self.m[0], 0]
        
        if y == 0:
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)
            r[0] = r[0]^r[1]
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]       
            
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]
        elif y == 1:
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)
            r[0] = r[0]^r[1]
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]       
            
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]            
        elif y == 2:
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> c
            r[0] = r[0]^r[1]             
        elif y == 3:
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> a
            r[0] = r[0]^r[1]               
        elif y == 4:
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]            
        elif y == 5:
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]              
        elif y == 6:
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]             
        elif y == 7:
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]             
        
        self.m[0] = r[0]  
        return r[0]
        
    def random64(self):
        pass
    
    def random64_Deep(self):
        """Showing more options for shift values
        The Florida State University - George Marsaglia - Xorshift RNGs
        """
        assert self.bitlength == 64
        
        #initializes to pick a random shift value and shift pattern
        try:
            x = self.x
            y = self.y
        except:
            self.x = random.randint(0,275-1)
            self.y = random.randint(0,7)
            #yes, I am aware of the irony =P
            
            x = self.x
            y = self.y
        
        shiftValues = [
            ( 1, 1,54),( 1, 1,55),( 1, 3,45),( 1, 7, 9),( 1, 7,44),( 1, 7,46),( 1, 9,50),( 1,11,35),( 1,11,50),
            ( 1,13,45),( 1,15, 4),( 1,15,63),( 1,19, 6),( 1,19,16),( 1,23,14),( 1,23,29),( 1,29,34),( 1,35, 5),
            ( 1,35,11),( 1,35,34),( 1,45,37),( 1,51,13),( 1,53, 3),( 1,59,14),( 2,13,23),( 2,31,51),( 2,31,53),
            ( 2,43,27),( 2,47,49),( 3, 1,11),( 3, 5,21),( 3,13,59),( 3,21,31),( 3,25,20),( 3,25,31),( 3,25,56),
            ( 3,29,40),( 3,29,47),( 3,29,49),( 3,35,14),( 3,37,17),( 3,43, 4),( 3,43, 6),( 3,43,11),( 3,51,16),
            ( 3,53, 7),( 3,61,17),( 3,61,26),( 4, 7,19),( 4, 9,13),( 4,15,51),( 4,15,53),( 4,29,45),( 4,29,49),
            ( 4,31,33),( 4,35,15),( 4,35,21),( 4,37,11),( 4,37,21),( 4,41,19),( 4,41,45),( 4,43,21),( 4,43,31),
            ( 4,53, 7),( 5, 9,23),( 5,11,54),( 5,15,27),( 5,17,11),( 5,23,36),( 5,33,29),( 5,41,20),( 5,45,16),
            ( 5,47,23),( 5,53,20),( 5,59,33),( 5,59,35),( 5,59,63),( 6, 1,17),( 6, 3,49),( 6,17,47),( 6,23,27),
            ( 6,27, 7),( 6,43,21),( 6,49,29),( 6,55,17),( 7, 5,41),( 7, 5,47),( 7, 5,55),( 7, 7,20),( 7, 9,38),
            ( 7,11,10),( 7,11,35),( 7,13,58),( 7,19,17),( 7,19,54),( 7,23, 8),( 7,25,58),( 7,27,59),( 7,33, 8),
            ( 7,41,40),( 7,43,28),( 7,51,24),( 7,57,12),( 8, 5,59),( 8, 9,25),( 8,13,25),( 8,13,61),( 8,15,21),
            ( 8,25,59),( 8,29,19),( 8,31,17),( 8,37,21),( 8,51,21),( 9, 1,27),( 9, 5,36),( 9, 5,43),( 9, 7,18),
            ( 9,19,18),( 9,21,11),( 9,21,20),( 9,21,40),( 9,23,57),( 9,27,10),( 9,29,12),( 9,29,37),( 9,37,31),
            ( 9,41,45),(10, 7,33),(10,27,59),(10,53,13),(11, 5,32),(11, 5,34),(11, 5,43),(11, 5,45),(11, 9,14),
            (11, 9,34),(11,13,40),(11,15,37),(11,23,42),(11,23,56),(11,25,48),(11,27,26),(11,29,14),(11,31,18),
            (11,53,23),(12, 1,31),(12, 3,13),(12, 3,49),(12, 7,13),(12,11,47),(12,25,27),(12,39,49),(12,43,19),
            (13, 3,40),(13, 3,53),(13, 7,17),(13, 9,15),(13, 9,50),(13,13,19),(13,17,43),(13,19,28),(13,19,47),
            (13,21,18),(13,21,49),(13,29,35),(13,35,30),(13,35,38),(13,47,23),(13,51,21),(14,13,17),(14,15,19),
            (14,23,33),(14,31,45),(14,47,15),(15, 1,19),(15, 5,37),(15,13,28),(15,13,52),(15,17,27),(15,19,63),
            (15,21,46),(15,23,23),(15,45,17),(15,47,16),(15,49,26),(16, 5,17),(16, 7,39),(16,11,19),(16,11,27),
            (16,13,55),(16,21,35),(16,25,43),(16,27,53),(16,47,17),(17,15,58),(17,23,29),(17,23,51),(17,23,52),
            (17,27,22),(17,45,22),(17,47,28),(17,47,29),(17,47,54),(18, 1,25),(18, 3,43),(18,19,19),(18,25,21),
            (18,41,23),(19, 7,36),(19, 7,55),(19,13,37),(19,15,46),(19,21,52),(19,25,20),(19,41,21),(19,43,27),
            (20, 1,31),(20, 5,29),(21, 1,27),(21, 9,29),(21,13,52),(21,15,28),(21,15,29),(21,17,24),(21,17,30),
            (21,17,48),(21,21,32),(21,21,34),(21,21,37),(21,21,38),(21,21,40),(21,21,41),(21,21,43),(21,41,23),
            (22, 3,39),(23, 9,38),(23, 9,48),(23, 9,57),(23,13,38),(23,13,58),(23,13,61),(23,17,25),(23,17,54),
            (23,17,56),(23,17,62),(23,41,34),(23,41,51),(24, 9,35),(24,11,29),(24,25,25),(24,31,35),(25, 7,46),
            (25, 7,49),(25, 9,39),(25,11,57),(25,13,29),(25,13,39),(25,13,62),(25,15,47),(25,21,44),(25,27,27),
            (25,27,53),(25,33,36),(25,39,54),(28, 9,55),(28,11,53),(29,27,37),(31, 1,51),(31,25,37),(31,27,35),
            (33,31,43),(33,31,55),(43,21,46),(49,15,61),(55, 9,56)
            ]
        #is shiftValues[60] a typo? it's ( 9, 5, 1), but it looks like it 'should' be ( 9, 5, 10) because a !< c? or is ( 9, 5, 1) valid because it can be rearranged?
        
        a,b,c = shiftValues[x]
        
        r = [self.m[0], 0]
        
        if y == 0:
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)
            r[0] = r[0]^r[1]
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]       
            
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]
        elif y == 1:
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)
            r[0] = r[0]^r[1]
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]       
            
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]            
        elif y == 2:
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> c
            r[0] = r[0]^r[1]             
        elif y == 3:
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> a
            r[0] = r[0]^r[1]               
        elif y == 4:
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]            
        elif y == 5:
            r[1] = r[0] << c
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << a
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> b
            r[0] = r[0]^r[1]              
        elif y == 6:
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]             
        elif y == 7:
            r[1] = r[0] >> c
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] >> a
            r[0] = r[0]^r[1] 
            
            r[1] = r[0] << b
            r[1] = r[1] & (2**self.bitlength-1)        
            r[0] = r[0]^r[1]             
        
        self.m[0] = r[0]  
        return r[0]        
    
    def random128(self):
        pass
    
if __name__ == "__main__":
    animationDelay = 0.0
    bitlength = 64 #TODO set it up to cycle through the different bitlengths, since only the short bitlength is animated
    
    seed = random.randint(1,2**(bitlength)-1)
    generator = XorShift(seed, (bitlength))
    generator.random = generator.random64_Deep
    
    print("random seed is = " + str(seed))
    for i in range(10):
        print(generator.random())
