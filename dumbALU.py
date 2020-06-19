class DumbALU:
    def __init__(self, bitLength=16, intermediateSize=0, registerSize=1, memorySize=0, verboseLevel=1, animationDelay=0.5):
        import time
        self.sleep = time.sleep #avoids having to reimport time module in _display function every time it's called
        self.animationDelay = animationDelay
        
        self.bitLength = bitLength #the length of the registers in bits
        self.verboseLevel = verboseLevel
        self.memory = {}
        self.memory['i'] = [0 for i in range(intermediateSize)] #double length registers for stuff like multiplication
        self.memory['r'] = [0 for i in range(registerSize)] #standard registers
        self.memory['m'] = [0 for i in range(memorySize)] #standard memory
        self.memory['s'] = [0] #special register for storing static numbers that would be encoded in the instruction word
        self.memory['pc'] = 0
        self.code = None
        self.lastState = None

        self._snapshot()

    def _snapshot(self):
        lastState = {}
        lastState['i'] = [self.memory['i'][j] for j in range(len(self.memory['i']))]
        lastState['r'] = [self.memory['r'][j] for j in range(len(self.memory['r']))]
        lastState['m'] = [self.memory['m'][j] for j in range(len(self.memory['m']))]
        lastState['s'] = [self.memory['s'][0]]
        lastState['pc'] = self.memory['pc']
        self.lastState = lastState

    def _display(self, operation, readList, writeList):
        """displays the current operation

        display is arranged horizontally"""
        #TODO figure out how to display memory

        readColour = "\u001b[96m" #forground teal
        writeColour = "\u001b[31m" #forground red
        ansiEnd = "\u001b[0m"

        opLine = '0x' + hex(self.lastState['pc'])[2:].rjust(2, '0') + '    '
        opLine += str(operation.expandtabs(8))
        
        opLine = opLine.ljust(80 - (self.bitLength+2), ' ')
        if 's0' in readList: #prints the 'static register' for static numbers, IE; adding a register to a number in the instruction word
            opLine += "[" + readColour + str(bin(self.memory['s'][0])[2:].rjust(self.bitLength, '0')) + ansiEnd + "]"
        else:
            opLine += ''.ljust(self.bitLength+2, ' ')

        registers = []
        for i in range(len(self.memory['i'])):
            column1 = '    ' + ('I' + str(i)).ljust(4, ' ')
            
            column2 = '['
            if ('i'+str(i)) in readList:
                column2 += readColour
            column2 += str(bin(self.lastState['i'][i])[2:].rjust(self.bitLength*2, '0'))
            if ('i'+str(i)) in readList:
                column2 += ansiEnd
            column2 += ']'

            column3 = '['
            if ('i'+str(i)) in writeList:
                column3 += writeColour
            column3 += str(bin(self.memory['i'][i])[2:].rjust(self.bitLength*2, '0'))
            if ('i'+str(i)) in writeList:
                column3 += ansiEnd
            column3 += ']'

            registers += [column1 + column2 + '    ' + column3]

        for i in range(len(self.memory['r'])):
            column1 = '    ' + ('R' + str(i)).ljust(4, ' ')
            
            column2 = '['
            if ('r'+str(i)) in readList:
                column2 += readColour
            column2 += str(bin(self.lastState['r'][i])[2:].rjust(self.bitLength, '0'))
            if ('r'+str(i)) in readList:
                column2 += ansiEnd
            column2 += ']'

            column3 = '['
            if ('r'+str(i)) in writeList:
                column3 += writeColour
            column3 += str(bin(self.memory['r'][i])[2:].rjust(self.bitLength, '0'))
            if ('r'+str(i)) in writeList:
                column3 += ansiEnd
            column3 += ']'

            registers += [column1 + column2 + ''.ljust(self.bitLength, ' ') + '    ' + column3]

        screen = ''
        screen += opLine
        for i in registers:
            screen += '\n' + i

        self.sleep(self.animationDelay)
        print(screen)
    
    def _display2(self, operation, readList, writeList):
        """displays the current operation

        does not scale, will need to be replaced with 'verticle orentation'"""
        readColour = "\u001b[96m" #forground teal
        writeColour = "\u001b[31m" #forground red
        ansiEnd = "\u001b[0m"

        line1 = '0x' + hex(self.lastState['pc'])[2:].rjust(2, '0') + '    '
        line1 += str(operation.expandtabs(8))
        line1 = line1.ljust(80 - (self.bitLength+2), ' ')

        if 's0' in readList:
            line1 += "[" + readColour + str(bin(self.memory['s'][0])[2:].rjust(self.bitLength, '0')) + ansiEnd + "]"
        else:
            line1 += ''.ljust(self.bitLength+2, ' ')
        line1 += "\n"
        
        line2 = "   r"
        for i in range(len(self.lastState['r'])):
            line2 += "["
            if ('r'+str(i)) in readList:
                line2 += readColour
            line2 += str(bin(self.lastState['r'][i])[2:].rjust(self.bitLength, '0'))
            if ('r'+str(i)) in readList:
                line2 += ansiEnd
            line2 += ']'
        line2 += "\n"

        line3 = "   r"
        for i in range(len(self.memory['r'])):
            line3 += "["
            if ('r'+str(i)) in writeList:
                line3 += writeColour
            line3 += str(bin(self.memory['r'][i])[2:].rjust(self.bitLength, '0'))
            if ('r'+str(i)) in writeList:
                line3 += ansiEnd
            line3 += ']'
        line3 += ""

        print(line1 + line2 + line3)

    def lazyDecode(command):
        """parse a full assmbly string because calling operations directly with full syntax is tedious and error-prone, let the computer do the boring stuff"""
        pass

    def _inject(self):
        """injects an array of data into memory"""
        pass

    def _flush(self):
        """makes display go to next line"""
        pass

    def opNoop(self, lineNumber, text="no-op"):
        self._display(text, [], [])
        return 1

    def opLoad(self, lineNumber, operation, source, destination):
        self.memory['pc'] = lineNumber
        self._snapshot()
        self.memory['pc'] += 1
        operation = "load" + "\t" + str(source) + " -> " + str(destination)

        if type(source) is int:
            self.memory['s'] = [source]
            source = 's0'
        
        self.memory[destination[0]][int(destination[1:])] = self.memory[source[0]][int(source[1:])]

        self._display(operation,
                      [source],
                      [destination]
                      )
        return 1

    def opAnd (self, lineNumber, operation, source1, source2, destination):
        self.memory['pc'] = lineNumber
        self._snapshot()
        self.memory['pc'] += 1
        operation = "and" + "\t" + str(source1) + ', ' + str(source2) + " -> " + str(destination)

        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] & self.memory[source2[0]][int(source2[1:])]

        self._display(operation,
                      [source1, source2],
                      [destination]
                      )
        return self.memory[destination[0]][int(destination[1:])]

    def opShiftL(self, lineNumber, operation, source1, source2, destination):
        self.memory['pc'] = lineNumber
        self._snapshot()
        self.memory['pc'] += 1
        operation = "shiftL" + "\t" + str(source1) + ', ' + str(source2) + " -> " + str(destination)

        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] << self.memory[source2[0]][int(source2[1:])]

        self._display(operation,
                      [source1, source2],
                      [destination]
                      )
        return self.memory[destination[0]][int(destination[1:])]
        
    def opShiftR(self, lineNumber, operation, source1, source2, destination):
        self.memory['pc'] = lineNumber
        self._snapshot()
        self.memory['pc'] += 1
        operation = "shiftR" + "\t" + str(source1) + ', ' + str(source2) + " -> " + str(destination)

        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] >> self.memory[source2[0]][int(source2[1:])]

        self._display(operation,
                      [source1, source2],
                      [destination]
                      )
        return self.memory[destination[0]][int(destination[1:])]

    def opAdd(self, lineNumber, operation, source1, source2, destination):
        self.memory['pc'] = lineNumber
        self._snapshot()
        self.memory['pc'] += 1
        operation = "add" + "\t" + str(source1) + ', ' + str(source2) + " -> " + str(destination)

        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] + self.memory[source2[0]][int(source2[1:])]

        self._display(operation,
                      [source1, source2],
                      [destination]
                      )
        return self.memory[destination[0]][int(destination[1:])]

    def opJump(self, lineNumber, operation, pc):
        self.memory['pc'] = lineNumber
        self._snapshot()
        operation = "jump" + "\t" + str(pc) + " -> " + "pc"

        if type(pc) is int:
            self.memory['s'] = [pc]
            pc = 's0'
        self.memory['pc'] = lineNumber

        self._display(operation,
                      [],
                      []
                      )
        return 1

    def braEqual(self, lineNumber, operation, source1, source2, pc):
        self.memory['pc'] = lineNumber
        self._snapshot()
        operation = '==' + '\t' + str(source1) + ', ' + str(source2) + ' -> ' + str(pc)
        
        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        if self.memory[source1[0]][int(source1[1:])] == self.memory[source2[0]][int(source2[1:])]:
            self.memory['pc'] = pc
        else:
            self.memory['pc'] += 1
            
        self._display(operation,
                      [],
                      []
                      )
        return self.memory[source1[0]][int(source1[1:])] == self.memory[source2[0]][int(source2[1:])]

    def braNotEqual(self, lineNumber, operation, source1, source2, pc):
        self.memory['pc'] = lineNumber
        self._snapshot()
        operation = '!=' + '\t' + str(source1) + ', ' + str(source2) + ' -> ' + str(pc)
        
        if type(source1) is int:
            self.memory['s'] = [source1]
            source1 = 's0'

        if type(source2) is int:
            self.memory['s'] = [source2]
            source2 = 's0'

        if self.memory[source1[0]][int(source1[1:])] != self.memory[source2[0]][int(source2[1:])]:
            self.memory['pc'] = pc
        else:
            self.memory['pc'] += 1
            
        self._display(operation,
                      [],
                      []
                      )
        return self.memory[source1[0]][int(source1[1:])] != self.memory[source2[0]][int(source2[1:])]

    def halt(self, lineNumber, operation):
        self.memory['pc'] = lineNumber
        self._snapshot()
        operation = 'halt'
        
        self._display(operation,
                      [],
                      []
                      )
        return 0
        
