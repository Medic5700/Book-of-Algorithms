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

Goals:
    A CPU simulator that can simulate CPU instructions and architectures at a high level (performance/speed/effeiency is sacrificed)
    Allows for creating and testing a CPU 'instruction set' at a high level.
    There is enough functionality to be a teaching tool.
        Allow easy creation of instruction sets for teaching/documentation/instructional purposes. 
            IE: this is everything this CPU instruction does and interacts with in these 15 lines of source code
        Includes a customizable (if unstable) parser to allow for parsing multiple different low level assembly languages.
            This allows for simulating old CPUs, like the 6502 with native source code.
            Holy Hell this is very far outside the box compaired to how parsers should work.
    Allow for meaningfull compairisons between various low level algorithms on the same architectures using various metrics (memory accesses, energy usage, etc)
    Allow for meaningfull compairisons between various architectures running the same algorithms using various metrics (energy usage, execution cycles, etc)
    A modular simulator where various things can be swapped in and out. IE: swapping in a different instruction set, different 'displays', different memory configurations, etc.

Getting Started:
    Note: this is a prototype, so the entire API is in flux
    refer to "def multiply2" for an example of a possible use case.
    refer to "class RiscV" for a mockup of how it could be used to 'create' a processor instruction set at a highlevel.

    #TODO: put API list here
