"""
By: Medic5700
An implementation of an CPU simulator to allow a better and standardized way to illistrate bitwise instructions in lowlevel algorithms.
This project is geared towards demonstrating algorithms, and therefor generalizes a lot of stuff. IE: bitLength is settable, instruction words are one memroy element big, etc

IE: I needed something for a super dumb/special use case of demonstrating how a low level operation/algorithm works (memory error correction)
    without using a weird workaround (having a seperate 8-bit memory and 1-bit parity array vs creating a cpu with 9-bit memory)
    in a reliable and extensable way (making a cpu simulator that can be used for multiple algorithms)

Development Stack:
    Python 3.8 or greater
    A terminal that supports ANSI (IE: default Ubuntu Terminal or the "Windows Terminal" app for Windows)
"""

import sys
version = sys.version_info
assert version[0] == 3 and version[1] >= 8 #asserts python version 3.8 or greater

import copy #copy.deepcopy() required because state['flag'] contains a dictionary which needs to be copied
#import re #Regex, used in CPUsimualtorV2._translateArgument()

#debugging and logging stuff
import logging
import inspect
debugHighlight = lambda x : False #debugHighlight = lambda x : 322 <= x <= 565 #will highlight the debug lines between those number, or set to -1 to highlight nothing
def debugHelper(frame : "Frame Object") -> str:
    """Takes in a frame object, returns a string representing debug location info (IE: the line number and container name of the debug call)

    Usage -> logging.debug(debugHelper(inspect.currentframe()) + "String") -> DEBUG:root:<container>"remove"[0348]@line[0372] = String
    Used for easy debugging identification of a specific line
    No, you can't assign that code segment to a lambda function, because it will always return the location of the original lambda definition

    Reference:
        https://docs.python.org/3/library/inspect.html#types-and-members
    """
    assert inspect.isframe(frame)
    
    #textRed = "\u001b[31m" #forground red
    textTeal = "\u001b[96m" #forground teal
    ANSIend = "\u001b[0m" #resets ANSI colours

    line : str = ""

    if debugHighlight(frame.f_lineno):
        line += textTeal
   
    line += "<container>\"" + str(frame.f_code.co_name) + "\"" #the name of the encapuslating method that the frame was generated in
    line += "[" + str(frame.f_code.co_firstlineno).rjust(4, '0') + "]" #the line number of the encapsulating method that the frame was generated in
    line += "@line[" + str(frame.f_lineno).rjust(4, '0') + "]" #the line number when the frame was generate
    line += " = "

    if debugHighlight(frame.f_lineno):
        line += ANSIend

    return line