def multiply1(a, b, bitlength=8):
    '''Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits
    https://en.wikipedia.org/wiki/Binary_multiplier#Basics
    '''
    assert a < 2**bitlength
    assert b < 2**bitlength

    ALU = DumbALU(8, 0, 4, 0, 0)

    r = [0 for i in range(4)]

    ALU.opNoop("init")

    ALU.opLoad(0, "load", a, 'r0')
    r[0] = a #needs to be double the bit size of the number inputs
    ALU.opLoad(1, "load", b, 'r1')
    r[1] = b
    ALU.opLoad(2, "load", 0, 'r3')
    r[3] = 0 #needs to be double the bit size of the number inputs

    #ALU.braEqual(3, '==', 'r1', 0, 11) #ommitted for clearity        
    while(r[1] != 0):
        ALU.braEqual(3, '==', 'r1', 0, 11)

        ALU.opAnd(4, 'and', 'r1', 1, 'r2')
        r[2] = r[1] & 1
        
        ALU.braNotEqual(5, '!=', 'r2', 1, 8)
        if r[2] == 1:
            ALU.opAdd(6, 'add', 'r0', 'r3', 'r3')
            r[3] = r[0] + r[3]
        ALU.opShiftL(8, 'shiftL', 'r0', 1, 'r0')
        r[0] = r[0] << 1
        ALU.opShiftR(9, 'shiftR', 'r1', 1, 'r1')
        r[1] = r[1] >> 1
        ALU.opJump(10, 'jump', 3)
    ALU.halt(11, 'halt')

    z = r[3]
    
    assert z == a * b #sanity check
    return z

if __name__ == "__main__":
    print(multiply1(3,4))