"""

#asserts python version 3.8 or greater, needed due to new feature used [variable typing]
import sys
version = sys.version_info
assert version[0] == 3 and version[1] >= 8

import copy #copy.deepcopy() required because states are a nested dictionary, and need to be copied instead of referenced
import functools #used for partial functions when executioning 'instruction operations'
from typing import Any, Callable, Dict, List, Tuple #used for more complex annotation typing

#debugging and logging stuff
import logging
import inspect #used for logging, also used to assertion testing
debugHighlight = lambda _ : False #debugHighlight = lambda x : 322 <= x <= 565 #will highlight the debug lines between those number, or set to -1 to highlight nothing
def debugHelper(frame : "Frame Object") -> str:
    """Takes in a frame object, returns a string representing debug location info (IE: the line number and container name of the debug call)

    Usage 
        -> logging.debug(debugHelper(inspect.currentframe()) + "String")
        -> DEBUG:root:<container>"remove"[0348]@line[0372] = String
    Used for easy debugging identification of a specific line
    No, you can't assign that code segment to a lambda function, because it will always return the location of the original lambda definition

    Reference:
        https://docs.python.org/3/library/inspect.html#types-and-members
    """
    assert inspect.isframe(frame)
    
    #textRed : str = "\u001b[31m" #forground red
    textTeal : str = "\u001b[96m" #forground teal
    ANSIend : str = "\u001b[0m" #resets ANSI colours

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
        Note: Use Big Endian, it's convention in most cases
            If an array pointer points to a specific byte in a four byte word, does it point to the big side or little side (Big Endian points to the big side)
        Load upper immediate needs to be a thing
            Some instructions can't store a large immediate value, and use 'load upper immediate' to load the upper bytes of a large immediate
            since immediate registers are generated on the fly, and 'load upper immediate' is called before a specific a instruction...
                There needs to be a way to specify that a just declared immediate should be bolted onto the next declared immediate
            How does this impact out of order execution?
            possible implimentation:
                could have imm registers always have the last index be a blank index, and some operation is done to it whenever the next immediate is added?
                A special temp immediate register that is only used for loading upper immediates
                Immediate registers could be generated in pairs, allowing different instructions to interact with multiple pairs of immediates
                    IE: 'load upper immediate' creates 'imm1[1]' and 'imm2[1]' puts a number in 'imm1[1]', 'add immediate' creates 'imm1[2]' and 'imm2[2]', puts a number in 'imm2[2]' and combines it with 'imm1[1]'
                    Immediate registers are reset between instructions, so this wouldn't be visible to the next instruction
                could create an 'upperImm' register as part of custom ISA, and a special 'combine with immediate' function in the custom ISA (like enforceImmediate()) (which also resets the 'upperImm' register)
                    Would get around the persistance problem
                    Would be kind of 'hacky' as it could require extra control flags, etc
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
        Instructions/Special considerations
            System Calls
                How to handle system calls?
            Load and Store instructions should be able to handle bit-addressing within a memory element
            Should I define a function that enforces only a specific memory access?
                Like enforceImm(imm), enforcing access only to the imm registers. But for different registers, like 'r', or 'm'
            https://youtu.be/QKdiZSfwg-g?t=5728
                The 'repeat' prefix instruction in x86
                'repeat' (1 byte) prefix, 'moveString' (1 byte) instruction, with registers EDI (extended implicid source) defined, ESI (extended implicid destination) defined, ECX (implicid count register)
                    Allows copying an arbitry length string from ESI memory pointer to EDI memory pointer of ECX string length
        configAddAlias() should be split into addParserAlias and addEngineAlias
            addParserAlias is just like it is now, the parser searches for and replaces a token with another token (or series of tokens)
            addEngineAlias would have to be run in the execution engine, dynamically changing register names as they are being executed
                would also have to add names for each register as part of self.config (IE: each register/memory element would get a dictionary of properties)
        ? should self.config store a config dictionary for EVERY key, index pair?
            Would use a tremendous amount of memory
            Would also make accessing data on a particular register/memory element more consistent
        Execution engine should not rely on Node labels to be labeled 'container' to recurse (it doesn't rely on it, but it also shouldn't be a case if it's handled by else?)
        MicroArchitecture something something NOT MicroCode?
            self.instructionSet : dict { 
                #a single instruction, the normal case, SISD. Note: The engine should treat this as a single instruction executing
                "add"   : (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, a, b))
            }
            self.instructionSet : dict = { 
                #a vector, where each instruction actually represents multiple similar instructions. SIMD. Note: The engine should treat this as 4 instructions executing, with 4 seperate memory accesses
                
                "addVector": Vector(
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, (a[0], a[1] + 0), (b[0], b[1] + 0)   )),
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, (a[0], a[1] + 1), (b[0], b[1] + 1)   )),
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, (a[0], a[1] + 2), (b[0], b[1] + 2)   )),
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z1, z2, z3, z4,        des, (a[0], a[1] + 3), (b[0], b[1] + 3)   ))
                    
                )
            }
            self.instructionSet : dict = { 
                #Executing as a single instruction. SISD. The engine should treat this as 1 instruction executing, with one memory access.
                #Not entirly sure this is needed, or how usefull it is, as I can't think of a good example. Maybe multiply and accumulate?
                #The instructions are executed linearly as a list.
                "loadAndIncrement" : Single( #think accessing/loading stuff from an array, where one register 'r0' holds a pointer
                    (lambda z1, z2, z3, z4,   des             : self.opLoad(z1, z2, z3, z4,       des, ('r', 0)             )),
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAdd(z2, z2, z3, z4,        ('r', 0), ('r', 0), 1     )), #Notice "self.opAdd(z2, z2, z3, z4, " has the nextState 'z2' as both the lastState and nextState
                )
            }
            self.instructionSet: dict = {
                #implimenting NAND as a linear combination of AND and NOT instructions. Node: The engine should treat this as one instruction executing, with one memory access
                #Note: this is a further case where the instruction functions should not be altering the PC by themselves. #TODO
                "nand" : Single(
                    (lambda z1, z2, z3, z4,   des, a, b       : self.opAnd(z1, z2, z3, z4,        des, a, b     )),
                    (lambda z1, z2, z3, z4,   des             : self.opNot(z2, z2, z3, z4,        des, des      )) #Notice "self.opNot(z2, z2, z3, z4, " has the nextState 'z2' as both the lastState and nextState
                    #adding a NOP here just to reset the PC is dumb and confusing
                )
            }
            self.instructionSet : dict = {
                #microcode?
                #possible cases = 
                #   1: the microcode functions like a function call, and after a context switch operates on the same registers as a user space program
                #   2: the microcode functions as a translation layer that queues up a series of instructions operating on hidden registers not exposed to the user space program
                #might have to use complex numbers for the program counter to represent multi-vector instruction streams...? IE: one component keeps track of the user space PC, the other component keeps track of the microcode PC
                "multiply" : HardwareTranslationEngine("""
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
                    """
                )
            }
            self.instructionSet: dict = {
                #'repeat' (1 byte) prefix, 'moveString' (1 byte) instruction, with registers EDI (extended implicid source) defined, ESI (extended implicid destination) defined, ECX (implicid count register)
                #   Allows copying an arbitry length string from ESI memory pointer to EDI memory pointer of ECX string length
                "repeatMoveString" : Single(
                    (lambda z1, z2, z3, z4,                : self.opMove(z1, z2, z3, z4,       ESI, EDI      )),
                    (lambda z1, z2, z3, z4,                : self.opSub(z2, z2, z3, z4,        ECX, ECX, 1   )),
                    (lambda z1, z2, z3, z4,                : self.opJump(z2, z2, z3, z4,       '==', PC + 1, ECX, 0  )), #assuming PC is not altered by other instructions, which hasn't been implimented
                    (lambda z1, z2, z3, z4,                : self.opJump(z2, z2, z3, z4,       '!=', PC - 1, ECX, 0  ))
                )
            }
            #is a double indirect load possible? IE: take a register 'r=255' as a pointer, load the memory address 'm255=64' of the pointer, use that as a pointer to load another memory address 'm64=Whatever'
            
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
        https://www.youtube.com/watch?v=UvCri1tqIxQ #Making Your First Game: Minimum Viable Product - Scope Small, Start Right - Extra Credits
            What is Minimum Viable Product

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
                No, will make it harder to understand instruction source code/cause confusion
            Case 1: Track register reads/writes
            Case 2: Keep track of data in a cache hierarchy
            Case 3: Allow multiple reads/writes per line/instruction word in the case of sloppy written source code, or Very Long Instruction Words which have multiple paralell instructions
            Case 4: Speculative execution will require keeping track of all reads/writes on a instruction word by instruction word basis, and allow for discarding some speculative results/operations
            Case 5: Since instructions are customizable, it is impossible to predict the dynamics of an instruction before executing it.
                Therefore implimenting superscaler stuff would require actually executing MANY following instructions and seeing which instructions conflict before deciding which instructions to schedual
                (yes, it's as backwords as it sounds, in possibly the most glorious and ironic way possible)
            Case 6: Out of Order execution would require keeping track of which instructions changed what, and when to commit the changes
        Microcode. The execution engine just isn't built out enough yet to consider this yet
            Microcode could run as a recursive CPU call, elimating the need for complex tracking of register windows, since it's run in a 'custom cpu construct' made for that instruction
            Microcode could be implimented at the instruction set composition level instead
                IE: add(a,b,c) used to make a vector add instruction (lambda a,b,c : add(a,b,c), add(a+1,b+1,c+1), add(a+2,b+2,c+2), etc)
                Only useful for simple instructions
        Instruction non-execution analysis utilities to better help calabrate instructions (IE: some utilities to help the user see energy use for each instruction in a graph before code is run)
        Support for virtual memory?
    '''

    def __init__(self, bitLength : int = 16, defaultSetup : bool = True):
        assert type(bitLength) is int
        assert bitLength >= 1

        assert type(defaultSetup) is bool
        
        self.bitLength : int = bitLength #the length of the registers in bits

        '''core engine variables, used by a number of different functions, classes, etc. It's assumed that these variables always exist'''
        self.state      : Dict[str, Dict[str or int, int]] = {}
        self.lastState  : Dict[str, Dict[str or int, int]] = {}
        self.config     : Dict[str, Dict[str or int, dict]] = {}
        self.stats : dict = {} #FUTURE used to keep track of CPU counters, like instruction executed, energy used, etc
        self.engine : dict = {} #FUTURE used to keep track of CPU engine information?, should it be merged with self.stats?

        self.engine["run"] = False 

        #TODO find a better structure for this
        self.engine["labels"] : Dict[str, int] = None
        self.engine["instructionArray"] : List["Nodes"] = None
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
        self._displayRuntime : Callable[[], None] = lambda : None
        self._displayPostRun : Callable[[], None] = lambda : None
        #self.configSetInstructionSet
        self.userInstructionSet : __class__ = None
        self._instructionSet : Dict[str, Callable[[dict, dict, dict, dict, "Args"], None]] = {}
        self._directives : dict = {}
        #self.configSetParser
        self.userPraser : __class__ = None
        self._parseCode : Callable[[str], "Node"] = lambda x : None
        self._updateNameSpace : "function" = lambda x, y : None #TODO change name to _parseUpdate()
        #self.configSetPostCycleFunction
        self.userPostCycle : Callable[[dict], Tuple[dict, dict]] = lambda x : (x, x)
        #self.configAddAlias
        self._tokenAlias : dict = {}

        self._namespace : dict = {}

        #initialize CPU flag datastructure
        self.configAddRegister('flag', 1, 0) #done this way so any changes to the 'self.config' data structure is also added to 'flag', for consistancy reasons
        self.state['flag'] : dict = {} #overrides default array of numbers
        self.lastState['flag'] : dict = {}

        #adds special registers that are required
        self.configAddRegister('imm', bitLength, 1024) #holds immidiate values, IE: litteral numbers stored in the instruction, EX: with "add 2,r0->r1", the '2' is stored in the instruction
        self.lastState['imm'] = {}
        self.state['imm'] = {}

        self.configAddRegister('pc', bitLength, 1) #program counter, it's a list for better consistancy with the other registers
        
        #self.state['sp'] = [0] #stack pointer #FUTURE
        #self.state['stack'] = [None for i in range(memoryAmount)] #stores stack data #FUTURE
        #the entire state information for registers, program pointers, etc, should be stored as one memory unit for simplicity

        #convinence added stuff for 'works out of the box' functionality
        if defaultSetup:
            self.configAddRegister('r', bitLength, 8) #standard registers
            self.configAddRegister('m', bitLength, 32) #standard memory
            self.configAddFlag('carry')

        self.configSetDisplay(self.DisplaySimpleAndClean())
        self.configSetInstructionSet(self.InstructionSetDefault())
        self.configSetParser(self.ParseDefault({}))

        self.configSetPostCycleFunction(self._postCycleUserDefault)

        #engine stuff?
        self.lastState, self.state = self.userPostCycle(self.state)
        self._postCycleEngine()

    def _computeNamespace(self): #TODO this should serve a different function, updating namespaces throughout program WITHOUT using a centralized 'namespace' variable
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
        """Takes in a 'token' and a 'replacement' str
        
        When used, adds it to self._tokenAlias.
        Parsing source code will replace that token with it's replacement during parsing"""
        assert type(token) is str
        assert type(replacement) is str
        assert len(token) != 0
        assert len(replacement) != 0
        assert token != replacement

        self._tokenAlias[token] = replacement
        
        self._computeNamespace()

    def configSetDisplay(self, displayInstance):
        """Takes in an display class

        class must have:
            runtime(lastState, state, config, stats, engine) - runs after every execution cycle
            postrun(lastState, state, config, stats, engine) - runs after the CPU halts

        Note: runtime() must be able to handle the 'imm' register having a variying sized array, since it's size changes based on what the currect instruction needs
        """
        assert displayInstance.runtime
        assert displayInstance.postrun
        assert callable(displayInstance.runtime)
        assert callable(displayInstance.postrun)
        assert len((inspect.signature(displayInstance.runtime)).parameters) == 5
        assert len((inspect.signature(displayInstance.postrun)).parameters) == 5

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
        assert all([type(i) is str for i in instructionSetInstance.instructionSet]) #some keys in instructionSet are not strings
        assert all([len(i) > 0 for i in instructionSetInstance.instructionSet]) #some keys in instructionSet are null strings
        assert all([callable(instructionSetInstance.instructionSet[i]) for i in instructionSetInstance.instructionSet.keys()]) #some keys in instructionSet have non-function values
        assert all([len((inspect.signature(instructionSetInstance.instructionSet[i])).parameters) >= 4 for i in instructionSetInstance.instructionSet.keys()]) #some instructionSet functions take less than the minimum required functions

        self.userInstructionSet : __class__ = instructionSetInstance
        self._instructionSet : dict = instructionSetInstance.instructionSet
        self._directives : dict = instructionSetInstance.directives

        self._computeNamespace()

        logging.info(debugHelper(inspect.currentframe()) + "Imported Instruction Set\n" + \
            "".join(
                [("    " + str(i).ljust(12, " ") + str(inspect.signature(instructionSetInstance.instructionSet[i])) + "\n") for i in instructionSetInstance.instructionSet]
                )
            )

    def configSetParser(self, parserInstance):
        """Takes in a class representing a source code parser

        class must have:
            parseCode(sourceCode : str) - a function that takes in a string, and returns an execution tree
            updateNameSpace(nameSpace : dict) - a function which takes in a nameSpace dictionary representing the CPUs registers, flags, instructions, etc
        """
        assert parserInstance.parseCode
        assert callable(parserInstance.parseCode)
        assert len(inspect.signature(parserInstance.parseCode).parameters) >= 1
        assert parserInstance.updateNameSpace
        assert callable(parserInstance.updateNameSpace)
        #TODO assert update function takes right number of arguments

        self.userParser = parserInstance
        self._parseCode = parserInstance.parseCode
        self._updateNameSpace = parserInstance.updateNameSpace

        self._computeNamespace()

    def configSetPostCycleFunction(self, postCycle : Callable[[dict], Tuple[dict, dict]]):
        """Takes in a function that is executed after every execution cycle.

        Function must take in a dictionary currentState representing the current state
        Function must output a tuple containing a lastState dictionary and a newState dictionary, in that order.
        See self._postCycleUserDefault() for the default implimentation

        That function is used for (aside from explicidly copies the old state to the new state, etc) to reset CPU Flags, reset registers that are supposed to be hardwired to zero, to zero, etc.
        """
        assert callable(postCycle)
        assert len(inspect.signature(postCycle).parameters) == 1

        self.userPostCycle = postCycle

    def configAddRegister(self, name : str, bitlength : int, amount : int, show : bool = True):
        """takes in the name of the register/memory symbol to add, the amount of that symbol to add (can be zero for an empty array), and bitlength. Adds and configures that memory to self.state"""
        #TODO make this function use configConfigRegister() to create registers to centralize default values
        assert type(name) is str
        assert len(name) >= 1

        assert type(bitlength) is int 
        assert bitlength > 0

        assert type(amount) is int 
        assert amount >= 0

        assert type(show) is bool
        
        self.state[name.lower()] = {i:0 for i in range(amount)}
        self.lastState[name.lower()] = {i:0 for i in range(amount)}
        self.config[name.lower()] = {i:{'bitlength':bitlength, 'show':show} for i in range(amount)}

        self._computeNamespace()

    def configAddFlag(self, name : str):
        """Takes in a name for a CPU flag to add, Adds it to self.state"""
        assert type(name) is str
        assert len(name) >= 1

        assert 'flag' in self.state.keys()

        self.state['flag'][name.lower()] = 0
        self.lastState['flag'][name.lower()] = 0

        self.config['flag'][name.lower()] = {'bitlength':1, 'show':True}

        self._computeNamespace()

    def inject(self, key : str, index : int or str, value : int):
        """Takes in a key index pair representing a specific register. Assigns int value to register.
        
        value >= 0
        Does not increment the simulatition"""
        assert type(key) is str
        assert type(index) is int or type(index) is str
        assert type(value) is int
        assert value >= 0

        t1 = key.lower()
        t2 = index.lower() if type(index) is str else index

        #TODO check if key/index pair is in state before assigning value
        self.state[t1][t2] = value & (2**self.config[t1][t2]['bitlength']-1)

        self._displayRuntime()

        self._postCycleEngine()

    def extract(self, key : str, index : int or str) -> int:
        """Takes in a key index pair representing a specific register. Returns an int representing the value stored in that register"""
        assert type(key) is str
        assert type(index) is int or type(index) is str

        t1 = key.lower()
        t2 = index.lower() if type(index) is str else index

        self._postCycleEngine()

        return self.state[t1][t2]

    def lazy(self, code : str):
        """NotImplimented
        decodes and executes a single instruction line"""
        pass

    def _postCycleUserDefault(self, currentState : dict) -> Tuple[dict, dict]: #TODO this needs a redesign, should be more functional/modular
        """Takes in a dictionary currentState, returns a tuple containing two dictionaries representing the oldState and the newState, respectivly.

        resets all required registers and flags between instructions, copies current state into lastState"""
        assert type(currentState) is dict

        oldState = copy.deepcopy(currentState) #required deepCopy because state['flags'] contains a dictionary which needs to be copied
        newState = copy.deepcopy(currentState)
        
        for i in newState['flag'].keys(): #resets all flags
            newState['flag'][i] = 0
        newState['imm'] = {} 

        return (oldState, newState)

    def _postCycleEngine(self):
        """Prototype
        runs at the end of each execution cycle, meant to handle engine level stuff. Should also run checks to verify the integrity of self.state"""
        self.engine["cycle"] += 1
        
        '''#TODO
        assert state and last state have the same keys (except for immediate values/registers)
        assert state and last state registers have int values
            assert those values are positive
        assert all state variables are the correct type (dict)
        '''

        #for i in self.state.keys():
        #    assert all([type(j) is int for j in self.state[i]])

    #==================================================================================================================

    def linkAndLoad(self, code: str):
        """Takes in a string of assembly instructions, and "compiles"/loads it into memory, 'm' registers
        
        configures:
            program counter to label __main, 0 if __main not present
            self.engine["instructionArray"] to contain instruction Nodes
            self.state["m"] to contain the memory of the program (but not instruction binary encodings, instructions are written as zeros)
            self.engine["labels"] to contain a dictionary of associations of labels with memory pointers

        #TODO '__main__' label should be changeable
        """
        assert type(code) is str
        assert len(code) > 0

        logging.info(debugHelper(inspect.currentframe()) + "Loading source code = " + "\n" + str(code))

        self.engine["sourceCode"] : str = code
        parseTree, parseLabels = self._parseCode(code)

        logging.debug(debugHelper(inspect.currentframe()) + "parseLabels = " + str(parseLabels))
        logging.info(debugHelper(inspect.currentframe()) + "linkAndLoad parseTree = " + "\n" + str(parseTree))

        assemmbledObject = self.compileDefault(self._instructionSet, self._directives)
        instructionArray : List["Node" or None] = [] #instructionArray is list of instruction nodes
        memoryArray : List[int] = [] #memoryArray is an integer array of memory elements/registers
        compileLabels : Dict[str, int] = {} #compileLabels is labels, a dictionary accossiating 'labels' to a specific memory addresses
        instructionArray, memoryArray, compileLabels = assemmbledObject.compile(self.config, parseTree, parseLabels)
        
        #some checks on the returned values from compile function
        if len(memoryArray) > len(self.state["m"]):
            raise Exception("Program is too large to fit into memory array")
        assert type(instructionArray) is list
        assert type(memoryArray) is list
        assert type(compileLabels) is dict
        assert len(instructionArray) == len(memoryArray)
        assert all([(callable(i) or i == None) for i in instructionArray])
        assert all([len(i.child) != 0 for i in instructionArray]) #asserts there are no empty lines
        assert all([type(i) is int for i in memoryArray])
        assert all([(type(key) is str and type(value) is int) for key, value in compileLabels.items()])

        self.engine["instructionArray"] = instructionArray

        #TODO program is imported into memory 'm', this should be changeable
        for i in range(len(memoryArray)): #loads program memory into memory one element at a time
            self.state["m"][i] = memoryArray[i]
        
        self.engine["labels"] = compileLabels
        logging.debug(debugHelper(inspect.currentframe()) + "compilerLabels = " + str(compileLabels))

        #sets the program counter to the label __main, if the label __main exists
        #TODO allow a settable 'main' label. IE: allow different labels to be used as the program start instead of '__main'
        if "__main" in self.engine["labels"]:
            self.state["pc"][0] = self.engine["labels"]["__main"]

        logging.info(debugHelper(inspect.currentframe()) + "Program Counter set to " + hex(self.state["pc"][0]))

    def run(self, cycleLimit = 1024):
        """Prototype
        starts execution of instructions
        
        #TODO check for empty instruction lines
        #TODO perform checks on everything"""

        '''
            do a depth first search on the execution tree
            apply 'rule functions' based on what the token is
            recursivly evaluate
        '''
        self._displayRuntime()
        self.lastState, self.state = self.userPostCycle(self.state)
        self._postCycleEngine()

        self.engine["run"] = True
        self.engine["cycle"] = 0

        i = 0
        while i < cycleLimit:
            i += 1
            if self.engine["run"] == False:
                break

            #logging.info(debugHelper(inspect.currentframe()) + str(i))
            line = self.engine["instructionArray"][self.state["pc"][0]]
            #logging.info(debugHelper(inspect.currentframe()) + "\n" + str(line))
            if line is None: #TODO this should raise an exception, since it's trying to execute a non-instruction
                break

            self.engine["sourceCodeLineNumber"] = line.lineNum

            self._evaluateNested(line)

            if self.lastState['pc'][0] == self.state['pc'][0] and self.engine["run"] == True:
                logging.warning(debugHelper(inspect.currentframe()) + "Program Counter has not incremented\n" + str(line))

            self._displayRuntime()
            self.lastState, self.state = self.userPostCycle(self.state)
            self._postCycleEngine()

        self._displayPostRun()
            
    class _registerObject: #TODO this is a short cut
        def __init__(self, key, index):
            self.key : str = key
            self.index : "str/int" = index

    def _evaluateNested(self, tree : "Node") -> Tuple["Object"]:
        #logging.info(debugHelper(inspect.currentframe()) + "Recurse\n" + str(tree))

        if tree.token in self._instructionSet.keys():
            '''case 1
            tree is an intruction
                recursivly call _evaluateNested on children if there is any -> arguments
                process arguments
                run instruction on arguments
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 1 instruction")

            #evaluates children to get arguments
            arguments = []
            if len(tree.child) != 0:
                for i in tree.child:
                    temp = self._evaluateNested(i)
                    
                    if type(temp) is tuple: #incase child is container, unpacks container
                        for j in temp:
                            arguments.append(j)
                    else:
                        arguments.append(temp)
            #logging.info(debugHelper(inspect.currentframe()) + "instruction raw input: " + str(arguments))

            #unpacks register objects
            newArguments = []
            for i in arguments:
                if type(i) is self._registerObject:
                    newArguments.append((i.key, i.index))
                else:
                    newArguments.append(i)
            arguments = newArguments
            #logging.info(debugHelper(inspect.currentframe()) + "instruction arguments: " + str(arguments))

            #adds immediate values to self.state
            newArguments = []
            for i in range(len(arguments)):
                if type(arguments[i]) is int: #TODO this case 'should' no longer be possible, but is somehow still active
                    #self.lastState["imm"].append(arguments[i])
                    self.lastState["imm"][len(self.lastState["imm"])] = arguments[i] #the created 'index' of the key/index pair will always be an int == length, int + 1 == previous index

                    newArguments.append(("imm", len(self.lastState["imm"]) - 1))
                    
                elif type(arguments[i]) is self._registerObject:
                    newArguments.append((arguments[i].key, arguments[i].index))
                else:
                    newArguments.append(arguments[i])

            #logging.info(debugHelper(inspect.currentframe()) + "instruction immidiate processing: " + str(newArguments))

            instruction : Callable[[dict, dict, dict, dict, Any], None] = self._instructionSet[tree.token]
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
            #logging.info(debugHelper(inspect.currentframe()) + "case 2 empty")
            result = None
            if tree.token in self.engine["labels"]:
                #self.lastState["imm"].append(self.engine["labels"][tree.token])
                self.lastState["imm"][len(self.lastState["imm"])] = self.engine["labels"][tree.token] #the created 'index' of the key/index pair will always be an int == length, int + 1 == previous index
                
                result = self._registerObject("imm", len(self.lastState["imm"]) - 1)
            else:
                result = tree.token                
            return result

        elif tree.type == "container": #TODO this should not rely on the parser properly labeling Nodes
            '''Case 3
            tree is a container _evaluateNested on children
                if there is only one child, 'pass through' results
                else, return a tuple of results
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 3 container")
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
            tree is a register
                assumes a single child
                assumes child is index
            returns register object
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case 4 register")
            return self._registerObject(tree.token, self._evaluateNested(tree.child[0]))

        else:
            '''Case X
            similar to the container case, mainly just 'passes through' the result of a recursive call on children
            '''

            #logging.info(debugHelper(inspect.currentframe()) + "case x else")
            #logging.info(debugHelper(inspect.currentframe()) + "tree = \n" + str(tree))
            stack = []
            for i in tree.child:
                stack.append(self._evaluateNested(i))
            
            if len(stack) == 1:
                return stack[0]
            else:
                return tuple(stack)
        
    class compileDefault:
        """a working prototype, provides functions that take in an execution tree, and return a programs instruction list, memory array, etc"""

        def __init__(self, instructionSet, directives):
            self.instructionSet = instructionSet
            self.directives = directives

        def compileOld(self, oldState, config, executionTree : "Node") -> Tuple[List["Node"], List[int], Dict[str, int]]:
            #assumes the instruction array is register array "m"
            
            instructionArray : List["Node"] = [None for i in range(len(oldState["m"]))]
            memoryArray : List[int] = [0 for i in range(len(oldState["m"]))]
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

        def compile(self, config : dict, executionTree : "Node", parseLabels : Dict[str, "Node"]) -> Tuple[List["Node"], List[int], Dict[str, int]]:
            """Takes in in a dict containing the config information of registers, A node representing an execution tree, and parseLabels a dict (where key is the label, and value is a line number).
            Returns a list of Tree Nodes (representing each instruction), A list of ints (representing the program memory/binary), and a dictionary of labels (where each value corisponds to a memory index)

            config should contain only the config information of the registers the program is being loaded into
            executionTree should be a properly formated execution Node Tree, duh
            parseLabels should be of the form {Label : Node}, multiple Labels for the same line number is allowed
            """
            assert type(config) is dict
            #can't assert execution tree is type node because that's only available in the parser?
            assert type(parseLabels) is dict

            logging.debug(debugHelper(inspect.currentframe()) + "compile input ExecutionTree = \n" + str(executionTree))

            instructionArray : List["Node"] = []
            memoryArray : List[int] = []
            labels : Dict[str, int] = {} #Note: needs to handle multiple keys refering to the same value

            for i in range(len(executionTree.child)): #goes through program line by line
                tempInstruction = executionTree.child[i].copyDeep()

                tempArrayInstruction = [tempInstruction]
                tempArrayMemory = [0]

                #TODO check for directives should happen here

                #check for labels and associate with memory index (IE: the current len(instructionArray))
                for i in parseLabels.keys():
                    if parseLabels[i].lineNum == tempInstruction.lineNum:
                        labels[i] = len(instructionArray)

                #appends instruction word to memory
                assert len(tempArrayInstruction) == len(tempArrayMemory)
                for i in range(len(tempArrayInstruction)):
                    memoryArray.append(tempArrayMemory[i])
                    instructionArray.append(tempArrayInstruction[i])
                #TODO empty instructionArray indices should be filled with a function that raises an error if run? or a special value denoting an error if it is tried to be executed?

            return instructionArray, memoryArray, labels

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
            import timeit
            self.timer : "function" = lambda : timeit.default_timer()
            self.lastTime : int = 0

            self.animationDelay : int = animationDelay

            self.textRed : str = "\u001b[31m" #forground red, meant for register writes
            self.textTeal : str = "\u001b[96m" #forground teal, meant for register reads
            self.textGrey : str = "\u001b[90m" #forground grey
            self.ANSIend : str = "\u001b[0m" #resets ANSI colours

        def runtime(self, oldState : dict, newState : dict, config : dict, stats : dict = None, engine : dict = None):
            """Executed after every instruction/cycle. Accesses/takes in all information about the engine, takes control of the screen to print information.
            
            #TODO program counter does not take into account the config bitlength of the program counter"""
            
            screen : str = ""
            highlight : str = ""

            #The program counter
            lineOp : str = "0x" + hex(oldState['pc'][0])[2:].rjust(8, '0').upper() + "\t"
            #handles the 'instruction' line (IE: the first line)
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
            lineRequired += "    " + "PC".ljust(8, ' ') \
                + "[" + self.textGrey + "0x" + self.ANSIend + hex(oldState['pc'][0])[2:].rjust(config['pc'][0]['bitlength'] // 4, "0").upper() + "]" \
                + "\t" \
                + "[" + self.textGrey + "0x" + self.ANSIend + highlight + hex(newState['pc'][0])[2:].rjust(config['pc'][0]['bitlength'] // 4, "0").upper() + self.ANSIend + "]" \
                + "\n"
            for i in oldState['imm']: #handles the immidiate registers
                lineRequired += "    " + ("imm[" + str(i) + "]").ljust(8, " ") \
                    + "[" + self.textGrey + "0b" + self.ANSIend + self.textTeal + str(bin(oldState["imm"][i]))[2:].rjust(config["imm"][i]['bitlength'], "0") + self.ANSIend + "]" \
                    + "\n"
            for i in oldState["flag"].keys(): #handles the CPU flags
                highlight = self.textRed if (oldState["flag"][i] != newState["flag"][i]) else ""
                lineRequired += "    " + ("flag[" + str(i) + "]").ljust(16, " ") \
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
            if "imm" in keys:
                keys.remove("imm")

            for i in keys:
                for j in range(len(oldState[i])):
                    if config[i][j]['show'] == True:
                        highlight = ""

                        ''' #this highlights the registers containing instructions with grey, but doesn't make the display more readable... should be used for another display class
                        if engine["instructionArray"] != None and i == "m":
                            highlight = self.textGrey if not (engine["instructionArray"][j] is None) else ""
                        '''
                        highlight = self.textRed if (oldState[i][j] != newState[i][j]) else highlight

                        lineRegisters += "    " + (str(i) + "[" + str(j) + "]").ljust(8, " ") \
                            + "[" + self.textGrey + "0b" + self.ANSIend + str(bin(oldState[i][j]))[2:].rjust(config[i][j]['bitlength'], "0") + "]" \
                            + "\t" \
                            + "[" + self.textGrey + "0b" + self.ANSIend + highlight + str(bin(newState[i][j]))[2:].rjust(config[i][j]['bitlength'], "0") + self.ANSIend + "]" \
                            + "\n"

            screen += lineOp
            screen += lineRequired
            screen += lineRegisters

            print(screen)

            #the animation delay
            delay : float = (self.animationDelay - self.timer() + self.lastTime) if 0 < (self.animationDelay - self.timer() + self.lastTime) < self.animationDelay else 0
            self.sleep(delay)
            self.lastTime = self.timer()

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

    class DisplayInstruction:
        #TODO

        def __init__(self):
            import shutil #used to get the terminal window size

            #will return (80, 24) as a default if the terminal size is undefined
            self.getTerminalSize : function = lambda : (shutil.get_terminal_size()[0], shutil.get_terminal_size()[1])
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
                if type(lineNum) is int:
                    assert lineNum >= 0
                assert type(charNum) is int or charNum == None
                if type(charNum) is int:
                    assert charNum >= 0

                self.type : str = typeStr
                self.token : str = token
                self.child : list = []

                #relational references to other nodes
                self.parent : self.__class__ = None
                self.nodePrevious : self.__class__ = None
                self.nodeNext : self.__class__ = None

                #the line number of the string or character position in a line, will be needed for indentation awareness if it's ever needed
                self.lineNum : int = lineNum 
                self.charNum : int = charNum

            def append(self, node : "Node"):
                """Adds a new node object to self as a child (at end of list)"""
                assert type(node) is self.__class__

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
                """Creates a new node with all properties of current node including recursivly copying all children (but not relational data). Returns a node tree.
                
                Has the side effect of 'resetting' all relational links (parent, nodeNext, nodePrevious)"""
                
                newNode = self.__class__(self.type, self.token, self.lineNum, self.charNum)

                logging.debug(debugHelper(inspect.currentframe()) + "attempting to copyDeep node"+ "\n" + str((
                        self.type,
                        self.token,
                        self.lineNum,
                        self.charNum,
                        self.child))
                    )

                for i in range(len(self.child)):
                    newNode.append(self.child[i].copyDeep())
                return newNode

            def replace(self, oldNode : "Node", newNode : "Node"):
                """Takes in an oldNode that is child of self, and replaces it with newNode. Deletes oldNode"""
                assert type(oldNode) is self.__class__
                assert type(newNode) is self.__class__

                index = None
                for i in range(len(self.child)):
                    if self.child[i] is oldNode:
                        index = i
                
                if index == None:
                    raise Exception("oldNode not found, can not replace oldNode. oldNode = \n" + str(oldNode))

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

            def remove(self, node : "Node"):
                """Takes in a node that is a child of self, removes node. raises exception if node is not a child
                
                deletes references to other nodes from Node, recursively removes child nodes of Node using remove()
                This is to make it easier to the python garbage collecter to destroy it, because cyclic references"""
                assert type(node) is self.__class__

                index : int = None
                for i in range(len(self.child)):
                    if self.child[i] is node:
                        index = i

                if index == None:
                    raise Exception("node is not found, can not remove. node = \n" + str(node))

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

            def __repr__(self, depth : int = 1) -> str:
                """Recursivly composes a string representing the node hierarchy, returns a string.
                
                Called by print() to display the object"""
                assert type(depth) is int
                assert depth >= 1

                block : str = ""
                line : str = ""
                for i in range(depth):
                    line += "    "
                line += repr(self.token)
                line = line.ljust(40, " ")
                line += "\t:" + str(self.type).capitalize().ljust(8)
                line += "\t" + str(depth)

                line += "\t" + "lineNum=" + str(self.lineNum) + "\t" + "charNum=" + str(self.charNum)

                line += "\n"

                childLines : List[str] = [i.__repr__(depth+1) for i in self.child]
                block += line
                for i in childLines:
                    block += i

                return block
                
            def __eq__(self, other) -> bool:
                """A custom equals comparision. Takes in another object other, and compaires it to self.token. Returns True if equal, False otherwise"""
                logging.debug(debugHelper(inspect.currentframe()) + "Custom equals comparison")

                #return self.token == other
                if type(other) is self.__class__:
                    return self.token == other.token
                else:
                    return self.token == other

            def __ne__(self, other) -> bool:
                """A custom not equals comparision. Takes in another object other, and compaires it to self.token. Returns True if not equal, False otherwise"""
                logging.debug(debugHelper(inspect.currentframe()) + "Custom equals comparison")

                #return self.token != other
                if type(other) is self.__class__:
                    return self.token != other.token
                else:
                    return self.token != other

            #No longer needed since remove() cleans up enough recursivly for the python garbage collector to pick it up. This function might be useful for debugging purposes
            def __del__(self):
                """Decontructor, needed because the various inter-node references may make it harder for the python garbage collector to properly delete an entire tree.
                
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

        def _tokenize(self, code : str) -> List[Tuple[str, int, int]] :
            """Takes in a string of code, returns a list of tuples representing the code in the form of (string/tuple, line location, character location in line). 
            
            No characters are filtered out
            
            Case 1: "test\n\nHello World" =>
            [
                ('test',    0, 0),
                ('\n',      0, 0),
                ('\n',      1, 0),
                ('Hello',   2, 0),
                (' ',       2, 5),
                ('World',   2, 6)
            ]
            """
            assert type(code) is str
            assert len(code) > 0

            #done like this to easily add extra characters
            _isName : Callable[[str], bool] = lambda x : x.isalnum() or x in "_" #returns True is character can be in a name, False otherwise

            tokenList : List[Tuple[str, int, int]] = []
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
            """Takes in a Node Tree of depth 2, casts all children that are integers to integers (with labels). Returns a Node Tree of depth 2.

            Does not recurse #TODO should recruse

            Case: "123 456 789" =>
            Node
                '123'   |
                ' '
                '456'   |
                ' '
                '789'   |
            =>
            Node
                123     |
                ' '
                456     |
                ' '
                789     |
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
            """Takes in a Node Tree of depth 2, casts all children that are in hex format to integers (with labels). Returns a node tree of depth 2.

            Does not recurse #TODO should recurse

            Case: "0x0 0x000A 0xff" =>
            Node
                '0x0'       |
                ' '
                '0x000A'    |
                ' '
                '0xff'      |
            =>
            Node
                0           |
                ' '
                10          |
                ' '
                255         |
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if type(i.token) == str:
                    if i.token.startswith("0x") or i.token.startswith("0X"):
                        temp : self.Node = i.copyDeep()
                        temp.token = int(i.token, 16)
                        temp.type = "int"
                        root.append(temp)
                    else:
                        root.append(i.copyDeep())
                else:
                    root.append(i.copyDeep())

            return root

        def ruleRemoveEmptyLines(self, tree : Node) -> Node:
            """Takes in a Node Tree of depth 2. Removes all empty lines. Returns a Node Tree of depth 2.

            Does not recurse

            Case 1: "test\ntest\n\n\ntest\n" =>
            Node
                'test'
                '\n'
                'test'
                '\n'    |
                '\n'    |
                '\n'    |
                'test'
                '\n'
            Node
                'test'
                '\n'
                'test'
                '\n'    |
                'test'
                '\n'
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()

            stack : str = "\n"

            for i in tree.child:
                #if previous == "\n" and current == "\n" do nothing, else copy Node
                if i != "\n" or stack != "\n":
                    root.append(i.copyDeep())
                    stack = i.token

            return root

        def ruleRemoveLeadingWhitespace(self, tree : Node, whiteSpace : List[str] = [" ", "\t"]) -> Node:
            """Takes in a Node Tree of depth 2, removes all white space tokens between a new line token and the next token. Returns a Node Tree of depth 2.
            
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
            assert type(whiteSpace) is list
            assert all([len(i) == 1 for i in whiteSpace])

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
            """Takes in a Node Tree of depth 2, combines all the tokens that are contained by quote tokens into a string node. Returns a Node Tree of depth 2.
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
                raise Exception("Parse Error: Mismatched quotes")

            return root

        def ruleFilterLineComments(self, tree : Node, character : str = "#") -> Node:
            """Takes in a Node Tree of depth 2, removes any tokens between a "#" token and a new line token. Returns a Node Tree of depth 2.

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

        def ruleContainer(self, tree : Node, containers : Dict[str, str] = {"(":")", "[":"]", "{":"}"}, nodeType : str = "container") -> Node:
            """Takes in a Node Tree of depth 2, finds containers "([{}])" and rearranges nodes to form a tree respecting the containers. Returns a Node Tree of arbitrary depth.

            Containers are of the form {"opening bracket": "closing bracket", ...}
            Does not copy closing brackets
            Does not recurse
            
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
            stack : List[Tuple[str, self.Node]] = []

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

            if len(stack) != 0:
                raise Exception("Parse Error: mismatching brackets")

            return root

        def ruleFindLabels(self, tree : Node) -> Tuple[Node, Dict[str, Node]]:
            """Takes in a Node Tree of depth 2, attempts to find a label that is immidiatly followed by a ":", returns a Node Tree of depth 2, and a dictionary of labels
            
            Does not recurse"""
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()
            previous : str = "\n"
            skipToken : bool = False

            labels : Dict[str, self.Node] = {}

            for i in tree.child:
                if (i.nodePrevious == previous or i.nodePrevious == None) and i.nodeNext == ":":
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
            """Takes in a node tree, and a nameSpace. Labels all nodes that are in nameSpace as 'NameSpace'. Returns Node Tree of depth 2.
            
            Does not recurse
            #TODO find a better/less confusing name (conflicts with ruleFindLabels)?"""
            assert type(tree) is self.Node
            assert type(nameSpace) is dict
            assert type(tokenType) is str

            root : self.Node = tree.copyInfo()
            keys : List[str]= [i.lower() for i in nameSpace.keys()]

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
        
        def ruleRemoveToken(self, tree : Node, token : str, recurse : bool = True) -> Node:
            """Takes in a Node Tree of arbitrary depth, and a token. Removes all instances of token in tree.child. Returns a Node Tree of arbitrary depth.
            
            Case 1: token = '\n'
            Node
                'test1'
                '\n'
                'test2'
            =>
            Node
                'test1'
                'test2'

            Case 2: token = ','
            Node
                'add'
                    'arg1'
                    ','
                    'arg2'
                ','
                'mult'
                    'arg1'
                    ','
                    'arg2'
            =>
            Node
                'add'
                    'arg1'
                    'arg2'
                'mult'
                    'arg1'
                    'arg2'
            """
            assert type(tree) is self.Node
            
            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if i != token:
                    root.append(i.copyDeep())

            if recurse:
                newRoot : self.Node = tree.copyInfo()
                for i in root.child:
                    newRoot.append(self.ruleRemoveToken(i.copyDeep(), token, True))
                root = newRoot

            return root
        
        def ruleSplitLines(self, tree : Node, tokenType : str = "line", splitToken : str = "\n") -> List[Node]:
            """Takes in a Node Tree of arbitrary depth. Returns a list of Node Trees of arbitrary depth, split by the splitToken ("\n") with the splitToken ommited.
            
            #TODO should be able to recurse
            """
            assert type(tree) is self.Node
            assert type(tokenType) is str
            assert type(splitToken) is str

            result : List[self.Node] = []
            current : self.Node = self.Node(tokenType, None, 0, 0)

            for i in tree.child:
                if i == splitToken:
                    result.append(current)
                    current = self.Node(tokenType, None, 0, 0)
                else:
                    current.append(i.copyDeep())

            if len(current.child) >= 1:
                result.append(current)

            #Goes through all 'lines' and sets lineNum and charNum to the values of the first child Node in them
            for i in result:
                if len(i.child) != 0:
                    i.lineNum = i.child[0].lineNum
                    i.charNum = i.child[0].charNum

            return result

        def ruleSplitTokens(self, tree : Node, tokenType : str = "line", splitToken : str = "\n", recurse : bool = True) -> Node:
            """Takes in a Node Tree of arbitrary depth. Returns a Node Trees of arbitrary depth, split by the splitToken ("\n") with the splitToken ommited, and in containers.

            #TODO should be implemented more elegently

            Case 1: splitToken = "\n"
            Node
                'test'
                '\n'    #notice the splitToken '\n' is omitted
                'abc'
            =>
            Node
                None
                    'test'
                None
                    'abc' 

            Case 2: splitToken = ','
            Node
                'test1'
                'test2'
                    'abc1'
                    ','
                    'abc2'
                    ','
                    'abc3'
                    'abc4'
            =>
            Node
                'test1'
                'test2'
                    None
                        'abc1'
                    None
                        'abc2'
                    None
                        'abc3'
                        'abc4'
            
            Case 3: splitToken = ','
            Node
                'test1'
                    'abc1'
                    ','
                    'abc2'
                ','
                'test2'
            =>
            Node
                None
                    'test1'
                        None
                            'abc1'
                        None
                            'abc2'
                None
                    'test2'

            Case 4: splitToken = '\n'
            Node
                'test1'
                'test2'
                'test3'
            =>
            Node
                'test1'
                'test2'
                'test3'
            """
            assert type(tree) is self.Node
            assert type(tokenType) is str
            assert len(tokenType) > 0
            assert type(splitToken) is str
            assert len(splitToken) > 0
            assert type(recurse) is bool

            root : self.Node = tree.copyInfo()
            tokenFound : bool = False

            #checks if there is a splitToken in children
            for i in tree.child:
                if i == splitToken:
                    tokenFound = True

            if tokenFound:
                stack : List[self.Node] = []
                for i in tree.child:
                    if i == splitToken:
                        temp : self.Node = self.Node(tokenType, None, stack[0].lineNum, stack[0].charNum)
                        while len(stack) != 0:
                            temp.append(stack.pop(0))
                        root.append(temp)
                    else:
                        #stack.append(self.ruleSplitTokens(i.copyDeep(), tokenType, splitToken, recurse) if recurse else i.copyDeep())
                        temp : self.Node = None
                        if recurse:
                            temp = self.ruleSplitTokens(i.copyDeep(), tokenType, splitToken, recurse)
                        else:
                            temp = i.copyDeep()
                        stack.append(temp)

                if len(stack) != 0:
                    temp : self.Node = self.Node(tokenType, None, stack[0].lineNum, stack[0].charNum)
                    while len(stack) != 0:
                        temp.append(stack.pop(0))
                    root.append(temp)
                    
            else: #the splitToken not found case
                for i in tree.child:
                    temp : self.Node = None
                    if recurse:
                        temp = self.ruleSplitTokens(i.copyDeep(), tokenType, splitToken, recurse)
                    else:
                        temp = i.copyDeep()
                    root.append(temp)
            

            return root

        def ruleNestContainersIntoInstructions(self, tree : Node, nameSpace : dict, recurse : bool = True) -> Node:
            """Takes in a Node Tree of arbitrary depth, and a nameSpace dict represeting instructions, registers, etc. 
            If a container node follows a nameSpace node, make container node a child of the nameSpace node.
            Returns a Node Tree of arbitrary depth.

            Recurses by default            
            """
            assert type(tree) is self.Node
            assert type(nameSpace) is dict
            
            root : self.Node = tree.copyInfo()

            for i in tree.child:
                if i.type == "container":  
                    temp : self.Node = None
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

        def ruleLowerCase(self, tree : Node, recurse : bool = True) -> Node:
            """Takes in a Node Tree of arbitrary depth. Sets all tokens in the Node Tree's children as lower case. Recurses by default. Returns a Node Tree of arbitrary depth.
            
            Case 1:
            Node
                'HELLO'
                ' '
                'WORLD'
                    'test'
                    'ABC'
            =>
            Node
                'hello'
                ' '
                'world'
                    'test'
                    'abc'
            """
            assert type(tree) is self.Node

            root : self.Node = tree.copyInfo()
            for i in tree.child:
                temp : self.Node = i.copyDeep()
                if type(temp.token) is str:
                    temp.token = temp.token.lower()
                if recurse:
                    temp = self.ruleLowerCase(temp, True)
                root.append(temp)
            
            return root

        def ruleApplyAlias(self, tree : Node, alias : Dict[str, str]) -> Node:
            """Takes in a Node Tree of Depth 2. If a token is in alias, replaces that token, then tokenizes it. Returns a Node Tree of Depth 2.
            
            Case 1: alias = {'123': 'hello world'}
            Node
                'test'
                ' '
                '123'       |
                ' '
                'abc'
            =>
            Node
                'test'
                ' '
                'hello'     | #notice how the string 'hello world' was tokenized
                ' '         |
                'world'     |
                ' '
                'abc'
            
            Case 2: alias = {'abc' : '1 2 3'}
            Node
                'test'
                ' '
                'abc'       |
                    'hello' |
                    ' '     |
                    'world' |
                ' '
                'temp
            =>
            Node
                'test'
                ' '
                '1'         | #notice how the children of 'abc' was added to the first of the replacement nodes
                    'hello' |
                    ' '     |
                    'world' |
                ' '         |
                '2'         |
                ' '         |
                '3'         |
                ' '
                'temp'
            """
            assert type(tree) is self.Node
            assert type(alias) is dict
            assert all([type(i) is str for i in alias.keys()])
            assert all([type(i) is str for i in alias.values()])
            assert all([i != j for i, j in alias.items()])

            root : self.Node = tree.copyInfo()

            for i in tree.child:
                temp = []
                if type(i.token) is str and i.token in alias: #if alias token found, tokenize it's replacement string, and add that series of tokens to root
                    for j in self._tokenize(alias[i.token]):
                        temp.append(self.Node("token", j[0], i.lineNum, i.charNum))
                else:
                    temp.append(i.copyInfo())

                for j in i.child: #if alias token has children, add children to first token of the replacement tokens
                    temp[0].append(j.copyDeep)
                
                #append tokens to root
                for j in temp:
                    root.append(j)

            return root

        def ruleFilterBlockComments(self, tree : Node, character : dict = {}) -> Node:
            pass

        def ruleFindDirectives(self, tree : Node, directives : dict) -> Node:
            pass

        def parseCode(self, sourceCode : str) -> Tuple[Node, Dict[str, Node]]:
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
            root : self.Node = self.Node("root")
            for i in self._tokenize(sourceCode):
                root.append(self.Node("token", i[0], i[1], i[2]))

            logging.debug(debugHelper(inspect.currentframe()) + "this is the original code: " + "\n" + repr(sourceCode))
            logging.debug(debugHelper(inspect.currentframe()) + "tokenized code: " + "\n" + str(root))

            #Note: at this point, rules do operations on the Node Tree, but the depth of the Node Tree remains 2

            root = self.ruleFilterLineComments(root, "#")
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFilterLineComments: " + "\n" + str(root))

            root = self.ruleStringSimple(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleStringSimple: " + "\n" + str(root))

            root = self.ruleApplyAlias(root, self.alias)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleApplyAlias: " + "\n" + str(root))

            root = self.ruleLowerCase(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLowerCase: " + "\n" + str(root))            

            root = self.ruleRemoveLeadingWhitespace(root, [" ", "\t"])
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveLeadingWhitespace: " + "\n" + str(root))

            root = self.ruleRemoveEmptyLines(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveEmptyLines: " + "\n" + str(root))

            root, self.labels = self.ruleFindLabels(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFindLabels: " + "\n" + str(root) + "\nlabels: " + str(self.labels))
            i = 0
            while i < len(root.child): #removes the label nodes, as they don't need to be executed
                if root.child[i].type == "label":
                    root.remove(root.child[i])
                else:
                    i += 1
            
            root = self.ruleLabelNamespace(root, self.nameSpace)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLabelNamespace: " + "\n" + str(root))

            root = self.ruleRemoveToken(root, " ", False)
            root = self.ruleRemoveToken(root, "\t", False)
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

            temp : List[self.Node] = self.ruleSplitLines(root, "line", "\n")
            root = self.Node("root")
            for i in temp:
                root.append(i)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitLines: " + "\n" + str(root))

            #removes empty lines/empty line nodes
            i = 0
            while i < len(root.child):
                if len(root.child[i].child) == 0:
                    root.remove(root.child[i])
                else:
                    i += 1
            logging.debug(debugHelper(inspect.currentframe()) + "remove empty line nodes: " + "\n" + str(root))

            #root = self.ruleRemoveToken(root, ",") #TODO this needs to be replaced with a proper way to seperate arguments
            #logging.debug(debugHelper(inspect.currentframe()) + "remove commas #TODO: " + "\n" + str(root))

            root = self.ruleSplitTokens(root, "argument", ',', True)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitTokens: " + "\n" + str(root))

            return root, self.labels
            
    #==================================================================================================================

    class InstructionSetDefault:
        """A non-functional mockup of what an instructionset definition could look like
        
        Note: uses 'carry' flag, but doesn't need that flag to run. IE: will use 'carry' flag if present
        Note: instruction functions do not 'see' immediate values, they instead see an index of register 'imm' (IE: immediate values are filtered out before instructions are called)
        """

        def __init__(self):
            self.instructionSet : Dict[str, Callable[[dict, dict, dict, dict, "Arguments"], None]] = {
                "nop"   : self.opNop,
                "add"   : self.opAdd,
                "and"   : self.opAND,
                "or"    : self.opOR,
                "xor"   : self.opXOR,
                "jumpeq": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "==", pointer, a, b)),
                "jumpne": (lambda z1, z2, z3, z4,   pointer, a, b     : self.opJump(z1, z2, z3, z4,       "!=", pointer, a, b)),
                "jump"  : (lambda z1, z2, z3, z4,   pointer           : self.opJump(z1, z2, z3, z4,       "goto", pointer)),
                "shiftl": (lambda z1, z2, z3, z4,   des, a            : self.opShiftL(z1, z2, z3, z4,     des, a, 1)),
                "shiftr": (lambda z1, z2, z3, z4,   des, a            : self.opShiftR(z1, z2, z3, z4,     des, a, 1)),

                "halt"  : self.opHalt
            }

            self.stats : dict = {}

            self.directives : dict = {}

        def redirect(self, redirection : str, register : str, index : "str/int") -> Tuple[str, int]:
            """Takes in redirection as a pointer to the memory array to access, and a register index pair. Returns a key index pair corrispoding to redirection as key, index as value stored in register[index]"""
            assert type(redirection) is str
            assert type(register) is str
            assert type(index) is str or type(index) is int

            return (redirection, register[index])

        def enforceImm(self, registerTuple : Tuple[str, int]) -> Tuple[str, int]:
            """Takes in a register key index pair. Returns a register key index pair iff key is 'imm' for immediate. Raises an Exception otherwise
            
            #TODO should also be able to limit the size of the immediate value. IE: imm < 2**12"""
            assert type(registerTuple) is tuple and len(registerTuple) == 2 
            assert type(registerTuple[0]) is str and (type(registerTuple[0]) is int or type(registerTuple[0]) is str) 

            if registerTuple[0] != "imm":
                raise Exception("Expected immediate value, got register instead")
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
                if newState[des1][des2] >= 2**config[des1][des2]['bitlength']:
                    newState['flag']['carry'] = 1
            
            newState[des1][des2] = newState[des1][des2] & (2**config[des1][des2]['bitlength'] - 1)

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

            newState[des1][des2] = newState[des1][des2] & (2**config[des1][des2]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

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

            newState[des1][des2] = newState[des1][des2] & (2**config[des1][des2]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

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

            newState[des1][des2] = newState[des1][des2] & (2**config[des1][des2]['bitlength'] - 1) #'cuts down' the result to something that fits in the register/memory location

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

            newState[des1][des2] = newState[des1][des2] & (2**config[des1][des2]['bitlength'] - 1)

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

            amount : int = 0
            if type(n) is int:
                amount = n
            elif type(n) is tuple:
                amount = oldState[n[0]][n[1]]

            result = oldState[a1][a2]
            for i in range(amount):
                t1 : int = 0
                if arithmetic:
                    t1 = 2 ** (config[a1][a2]['bitlength'] - 1)
                    t1 = t1 & result
                result = result >> 1
                result = result | t1

            result : int = result & (2**config[des1][des2]['bitlength'] - 1)

            newState[des1][des2] = result
            newState['pc'][0] = oldState['pc'][0] + 1

        def opHalt(self, oldState, newState, config, engine):
            engine["run"] = False

        def dirString(self, config) -> List[int]:
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
        CPU.configAddRegister("pc", 32, 1) #explicidly set the Program Counter to 32-bit
        CPU.configAddRegister("x", 32, 32)
        #CPU.configAddRegister("m", 8, 2**16, show=False)
        CPU.configAddRegister("m", 8, 2**4, show=False)
        
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

    def postCycle(self, currentState : dict) -> Tuple[dict, dict]:
        """Takes in the currentState dict, returns a tuple containing the oldState dict, and the newState dict

        resets CPU Flags to zero (if there are CPU Flags)
        resets x0 to zero
        """
        assert type(currentState) is dict

        oldState = copy.deepcopy(currentState)
        newState = copy.deepcopy(currentState)
        
        oldState["x"][0] = 0 #resets x0 to zero

        for i in newState['flag'].keys():
            newState['flag'][i] = 0
        newState['imm'] = {}

        return (oldState, newState)

    class RiscVISA(CPUsim.InstructionSetDefault):
        def __init__(self):
            self.instructionSet : dict = {
                #arithmetic (add, add immidiate, subtract, load upper immediate, add upper immediate to PC)
                "add"   : self.opAdd,
                "addi"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opAdd(z1, z2, z3, z4,        des, a, self.enforceImm(imm))), #note: no enforcement of imm being an immediate value
                #"sub"   : None,
                #"lui"   : None,
                #"auipc" : None,

                #logical
                "xor"   : self.opXOR, 
                "xori"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opXOR(z1, z2, z3, z4,        des, a, self.enforceImm(imm))),
                "or"    : self.opOR,
                "ori"   : (lambda z1, z2, z3, z4,   des, a, imm     : self.opOR(z1, z2, z3, z4,         des, a, self.enforceImm(imm))),
                "and"   : self.opAND,
                "andi"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opAND(z1, z2, z3, z4,        des, a, self.enforceImm(imm))),

                #branch (equal, not equal, less than, greater or equal, less then unsigned, greater or equal unsigned)
                "beq"   : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "==", pointer, a, b)), 
                "bne"   : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "!=", pointer, a, b)), 
                #"blt"   : None, #opJump doesn't handle signed compairisons
                #"bge"   : None,  
                "bltu"  : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       "<", pointer, a, b)), 
                "bgeu"  : (lambda z1, z2, z3, z4,   a, b, pointer   : self.opJump(z1, z2, z3, z4,       ">=", pointer, a, b)), 

                #shifts (shift left, shilf left immediate, shift right, shift right immediate, shift right arithmetic, shift right arithmetic immediate)
                "sll"   : self.opShiftL,
                "slli"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftL(z1, z2, z3, z4,     des, a, self.enforceImm(imm))),
                "srl"   : self.opShiftR,
                "srli"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftR(z1, z2, z3, z4,     des, a, self.enforceImm(imm))),
                "sra"   : (lambda z1, z2, z3, z4,   des, a, n       : self.opShiftR(z1, z2, z3, z4,     des, a, n, True)),
                "srai"  : (lambda z1, z2, z3, z4,   des, a, imm     : self.opShiftR(z1, z2, z3, z4,     des, a, self.enforceImm(imm), True)),

                #compare (set less than, set less than immediate, set less that unsigned, set less that immediate unsigned)
                #"slt"   : None, #signed compairsons for opSetLessThen is not implimented
                #"slti"  : None,
                "sltu"  : (lambda z1, z2, z3, z4,   des, a, b       : self.opSetLessThan(z1, z2, z3, z4,     des, a, b, False)),
                "sltiu" : (lambda z1, z2, z3, z4,   des, a, imm     : self.opSetLessThan(z1, z2, z3, z4,     des, a, self.enforceImm(imm), False)),

                #jump and link
                #"jal"   : None,
                #"jalr"  : None,

                #load
                #"lb"    : None,
                #"lh"    : None,
                #"lw"    : None,
                #"lbu"   : None,
                #"lhu"   : None,

                #store
                #"sb"    : None,
                #"sh"    : None,
                #"sw"    : None

                #hotwired system call because I haven't figured out how to impliment system calls yet
                "halt"  : self.opHalt
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

        def parseCode(self, sourceCode : str) -> Tuple["Node", Dict[str, "Node"]]:
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
            root : self.Node = self.Node("root")
            for i in self._tokenize(sourceCode):
                root.append(self.Node("token", i[0], i[1], i[2]))

            logging.debug(debugHelper(inspect.currentframe()) + "this is the original code: " + "\n" + repr(sourceCode))
            logging.debug(debugHelper(inspect.currentframe()) + "tokenized code: " + "\n" + str(root))

            #Note: at this point, rules do operations on the Node Tree, but the depth of the Node Tree remains 2

            root = self.ruleFilterLineComments(root, "#")
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFilterLineComments: " + "\n" + str(root))

            root = self.ruleStringSimple(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleStringSimple: " + "\n" + str(root))

            root = self.ruleApplyAlias(root, self.alias)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleApplyAlias: " + "\n" + str(root))

            root = self.ruleLowerCase(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLowerCase: " + "\n" + str(root))            

            root = self.ruleRemoveLeadingWhitespace(root, [" ", "\t"])
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveLeadingWhitespace: " + "\n" + str(root))

            root = self.ruleRemoveEmptyLines(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleRemoveEmptyLines: " + "\n" + str(root))

            root, self.labels = self.ruleFindLabels(root)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleFindLabels: " + "\n" + str(root) + "\nlabels: " + str(self.labels))
            i = 0
            while i < len(root.child): #removes the label nodes, as they don't need to be executed
                if root.child[i].type == "label":
                    root.remove(root.child[i])
                else:
                    i += 1
            
            root = self.ruleLabelNamespace(root, self.nameSpace)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleLabelNamespace: " + "\n" + str(root))

            root = self.ruleRemoveToken(root, " ", False)
            root = self.ruleRemoveToken(root, "\t", False)
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

            temp : List[self.Node] = self.ruleSplitLines(root, "line", "\n")
            root = self.Node("root")
            for i in temp:
                root.append(i)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitLines: " + "\n" + str(root))

            #removes empty lines/empty line nodes
            i = 0
            while i < len(root.child):
                if len(root.child[i].child) == 0:
                    root.remove(root.child[i])
                else:
                    i += 1
            logging.debug(debugHelper(inspect.currentframe()) + "remove empty line nodes: " + "\n" + str(root))

            #root = self.ruleRemoveToken(root, ",") #TODO this needs to be replaced with a proper way to seperate arguments
            #logging.debug(debugHelper(inspect.currentframe()) + "remove commas #TODO: " + "\n" + str(root))

            temp = root.copyInfo()
            for i in root.child:
                temp.append(self.ruleContainerTokensFollowingInstruction(i, self.nameSpace))
            root = temp                            
            logging.debug(debugHelper(inspect.currentframe()) + "ruleContainerTokensFollowingInstruction: " + "\n" + str(root))

            root = self.ruleSplitTokens(root, "argument", ',', True)
            logging.debug(debugHelper(inspect.currentframe()) + "ruleSplitTokens: " + "\n" + str(root))

            return root, self.labels

        def ruleContainerTokensFollowingInstruction(self, tree : "Node", nameSpace : Dict[str, Any]) -> "Node":
            """Takes in a Node Tree of arbitrary depth, and a nameSpace dictionary. Returns a Node Tree of arbitrary depth.
            If an instruction token is found, all following tokens are made children of the instruction token.

            Case 0: nameSpace = {'add' : Any}
            Node
                'test'
                'add'       |
                '1'         |
                '2'         |
                '3'         |
            =>
            Node
                'test'
                'add'       |   #all the following tokens were appended to 'add'
                    '1'     |
                    '2'     |
                    '3'     |

            Case 1: nameSpace = {'add' : Any}
            Node
                'add'       |
                '\n'        |
                '1'         |
                '2'         |
                '3'         |
            =>
            Node
                'add'       |
                    '\n'    |   #note: newline is not respected
                    '1'     |
                    '2'     |
                    '3'     |
            """
            assert type(tree) is self.Node
            assert type(nameSpace) is dict

            root : self.Node = tree.copyInfo()
            instruction : self.Node = None

            for i in tree.child:
                if i.token in nameSpace and instruction is None:
                    instruction = i.copyDeep()
                elif not (instruction is None):
                    instruction.append(i.copyDeep())
                else:
                    root.append(i.copyDeep())

            if not(instruction is None):
                root.append(instruction)

            return root

def multiply2(a : int, b : int, bitlength : int = 8) -> int:
    """Takes in two unsigned integers, a, b -> returns an integer a*b

    bitlength is the size of the numbers/architecture, in bits

    This is a real world use case
    """
    assert type(a) is int
    assert type(b) is int
    assert type(bitlength) is int
    assert bitlength >= 1
    assert 0 <= a < 2**bitlength
    assert 0 <= b < 2**bitlength

    #configure memory
    t = [0 for j in range(2)]
    r = [0 for i in range(2)]
    
    t[0] = a
    r[0] = b

    #A python algorithm that multiplies two numbers together
    while(r[0] != 0):
        r[1] = r[0] & 1
        if r[1] == 1:
            t[1] = t[0] + t[1]
        t[0] = t[0] << 1
        r[0] = r[0] >> 1
        
    resultPython = t[1]

    #the same algorithm, but using a generic assembly like algorithm
    ALU = CPUsim(bitlength) #bitlength
    ALU.configSetDisplay(ALU.DisplaySimpleAndClean(0))

    #configure memory
    ALU.configAddRegister('r', bitlength, 2) #namespace symbol, bitlength, register amount #will overwrite defaults
    ALU.configAddRegister('m', bitlength, 8, show=False) #the program is loaded into here
    ALU.configAddRegister('t', bitlength * 2, 2) #note that the register bitlength is double the input register size

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
    #loads arguments into correct registers
    ALU.inject(key='t', index=0, value=a)
    ALU.inject(key='r', index=0, value=b)
    ALU.run()
    resultALU = ALU.extract(key='t', index=1)

    #sanity check
    assert resultALU == a * b
    assert resultPython == a * b
    
    return resultALU

if __name__ == "__main__":
    #set up debugging
    logging.basicConfig(level = logging.INFO)
    debugHighlight = lambda x : 1350 <= x <= 1500

    result = multiply2(7, 3)
    print("multiply 7 * 3 =>".ljust(32, " ") + str(result) + "\t" + str(result == 7 * 3))
    print("===========================================================================================================")
    
    temp = RiscV() #a couple hundred lines of setup discribing (part of) a RiscV CPU
    CPU = temp.CPU
    CPU.configSetDisplay(CPU.DisplaySimpleAndClean(0))
    """
    CPU.linkAndLoad('''
                        addi    a2, zero, 8
                loop:   addi    a1, a1, 1
                        bne     a1, a2, loop
                        halt
                    ''')
    """
    CPU.linkAndLoad('''
                    # Multiplies two number together using shift and add
                    # Inputs: a0 (x10), a2 (x12)
                    # Outputs: a3 (x13)
                    # [register mappping from other program]: r0 => a0 (x10), r1 => a1 (x11), t0 => a2 (x12), t1 => a3 (x13)
                    loop:   beq     a0, 0, end          #note: the destination pointer is the third argument, where in the previous example it was the first argument
                            andi    a1, a0, 1
                            bne     a1, 1, temp
                            add     a3, a2, a3
                    temp:   slli    a2, a2, 1           #can't use zero as a label, it's a register (x0)
                            srli    a0, a0, 1
                            beq     zero, zero, loop    #a psudoinstruction for an unconditional jump
                    end:    halt                        #this is a jurry-rigged instruction for 'halt' because I haven't figured out how to implement system calls yet
                    ''')
    CPU.inject('x', 10, 7)
    CPU.inject('x', 12, 3)
    CPU.run()

    
