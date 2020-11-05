"""
By: Medic5700
An implementation of an CPU simulator to allow a better and standardized way to illistrate bitwise instructions in lowlevel algorithms.
This project is geared towards demonstrating algorithms, and therefor generalizes a lot of stuff. IE: bitLength is settable, instruction words are one memroy element big, etc

IE: I needed something for a super dumb/special use case of demonstrating how a low level operation/algorithm works (memory error correction)
    without using a weird workaround (having a seperate 8-bit memory and 1-bit parity array vs creating a cpu with 9-bit memory)
    in a reliable and extensable way (making a cpu simulator that can be used for multiple algorithms)
"""

import sys
version = sys.version_info
assert version[0] == 3 and version[1] >= 8 #asserts python version 3.8 or greater

class CPUsimulatorV2:
    """A an implimentation of a generic and abstract ALU mainly geared towards illistrating algorithms

    Issues:
    should allow for adding arbitrary amount of arbitrary sized registers
        -> registers that are not bitLength sized should be able to be added with a method instead of with the constructor.

    references:
        https://en.wikipedia.org/wiki/Very_long_instruction_word
        https://en.wikipedia.org/wiki/Explicitly_parallel_instruction_computing
        https://en.wikipedia.org/wiki/IA-64
        Google(intel microarchitecture)
            https://www.servethehome.com/intel-xeon-scalable-processor-family-microarchitecture-overview/
        https://cs.lmu.edu/~ray/notes/gasexamples/
        https://en.wikibooks.org/wiki/X86_Assembly/GAS_Syntax
        https://en.wikipedia.org/wiki/GNU_Assembler
        https://github.com/vmmc2/Vulcan     #a "RISC-V Instruction Set Simulator Built For Education"
        https://www.youtube.com/watch?v=QKdiZSfwg-g     #Lecture 3. ISA Tradeoffs - Carnegie Mellon - Computer Architecture 2015 - Onur Mutlu
        https://www.anandtech.com/show/16195/a-broadwell-retrospective-review-in-2020-is-edram-still-worth-it #memroy latency of different cache levels

    Issues:
        Instruction functions return display highlight stuff, should be handled auto-magically by register arrays with a custom list class.
        Instruction functions should give warnings when input/output bitlengths aren't compatible. IE: multiplying 2 8-bit numbers together should be stored in a 16-bit register

    Out of scope:
        caching
        multi-threading
        memory controler/address translation
        instruction scedualer
        register file
        CPU interupts
            syscalls
        CPU power states/sleep
            device drivers/interactions
        CISC recursion to simulate a context switch
        execution unit instruction queueing
        enforcment of hardware register limitations (IE: r0 is hardwared to be zero)
        importing instruction functions and instruction sets
            instruction function currying on instruction set assignment (IE: 'addInt' = curry(add, 8 bit), 'addDouble' = curry(add, 16 bit))
        parsing
            math operorators
            indentation
            escape characters
            allowing accessing individual bytes in a register, IE: copy the lower 8 bits of a 64-bit register
        Reverse dirty bit for register file to impliment out of order super scaler execution
            IE: an instruction is run on dummy data at runtime to see what registers are accessed, and marked dirty.
            Allowing multiple instructions to be queeued up without implimenting a complex dependency graph (a short cut)
        _baked
            allow instructions to override instruction annotations during runtime execution
            IE: an instruction uses a variable amount of energy dependent on the data processed. It can report the energy used during its execution
    """

    def __init__(self, bitLength=16, memoryAmount=0, registerAmount=1):
        #import time
        #self.sleep = time.sleep #avoids having to reimport time module in _display function every time it's called
        import copy
        self.deepCopy = copy.deepcopy #required because state['flags'] contains a dictionary which needs to be copied
        
        self.bitLength : int = bitLength #the length of the registers in bits
        self.state = {}
        self.state['m'] : list[int] = [0 for i in range(memoryAmount)] #standard memory
        self.state['r'] : list[int] = [0 for i in range(registerAmount)] #standard registers
        self.state['i'] : list[int] = [] #holds immidiate values, IE: litteral numbers stored in the instruction, EX: with "add 1,r0->r1", the '1' is stored in the instruction
        self.state['pc'] : list[int] = [0] #program counter, it's a list because the parser will auto-convert references to 'pc' to 'pc[0]'
        self.state['flag'] : dict = {'carry': 0,
                                     'overflow': 0
                                     }
        self.state['instruction'] : list[str] = [None for i in range(memoryAmount)] #stores the instructions
        '''instruction words are assumed to be one memory unit big for simplicity
        can impliment a data execution protection using this info
        does not allow for dynamically altering/generating instructions, which is beyond the scope of this project (though if I can find a generic way to do it, I probably will)
        '''
        #self.state['currentInstruction'] = "" #FUTURE
        
        #self.state['sp'] = [0] #stack pointer #FUTURE
        #self.state['stack'] = [None for i in range(memoryAmount)] #stores stack data #FUTURE
        #'''the entire state information for registers, program pointers, etc, is stored as one memory unit for simplicity'''

        self.config = {}
        self.config['m'] : int = bitLength
        self.config['r'] : int = bitLength
        self.config['i'] : int = bitLength
        
        self.lastState = None

        self.animationDelay = 0.5

        #self.stats = {} #FUTURE used to keep track of CPU counters, like instruction executed, energy used, etc

        #FUTURE the instructions table should be able to be overloaded (IE: add could have an array of funtions) where one is chosen (based on bitlength, etc) to be included 
        instructionSetTest = {'add'     : self._testAdd,
                              'and'     : self._testAnd,
                              'nop'     : self._testNop,
                              '.int'    : self._directiveInt
                              }
        self.instructionSet = instructionSetTest #used by the decoder to parse instructions

        self._refresh()

    def addRegister(self, bitlength : int, amount : int, name : str):
        #TODO allow flags to be added
        assert type(name) is str
        assert name not in self.state.keys()
        
        self.state[name] = [0 for i in range(amount)]
        self.config[name] = bitlength
        self._refresh()

    def inject(self, target : str, value : int):
        assert type(value) is int
        #TODO handle negative value
        t1, t2 = self._translateArgument(target)
        self.state[t1][t2] = value & (2**self.config[t1]-1)

    def extract(self, target : str) -> int:
        t1, t2 = self._translateArgument(target)
        return self.state[t1][t2]

    def decode(self, code: str): #TODO MVP
        """takes in a string of assembly instructions, and compiles/loads it into memory"""
        pass

    def run(self, cycleLimit=None): #TODO MVP
        """starts execution of instructions"""
        pass

    def Parse:
        class Node:
            def __init__(self, typeStr: str, content: str):
                self.type : str = typeStr
                self.content : str = content
                self.child : list = []
                self.parent : Node = None

            def addChild(self, node : "Node"):
                self.child.append(node)
    def _display(self): #TODO MVP
        for i in range(len(self.state['r'])):
            print('r' + str(i) + '\t' + '=\t[' + str(self.state['r'][i]) + ']')

    #=====================================================================================================================
            
            def __repr__(self, depth=0):
                block = ""
                line = ""
                for i in range(depth):
                    line += " "
                line += str(self.content)
                line.ljust(40, " ")
                line += ":" + str(self.type) + "\n"

                childLines = [i.__repr__(depth+1) for i in self.child]
                block += line
                for i in childLines:
                    block += i

                return block
                
        def parse(line : str) -> Node:
            '''
            https://tomassetti.me/parsing-in-python/
            '''
            '''assembles the tree as it goes

            starts with a root node, "line"
            currentnode = root

            goes through character by charcter
                if word:
                    create node
                    currentnode.child = node
                    currentnode = node
                if bracket:
                    create node
                    currentnode.child = node
                    currentnode = node
                if ',':
                    currentnode = currentnode.parent
                if operator +-*/:
                    create node for operator
                    node.child = currentnode
                    currentnode.replace(node)
            '''
            '''#test use cases, but strictly focusing on token parsing without the application of rules
            test(2,3,4), test(2 + 5, 3)

            test    <keyword>
            (   <function>
                2   <number>
                ,   <seperator>
                3   <number>
                ,   <seperator>
                4   <number>
            test    <keyword>
            (   <function>
                2   <number>
                +   <operator>
                5   <number>
                ,   <seperator>
                3   <number>

            test(r[5], r10), test(r6, r[5 + 3])

            test    <keyword>
            (   <function>
                r   <keyword>
                [   <index>
                    5   <number>
                ,   <seperator>
                r10 <keyword>
            test    <keyword>
            (   <function>
                r6  <keyword>
                ,   <seperator>
                r   <keyword>
                [   <index>
                    5   <number>
                    +   <operator>
                    3   <number>

            test(r[1][3])

            test    <keyword>
            (       <function>
                r   <keyword>
                [   <index>
                    1   <number>
                [   <index>
                    2   <number>
            '''
            

        pass
        
    #=================================================================================================================

    def lazy(self, code : str): #TODO MVP
        """decodes and executes a single instruction line"""
        pass
        
    def _integrityCheck(self): #TODO
        """checks the integridy of all current registers, memory, etc"""
        pass

    def _refresh(self):
        """resets all required registers and flags between instructions, copies current state into lastState

        note: can be omited in some cases, such as micro-code that sets flags for the calling procedure"""

        #self._integrityCheck()

        self.lastState = self.deepCopy(self.state) #required deepCopy because state['flags'] contains a dictionary which needs to be copied
        
        for i in self.state['flag'].keys(): #resets all flags
            self.state['flag'][i] = 0
        self.state['i'] = []

    def _translateArgument(self, arg : str) -> 'tuple[str, int]':
        #FUTURE may have to take pointers of form m*r[0] IE: number in r0 points to memory index
        
        import re #TODO move this

        key : str = None
        index : 'int xor str' = None

        word = arg.strip().lower()

        #matches if the arg IS a key
        if arg in self.state.keys():
            key = arg
            index = 0
        #matches a postive or negative integer
        elif re.match("^[-]{0,1}[\d]*$", arg) != None:
            key = 'i'
            self.state['i'].append(int(arg))
            index = len(self.state['i']) - 1
        #matchs an integer in hex notation
        elif re.match("^0x[0-9a-fA-F]*$", arg) != None:
            key = 'i'
            self.state['i'].append(int(arg, 16))
            index = len(self.state['i']) - 1
        #matches a register index of form 'r0', 'r25', etc
        if key == None: #this skips maching if key index was already found
            for i in self.state.keys():
                if re.match("^" + str(i) + "[\d]*$", arg) != None:
                    key = i
                    temp = arg.replace(i, '')
                    index = int(temp)
                    break
        #matches a register index of form 'r[0]', 'r[25]', etc
        if key == None: #this skips maching if key index was already found
            for i in self.state.keys():
                if re.match("^" + str(i) + "\[[\d]*\]$", arg) != None:
                    key = i
                    temp = arg.replace(i, '')
                    temp = temp.replace('[', '')
                    temp = temp.replace(']', '')
                    index = int(temp)
                    break
        
        test = self.state[key][index] #test if key index pair is accessable

        return (key, index)

    def _testNop(self):
        self._refresh()
        
        self.state['pc'][0] = self.lastState['pc'][0] + 1

        return
    _testNop.type = 'test' #the instruction type, CISC, RISC, VLIW
    #_testNop.inputs = 0 #the number of acceptable input args
    #_testNop.outputs = 0 #the number of acceptable output args
    #_testNop.executionUnit = [] #the execution unit this instruction would be mapped to (IE: add, integer, multiply, floiting point, memory management, etc)
    #_testNop.energyCost = lambda x : 0
    #_testNop.propagationDelay = lambda x : 0
    _testNop.bitLengthOK = lambda x: True #a function that takes in a bitLength and returns True if the function can handle that bitlength (IE: a 64-bit floating point operation needs registers that are 64-bits)

    def _testAdd(self, a, b, c):
        #self._refresh()
        #argsParsed = self._parseArguments(args)
        a1, a2 = a
        b1, b2 = b
        c1, c2 = c

        self.state[c1][c2] = self.lastState[a1][a2] + self.lastState[b1][b2]
        if self.state[c1][c2] >= 2**self.config[c1]:
            self.state['flag']['carry'] = 1
            
        self.state[c1][c2] = self.state[c1][c2] & (2**self.config[c1] - 1)

        self.state['pc'][0] = self.lastState['pc'][0] + 1

        return
    # https://www.servethehome.com/intel-xeon-scalable-processor-family-microarchitecture-overview/
    _testAdd.type = 'test' #the instruction type, CISC, RISC, VLIW
    #_testAdd.inputs = 2 #the number of acceptable input args
    #_testAdd.executionUnit = ['integer'] #the execution unit this instruction would be mapped to (IE: add, integer, multiply, floiting point, memory management, etc)
    #_testAdd.energyCost = lambda x : x #IE: the bitlength multiplied by how complex the operation is
    #_testAdd.propagationDelay = lambda x : x #IE: the distance a bit change can propograte
    _testAdd.bitLengthOK = lambda x : x > 0 #a function that takes in a bitLength and returns True if the function can handle that bitlength (IE: a 64-bit floating point operation needs registers that are 64-bits)

    def _testAnd(self, a : 'tuple[str, int]', b : 'tuple[str, int]', c : 'tuple[str, int]') -> 'tuple[list, list]':  #a different instruction with a different backend, to test out different styles
        #self._refresh() is done by the calling function
        #self._parseArguments(args) is done by the calling function, the arguments for this function are tuples

        #arguments are (str, int) pairs, representing the memory type and index
        a1, a2 = a
        b1, b2 = b
        c1, c2 = c

        #a check that the registers that are being accessed are of a compatible bitlength
        assert self.config[a1] > 0
        assert self.config[b1] > 0
        assert self.config[c1] > 0

        self.state[c1][c2] = self.lastState[a1][a2] & self.lastState[b1][b2] #performs the bitwise and operation

        self.state[c1][c2] = self.state[c1][c2] & (2**self.config[c1] - 1) #'cuts down' the result to something that fits in the register/memory location

        self.state['pc'][0] = self.lastState['pc'][0] + 1 #incriments the program counter

        return
    _testAnd.type : str = 'test' #what type of function/instruction is it ('test', 'risc', 'cisc', 'directive')
    #_testAnd.executionUnit : 'list[str]' = ['logic'] #what execution unit this instruction corrisponds to ('integer, multiply, floiting point, memory management')
    #_testAnd.energyCost = lambda x : 1
    #_testAnd.propagationDelay = lambda x : 1
    _testAnd.bitLengthOK = lambda x : x > 0 #a function that takes in a bitLength and returns True if the function can handle that bitlength, used at modual initialization (IE: a 64-bit floating point operation needs registers that are 64-bits)
    #function should perform own check on inputs and output registers to determin if individual registers are compatible with the operation at run time
    
    def _directiveInt(self, *args): #(self, memory pointer, value)
        pass
    _directiveInt.type = 'directive'
    #_directiveInt.inputs = 2
    #_directiveInt.outputs = 0
    _directiveInt.bitLengthOK = lambda x : x > 0

