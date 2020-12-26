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
import functools #used for partial functions when executioning 'instruction operations'

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
        configSetInstructionSet() should autofill stats datastructer for any unfilled in data. (but should also show a warning)
        ProgramCounter should be semi-indipendant from instruction functions (unless explicidly modified by instruction functions)(IE: not an automatic += 1 after every instruction executed)
            This would allow for representation of variable length instructions in 'memory'
        Data to keep track of:
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
            Impliment Parsing exception
        System Calls
            HALT uses self.engine["run"] as a flag for running, or stopping the simulation... there has to be a better more generic way to handle system calls

        BUG #TODO: Compiler/Parser does not pick up on labels if it's in the first line/first instruction line of code?
            
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

    Out of scope (for this itteration): #it's sometimes helpful to know what not to do
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
        parsing
            math operorators
            indentation
            allowing accessing individual bytes in a register, IE: copy the lower 8 bits of a 64-bit register
        Reverse dirty bit for register file to impliment out of order super scaler execution
            IE: an instruction is run on dummy data at runtime to see what registers are accessed, and marked dirty.
            Allowing multiple instructions to be queeued up without implimenting a complex dependency graph (a short cut)
        ? allow instructions to override instruction annotations during runtime execution
            IE: an instruction uses a variable amount of energy dependent on the data processed. It can report the energy used during its execution
        Support for self-modifying code
        Custom register/memory objects (instead of simple arrays) for tracking access (reads/writes) + transational history + additional stats and stat tracking
            memory controler/address translation
            will need a simple address pointer lookup function to simulate a redirect at the instruction composting stage
                IE: add(m[r[0]], r[1], r[4]) needs to be allowed
            can merge self.lastState and self.state into single state?
        Microcode. The execution engine just isn't built out enough yet to consider this yet
            Microcode could run as a recursive CPU call, elimating the need for complex tracking of register windows, since it's run in a 'custom cpu construct' made for that instruction
            Microcode could be implimented at the instruction set composition level instead
                IE: add(a,b,c) used to make a vector add instruction (lambda a,b,c : add(a,b,c), add(a+1,b+1,c+1), add(a+2,b+2,c+2), etc)
                Only useful for simple instructions
        Instruction non-execution analysis utilities to better help calabrate instructions (IE: some utilities to help the user see energy use for each instruction in a graph before code is run)
    '''

    def __init__(self, bitLength : int = 16):
        assert type(bitLength) is int
        assert bitLength >= 1
        
        self.bitLength : int = bitLength #the length of the registers in bits

        '''core engine variables, used by a number of different functions, classes, etc. It's assumed that these variables always exist'''
        self.state : dict = {}
        self.lastState : dict = {}
        self.config : dict = {}
        self.stats : dict = {} #FUTURE used to keep track of CPU counters, like instruction executed, energy used, etc
        self.engine : dict = {} #FUTURE used to keep track of CPU engine information?, should it be merged with self.stats?

        self.engine["run"] = False 

        #TODO find a better structer for this
        self.engine["labels"] : "{str : int}" = None
        self.engine["instructionArray"] : ["Nodes", ...] = None
        self.engine["sourceCode"] : str = None
        self.engine["sourceCodeLineNumber"] : int = None #TODO this should be an array of ints, to represent multiple instructions being executed
        self.engine["cycle"] : int = 0

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
        self._updateNameSpace : "function" = lambda x, y : None #TODO change name to _parseUpdate()
        #self.configSetPostCycleFunction
        self.userPostCycle : "function" = lambda x : None
        #self.configAddAlias
        self._tokenAlias : dict = {}

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

        #convinence added stuff for 'works out of the box' functionality
        self.configAddRegister('r', 8, bitLength) #standard registers
        self.configAddRegister('m', 32, bitLength) #standard memory

        self.configAddFlag('carry')
        #self.configAddFlag('overflow')

        self.configSetDisplay(self.DisplaySimpleAndClean())
        self.configSetInstructionSet(self.InstructionSetDefault())
        self.configSetParser(self.ParseDefault({}))

        self.configSetPostCycleFunction(self._postCycleUserDefault)

        #engine stuff?
        self.userPostCycle()
        self._postCycleEngine()

    def _computeNamespace(self):
        """computes the namespace of instructions, registers, etc for the CPU. Updates self._updateNameSpace : dict"""

        names = {}
        keys = self.state.keys()
        for i in keys:
            names[str(i)] = self.state[i]
        names.update(self._instructionSet)
        names.update(self._directives)
        names.update(self._tokenAlias)
        self._namespace = names
        self._updateNameSpace(names, self._tokenAlias)

    def configAddAlias(self, token : str, replacement : str):
        self._tokenAlias[token] = replacement
        
        self._computeNamespace()

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

        self._computeNamespace()

    def configSetPostCycleFunction(self, postCycle : "function"):
        """Takes in a function that is executed after every execution cycle

        explicifly copies the self.state to self.lastState, resets CPU flags, etc
        Note: must take in self as an argument
        #TODO it doesn't seem right that the uninstantiated function needs to take in self... research required
        """
        self.userPostCycle = postCycle

    def configAddRegister(self, name : str, amount : int, bitlength : int):
        """takes in the name of the register/memory symbol to add, the amount of that symbol to add (can be zero for an empty array), and bitlength. Adds and configures that memory to self.state"""
        assert type(name) is str
        assert len(name) >= 1
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
        assert len(name) >= 1
        assert 'flag' in self.state.keys()

        self.state['flag'][name.lower()] = 0
        self.lastState['flag'][name.lower()] = 0

        self._computeNamespace()

    def inject(self, key : str, index : "int/str", value : int):
        """Takes in a key index pair representing a specific register. Assigns int value to register.
        
        value >= 0
        Does not increment the simulatition"""
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

    #==================================================================================================================

    class DisplaySimpleAndClean:
        """A simple display example of the interface expected for displaying information on the screen during and post runtime
        
        Displays all registers, memory, and flags after every execution cycle. Displays some postrun stats.
        Uses ANSI for some colouring
        """

        def __init__(self, animationDelay : float = 0.5):
            assert type(animationDelay) is float or type(animationDelay) is int
            assert animationDelay >= 0

            import time #this is imported for this specific class because this class is supposed to able to be 'swapped out' and may not be neccassary if another display class doesn't need the 'time' module
            self.sleep : "function" = time.sleep

            self.animationDelay : int = animationDelay

            self.textRed = "\u001b[31m" #forground red, meant for register writes
            self.textTeal = "\u001b[96m" #forground teal, meant for register reads
            self.textGrey = "\u001b[90m" #forground grey
            self.ANSIend = "\u001b[0m" #resets ANSI colours

        def runtime(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None):
            """Executed after every instruction/cycle. Accesses/takes in all information about the engine, takes control of the screen to print information."""
            
            screen : str = ""
            highlight : str = ""

            lineOp : str = "0x" + hex(oldState['pc'][0])[2:].rjust(8, '0').upper() + "\t"

            if engine["sourceCode"] != None and engine["sourceCodeLineNumber"] != None:
                sourceCode = engine["sourceCode"].split("\n")
                lineOp += "[line " + str(engine["sourceCodeLineNumber"]).rjust(4, "0") + "]" + "\t"
                lineOp += sourceCode[engine["sourceCodeLineNumber"]].lstrip()
            else:
                lineOp += "No Instruction Found" #TODO
            lineOp = lineOp.ljust(68, " ")
            lineOp += "[Cycle " + str(engine["cycle"]).rjust(4, "0") + "]"
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
                    highlight = ""

                    ''' #this highlights the registers containing instructions with grey, but doesn't make the display more readable... should be used for another display class
                    if engine["instructionArray"] != None and i == "m":
                        highlight = self.textGrey if not (engine["instructionArray"][j] is None) else ""
                    '''
                    highlight = self.textRed if (oldState[i][j] != newState[i][j]) else highlight

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
            self.alias : dict = {}
            self.labels : dict = None

        def updateNameSpace(self, nameSpace : dict, alias : dict):
            """Takes in nameSpace a dictionary whose keys represent the CPU flags, registers, instructions, etc"""
            assert type(nameSpace) is dict
            assert type(alias) is dict

            self.nameSpace = nameSpace
            self.alias = alias

        class Node:
            """A data class for storing information in a tree like structure. 

            Each Node also has a coupld relational links between children (nodeNext, nodePrevious, nodeParent)
            Note: __eq__() and __ne__() are implimented to make it easier for compairsions with Node.token and other values.
            """

            def __init__(self, typeStr : str = None, token : "str/int" = None, lineNum : int = None, charNum : int = None):
                assert type(typeStr) is str or typeStr == None
                #check for type(token) not done for better flexibility
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
                assert type(depth) is int
                assert depth >= 0

                block = ""
                line = ""
                for i in range(depth):
                    line += "    "
                line += repr(self.token)
                line = line.ljust(40, " ")
                line += "\t:" + str(self.type).capitalize().ljust(8)
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
            
            Does not recurse

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
            """Takes in a Node Tree, removes any tokens between a "#" token and a new line token. Returns a Node Tree.

            Does not recurse

            Case: "test #test\n #test\n\t\\#test" -> "test \n \n\t\\#test" ->
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
            
            Case: "test test \\# test #abc abc abc \\n abc \n test test" ->
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

        def ruleNestContainersIntoInstructions(self, tree : Node, nameSpace : dict, recurse : bool = True) -> Node:
            """Takes in a Node Tree, and a nameSpace dict represeting instructions, registers, etc. 
            If a container node follows a nameSpace node, make container node a child of the nameSpace node.
            Returns a Node Tree

            Recurses by default"""
            assert type(tree) is self.Node
            assert type(nameSpace) is dict
            
            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if i.type == "container":  
                    if recurse:
                        temp = self.ruleNestContainersIntoInstructions(i.copyDeep(), nameSpace, True)
                    else:
                        temp = i

                    if type(i.nodePrevious) is self.Node: #IE: the node exists
                        if i.nodePrevious.token in nameSpace:
                            root.child[-1].append(temp.copyDeep())
                        else:
                            root.append(temp.copyDeep())
                else:
                    root.append(i.copyDeep())

            return root

        def ruleLowerCase(self, tree : Node) -> Node:
            """Takes in a Node Tree. Sets all tokens in the Node Tree's children as lower case. Returns a Node Tree.

            Does not recurse"""
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()
            for i in tree.child:
                temp = i.copyDeep()
                if type(temp.token) is str:
                    temp.token = temp.token.lower()
                root.append(temp)
            return root

        def ruleApplyAlias(self, tree : Node, alias : dict) -> Node:
            pass

        def ruleFilterBlockComments(self, tree : Node, character : str = "#") -> Node:
            pass

        def ruleFindDirectives(self, tree : Node, directives : dict) -> Node:
            pass

        def parseCode(self, sourceCode : str) -> Node:
            """Takes a string of code, returns a parsed instruction tree
            
            Applies following rules to sourceCode, in order:
                tokenizes
                finds strings
                filter out line comments
                lowercase everything
                remove leading whitespace
                remove empty lines
                find labels and return
                find stuff in nameSpace, change node type to reflect it
                remove spaces
                remove tabs
                remove commas #TODO this should actually be a split line
                cast ints
                cast hex
                process containers ([{brackets}])

                set containers as children of previous token iff previous token is in namespace

                split lines
            """
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

            root = self.ruleLowerCase(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLowerCase: " + "\n" + str(root))

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

            #This is where the Node Tree is allowed to go to depth > 2
            root = self.ruleContainer(root, {"(":")", "[":"]"})
            logging.debug(debugHelper(inspect.currentframe()) + "ruleContainer: " + "\n" + str(root))

            root = self.ruleNestContainersIntoInstructions(root, self.nameSpace, True)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleNestContainersIntoInstructions: " + "\n" + str(root))

            temp : list = self.ruleSplitLines(root)
            root = self.Node("root")
            for i in temp:
                root.append(i)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitLines: " + "\n" + str(root))

            return root

    #==================================================================================================================

    def linkAndLoad(self, code: str):
        """Takes in a string of assembly instructions, and "compiles"/loads it into memory, 'm' registerrs
        
        sets:
            program counter to label __main, 0 if __main not present
            self.engine["instructionArray"] to contain instruction Nodes
            self.state["m"] to contain the memory of the program (but not instruction binary encodings)
            self.engine["labels"] to contain a dictionary of accossations of labels with memory pointers
        """
        assert type(code) is str

        self.engine["sourceCode"] : str = code
        parseTree : "Node" = self._parseCode(code)

        assemmbledObject = self.compileDefault(self._instructionSet, self._directives)
        t1, t2, t3 = assemmbledObject.compile(self.state, self.config, parseTree)
        #t1 is list of instruction nodes
        #t2 is an integer array of memory elements/registers
        #t3 is labels, a dictionary accossiating 'labels' to a specific memory addresses

        self.engine["instructionArray"] = t1

        #TODO program is imported into memory, this should be changeable
        for i in range(len(t2)): #loads program memory into memory one element at a time
            self.state["m"][i] = t2[i]
        
        self.engine["labels"] = t3

        #sets the program counter to the label __main, if the label __main exists
        if "__main" in self.engine["labels"]:
            self.state["pc"][0] = self.engine["labels"]["__main"]

    def run(self, cycleLimit = 64):
        """Prototype
        starts execution of instructions"""

        '''
            do a depth first search on the execution tree
            apply 'rule functions' based on what the token is
            recursivly evaluate
        '''
        self.engine["run"] = True
        self._displayRuntime()
        self.userPostCycle()
        self._postCycleEngine()

        i = 0
        while i < cycleLimit:
            i += 1
            if self.engine["run"] == False:
                break
            
            #logging.info(debugHelper(inspect.currentframe()) + str(i))
            line = self.engine["instructionArray"][self.state["pc"][0]]
            #logging.info(debugHelper(inspect.currentframe()) + "\n" + str(line))
            if line is None:
                break

            self._evaluateNested(line)

            self.engine["sourceCodeLineNumber"] = line.lineNum

            self._displayRuntime()
            self.userPostCycle()
            self._postCycleEngine()

        self._displayPostRun()
            
    class _registerObject: #TODO this is a short cut
        def __init__(self, key, index):
            self.key : str = key
            self.index : "str/int" = index

    def _evaluateNested(self, tree : "Node") -> ("Object", ...):
        #logging.info(debugHelper(inspect.currentframe()) + "Recurse\n" + str(tree))

        if tree.token in self._instructionSet.keys():
            '''case 1
            tree is an intruction
                recursivly call _evaluateNested on children if there is any -> arguments
                process arguments
                run instruction on arguments
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 4 instruction")
            if len(tree.child) != 0:
                arguments = self._evaluateNested(tree.child[0])
            else:
                arguments = []
            if type(arguments) is self._registerObject:
                arguments = [(arguments.key, arguments.index)]
            #logging.info(debugHelper(inspect.currentframe()) + "instruction arguments: " + str(arguments))

            newArguments = []
            for i in range(len(arguments)):
                if type(arguments[i]) is int:
                    self.lastState["i"].append(arguments[i])
                    newArguments.append(("i", len(self.lastState["i"]) - 1))
                elif type(arguments[i]) is self._registerObject:
                    newArguments.append((arguments[i].key, arguments[i].index))
                else:
                    newArguments.append(arguments[i])

            #logging.info(debugHelper(inspect.currentframe()) + "instruction immidiate processing: " + str(newArguments))

            instruction : "function" = self._instructionSet[tree.token]
            instruction = functools.partial(instruction, copy.deepcopy(self.lastState), self.state, copy.deepcopy(self.config), self.engine)

            for i in newArguments:
                instruction = functools.partial(instruction, i)

            #logging.info(debugHelper(inspect.currentframe()) + "instruction function?: " + str(instruction))
            
            instruction()

        elif len(tree.child) == 0:
            '''Case 2
            tree is a simple base type (int, str, etc) or a label
                if tree is a label, convert into a register object
                return object
            '''
            #logging.info(debugHelper(inspect.currentframe()) + "case 1 empty")
            result = None
            if tree.token in self.engine["labels"]:
                self.lastState["i"].append(self.engine["labels"][tree.token])
                result = self._registerObject("i", len(self.lastState["i"]) - 1)
            else:
                result = tree.token                
            return result

        elif tree.type == "container":
            '''Case 3
            tree is a container _evaluateNested on children
                if there is only one child, 'pass through' results
                else, return a tuple of results
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 2 container")
            stack = []
            for i in tree.child:
                stack.append(self._evaluateNested(i))

            if len(stack) == 1:
                return stack[0]
            else:
                return tuple(stack)
            
            #return tuple(stack)

        elif tree.token in self.state.keys():
            '''Case 4
            uh... huh... this needs a rewrite
            #TODO this SHOULD return a _register object
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 3 register")
            return (tree.token, self._evaluateNested(tree.child[0]))

        else:
            '''Case X
            similar to the container case, mainly just 'passes through' the result of a recursive call on children
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case x else")
            stack = []
            for i in tree.child:
                stack.append(self._evaluateNested(i))
            return tuple(stack)
        
    class compileDefault:
        """a working prototype, provides functions that take in an execution tree, and return a programs instruction list, memory array, etc"""

        def __init__(self, instructionSet, directives):
            self.instructionSet = instructionSet
            self.directives = directives

        def compile(self, oldState, config, executionTree : "Node") -> (["Node", ...], [int, ...], {str : int}):
            #assumes the instruction array is register array "m"
            
            instructionArray : "[Node, ...]" = [None for i in range(len(oldState["m"]))]
            memoryArray : [int, ...] = [0 for i in range(len(oldState["m"]))]
            labels : dict = {}

            #scans for labels, removes labels from execution tree
            #TODO this should be in the parser
            for i in range(len(executionTree.child)):
                instructionArray[i] = executionTree.child[i].copyDeep()
                if len(instructionArray[i].child) != 0:
                    if instructionArray[i].child[0].type == "label":
                        labels[instructionArray[i].child[0].token] = i
                        instructionArray[i].remove(instructionArray[i].child[0])

            #TODO scan for directives, process directives.

            return instructionArray, memoryArray, labels

        def compile2(self, config, executionTree : "Node", parseLabels : '{str : "Node", ...}') -> (["Node", ...], [int, ...], '{str : int, ...}'): #TODO a more functional way to do it
            instructionArray : ["Node", ...] = []
            memoryArray : [int, ...] = []
            labels : '{str : int, ...}' = {}

            ##reverses the key value pair with the labels dictionary, makes it easier to 
            #temp : {"Node" : str, ...} = {}
            #for i in parseLabels.keys():
            #    temp[parseLabels[i]] = str(i)

            for i in range(len(executionTree.child)):
                instructionArray.append(executionTree.child[i].copyDeep())
                memoryArray.append(0)
                #TODO empty instructionArray indices should be filled with a function that raises an error if run? or a special value denoting an error if it is tried to be executed?


            
    #==================================================================================================================

    def lazy(self, code : str):
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
        """Prototype
        runs at the end of each execution cycle, meant to handle engine level stuff. Should also run checks to verify the integrity of self.state"""
        self.engine["cycle"] += 1

    #==================================================================================================================

    class InstructionSetDefault:
        """A non-functional mockup of what an instructionset definition could look like
        
        Note: uses 'carry' flag, but doesn't need that flag to run. IE: will use 'carry' flag if present
        """

        def __init__(self):
            self.instructionSet : dict = {
                "nop"   : self.opNop,
                "add"   : self.opAdd,
                "and"   : self.opAND,
                "jumpeq": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "==", pointer, a, b)),
                "jumpne": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "!=", pointer, a, b)),
                "jump"  : (lambda z1, z2, z3, z4,   pointer           : self.opJump(z1, z2, z3, z4,       "goto", pointer)),
                "shiftl": (lambda z1, z2, z3, z4,   des, a            : self.opShiftL(z1, z2, z3, z4,     des, a, 1)),
                "shiftr": (lambda z1, z2, z3, z4,   des, a            : self.opShiftR(z1, z2, z3, z4,     des, a, 1)),

                "or"    : self.opOR,
                "xor"   : self.opXOR,

                "halt"  : self.opHalt
            }

            self.stats : dict = {}

            self.directives : dict = {}

        def redirect(self, redirection : str, register : str, index : "str/int") -> (str, int):
            """Takes in redirection as a pointer to the memory array to access, and a register index pair. Returns a key index pair corrispoding to redirection as key, index as value stored in register[index]"""
            assert type(redirection) is str
            assert type(register) is str
            assert type(index) is str or type(index) is int

            return (redirection, register[index])

        def enforceImm(self, registerTuple : (str, int)) -> (str, int):
            """Takes in a register key index pair. Returns a register key index pair iff key is 'i' for immediate. Raises an Exception otherwise"""
            assert type(registerTuple) is tuple and len(registerTuple) == 2 
            assert type(registerTuple[0]) is str and (type(registerTuple[0]) is int or type(registerTuple[0]) is str) 

            if registerTuple[0] != "i":
                raise Exception
            return registerTuple

        def opNop(self, oldState, newState, config, engine):
            newState['pc'][0] = oldState['pc'][0] + 1

        def opAdd(self, oldState, newState, config, engine, des, a, b):
            """adds registers a and b, stores result in des"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(b) is tuple and len(b) == 2 
            assert type(b[0]) is str and (type(b[0]) is int or type(b[0]) is str) 

            a1, a2 = a
            b1, b2 = b
            des1, des2 = des

            newState[des1][des2] = oldState[a1][a2] + oldState[b1][b2]

            if 'carry' in newState['flag']:
                if newState[des1][des2] >= 2**config[des1]['bitlength']:
                    newState['flag']['carry'] = 1
            
            newState[des1][des2] = newState[des1][des2] & (2**config[des1]['bitlength'] - 1)

            newState['pc'][0] = oldState['pc'][0] + 1
            
        def opAND(self, oldState, newState, config, engine, des, a, b):
            """performs operation AND between registers a and b, stores result in des"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(b) is tuple and len(b) == 2 
            assert type(b[0]) is str and (type(b[0]) is int or type(b[0]) is str) 

            a1, a2 = a
            b1, b2 = b
            des1, des2 = des

            newState[des1][des2] = oldState[a1][a2] & oldState[b1][b2] #performs the bitwise and operation

            newState[des1][des2] = newState[des1][des2] & (2**config[des1]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

            newState['pc'][0] = oldState['pc'][0] + 1 #incriments the program counter

        def opOR(self, oldState, newState, config, engine, des, a, b):
            """performs operation OR between registers a and b, stores result in des"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(b) is tuple and len(b) == 2 
            assert type(b[0]) is str and (type(b[0]) is int or type(b[0]) is str) 

            a1, a2 = a
            b1, b2 = b
            des1, des2 = des

            newState[des1][des2] = oldState[a1][a2] | oldState[b1][b2] #performs the bitwise and operation

            newState[des1][des2] = newState[des1][des2] & (2**config[des1]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

            newState['pc'][0] = oldState['pc'][0] + 1 #incriments the program counter

        def opXOR(self, oldState, newState, config, engine, des, a, b):
            """performs operation XOR between registers a and b, stores result in des"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(b) is tuple and len(b) == 2 
            assert type(b[0]) is str and (type(b[0]) is int or type(b[0]) is str) 

            a1, a2 = a
            b1, b2 = b
            des1, des2 = des

            newState[des1][des2] = oldState[a1][a2] ^ oldState[b1][b2] #performs the bitwise and operation

            newState[des1][des2] = newState[des1][des2] & (2**config[des1]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

            newState['pc'][0] = oldState['pc'][0] + 1 #incriments the program counter

        def opJump(self, oldState, newState, config, engine, mode : str, gotoIndex, a = None, b = None):
            """Conditional jump to gotoIndex, conditional on mode, and optional registers a and b

            #TODO needs to handle signed and unsigned ints

            mode:
                goto    - a simple jump without any condition testing, a and b must be set to None
                <       - less than
                <=      - less than or equal to
                >       - greater than
                >=      - greater than or equal to
                ==      - equal
                !=      - not equal
            """
            assert mode in ("goto", "<", "<=", ">", ">=", "==", "!=")
            assert (mode == "goto" and a == None and b == None) ^ (mode != "goto" and a != None and b != None)
            assert type(gotoIndex) is tuple and len(gotoIndex) == 2 #assert propper formated register
            assert type(gotoIndex[0]) is str and (type(gotoIndex[0]) is int or type(gotoIndex[0]) is str) #assert propper formated register

            pointer = oldState[gotoIndex[0]][gotoIndex[1]]

            if mode == "goto":
                newState['pc'][0] = pointer
            else:
                a1, a2 = a
                b1, b2 = b

                if mode == "<" and oldState[a1][a2] < oldState[b1][b2]:
                    newState['pc'][0] = pointer
                elif mode == "<=" and oldState[a1][a2] <= oldState[b1][b2]:
                    newState['pc'][0] = pointer
                elif mode == ">" and oldState[a1][a2] > oldState[b1][b2]:
                    newState['pc'][0] = pointer
                elif mode == ">=" and oldState[a1][a2] >= oldState[b1][b2]:
                    newState['pc'][0] = pointer
                elif mode == "==" and oldState[a1][a2] == oldState[b1][b2]:
                    newState['pc'][0] = pointer
                elif mode == "!=" and oldState[a1][a2] != oldState[b1][b2]:
                    newState['pc'][0] = pointer
                else:
                    newState['pc'][0] = oldState['pc'][0] + 1

        def opShiftL(self, oldState, newState, config, engine, des, a, n = 1):
            """Takes register a, shifts it left by n (key index pair, or int) bits. Stores result in des"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(n) is int or (type(n) is tuple and type(n[0]) is str and (type(n[1]) is int or type(n[1]) is str))

            a1, a2 = a
            des1, des2 = des

            amount = 0
            if type(n) is int:
                amount = n
            elif type(n) is tuple:
                amount = oldState[n[0]][n[1]]

            newState[des1][des2] = oldState[a1][a2] << amount

            newState[des1][des2] = newState[des1][des2] & (2**config[des1]['bitlength'] - 1)

            newState['pc'][0] = oldState['pc'][0] + 1

        def opShiftR(self, oldState, newState, config, engine, des, a, n = 1, arithmetic : bool = False):
            """Takes register a, shifts it right by n (key index pair, or int) bits. Stores result in des
            
            #TODO test arithmetic shiftt"""
            assert type(des) is tuple and len(des) == 2 
            assert type(des[0]) is str and (type(des[0]) is int or type(des[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(n) is int or (type(n) is tuple and type(n[0]) is str and (type(n[1]) is int or type(n[1]) is str))
            assert type(arithmetic) is bool

            a1, a2 = a
            des1, des2 = des

            amount = 0
            if type(n) is int:
                amount = n
            elif type(n) is tuple:
                amount = oldState[n[0]][n[1]]

            result = oldState[a1][a2]
            for i in range(amount):
                t1 = 0
                if arithmetic:
                    t1 = 2 ** (config[a1]['bitlength'] - 1)
                    t1 = t1 & result
                result = result >> 1
                result = result | t1

            result = result & (2**config[des1]['bitlength'] - 1)

            newState[des1][des2] = result
            newState['pc'][0] = oldState['pc'][0] + 1

        def opHalt(self, oldState, newState, config, engine):
            #TODO
            engine["run"] = False

        def dirString(self, config) -> [int, ...]:
            pass

class RiscV:
    """A non-functional mockup of what a rudimentry Risc-V implimentation could look like. IE: this is what I'm aiming for, but nowhere near implimenting it, dispite half implimenting it

    useful for spotting architectual flaws, figuring out what to keep track of, etc.
    Specific implimentation attempts RV32I version 2.1 as per https://riscv.org/technical/specifications/ -> riscv-spec-20191213.pdf -> Volume 1, Unprivileged Spec v. 20191213

    Reference:
        https://riscv.org/technical/specifications/ -> riscv-spec-20191213.pdf -> Volume 1, Unprivileged Spec v. 20191213
            The technical specification for the RISC-V instruction set, and all it's modules
        https://www.cl.cam.ac.uk/teaching/1617/ECAD+Arch/files/docs/RISCVGreenCardv8-20151013.pdf 
            A cheat sheet of some of RISC-Vs instructions, instruction byte layout, etc
        https://metalcode.eu/2019-12-06-rv32i.html
            Another cheat sheet of some RISC-V instructions, register layout, etc
            #Why that font?... why?
        https://smist08.wordpress.com/2019/09/07/risc-v-assembly-language-hello-world/
            Hello World example
        https://github.com/andrescv/Jupiter
            A RISC-V simulator/assembler as a standalone program
        http://venus.cs61c.org/
            A RISC-V simulator/assembler as a webpage
            https://github.com/ThaumicMekanism/venus
            https://github.com/ThaumicMekanism/venusbackend
        https://www.cs.cornell.edu/courses/cs3410/2019sp/riscv/interpreter/
            A RISC-V simulator as a webpage
            surprisingly simple and easy to use (at least for basic and simple instructions/programs)
        https://github.com/riscv/riscv-gnu-toolchain
            The RISC-V toolchain, used to compile C/C++ into RISC-V binaries, etc?
        https://github.com/d0iasm/rvemu
            The most complete RISC-V emulator I've seen so far, and you can run it in a web browser.
            https://rvemu.app/                          #The webapp
            https://github.com/d0iasm/rvemu-for-book
            https://book.rvemu.app/index.html           #A book about writing a RISC-V emulator
    """
    
    def __init__(self):
        #when initalizing this class making an instance of this class, initalizing this class should return a CPUsim() object

        CPU = CPUsim(32)
        CPU.configAddRegister("x", 32, 32)
        CPU.configAddRegister("m", 2**16, 8)
        
        #not implimented: after tokenization, should replace the token arg1 with (arg2 tokonized again). NOT A STRING FIND AND REPLACE
        #configAddAlias() should be for simple token replacement AND NOTHING MORE
        CPU.configAddAlias("zero",  "x[00]") #always zero
        CPU.configAddAlias("ra",    "x[01]") #call return address
        CPU.configAddAlias("sp",    "x[02]") #stack pointer
        CPU.configAddAlias("gp",    "x[03]") #global pointer
        CPU.configAddAlias("tp",    "x[04]") #thread pointer
        CPU.configAddAlias("t0",    "x[05]") #t0-t6 temporary registers
        CPU.configAddAlias("t1",    "x[06]")
        CPU.configAddAlias("t2",    "x[07]")
        CPU.configAddAlias("s0",    "x[08]") #s0-s11 saved registers
        CPU.configAddAlias("fp",    "x[08]") #note the two different mappings for x[08] = fp = s0
        CPU.configAddAlias("s1",    "x[09]")
        CPU.configAddAlias("a0",    "x[10]") #a0-a7 function arguments
        CPU.configAddAlias("a1",    "x[11]")
        CPU.configAddAlias("a2",    "x[12]")
        CPU.configAddAlias("a3",    "x[13]")
        CPU.configAddAlias("a4",    "x[14]")
        CPU.configAddAlias("a5",    "x[15]")
        CPU.configAddAlias("a6",    "x[16]")
        CPU.configAddAlias("a7",    "x[17]")
        CPU.configAddAlias("s2",    "x[18]")
        CPU.configAddAlias("s3",    "x[19]")
        CPU.configAddAlias("s4",    "x[20]")
        CPU.configAddAlias("s5",    "x[21]")
        CPU.configAddAlias("s6",    "x[22]")
        CPU.configAddAlias("s7",    "x[23]")
        CPU.configAddAlias("s8",    "x[24]")
        CPU.configAddAlias("s9",    "x[25]")
        CPU.configAddAlias("s10",   "x[26]")
        CPU.configAddAlias("s11",   "x[27]")
        CPU.configAddAlias("t3",    "x[28]")
        CPU.configAddAlias("t4",    "x[29]")
        CPU.configAddAlias("t5",    "x[30]")
        CPU.configAddAlias("t6",    "x[31]")

        CPU.configSetPostCycleFunction(self.postCycle)
        CPU.configSetInstructionSet(self.RiscVISA())
        CPU.configSetParser(self.RiscVParser())

        self.CPU = CPU

    def postCycle(self, notSelf): #which argument exactly is going to be getting the CPU state information?
        notSelf.lastState = copy.deepcopy(notSelf.state)
        
        notSelf.lastState["x"][0] = 0 #resets x0 to zero

        for i in notSelf.state['flag'].keys():
            notSelf.state['flag'][i] = 0
        notSelf.state['i'] = []

    class RiscVISA(CPUsim.InstructionSetDefault):
        def __init__(self):
            self.instructionSet : dict = {
                #arithmetic (add, add immidiate, subtract, load upper immediate, add upper immediate to PC)
                "add"   : self.opAdd, #(lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, a, b)),
                "addi"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opAdd(z1, z2, z3, z4,        des, a, self.enforceImm(imm))), #note: no enforcement of imm being an immediate value
                "sub"   : None,
                "lui"   : None,
                "auipc" : None,

                #logical
                "xor"   : self.opXOR, #(lambda z1, z2, z3, z4,   des, a, b       : self.opXOR(z1, z2, z3, z4,        des, a, b)),
                "xori"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opXOR(z1, z2, z3, z4,        des, a, self.enforceImm(imm))),
                "or"    : self.opOR, #(lambda z1, z2, z3, z4,   des, a, b       : self.opOR(z1, z2, z3, z4,         des, a, b)),
                "ori"   : (lambda z1, z2, z3, z4,   des, a, imm     : self.opOR(z1, z2, z3, z4,         des, a, self.enforceImm(imm))),
                "and"   : self.opAND, #(lambda z1, z2, z3, z4,   des, a, b       : self.opAND(z1, z2, z3, z4,        des, a, b)),
                "andi"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opAND(z1, z2, z3, z4,        des, a, self.enforceImm(imm))),

                #branch (equal, not equal, less than, greater or equal, less then unsigned, greater or equal unsigned)
                "beq"   : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "==", pointer, a, b)), 
                "bne"   : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "!=", pointer, a, b)), 
                "blt"   : None, #opJump doesn't handle signed compairisons
                "bge"   : None,  
                "bltu"  : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "<", pointer, a, b)), 
                "bgeu"  : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       ">=", pointer, a, b)), 

                #shifts (shift left, shilf left immediate, shift right, shift right immediate, shift right arithmetic, shift right arithmetic immediate)
                "sll"   : self.opShiftL, #(lambda z1, z2, z3, z4,   des, a, n       : self.opShiftL(z1, z2, z3, z4,     des, a, n)),
                "slli"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftL(z1, z2, z3, z4,     des, a, self.enforceImm(imm))),
                "srl"   : self.opShiftR, #(lambda z1, z2, z3, z4,   des, a, n       : self.opShiftR(z1, z2, z3, z4,     des, a, n)),
                "srli"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftR(z1, z2, z3, z4,     des, a, self.enforceImm(imm))),
                "sra"   : (lambda z1, z2, z3, z4,   des, a, n       : self.opShiftR(z1, z2, z3, z4,     des, a, n, True)),
                "srai"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftR(z1, z2, z3, z4,     des, a, self.enforceImm(imm), True)),

                #compare (set less than, set less than immediate, set less that unsigned, set less that immediate unsigned)
                "slt"   : None, #signed compairsons for opSetLessThen is not implimented
                "slti"  : None,
                "sltu"  : (lambda z1, z2, z3, z4,   des, a, b       : self.opSetLessThan(z1, z2, z3, z4,     des, a, b, False)),
                "sltiu" : (lambda z1, z2, z3, z4,   des, a, imm     : self.opSetLessThan(z1, z2, z3, z4,     des, a, self.enforceImm(imm), False)),

                #jump and link
                "jal"   : None,
                "jalr"  : None,

                #load
                "lb"    : None,
                "lh"    : None,
                "lw"    : None,
                "lbu"   : None,
                "lhu"   : None,

                #store
                "sb"    : None,
                "sh"    : None,
                "sw"    : None
            }

            '''instructions missing according to riscv-spec-20191213.pdf -> page 90 (108 of 238) -> RV32I Base Integer Instruction Set
            #Store, these instructions show up in https://metalcode.eu/2019-12-06-rv32i.html, but not in riscv-spec-20191213.pdf
            "sbu"   - Store byte unsigned
            "shu"   - Store half unsigned

            #fence
            "fence"
            "fence.i"

            "ecall"
            "ebreak"
            "csrrw"
            "csrrs"
            "csrrc"
            "csrrwi"
            "csrrsi"
            "csrrci"
            '''

            #for energy and latency, 1 is normalized to 1-ish logic gates-ish
            #length is unused, but is for the assembler to compute how much memory it takes, 1 is 1 byte (don't know all the edge cases that could break a simple assignment like this)
            self.stats : dict = {
                #arithmetic (add, add immidiate, subtract, load upper immediate, add upper immediate to PC)
                "add"   : {"energy"         : 5 * 32,   "latency"       : 3 * 32,   "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "addi"  : {"energy"         : 5 * 32,   "latency"       : 3 * 32,   "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "sub"   : {"energy"         : 5 * 32,   "latency"       : 3 * 32,   "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"}, #a guess for energy and latency
                "lui"   : None,
                "auipc" : None,

                #logical
                "xor"   : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "xori"  : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "or"    : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "ori"   : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "and"   : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},
                "andi"  : {"energy"         : 32,       "latency"       : 1,        "cycles"        : 1,        "length"        : 4,    "executionUnit" : "int"},

                #branch (equal, not equal, less than, greater or equal, less then unsigned, greater or equal unsigned)
                "beq"   : None,
                "bne"   : None,
                "blt"   : None,
                "bge"   : None,
                "bltu"  : None,
                "bgeu"  : None,

                #shifts (shift left, shilf left immediate, shift right, shift right immediate, shift right arithmetic, shift right arithmetic immediate)
                "sll"   : None,
                "slli"  : None,
                "srl"   : None,
                "srli"  : None,
                "sra"   : None,
                "srai"  : None,

                #compare (set less than, set less than immediate, set less that unsigned, set less that immediate unsigned)
                "slt"   : None,
                "slti"  : None,
                "sltu"  : None,
                "sltiu" : None,

                #jump and link
                "jal"   : None,
                "jalr"  : None,

                #load
                "lb"    : None,
                "lh"    : None,
                "lw"    : None,
                "lbu"   : None,
                "lhu"   : None,

                #store
                "sb"    : None,
                "sh"    : None,
                "sw"    : None
            }

            self.directives : dict = {}

        def opSetLessThan(self, oldState, newState, config, engine, destination, a, b, signed = False):
            assert type(destination) is tuple and len(destination) == 2 
            assert type(destination[0]) is str and (type(destination[0]) is int or type(destination[0]) is str) 
            assert type(a) is tuple and len(a) == 2 
            assert type(a[0]) is str and (type(a[0]) is int or type(a[0]) is str) 
            assert type(b) is tuple and len(b) == 2 
            assert type(b[0]) is str and (type(b[0]) is int or type(b[0]) is str) 

            a1, a2 = a
            b1, b2 = b
            des1, des2 = destination

            if oldState[a1][a2] < oldState[b1][b2]:
                newState[des1][des2] = 1
            else:
                newState[des1][des2] = 1
        
            newState['pc'][0] = oldState['pc'][0] + 1

    class RiscVParser(CPUsim.ParseDefault):
        
        def parseCode(self, sourceCode : str) -> "Node":
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

            root = self.ruleApplyAlias(root, self.alias)                                    #<=============================================================
            logging.debug(debugHelper(inspect.currentframe()) + "ruleApplyAlias: " + "\n" + str(root))

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
            #root = self.ruleRemoveToken(root, ",") #TODO this needs to be replaced with a proper way to seperate arguments
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveToken: " + "\n" + str(root))

            root = self.ruleCastInts(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleCastInts: " + "\n" + str(root))

            root = self.ruleCastHex(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleCastHex: " + "\n" + str(root))

            #This is where the Node Tree is allowed to go to depth > 2
            root = self.ruleContainer(root, {"(":")", "[":"]"})
            logging.debug(debugHelper(inspect.currentframe()) + "ruleContainer: " + "\n" + str(root))

            root = self.ruleContainerTokensFollowingInstruction(root)                               #<=================================================
            logging.debug(debugHelper(inspect.currentframe()) + "ruleContainerTokensFollowingInstruction: " + "\n" + str(root))

            temp : list = self.ruleSplitLines(root)
            root = self.Node("root")
            for i in temp:
                root.append(i)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitLines: " + "\n" + str(root))

            return root

        def ruleContainerTokensFollowingInstruction(self, root : "Node") -> "Node":
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

    ALU.linkAndLoad('''
                # Multiplies two numbers together
                # Inputs: r[0], t[0]
                # Output: t[1]
                loop:   jumpEQ  (end, r[0], 0)
                            and     (r[1], r[0], 1)
                            jumpNE  (zero, r[1], 1)
                                add     (t[1], t[0], t[1])
                zero:       shiftL  (t[0], t[0])
                            shiftR  (r[0], r[0])
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
    debugHighlight = lambda x : 1350 <= x <= 1500

    #print(multiply1(3,4)) #old working prototype
    
    #What works
    CPU = CPUsim(8)
    CPU.configSetDisplay(CPU.DisplaySimpleAndClean(0))
    #CPU.configSetDisplay(CPU.DisplaySilent())
    print("".rjust(80, "="))

    CPU.configAddRegister('r', 2, 16)
    CPU.configAddRegister('m', 16, 8)
    CPU.configAddRegister('t', 2, 16)
    CPU.configAddFlag("random")
    CPU.inject('r', 0, 8)
    CPU.inject('t', 0, 8)
    CPU.inject('flag', 'carry', 1)
    print("".rjust(80, "="))

    root = CPU._parseCode('''
                # Multiplies two numbers together
                # Inputs: r[0], t[0]
                # Output: t[1]
                loop:   jumpEQ  (end, r[0], 0)
                            and     (r[1], r[0], 1)
                            jumpNE  (zero, r[1], 1)
                                add     (t[1], t[0], t[1])
                zero:       shiftL  (t[0], t[0])
                            shiftR  (r[0], r[0])
                            jump    (loop)
                end:    halt
                ''')
    print(root)
    print(CPU.userParser.labels)
    print("".rjust(80, "="))

    """
    CPU.linkAndLoad('''
                # Multiplies two numbers together
                # Inputs: r[0], t[0]
                # Output: t[1]
                        nop #required because bug with labels
                loop:   jumpEQ  (end, r[0], 0)
                            and     (r[1], r[0], 1)
                            jumpNE  (zero, r[1], 1)
                                add     (t[1], t[0], t[1])
                zero:       shiftL  (t[0], t[0])
                            shiftR  (r[0], r[0])
                            jump    (loop)
                end:    halt
                ''')
    """
    #"""
    CPU.linkAndLoad('''
                test:   nop     #required because bug with labels
                loop:   add     (r[0], 1, r[0])
                        jumpNe  (loop, r[0], 16)
                end:    halt
    ''') 
    #"""
    print("".rjust(80, "="))
    print(CPU.engine["labels"])
    print(CPU._namespace.keys())

    print("".rjust(80, "="))
    CPU.run()

    ''' #testing/implementing
    #CPU.lazy('nop #test test test') #comments get ignored
    #CPU.lazy('copy(5, r[0])') #an actual instruction
    #CPU._display()
    #CPU.run()
    '''
    """
    CPU = RiscV().CPU
    CPU.linkAndLoad('''
                        add     (x[0], x[0], x[0])
                loop:   addi    (x[1], x[1], 1)
                    ''') 
    """