class CPUsim:
    """A implimentation of a generic and abstract ALU/CPU mainly geared towards illistrating algorithms
    """

    '''Random Design Notes:

    Issues/TODO:
        Instruction functions should give warnings when input/output bitlengths aren't compatible. IE: multiplying 2 8-bit numbers together should be stored in a 16-bit register
        Instruction functions should be in their own class, for better modularity
            Instruction functions should be more functional (IE: they take in as arguments/pointers self.state, self.oldstate, self.config, etc) so as to make coding for it easier
            How exacly should a 'halt' instruction be implimented? Should all instructions be given access to engine information?
        ProgramCounter should be semi-indipendant from instruction functions (unless explicidly modified by instruction functions)(IE: not an automatic += 1 after every instruction executed)
            This would allow for representation of variable length instructions in 'memory'
        Data to keep track of:
            engine:
                original source code
                current cycle number (not program counter)
                current transaction number (an array, for every instruction executed across multiple execution units)
                current instruction being executing (an array of instructions)
            stats:
                number of times a line is executed
                energy use per line
                cycles used for execution
        ? Instruction functions on execution should return a dictionary of info on function stats (IE: energy used, latency, instruction unit used, etc?)
            Makes instruction set composition easier (since lambda functions don't also need to copy a bunch of function properties)
            Makes instruction manipulation harder (IE: you can't know how long an instruction will take to execute ahead of time, or which execution unit it will use, or how to profile it)
        Parser:
            split line rule needs to be able to recurse, and take different characters to split with
            needs a rule to label containers as function arguments, array indices, other?
            Parser currently assumes all source code to process is perfect with no errors/typos, and thus is super fragile
            Parser 'rules' need more functionality for each function, to make it more modular
            All 'rules' need a documentation overhaul
            Impliment Parsing exception
            
    references/notes:
        https://en.wikipedia.org/wiki/Very_long_instruction_word
            the instruction word contains multiple instruction for each individual execution unit, so less reliance on the CPU figuring out how to out of order execution
            can result in a lot of NOPs as not every execution unit needs to be doing something at every point in the code
            relies heavily on the compiler
            more hardware dependent
        https://en.wikipedia.org/wiki/Explicitly_parallel_instruction_computing
            VLIW refined
        https://en.wikipedia.org/wiki/IA-64
            Intel's attempt at EPIC architecture
        Google(intel microarchitecture)
            https://www.servethehome.com/intel-xeon-scalable-processor-family-microarchitecture-overview/
        https://cs.lmu.edu/~ray/notes/gasexamples/  #Some stuff on GCC, with a lot of assembly examples
        https://en.wikibooks.org/wiki/X86_Assembly/GAS_Syntax
        https://en.wikipedia.org/wiki/GNU_Assembler
        https://github.com/vmmc2/Vulcan     #a "RISC-V Instruction Set Simulator Built For Education", web based
        https://www.youtube.com/watch?v=QKdiZSfwg-g     #Lecture 3. ISA Tradeoffs - Carnegie Mellon - Computer Architecture 2015 - Onur Mutlu
        https://www.anandtech.com/show/16195/a-broadwell-retrospective-review-in-2020-is-edram-still-worth-it #memroy latency of different cache levels
        https://www.youtube.com/watch?v=Q4aTB0k633Y&ab_channel=Level1Techs #Ryzen is Released - Rant/Rave with Tech Tech Potato (Dr. Ian Cutress
            four times the L3 cache (16MB to 64MB), eight extra clock cycle access time
            AMD 64-bit int division, 19-ish cycles (down from like 90-120 cyles years ago)

    Out of scope (for this itteration):
        caching
        multi-threading
        instruction schedualer
            execution unit instruction queueing
        register file
        CPU interupts
            syscalls
        CPU power states/sleep
            device drivers/interactions
        CISC recursion to simulate a context switch
        enforcment of hardware register limitations (IE: r0 is hardwared to be zero)
        importing instruction functions and instruction sets #need to get MVP working first
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
        Support for self-modifying code
        Custom register/memory objects (instead of simple arrays) for tracking access (reads/writes) + transational history + additional stats and stat tracking
            memory controler/address translation
            will need a simple address pointer lookup function to simulate a redirect at the instruction composting stage
                IE: add(m[r[0]], r[1], r[4]) needs to be allowed
            can merge self.lastState and self.state into single state?
        Memory aliasing into namespace (IE: letting R[0] be refered to by an alias 'z0' instead of 'r[0]')
        Microcode. The execution engine just isn't built out enough yet to consider this yet
            Microcode could run as a recursive CPU call, elimating the need for complex tracking of register windows, since it's run in a 'custom cpu construct' made for that instruction
            Microcode could be implimented at the instruction set composition level instead
                IE: add(a,b,c) used to make a vector add instruction (lambda a,b,c : add(a,b,c), add(a+1,b+1,c+1), add(a+2,b+2,c+2), etc)
                Only useful for simple instructions
        Instruction non-execution analysis utilities to better help calabrate instructions (IE: some utilities to help the user see energy use for each instruction in a graph before code is run)
    '''

    def __init__(self, bitLength : int = 16):
        
        self.bitLength : int = bitLength #the length of the registers in bits

        self.state : dict = {}
        self.lastState : dict = {}
        self.config : dict = {}
        self.stats : dict = {} #FUTURE used to keep track of CPU counters, like instruction executed, energy used, etc
        self.engine : dict = {} #FUTURE used to keep track of CPU engine information?, should it be merged with self.stats?

        '''a bunch of variables that are required for proper functioning, but are reqired to be configured by config functions
        defined here for a full listing of all these variables
        defined here in a failsafe state such that they can be used without crashing (or at least a lower likelyhood of crashing)
        may result in a more difficult time debugging
        '''
        #self.configSetDisplay
        self.userDisplay : __class__ = None
        self._displayRuntime : "function" = lambda : None
        self._displayPostRun : "function" = lambda : None
        #self.configSetInstructionSet
        self.userInstructionSet : __class__ = None
        self._instructionSet : dict = {}
        self._directives : dict = {}
        #self.configSetParser
        self.userPraser : __class__ = None
        self._parseCode : "function" = lambda x : None
        self._updateNameSpace : "function" = lambda x : None

        self._namespace : dict = {}

        #initialize CPU flag datastructure
        self.configAddRegister('flag', 0, 1) #done this way so any changes to the 'self.config' data structure is also added to 'flag', for consistancy reasons
        self.state['flag'] : dict = {} #overrides default array of numbers
        self.lastState['flag'] : dict = {}

        #adds special registers that are required
        self.configAddRegister('i', 0, bitLength) #holds immidiate values, IE: litteral numbers stored in the instruction, EX: with "add 2,r0->r1", the '2' is stored in the instruction
        self.configAddRegister('pc', 1, bitLength) #program counter, it's a list for better consistancy with the other registers
        
        #self.state['sp'] = [0] #stack pointer #FUTURE
        #self.state['stack'] = [None for i in range(memoryAmount)] #stores stack data #FUTURE
        #the entire state information for registers, program pointers, etc, should be stored as one memory unit for simplicity

        self.postCycleUser = self._postCycleUserDefault
        '''This is a user swappable function call executed after every execution cycle.        
        explicidly copies the self.state to self.lastState, resets CPU flags, etc
        '''

        #convinence added stuff for 'works out of the box' functionality
        self.configAddRegister('r', 8, bitLength) #standard registers
        self.configAddRegister('m', 32, bitLength) #standard memory

        self.configAddFlag('carry')
        self.configAddFlag('overflow')

        self.configSetDisplay(self.DisplaySimpleAndClean())
        self.configSetInstructionSet(self.InstructionSetDefault())
        self.configSetParser(self.ParseDefault({}))

        #engine stuff?
        #self._namespace : dict = self._computeNamespace()
        self.postCycleUser()
        self._postCycleEngine()

    def _computeNamespace(self):
        """computes the namespace of instructions, registers, etc for the CPU. Updates self._updateNameSpace : dict"""

        names = {}
        keys = self.state.keys()
        for i in keys:
            names[str(i)] = self.state[i]
        names.update(self._instructionSet)
        names.update(self._directives)
        self._namespace = names
        self._updateNameSpace(names)

    def configSetDisplay(self, displayInstance):
        """Takes in an display class

        class must have:
            runtime(lastState, state, config, stats, engine) - runs after every execution cycle
            postrun(lastState, state, config, stats, engine) - runs after the CPU halts

        Note: runtime() must be able to handle the 'i' register having a variying sized array, since it's size changes based on what the currect instruction needs
        """
        assert displayInstance.runtime
        assert displayInstance.postrun

        self.userDisplay : __class__ = displayInstance
        self._displayRuntime = lambda : displayInstance.runtime(self.lastState, self.state, self.config, self.stats, self.engine)
        self._displayPostRun = lambda : displayInstance.postrun(self.lastState, self.state, self.config, self.stats, self.engine)

    def configSetInstructionSet(self, instructionSetInstance):
        """Takes in a class representing the instruction set

        class must have:
            instructionSet : {str: function} - contains a dictionary of operation names with instruction functions
            directives : {str: function} - contains a dictionary of assembler directives with directive functions
        """
        assert type(instructionSetInstance.instructionSet) is dict
        assert type(instructionSetInstance.directives) is dict

        self.userInstructionSet : __class__ = instructionSetInstance
        self._instructionSet : dict = instructionSetInstance.instructionSet
        self._directives : dict = instructionSetInstance.directives

        self._computeNamespace()

    def configSetParser(self, parserInstance):
        """Takes in a class representing a source code parser

        class must have:
            parseCode(sourceCode : str) - a function that takes in a string, and returns an execution tree
            updateNameSpace(nameSpace : dict) - a function which takes in a nameSpace dictionary representing the CPUs registers, flags, instructions, etc
        """
        assert parserInstance.parseCode
        assert type(parserInstance.nameSpace) is dict
        assert parserInstance.updateNameSpace

        self.userParser = parserInstance
        self._parseCode = parserInstance.parseCode
        self._updateNameSpace = parserInstance.updateNameSpace

    def configAddRegister(self, name : str, amount : int, bitlength : int):
        """takes in the name of the register/memory symbol to add, the amount of that symbol to add (can be zero for an empty array), and bitlength. Adds and configures that memory to self.state"""
        assert type(name) is str
        assert type(bitlength) is int and bitlength > 0
        assert type(amount) is int and amount >= 0
        
        self.state[name.lower()] = [0 for i in range(amount)]
        self.lastState[name.lower()] = [0 for i in range(amount)]
        self.config[name.lower()] = {}

        self.config[name]['bitlength'] = bitlength

        self._computeNamespace()

    def configAddFlag(self, name : str):
        """Takes in a name for a CPU flag to add, Adds it to self.state"""
        assert type(name) is str
        assert 'flag' in self.state.keys()

        self.state['flag'][name.lower()] = 0
        self.lastState['flag'][name.lower()] = 0

        self._computeNamespace()

    def inject(self, key : str, index : "int/str", value : int):
        """Takes in a key index pair representing a specific register. Assigns int value to register.
        
        value >= 0
        Does not increment the simulatition
        Does run self._displayRuntime)_"""
        assert type(key) is str
        assert type(index) is int or type(index) is str
        assert type(value) is int
        assert value >= 0

        t1 = key.lower()
        t2 = index.lower() if key.lower() == "flag" else index

        self.state[t1][t2] = value & (2**self.config[t1]['bitlength']-1)

        self._displayRuntime()

        self._postCycleEngine()

    def extract(self, key : str, index : "int/str") -> int:
        """Takes in a key index pair representing a specific register. Returns an int representing the value stored in that register"""
        assert type(key) is str
        assert type(index) is int or type(index) is str

        t1 = key.lower()
        t2 = index.lower() if key.lower() == "flag" else index

        self._postCycleEngine()

        return self.state[t1][t2]

    def decode(self, code: str): #TODO MVP
        """NotImplimented
        takes in a string of assembly instructions, and compiles/loads it into memory"""
        pass

    def run(self, cycleLimit=None): #TODO MVP
        """NotImplimented
        starts execution of instructions"""
        pass

    #==================================================================================================================

    class DisplaySimpleAndClean:
        """A simple display example of the interface expected for displaying information on the screen during and post runtime
        
        Displays all registers, memory, and flags after every execution cycle. Displays some postrun stats.
        Uses ANSI for some colouring
        """

        def __init__(self, animationDelay : float = 0.5):
            assert type(animationDelay) is float or type(animationDelay) is int

            import time #this is imported for this specific class because this class is supposed to able to be 'swapped out' and may not be neccassary if another display class doesn't need the 'time' module
            self.sleep : "function" = time.sleep

            self.animationDelay : int = animationDelay

            self.textRed = "\u001b[31m" #forground red, meant for register writes
            self.textTeal = "\u001b[96m" #forground teal, meant for register reads
            self.ANSIend = "\u001b[0m" #resets ANSI colours

        def runtime(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None):
            """Executed after every instruction/cycle. Accesses/takes in all information about the engine, takes control of the screen to print information."""
            
            screen : str = ""
            highlight : str = ""

            lineOp : str = "0x" + hex(oldState['pc'][0])[2:].rjust(8, '0').upper() + "\t"
            lineOp += "Instruction #TODO" #TODO
            lineOp += "\n"

            lineRequired : str = ""

            #handles the 'pc' register
            highlight = self.textRed if (oldState['pc'][0] != newState['pc'][0]) else ""
            lineRequired += "\t" + "PC".ljust(8, ' ') \
                + "[" + "0x" + hex(oldState['pc'][0])[2:].rjust(8, '0').upper() + "]" \
                + "\t" \
                + "[" + highlight + "0x" + hex(newState['pc'][0])[2:].rjust(8, '0').upper() + self.ANSIend + "]" \
                + "\n"
            for i in range(len(oldState['i'])): #handles the immidiate registers
                lineRequired += "\t" + ("i[" + str(i) + "]\t").ljust(8, " ") \
                    + "[" + self.textTeal + str(bin(oldState["i"][i]))[2:].rjust(config["i"]['bitlength'], "0") + self.ANSIend + "]" \
                    + "\n"
            for i in oldState["flag"].keys(): #handles the CPU flags
                highlight = self.textRed if (oldState["flag"][i] != newState["flag"][i]) else ""
                lineRequired += "\t" + ("flag[" + str(i) + "]").ljust(16, " ") \
                    + "[" + str(oldState["flag"][i]) + "]" \
                    + "\t" \
                    + "[" + highlight + str(newState["flag"][i]) + self.ANSIend + "]" \
                    + "\n"

            lineRegisters : str = ""

            #get keys, but exclude the 'special' keys
            keys : "list[str]" = list(oldState.keys())
            if "flag" in keys:
                keys.remove("flag")
            if "pc" in keys:
                keys.remove("pc")
            if "i" in keys:
                keys.remove("i")

            for i in keys:
                for j in range(len(oldState[i])):
                    highlight = self.textRed if (oldState[i][j] != newState[i][j]) else ""
                    lineRegisters += "\t" + (str(i) + "[" + str(j) + "]").ljust(8, " ") \
                        + "[" + str(bin(oldState[i][j]))[2:].rjust(config[i]['bitlength'], "0") + "]" \
                        + "\t" \
                        + "[" + highlight + str(bin(newState[i][j]))[2:].rjust(config[i]['bitlength'], "0") + self.ANSIend + "]" \
                        + "\n"

            screen += lineOp
            screen += lineRequired
            screen += lineRegisters

            print(screen)
            self.sleep(self.animationDelay)

        def postrun(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None): #TODO
            """When CPU execution HALTS, displays information about execution stats, etc"""
            print("CPU Halted")

    class DisplaySilent:
        """An intentionally empty definition, that will display nothing to the screen"""

        def __init__(self):
            pass

        def runtime(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None):
            pass

        def postrun(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None):
            pass

    #==================================================================================================================

    class ParseDefault:
        """Parses strings into an (almost) execution tree.
        ParseDefault.Node is the dataclass for storing tokens in a Node Tree.

        ParseDefault.parseCode("source code") is called which returns a Node Tree representing the "source code"

            ParseDefault.parseCode() calls ParseDefault._tokenize() to do the initial tokenization of the "source code"
            root -> Node
                    |- Token "test"
                    |- Token " "
                    |- Token "123"
                    |- ...

            "rule functions" are called to apply various rules to the Node Tree
            all "rule functions" are functional, and return a COPY of Nodes
            Note: most do not recurse
            by combining "rule functions" in different ways in ParseDefault.parseCode(), different syntaxes can be proccessed
            root = self.ruleRemoveToken(root, " ")
            root -> Node
                    |- Token "test"
                    |- Token "123"
                    |- ...
            root = ruleCastInts(root)
            root -> Node
                    |- Token "test"
                    |- Token 123
                    |- ...

            return root
        """

        def __init__(self, nameSpace : dict = {}):
            assert type(nameSpace) is dict

            self.nameSpace : dict = nameSpace
            self.labels : dict = None

        def updateNameSpace(self, nameSpace : dict):
            """Takes in nameSpace a dictionary whose keys represent the CPU flags, registers, instructions, etc"""
            assert type(nameSpace) is dict

            self.nameSpace = nameSpace

        class Node:
            """A data class for storing information in a tree like structure. 

            Each Node also has a coupld relational links between children (nodeNext, nodePrevious, nodeParent)
            Note: __eq__() and __ne__() are implimented to make it easier for compairsions with Node.token and other values.
            """

            def __init__(self, typeStr : str = None, token : "str/int" = None, lineNum : int = None, charNum : int = None):
                assert type(typeStr) is str or typeStr == None
                assert type(lineNum) is int or lineNum == None
                assert type(charNum) is int or charNum == None

                self.type : str = typeStr
                self.token : str = token
                self.child : list = []

                #relational references to other nodes
                self.parent : "Node" = None
                self.nodePrevious : "Node" = None
                self.nodeNext : "Node" = None

                #the line number of the string or character position in a line, will be needed for indentation awareness if it's ever needed
                self.lineNum : int = lineNum 
                self.charNum : int = charNum

            def append(self, node : "Node"):
                """Adds a new node object to self as a child (at end of list)"""
                assert type(node) == self.__class__

                if len(self.child) != 0:
                    self.child[-1].nodeNext = node
                    node.nodePrevious = self.child[-1]
                if node.parent == None:
                    node.parent = self
                self.child.append(node)
            
            def copyInfo(self) -> "Node":
                """Creates a new node with the properties (but not relational data) of this node. returns the created node. 
                
                IE: returns a copy of the node with type, token, lineNum, charNum. Does not copy links to children, parent, nodeNext, nodePrevious, etc"""

                return self.__class__(self.type, self.token, self.lineNum, self.charNum) #TODO This feels wrong, but I don't know why it's wrong

            def copyDeep(self) -> "Node": #name is copyDeep instead of deepCopy to avoid accedentally calling copy.copyDeep()
                """Creates a new node with all properties of current node including recursivly copying all children (but not relational data). Returns a node tree."""
                
                newNode = self.__class__(self.type, self.token, self.lineNum, self.charNum)

                logging.debug(debugHelper(inspect.currentframe()) + "attempting to copyDeep node"+ "\n" + str((
                        self.type,
                        self.token,
                        self.lineNum,
                        self.charNum,
                        self.child)))

                for i in range(len(self.child)):
                    newNode.append(self.child[i].copyDeep())
                return newNode

            def replace(self, oldNode : "Node", newNode : "Node"):
                """Takes in an oldNode that is child of self, and replaces it with newNode. Deletes oldNode"""
                assert type(oldNode) == self.__class__
                assert type(newNode) == self.__class__

                index = None
                for i in range(len(self.child)):
                    if self.child[i] is oldNode:
                        index = i
                
                if index == None:
                    raise Exception

                removeNode = self.child[index]
                
                #'rewires' the references of the children nodes
                newNode.parent = self
                if len(self.child) == 1: #case where oldNode is the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "only child detected")
                    pass
                elif index == 0: #case where oldNode is first child in the list, but not the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "first child detected")

                    newNode.nodeNext = self.child[1]
                    self.child[1].nodePrevious = newNode
                elif index == len(self.child) - 1: #case where oldNode is the last child in the list, but not the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "last child detected")

                    newNode.nodePrevious = self.child[-1]
                    self.child[-1].nodeNext = newNode
                elif 0 < index < len(self.child) -1: #case where oldNode is between two other nodes
                    logging.debug(debugHelper(inspect.currentframe()) + "middle child detected")

                    newNode.nodePrevious = self.child[index - 1]
                    newNode.nodeNext = self.child[index + 1]

                    self.child[index - 1] = newNode
                    self.child[index + 1] = newNode

                self.child[index] = newNode

                #deletes oldNode
                removeNode.parent = None
                removeNode.nodeNext = None
                removeNode.nodePrevious = None

                for i in range(len(removeNode.child) - 1, -1, -1):
                    removeNode.remove(removeNode.child[i])

            def refreshLinks(self, recurse : bool = False):
                """NotImplimented
                Refreshes/remakes the links between children nodes. recurse = True to recursivly refreshLinks on entire node tree"""
                pass


            def remove(self, node : "Node"):
                """Takes in a node that is a child of self, removes node. raises exception if node is not a child
                
                deletes references to other nodes from Node, recursively removes child nodes of Node using remove()
                This is to make it easier to the python garbage collecter to destroy it, because cyclic references"""
                assert type(node) == self.__class__

                index : int = None
                for i in range(len(self.child)):
                    if self.child[i] is node:
                        index = i

                if index == None:
                    raise Exception

                removeNode : self.__class__ = self.child[index]

                logging.debug(debugHelper(inspect.currentframe()) + "attempting to remove node"+ "\n" + str((
                        self.type,
                        self.token,
                        self.lineNum,
                        self.charNum,
                        self.child)))

                #'rewires' the references of the children nodes to remove removeNode
                if len(self.child) == 1: #case where removeNode is the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "only child detected")
                    pass
                elif index == 0: #case where removeNode is first child in the list, but not the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "first child detected")
                    if type(removeNode.nodeNext) is self.__class__: #TODO figure out why this is neccissary to avoid a specific error.
                        removeNode.nodeNext.nodePrevious = None
                elif index == len(self.child) - 1: #case where removeNode is the last child in the list, but not the only child in the list
                    logging.debug(debugHelper(inspect.currentframe()) + "last child detected")
                    if type(removeNode.nodePrevious) is self.__class__:
                        removeNode.nodePrevious.nodeNext = None
                elif 0 < index < len(self.child) -1: #case where removeNode is between two other nodes
                    logging.debug(debugHelper(inspect.currentframe()) + "middle child detected")
                    if type(removeNode.nodePrevious) is self.__class__:
                        removeNode.nodePrevious.nodeNext = removeNode.nodeNext
                    if type(removeNode.nodeNext) is self.__class__:
                        removeNode.nodeNext.nodePrevious = removeNode.nodePrevious
                
                removeNode.parent = None
                removeNode.nodeNext = None
                removeNode.nodePrevious = None
                
                self.child.pop(index)
                
                for i in range(len(removeNode.child) - 1, -1, -1):
                    removeNode.remove(removeNode.child[i])

            def __repr__(self, depth : int = 0) -> str:
                """Recursivly composes a string representing the node hierarchy, returns a string.
                
                Called by print() to display the object"""

                block = ""
                line = ""
                for i in range(depth):
                    line += "    "
                line += repr(self.token)
                line = line.ljust(40, " ")
                line += ":" + str(self.type).capitalize().ljust(8)
                line += "\t" + str(depth)

                line += "\t" + "lineNum=" + str(self.lineNum) + "\t" + "charNum=" + str(self.charNum)

                line += "\n"

                childLines = [i.__repr__(depth+1) for i in self.child]
                block += line
                for i in childLines:
                    block += i

                return block
                
            def __eq__(self, other) -> bool:
                """A custom equals comparision. Takes in another object other, and compaires it to self.token. Returns True if equal, False otherwise"""
                logging.debug(debugHelper(inspect.currentframe()) + "Custom equals comparison")

                #return self.token == other
                if type(other) == self.__class__:
                    return self.token == other.token
                else:
                    return self.token == other

            def __ne__(self, other) -> bool:
                """A custom not equals comparision. Takes in another object other, and compaires it to self.token. Returns True if not equal, False otherwise"""
                logging.debug(debugHelper(inspect.currentframe()) + "Custom equals comparison")

                #return self.token != other
                if type(other) == self.__class__:
                    return self.token != other.token
                else:
                    return self.token != other

            #No longer needed since remove() cleans up enough recursivly for the python garbage collector to pick it up. This function might be useful for debugging purposes
            def __del__(self):
                """Decontructor, needed because the various inter-node references may make it harder for the python garbage collector to properly delete an entire tree
                
                will not touch pointers to this node from other nodes. IE: nodeNext's pointer to this node could be set to None, but that could get messy?"""
                
                logging.debug(debugHelper(inspect.currentframe()) + "Deleting Node" + "\n" + str((
                        self.type,
                        self.token,
                        self.lineNum,
                        self.charNum))
                        )
                
                self.parent = None
                self.nodeNext = None
                self.nodePrevious = None

                while len(self.child) != 0:
                    self.remove(self.child[0])

        def _tokenize(self, code : str) -> [(str, int, int), ... ] :
            """Takes in a string of code, returns a list of tuples representing the code in the form of (string/tuple, line location, character location in line). 
            
            No characters are filtered out"""
            assert type(code) is str

            #done like this to easily add extra characters
            _isName : "function" = lambda x : x.isalnum() or x in "_" #returns True is character can be in a name, False otherwise

            tokenList : list = []
            token : str = ""
            lineNum : int = 0
            characterNum : int = 0
            for j in code:
                if _isName(j): #creates tokens from everything that could be a variable name
                    token += j
                else: #everything else is a special character
                    if token != "":
                        tokenList.append((token, lineNum, characterNum))
                        token = ""
                    tokenList.append((j, lineNum, characterNum))

                #keeps track of line and positition numbers
                if j == "\n":
                    lineNum += 1
                    characterNum = 0
                else:
                    characterNum += 1
            if token != "": #adds last token
                tokenList.append((token, lineNum, characterNum))
                token = ""

            return tokenList

        def ruleCastInts(self, tree : Node) -> Node:
            """Takes in a node tree, casts all children that are integers to integers (with labels). Returns a node tree

            Does not recurse

            Case: "123 456 789" ->
            Node
                123
                ' '
                456
                ' '
                789
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if type(i.token) is str:
                    if i.token.isdigit():
                        temp = i.copyDeep()
                        temp.token = int(i.token)
                        temp.type = "int"
                        root.append(temp)
                    else:
                        root.append(i.copyDeep())
                else:
                    root.append(i.copyDeep())

            return root

        def ruleCastHex(self, tree : Node) -> Node:
            """Takes in a node tree, casts all children that are in hex format to integers (with labels). Returns a node tree

            Does not recurse

            Case: "0x0 0x000A 0xff" ->
            node
                0
                ' '
                10
                ' '
                255
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if type(i.token) == str:
                    if i.token.startswith("0x") or i.token.startswith("0X"):
                        temp = i.copyDeep()
                        temp.token = int(i.token, 16)
                        temp.type = "int"
                        root.append(temp)
                    else:
                        root.append(i.copyDeep())
                else:
                    root.append(i.copyDeep())

            return root

        def ruleRemoveEmptyLines(self, tree : Node) -> Node:
            """Takes in a node tree, removes all empty lines. Returns a node

            Does not recurse

            Case: "test\ntest\n\n\ntest\n" ->
            Node
                'test'
                '\n'
                'test'
                '\n'
                'test'
                '\n'
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()

            stack = "\n"

            for i in tree.child:
                #if previous == "\n" and current == "\n" do nothing, else copy Node
                if i != "\n" or stack != "\n":
                    root.append(i.copyDeep())
                    stack = i.token

            return root

        def ruleRemoveLeadingWhitespace(self, tree : Node, whiteSpace : [str, ...] = [" ", "\t"]) -> Node:
            """Takes in a node, removes all white space tokens between a new line token and the next token. Returns a node
            
            does not recurse

            Case: "test test \ntest\n  \ttest\t\n     \n" -> "test test \ntest\ntest\t\n\n" ->
            Node
                'test'
                ' '
                'test'
                ' '
                '\n'
                'test'
                '\n'
                'test'
                '\t'
                '\n'
                '\n'
            """
            assert type(tree) is self.Node
            assert all([True if len(i) == 1 else False for i in whiteSpace])

            root : self.Node = tree.copyInfo()

            stack : str = "\n" #initialize to State 0
            if len(tree.child) != 0:
                if tree.child[0] == "\n":
                    stack = None #initialize to State 1

            ''' Finite State Machine
            State 0: at beginning of line
            State 1: after first token
            Edge: 0 -> 0: found whitespace, not copying
            Edge: 0 -> 1: found token, copying
            Edge: 1 -> 0: found newline
            Edge: 1 -> 1: did not find newline, copy token
            '''
            for i in tree.child:
                logging.debug(debugHelper(inspect.currentframe()) + repr(i.token))
                if stack != None: #State 0: at beginning of line
                    if i.token in whiteSpace: #Edge: 0 -> 0: found whitespace, not copying
                        logging.debug(debugHelper(inspect.currentframe()) + "\tEdge 0 -> 0")
                        pass
                    else: #Edge: 0 -> 1: found token, copying
                        logging.debug(debugHelper(inspect.currentframe()) + "\tEdge 0 -> 1")
                        root.append(i.copyDeep())
                        stack = None
                else: #State 1: after first token
                    if i == "\n": #Edge: 1 -> 0: found newline
                        logging.debug(debugHelper(inspect.currentframe()) + "\tEdge 1 -> 0")
                        stack = "\n"
                        root.append(i.copyDeep())
                    else: #Edge: 1 -> 1: did not find newline, copy token
                        logging.debug(debugHelper(inspect.currentframe()) + "\tEdge 1 -> 1")
                        root.append(i.copyDeep())

            return root

        def ruleStringSimple(self, tree : Node) -> Node:
            """Takes in a node, combines all the tokens that are contained by quote tokens into a string node. Returns a node
            #TODO allow for arbitrary definition of list of 'quote like characters'

            Does not recurse
            
            Case: "test 'test'" ->
            Node
                'test'
                ' '
                "test"

            Case: "\'test\n\\\'test\\\''\ntest" ->
            Node
                "test\n\\\'test\\\'"
                '\n'
                'test'

            Case: "\'test\n\'test\'\'\ntest" ->
            Node
                "test\n"
                "test"
                ""
                "\n"
                "test"

            Case: "test1\"abc\'123\'abc\"test2" ->
                "test1"
                "abc\'123\'abc"
                "test2"

            Case: "" ->
                None
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()
            string : str = ""

            stack : str = None
            lineNum : int = None
            charNum : int = None

            '''Finite State Machine
            State 0 #Looking for an opening quote
            State 1 #Looking for a closing quote
            Edge 0 -> 0 iff token != quote: append node to root
            Edge 0 -> 1 iff token == quote: setup looking for closing quote
            Edge 1 -> 1 iff token != quote: append string with token
            Edge 1 -> 0 iff token == quote: copy string to node, append to root
            '''
            for i in tree.child:
                if stack == None: #the 'looking for an opening quote' State 0
                    if i != "\"" and i != "\'": #Edge 0 -> 0
                        root.append(i.copyDeep())
                    if i == "\"" or i == "\'":
                        if i.nodePrevious != "\\": #Edge 0 -> 1
                            stack = i.token
                            lineNum = i.lineNum
                            charNum = i.charNum
                        elif i.nodePrevious == "\\": #Edge 0 -> 0
                            root.append(i.copyDeep())
                elif stack != None: #the 'in a quote' State 1
                    if i != stack: #Edge 1 -> 1
                        string += str(i.token)
                    if i == stack:
                        if i.nodePrevious != "\\": #Edge 1 -> 0
                            temp = self.Node("string", string, lineNum, charNum)
                            root.append(temp)

                            stack = None
                            lineNum = None
                            charNum = None
                            string = ""
                        elif i.nodePrevious == "\\": #Edge 1 -> 1
                            string += str(i.token)

            if stack != None: #TODO handle mis-matched quotes
                raise Exception

            return root

        def ruleFilterLineComments(self, tree : Node, character : str = "#") -> Node:
            """Takes in a node, removes any tokens between a "#" token and a new line token. Returns a Node Tree

            Does not recurse

            Case: "test #test\n #test\n\t\#test" -> "test \n \n\t\#test" ->
            Node
                'test'
                ' '
                '\n'
                ' '
                '\n'
                '\t'
                '\\
                '#'
                'test'
            
            Case: "test test \# test #abc abc abc \\n abc \n test test" ->
            Node
                'test'
                ' '
                'test'
                ' '
                '\\'
                '#'
                ' '
                'test'
                ' '
                '\n'
                ' '
                'test'
                ' '
                'test'
            """
            assert type(tree) is self.Node
            assert type(character) is str 
            assert len(character) == 1

            root : self.Node = tree.copyInfo()

            stack : str = None

            '''Finite State Machine
            State 0: Looking for comment begin
            State 1: Looking for comment end
            0 -> 0 iff token != # : append token to root
            0 -> 1 iff token == # : setup looking for \n
            1 -> 1 iff token != \n : do nothing
            1 -> 0 iff token == \n : append \n to root
            '''
            for i in tree.child:
                if stack == None:
                    if i != character:
                        root.append(i.copyDeep())
                    elif i == character:
                        if i.nodePrevious != "\\":
                            stack = character
                        elif i.nodePrevious == "\\":
                            root.append(i.copyDeep())
                elif stack != None:
                    if i != "\n":
                        pass
                    elif i == "\n":
                        if i.nodePrevious != "\\":
                            stack = None
                            root.append(i.copyDeep())
                        elif i.nodePrevious == "\\":
                            pass

            return root

        def _applyRuleFilterBlockComments(self, tree : Node, character : str = "#") -> Node:
            pass

        def ruleContainer(self, tree : Node, containers : dict = {"(":")", "[":"]", "{":"}"}, nodeType : str = "container") -> Node:
            """Takes in a Node Tree, finds containers "([{}])" and rearranges nodes to form a tree respecting the containers. Returns a node tree

            Containers are of the form {"opening bracket": "closing bracket", ...}
            Does not copy closing brackets
            Does not recurse
            #TODO raise error for mismatched brackets
            
            Case: "test[test(test)]" ->
            Node
                'test'
                '['
                    'test'
                    '('
                        'test'

            Case: "test[abc abc{123 123}{123 123}](abc)" ->
            Node
                'test'
                '['
                    'abc'
                    ' '
                    'abc'
                    '{'
                        '123'
                        ' '
                        '123'
                    '{'
                        '123'
                        ' '
                        '123'
                '('
                    'abc'
            """
            assert type(tree) is self.Node
            assert type(containers) is dict
            assert len(containers) >= 1
            assert all([True if type(i) is str else False for i in containers.keys()])
            assert all([True if type(containers[i]) is str else False for i in containers.keys()])
            assert all([True if len(i) == 1 else False for i in containers.keys()])
            assert all([True if len(containers[i]) == 1 else False for i in containers.keys()])
            assert all([True if containers[i] != i else False for i in containers.keys()]) #asserts that the 'matching bracket' isn't the same characters
            assert type(nodeType) is str

            root : self.Node = tree.copyInfo()
            stack : [(str, self.Node), ...] = []

            for i in tree.child:
                '''
                if openbracket
                    append to stack
                if closing bracket
                    pop from stack
                    append to root
                else
                    if len(stack) == 0
                        append to root
                    else
                        append to last element in stack
                '''
                if i.token in list(containers.keys()): #if open bracket
                    #append to stack
                    temp : self.Node = i.copyDeep()
                    temp.type = nodeType
                    stack.append((i.token, temp))
                elif len(stack) != 0:
                    if containers[stack[-1][0]] == i.token: #if closing bracket
                        temp : self.Node = stack.pop()[1] #pop from stack

                        if len(stack) != 0: #append to last element in stack, otherwise append to root
                            stack[-1][1].append(temp)
                        else:
                            root.append(temp)
                    else: #not container, append to last element in stack
                        stack[-1][1].append(i.copyDeep())
                else: #not container, append to last element in stack, otherwise append to root
                    if len(stack) == 0:
                        root.append(i.copyDeep())
                    else:
                        stack[-1][1].append(i.copyDeep())

            return root

        def ruleFindLabels(self, tree : Node, symbolTable : dict) -> (Node, dict):
            """Takes in a node, attempts to find a label (a token not in symbolTable) that is immidiatly followed by a ":", returns a Node Tree, and a dictionary of labels
            
            Does not recurse"""
            assert type(tree) is self.Node
            assert type(symbolTable) is dict

            root : self.Node = tree.copyInfo()
            previous : str = "\n"
            skipToken : bool = False

            labels : dict = {}

            for i in tree.child:
                if i.nodePrevious == previous and i.nodeNext == ":":
                    temp : self.Node = i.copyDeep()
                    temp.type = "label"
                    root.append(temp)

                    labels[i.token] = temp.copyInfo()

                    previous = i.token
                    skipToken = True
                elif skipToken == True:
                    skipToken = False
                else:
                    root.append(i.copyDeep())
                    previous = i.token

            return (root, labels)

        def ruleLabelNamespace(self, tree : Node, nameSpace : dict, tokenType : str = "namespace") -> Node:
            """Takes in a node tree, and a nameSpace. Labels all nodes that are in nameSpace as 'NameSpace'. Returns Node Tree
            
            Does not recurse
            #TODO find a better/less confusing name (conflicts with ruleFindLabels)?"""
            assert type(tree) is self.Node
            assert type(nameSpace) is dict
            assert type(tokenType) is str

            root : self.Node = tree.copyInfo()
            keys : [str, ...]= [i.lower() for i in nameSpace.keys()]

            for i in tree.child:
                if type(i.token) is str:
                    if i.token.lower() in keys:
                        temp = i.copyDeep()
                        temp.type = tokenType
                        root.append(temp)
                    else:
                        root.append(i.copyDeep())
                else:
                    root.append(i.copyDeep())

            return root
        
        def ruleRemoveToken(self, tree : Node, token : str) -> Node:
            """Takes in a Node Tree, and a token. Removes all instances of token in tree.child. Returns a Node Tree
            
            Does not recurse"""
            assert type(tree) is self.Node
            
            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if i != token:
                    root.append(i.copyDeep())

            return root
        
        def ruleSplitLines(self, tree : Node, tokenType : str = "line", splitChar : str = "\n") -> [Node]:
            """Takes in a node tree. Returns a list of Nodes, split by '\n'
            
            #TODO should be able to recurse
            """
            assert type(tree) is self.Node
            assert type(tokenType) is str
            assert type(splitChar) is str

            result : [self.Node, ...] = []
            current : self.Node = self.Node(tokenType, None, 0, 0)

            for i in tree.child:
                if i == splitChar:
                    result.append(current)
                    current = self.Node(tokenType, None, i.lineNum + 1, i.charNum)
                else:
                    current.append(i.copyDeep())

            if len(current.child) >= 1:
                result.append(current)

            return result

        def parseCode(self, sourceCode : str) -> Node:
            """Takes a string of code, returns a parsed instruction tree"""
            assert type(sourceCode) is str
            
            #tokenizes sourceCode, and turns it into a Node Tree
            root = self.Node("root")
            for i in self._tokenize(sourceCode):
                root.append(self.Node("token", i[0], i[1], i[2]))

            logging.debug(debugHelper(inspect.currentframe()) + "this is the original code: " + "\n" + repr(sourceCode))
            logging.debug(debugHelper(inspect.currentframe()) + "tokenized code: " + "\n" + str(root))

            #does operations on the Node Tree, but the depth of the Node Tree remains 2
            root = self.ruleStringSimple(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleStringSimple: " + "\n" + str(root))

            root = self.ruleFilterLineComments(root, "#")
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFilterLineComments: " + "\n" + str(root))

            root = self.ruleRemoveLeadingWhitespace(root, [" ", "\t"])
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveLeadingWhitespace: " + "\n" + str(root))

            root = self.ruleRemoveEmptyLines(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveEmptyLines: " + "\n" + str(root))

            root, self.labels = self.ruleFindLabels(root, self.nameSpace)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFindLabels: " + "\n" + str(root))

            root = self.ruleLabelNamespace(root, self.nameSpace)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLabelNamespace: " + "\n" + str(root))

            root = self.ruleRemoveToken(root, " ")
            root = self.ruleRemoveToken(root, "\t")
            root = self.ruleRemoveToken(root, ",") #TODO this needs to be replaced with a proper way to seperate arguments
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveToken: " + "\n" + str(root))

            root = self.ruleCastInts(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleCastInts: " + "\n" + str(root))

            root = self.ruleCastHex(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleCastHex: " + "\n" + str(root))

            #This is where the Node Tree is allowed to go to a depth > 2
            root = self.ruleContainer(root, {"(":")", "[":"]"})
            logging.debug(debugHelper(inspect.currentframe()) + "ruleContainer: " + "\n" + str(root))

            temp : list = self.ruleSplitLines(root)
            root = self.Node("root")
            for i in temp:
                root.append(i)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitLines: " + "\n" + str(root))

            return root

    #==================================================================================================================

    def lazy(self, code : str): #TODO MVP
        """NotImplimented
        decodes and executes a single instruction line"""
        pass

    def _postCycleUserDefault(self):
        """resets all required registers and flags between instructions, copies current state into lastState

        note: can be omited in some cases, such as micro-code that sets flags for the calling procedure"""

        self.lastState = copy.deepcopy(self.state) #required deepCopy because state['flags'] contains a dictionary which needs to be copied
        
        for i in self.state['flag'].keys(): #resets all flags
            self.state['flag'][i] = 0
        self.state['i'] = []

    def _postCycleEngine(self):
        """NotImplimented
        runs at the end of each execution cycle, meant to handle engine level stuff"""
        pass

    #==================================================================================================================
    '''
    def _testNop(self):
        
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
        #argsParsed = self._parseArguments(args)
        a1, a2 = a
        b1, b2 = b
        c1, c2 = c

        self.state[c1][c2] = self.lastState[a1][a2] + self.lastState[b1][b2]
        if self.state[c1][c2] >= 2**self.config[c1]['bitlength']:
            self.state['flag']['carry'] = 1
            
        self.state[c1][c2] = self.state[c1][c2] & (2**self.config[c1]['bitlength'] - 1)

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
        #self._parseArguments(args) is done by the calling function, the arguments for this function are tuples

        #arguments are (str, int) pairs, representing the memory type and index
        a1, a2 = a
        b1, b2 = b
        c1, c2 = c

        #a check that the registers that are being accessed are of a compatible bitlength
        assert self.config[a1]['bitlength'] > 0
        assert self.config[b1]['bitlength'] > 0
        assert self.config[c1]['bitlength'] > 0

        self.state[c1][c2] = self.lastState[a1][a2] & self.lastState[b1][b2] #performs the bitwise and operation

        self.state[c1][c2] = self.state[c1][c2] & (2**self.config[c1]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

        self.state['pc'][0] = self.lastState['pc'][0] + 1 #incriments the program counter

        return
    _testAnd.type : str = 'test' #what type of function/instruction is it ('test', 'risc', 'cisc', 'directive')
    #_testAnd.executionUnit : 'list[str]' = ['logic'] #what execution unit this instruction corrisponds to ('integer, multiply, floiting point, memory management')
    #_testAnd.energyCost = lambda x : 1
    #_testAnd.propagationDelay = lambda x : 1
    _testAnd.bitLengthOK = lambda x : x > 0 #a function that takes in a bitLength and returns True if the function can handle that bitlength, used at modual initialization 
        #(IE: a 64-bit floating point operation needs registers that are 64-bits)
    #function should perform own check on inputs and output registers to determin if individual registers are compatible with the operation at run time
    
    def _directiveInt(self, *args): #(self, memory pointer, value)
        pass
    _directiveInt.type = 'directive'
    #_directiveInt.inputs = 2
    #_directiveInt.outputs = 0
    _directiveInt.bitLengthOK = lambda x : x > 0
    '''

    class InstructionSetDefault:
        """A non-functional mockup of what an instructionset definition could look like"""

        def __init__(self):
            self.instructionSet : dict = {
                "nop"   : self.opNop,
                "add"   : self.opAdd,
                "and"   : self.opAnd,
                "jumpeq": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "==", pointer, a, b)),
                "jumpne": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "!=", pointer, a, b)),
                "jump"  : (lambda z1, z2, z3, z4,   pointer           : self.opJump(z1, z2, z3, z4,       "goto", pointer)),
                "shiftl": (lambda z1, z2, z3, z4,   a, b              : self.opShiftL(z1, z2, z3, z4,     a, b, 1)),
                "shiftr": (lambda z1, z2, z3, z4,   a, b              : self.opShiftR(z1, z2, z3, z4,     a, b, 1)),
                "halt"  : self.opHalt
            }

            self.stats : dict = {}

            self.directives : dict = {}

        def redirect(self, redirection : str, register : str, index : "str/int") -> (str, int):
            """Takes in redirection as a pointer to the memory array to access, and a register index pair. Returns a key index pair corrispoding to redirection as key, index as value stored in register[index]"""
            return (redirection, register[index])

        def opNop(self, oldState, newState, config, engine):
            newState['pc'][0] = oldState['pc'][0] + 1

        def opAdd(self, oldState, newState, config, engine, a, b, c):
            """adds registers a and b, stores result in c"""
            a1, a2 = a
            b1, b2 = b
            c1, c2 = c

            newState[c1][c2] = oldState[a1][a2] + oldState[b1][b2]
            if newState[c1][c2] >= 2**config[c1]['bitlength']:
                newState['flag']['carry'] = 1
            
            newState[c1][c2] = newState[c1][c2] & (2**config[c1]['bitlength'] - 1)

            newState['pc'][0] = oldState['pc'][0] + 1
            
        def opAnd(self, oldState, newState, config, engine, a, b, c):
            """performs operation AND between registers a and b, stores result in c"""
            a1, a2 = a
            b1, b2 = b
            c1, c2 = c

            newState[c1][c2] = oldState[a1][a2] & oldState[b1][b2] #performs the bitwise and operation

            newState[c1][c2] = newState[c1][c2] & (2**config[c1]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

            newState['pc'][0] = oldState['pc'][0] + 1 #incriments the program counter

        def opJump(self, oldState, newState, config, engine, mode : str, gotoIndex, a = None, b = None):
            """Conditional jump to gotoIndex, conditional on mode, and optional registers a and b

            mode:
                goto    - a simple jump without any condition testing, a and b must be set to None
                <       - less than
                <=      - less than or equal to
                >       - greater than
                >=      - greater than or equal to
                ==      - equal
                !=      - not equal
            """
            assert (mode == "goto" and a == None and b == None) ^ (mode != "goto" and a != None and b != None)

            if mode == "goto":
                newState['pc'][0] = gotoIndex
            else:
                a1, a2 = a
                b1, b2 = b

                if mode == "<" and oldState[a1][a2] < oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                elif mode == "<=" and oldState[a1][a2] <= oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                elif mode == ">" and oldState[a1][a2] > oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                elif mode == ">=" and oldState[a1][a2] >= oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                elif mode == "==" and oldState[a1][a2] == oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                elif mode == "!=" and oldState[a1][a2] != oldState[b1][b2]:
                    newState['pc'][0] = gotoIndex
                else:
                    newState['pc'][0] = oldState['pc'][0] + 1

        def opShiftL(self, oldState, newState, config, engine, a, b, c = 1):
            """Takes register a, shifts it left by c (key index pair, or int) bits. Stores result in b"""
            a1, a2 = a
            b1, b2 = b

            if type(c) is int:
                amount = c
            elif type(c) is tuple:
                amount = oldState[c[0]][c[1]]

            newState[b1][b2] = oldState[a1][a2] << amount

            newState[b1][b2] = newState[b1][b2] & (2**config[b1]['bitlength'] - 1)

            newState['pc'][0] = oldState['pc'][0] + 1

        def opShiftR(self, oldState, newState, config, engine, a, b, c = 1):
            """Takes register a, shifts it right by c (key index pair, or int) bits. Stores result in b
            
            #TODO handle a twos compliment left shift"""
            a1, a2 = a
            b1, b2 = b

            if type(c) is int:
                amount = c
            elif type(c) is tuple:
                amount = oldState[c[0]][c[1]]

            newState[b1][b2] = oldState[a1][a2] >> amount

            newState[b1][b2] = newState[b1][b2] & (2**config[b1]['bitlength'] - 1)

            newState['pc'][0] = oldState['pc'][0] + 1

        def opHalt(self, oldState, newState, config, engine):
            pass

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
    '''another non-functional mockup to show how CPUsimulatorV2 could be used, but a couple iterations of design later'''
    assert 0 <= a < 2**bitlength
    assert 0 <= b < 2**bitlength

    ALU = CPUsim(bitlength) #bitlength
    ALU.configAddRegister('r', 2, bitlength) #bitlength, register amount, namespace symbol #will overwrite defaults
    ALU.configAddRegister('m', 0, bitlength) #bitlength, register amount, namespace symbol #will overwrite defaults, in this case, erasing it
    ALU.configAddRegister('t', 2, bitlength * 2) #bitlength, register amount, namespace symbol

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
    ALU.inject('t', 0, a)
    ALU.inject('r', 0, b)
    ALU.run()
    resultALU = ALU.extract('t', 1)
    
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
    #set up debugging
    logging.basicConfig(level = logging.INFO)
    debugHighlight = lambda x : 750 <= x <= 800

    #print(multiply1(3,4)) #old working prototype
    
    #What works
    CPU = CPUsim(8)
    CPU.configSetDisplay(CPU.DisplaySimpleAndClean(0))
    print("".rjust(80, "="))

    CPU.configAddRegister('r', 2, 16)
    CPU.configAddRegister('m', 4, 8)
    CPU.configAddRegister('t', 2, 16)
    CPU.configAddFlag("random")
    CPU.inject('r', 1, 1)
    CPU.inject('m', 2, 8)
    CPU.inject('flag', 'carry', 1)
    print("".rjust(80, "="))

    root = CPU._parseCode('''
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
    print(root)
    print("".rjust(80, "="))

    ''' #testing/implementing
    #CPU.lazy('nop #test test test') #comments get ignored
    #CPU.lazy('copy(5, r[0])') #an actual instruction
    #CPU._display()
    #CPU.run()
    '''