class DumbALUv1:
    """A prototype implimentation of an ALU for illistratuve purposes

    issues:
    reading and writing to 'pc' program counter is clunky at best, confusing at worst
    program counter and ALU flags should only be shown when actually needed
    this was trying to serve two distinct use cases:
        illistrate one line operations along side python code, with python handling the logic and the ALU illistrating the binary operations
        a fully functional generic ALU able to interprite assembly, along with all the logic and control functions
        -> recommend making two different decoders to handle both use cases
    accessing memory registers while implementing opcodes is downright source code soup. recommend implementing helper function to parse arguments. IE:
        self.memory[destination[0]][int(destination[1:])] = self.memory[source1[0]][int(source1[1:])] & self.memory[source2[0]][int(source2[1:])]
    unable to cleanly handle registar names longer then 1 char (IE: 'r2' is easy to parse because you use the first char, 'pc' is hard because you can't look at only the first char)
    |what ALU flags are really needed in this kind of generic processor?
    |    -> carry flag, overflow?
    |    -> flags should be accessable just like any other register to allow for more direct access for stuff like conditional jumps without obtuse architecture specific flag commands and what not
    register binary display allignment should be right justified instead of left justified for easier reading/understandability
    instructions are stored seperatly from data, there are arguments both for and agenst attempting to throw that into ALU memory
        -> recomend the option of storing them seperatly/together at instantiation, seperatly by default and if using the lazyDecoder, together allowed if loading a full assembly program
    how to display ALU memory, and the changes made to it.
        Should everything be shown, at the expense of not being able to clearly show 'before and after' memory values?
        Should only read and written memory values be show, at the expense of showing almost no memory values at all
        Should only a relavent 'page' of memroy be shown at a time?
    what system calls are relavent? and how to implement them in a way that is human readable?
        IE: 'syscall r1,r2' vs 'syscall r1, print'
    how exactly should instruction values be handled? Storing a single value per instruction in a special 'static' register has a number of holes
        IE: "add 5,2->r1" the current ALU would not be able to support this use case, but this is also technically a use case to be avoided in assembly if not outright forbidden by the archtecture
        -> maybe make a seperate display line for what the instruction would might be, and have the value be taken from there?
    should direct access to ALU registers be allowed from calling program be allowed?
        IE: shifting a register left, but manually accessing it to trunk it
        -> needed as it makes loading initial values, and extracting results far easier then relying on a madeup syscall to try and do the same thing but more complicated
    no failsafes to check for memory integraty. IE: assert all values in registers are actually small enough to fit in the registers of a give bitlength size.
    should an arbitrary sized register be allowed?
        IE: taking in a 128-bit floating point value to be parsed/deconstructed so it's components can be moved into seperate small sized registers
        -> yes
    the bitlength of each memory type (registers, memory) should be stored in a way to enable algorithmically accessing it. neccissary for some operations (like rotate)
        IE: registerBitLength = self.memorySize['r']
    -> implement proper debugging/logging
    should a program stack be implimented?
    -> operation 'load' should be replaced with 'move'
    -> should have a displayConfigure function to configure what lines the display displays
    Should microcode be implimented? How exactly?
        microcode could run with a completly seperate set of registers or the register state would be saved and wiped so the microcode could use the same registers with the same architecture (IE: context switch)
            doesn't work since some operations require register value persistance or require reading/writing data to memory
        real (intel) cpus use 'register renaming' to map inputs and outputs to real registers before and after execution
        will have to take some sort of hybrid approch
        Could use a recursive instance of dumbALU to run the microcode, and inject/extract only the input/output values
            will not work since memory needs to be persistant
                could pass memory reference to dumbALU instance, allowing it to alter memory?
        UseCase1: multiply r1, r2 using shift add, store in r0
        UseCase2: miltiply r1, r2 using shift add, store in m0
        UseCase3: Add m0 through m255, store in r0
    Per thread incryption? IE: encrypting memory accesses? Would that actually matter since this is only a single thread?
    Should the different memory/registers have builtin counters (which would necessitate coding custom array types) for every read/write?
        -> Feature Creep, Hell No for the right now
    """
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
        print(self.memory)

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

        column1 = '    ' + 'PC  '
        column2 = '['
        if 'pc' in readList:
            column2 += readColour
        column2 += '0x' + hex(self.lastState['pc'])[2:].rjust(2, '0')
        if 'pc' in readList:
            column2 += ansiEnd
        column2 += ']'

        column3 = '['
        if 'pc' in writeList:
            column3 += writeColour
        column3 += '0x' + hex(self.memory['pc'])[2:].rjust(2, '0')
        if 'pc' in writeList:
            column3 += ansiEnd
        column3 += ']'

        statusLine = column1 + column2.ljust(self.bitLength*2+2, ' ') + '    ' + column3
        

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
        screen += '\n' + statusLine
        for i in registers:
            screen += '\n' + i

        self.sleep(self.animationDelay)
        print(screen)
    
    def _display_old(self, operation, readList, writeList):
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

    def lazyDecode(self, command):
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
        return self.memory[destination[0]][int(destination[1:])]

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
        self.memory['pc'] = self.memory['s'][0]

        self._display(operation,
                      [],
                      ['pc']
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
                      ['pc' if (self.memory[source1[0]][int(source1[1:])] == self.memory[source2[0]][int(source2[1:])]) else None]
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
                      ['pc' if (self.memory[source1[0]][int(source1[1:])] != self.memory[source2[0]][int(source2[1:])]) else None]
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
    """Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits
    https://en.wikipedia.org/wiki/Binary_multiplier#Basics
    """
    '''The inital prototype attempt that works'''
    assert a < 2**bitlength
    assert b < 2**bitlength

    ALU = DumbALUv1(8, 0, 4, 0, 0)

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

def multiply2(a, b, bitlength=8):
    """Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits
    """
    '''another non-functional mockup to show how dumbALU could be used, but a couple iterations of design later'''
    assert 0 <= a < 2**bitlength
    assert 0 <= b < 2**bitlength

    ALU = CPUsimulatorV2(bitlength, 2, 0) #bitlength, register amount, memory amount
    ALU.addRegister(bitlength * 2, 2, 't') #bitlength, register amount, namespace symbol

    t = [0 for j in range(2)]
    r = [0 for i in range(2)]

    ALU.decode('''
                        nop
                loop:   jumpEQ  (r[0], 0, end)
                            and     (r[0], 1, r[1])
                            jumpNEQ (r[1], 1, zero)
                                add     (t[0], t[1], t[1])
                zero:       shiftL  (t[0], 1, t[0])
                            shiftR  (r[0], 1, r[0])
                            jump    (loop)
                end:    halt
                ''')
    ALU.inject('t[0]', a)
    ALU.inject('r[0]', b)
    ALU.run()
    resultALU = ALU.extract('t[1]')
    
    t[0] = a
    r[0] = b
    
    while(r[0] != 0):
        r[1] = r[0] & 1
        if r[1] == 1:
            t[1] = t[0] + t[1]
        t[0] = t[0] << 1
        r[0] = r[0] >> 1
        
    resultPython = t[1]

    #sanity check
    assert resultALU == a * b
    assert resultPython == a * b
    
    return resultALU

if __name__ == "__main__":
    #print(multiply1(3,4)) #old working prototype

    CPU = CPUsimulatorV2(8, 0, 2)
    CPU.inject('r[0]', 1) #pattern matches 'r0' changes it to 'r[0]', then parses it


    #testing/implementing
    CPU._display()
    #CPU.lazy('nop #test test test') #comments get ignored
    #CPU.lazy('copy(5, r[0])') #an actual instruction
    #CPU.lazy('copy(1, r[1]), copy(2, r[2])') #a VLIW, these execute at the same time, for now no checks are in place for conflicting instructions
    #CPU._display()
    #CPU.run()
