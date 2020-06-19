class DumbALU:
    def __init__(self, bitLength=16, intermediateSize=0, registerSize=1, memorySize=0, verboseLevel=1, animationDelay=0.5):
        self.bitLength = bitLength #the length of the registers in bits
        self.verboseLevel = verboseLevel
        self.memory = {}
        self.memory['i'] = [0 for i in range(intermediateSize)] #double length registers for stuff like multiplication
        self.memory['r'] = [0 for i in range(registerSize)] #standard registers
        self.memory['m'] = [0 for i in range(memorySize)] #standard memory
        self.memory['s'] = [0] #special register for storing operation literals
        print(self.memory)
        self.code = None
        self.lastState = None
        self.pc = 0

        self._snapshot()

    def _snapshot(self):
        lastState = {}
        lastState['i'] = [self.memory['i'][j] for j in range(len(self.memory['i']))]
        lastState['r'] = [self.memory['r'][j] for j in range(len(self.memory['r']))]
        lastState['m'] = [self.memory['m'][j] for j in range(len(self.memory['m']))]
        lastState['s'] = [self.memory['s'][0]]
        self.lastState = lastState
    
    def _display(self, operation, readList, writeList):
        """displays the current operation"""

        text = ""
        line1 = str(operation) + "\t\t" + "[" + str(bin(self.memory['s'][0])[2:].rjust(self.bitLength, '0')) + "]" + "\n"
        
        line2 = "  "
        for i in range(len(self.lastState['r'])):
            line2 += "[" + str(bin(self.lastState['r'][i])[2:].rjust(self.bitLength, '0')) + "]"
        line2 += "\n"

        line3 = "  "
        for i in range(len(self.memory['r'])):
            line3 += "[" + str(bin(self.memory['r'][i])[2:].rjust(self.bitLength, '0')) + "]"
        line3 += ""

        print(line1 + line2 + line3)

    def _inject(self):
        """injects an array of data into memory"""
        pass

    def _flush(self):
        """makes display go to next line"""
        pass

    def opNoop(self, lineNumber, text="no-op"):
        self._snapshot()
        self._display(text, [], [])

    def opLoad(self, lineNumber, operation, source, destination):
        operation = "load" + "\t" + str(source) + " -> " + str(destination)

        if type(source) is int:
            self.memory['s'] = [source]
            source = 's0'
        
        self.memory[destination[0]][int(destination[1:])] = self.memory[source[0]][int(source[1:])]

        self._display(operation,
                      [source],
                      [destination]
                      )

    def opAnd (self, lineNumber, operation, source1, source2, destination):
        self._snapshot()

        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] & self.memory[source2[0]][int(source2[1:])]

        self._display("and",
                      [source1, source2],
                      [destination]
                      )

    def opShiftL(self):
        pass

    def opAdd(self):
        pass

def multiply1(a, b, bitlength=8):
    '''Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits
    https://en.wikipedia.org/wiki/Binary_multiplier#Basics
    '''
    assert a < 2**bitlength
    assert b < 2**bitlength

    ALU = DumbALU(16, 0, 4, 0, 0)

    r = [0 for i in range(4)]

    ALU.opNoop("init")

    ALU.opLoad(0, "load", a, 'r0')
    r[0] = a #needs to be double the bit size of the number inputs
    ALU.opLoad(0, "load", b, 'r1')
    r[1] = b
    ALU.opLoad(0, "load", 0, 'r3')
    r[3] = 0 #needs to be double the bit size of the number inputs

    #visualize(r, bitlength, "no-op", True)

    for i in range(bitlength):
        ALU.opAnd(0, 'and', 'r1', 1, 'r2')
        r[2] = r[1] & 1
        #visualize(r, bitlength, "and", False, rh=[1], sh=[2])
        #visualize(r, bitlength, "compare", False, rh=[2])
        if r[2] == 1:
            r[3] = r[0] + r[3]
            #visualize(r, bitlength, "add", False, rh=[0,3], sh=[3])
        r[0] = r[0] << 1
        #visualize(r, bitlength, "shift", False, rh=[0], sh=[0])
        r[1] = r[1] >> 1
        #visualize(r, bitlength, "shift", True, rh=[1], sh=[1])

    z = r[3]
    
    assert z == a * b #sanity check
    return z

if __name__ == "__main__":
    multiply1(2,5)
