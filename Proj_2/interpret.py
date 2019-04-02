#!/usr/bin/env python3

import sys
import re
import xml.etree.ElementTree as ET
from enum import Enum
import codecs

# arrays of all opcodes divided according to the number of operands
non_arg = ["CREATEFRAME", "PUSHFRAME", "POPFRAME" , "RETURN", "BREAK"]
non_arg = non_arg + ["CLEARS", "ADDS", "SUBS", "MULS", "IDIVS", "LTS", "GTS", "EQS", "ANDS", "ORS", "NOTS", "INT2CHARS", "STRI2INTS"]

one_arg = ["DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT", "JUMPIFEQS", "JUMPIFNEQS"]

two_arg = ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT"]

three_arg = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]

# parses input arguments
class Arguments:
    # initializes the arguments
    def __init__(self, arguments):
        # help argument
        if("--help" in arguments):
            if(len(arguments) == 1):
                self.print_help()
                sys.exit(0)
            else:
                sys.stderr.write("--help cannot be combined with other arguments\n")
                sys.exit(10)

        # sets booleans for input arguments
        self.source = False
        self.input = False
        self.stats = False
        self.stats_arg = []


        # iterate through all arguments
        for arg in arguments:
            if("--source=" in arg):
                if(self.source):    # check for multiple input of the same arguments
                    sys.stderr.write("Same argument was entered twice\n")
                    sys.exit(10)
                self.source = True
                self.source_file = self.parse_path(arg)
            elif("--input=" in arg):
                if(self.input):     # check for multiple input of the same arguments
                    sys.stderr.write("Same argument was entered twice\n")
                    sys.exit(10)
                self.input = True
                self.input_file = self.parse_path(arg)
            elif("--stats=" in arg):
                if(self.stats):     # check for multiple input of the same arguments
                    sys.stderr.write("Same argument was entered twice\n")
                    sys.exit(10)
                self.stats = True
                self.stats_file = self.parse_path(arg)
            elif("--insts" == arg or "--vars" == arg):
                if(arg in self.stats_arg):  # check for multiple input of the same arguments
                    sys.stderr.write("Same argument was entered twice\n")
                    sys.exit(10)
                self.stats_arg.append(arg)
            else:
                sys.stderr.write("Invalid arguments\n")
                sys.exit(10)


        # at least one file must be given
        if(self.source == False and self.input == False):
            sys.stderr.write("At least one file is needed\n")
            sys.exit(10)

        # stats were not entered but it's arguments were given
        if(self.stats == False and len(self.stats_arg) != 0):
            sys.stderr.write("File for stats is required\n")
            sys.exit(10)

        # stats were entered, but without any arguments
        if(self.stats == True and len(self.stats_arg) == 0):
            sys.stderr.write("Statistics need at least one paremeter from these: --insts --vars\n")
            sys.exit(10)

    # gets path
    def parse_path(self, path):
        new_path = re.search(r'(?<==).*', path)
        return new_path.group(0)

    # prints help
    def print_help(self):
        sys.stdout.write("Script is run as: python3.6 interpret.py\n")
        sys.stdout.write("With possible arguments:\n")
        sys.stdout.write("--help : prints help\n")
        sys.stdout.write("--source=file : sets the path to the XML representation of source file\n")
        sys.stdout.write("--input=file : sets path to the file that contains input for interpretation\n")
        sys.stdout.write("At least one file must be given\n")

# carries out all checks for particular operand
class Operand:
    # initializes operand
    def __init__(self, instruction):
        # get current type of operand
        try:
            self.type = instruction.attrib['type']
        except:
            sys.stderr.write("Missing type attribute\n")
            sys.exit(52)

        # parse arguments
        # type is variable
        if(self.type == "var"):
            try:    # check all arguments for variable
                if("@" in instruction.text):
                    self.frame = self.get_frame(instruction.text)
                    self.name = self.get_name(instruction.text)
                    self.check_name(self.name)
                    self.value = None
                else:
                    sys.stderr.write("Missing @ in variable name\n")
                    sys.exit(52)
            except:
                sys.stderr.write("Invalid variable\n")
                sys.exit(52)
        else:       # everything else
            if(self.type == "string"):
                if(instruction.text != None):
                    if "#" in instruction.text:
                        sys.stderr.write("Invalid character\n")
                        sys.exit(32)
            if(self.type == "type" or self.type == "bool" or self.type == "nil" or self.type == "int" or self.type == "string" or self.type == "label"):
                try:
                    self.value = instruction.text
                    self.frame = None
                    self.name = None
                except:
                    sys.stderr.write("Invalid instruction operand\n")
                    sys.exit(52)
            else:
                sys.stderr.write("Invalid XML format\n")
                sys.exit(32)

    # gets the frame
    def get_frame(self, name):  # TODO - try excep - both
        nam = re.search(r'.*(?=@)', name)
        return nam.group(0)

    # gets the name
    def get_name(self, name):
        frame = re.search(r'(?<=@).*', name)
        return frame.group(0)
    
    # check name
    def check_name(self, name):
        i = 0
        possible_chars = ["_", "-", "$", "&", "%", "*", "!", "?"]
        for char in name:
            if(char.isalpha()):
                i = i + 1
                continue
            elif(char.isdigit()):
                if(i == 0):
                    sys.stderr.write("Name cannot start with number\n")
                    sys.exit(32)
                i = i + 1
                continue
            elif(char in possible_chars):
                i = i + 1
                continue
            else:
                sys.stderr.write("Invalid name\n")
                sys.exit(32)
                

# does all the interpreting
class Interpret:
    # initializes all necessary arguments
    def __init__(self):
        # parse arguments
        self.arg = Arguments(sys.argv[1:])

        # set the input file
        if(self.arg.input):
            self.arg.i_f = open(self.arg.input_file, "r")
        else:
            self.arg.i_f = sys.stdin
            
        # set the source file
        if(self.arg.source):
            self.arg.s_f = open(self.arg.source, "r")
            try:
                tree = ET.parse(self.arg.source_file)
            except:
                sys.stderr.write("Invalid XML format\n")
                sys.exit(31)
        else:
            try:
                tree = ET.parse(sys.stdin)
            except:
                sys.stderr.write("Invalid XML format\n")
                sys.exit(31)

        # try to parse the language attribute
        try:
            root = tree.getroot()
            language = root.attrib['language']
        except:
            sys.stderr.write("Invalid XML format\n")
            sys.exit(31)

        if(language != "IPPcode19"):
            sys.stderr.write("Invalid language\n")
            sys.exit(32)

        # basic variables for frames and labels
        self.global_frame = {}
        self.local_frames = []
        self.data_stack = []
        self.labels = {}
        self.root = root
        self.call_stack = []
        self.can_miss_value = True

        # statistics variables
        self.insts = 0
        self.vars = 0
        

    # prepares labels and their respective order number
    def prepare_labels(self):
        try:
            for i in range(0, len(self.root)):
                if(self.root[i].attrib['opcode'] == "LABEL"):
                    for child in self.root[i]:
                        if(child.text in self.labels):
                            sys.stderr.write("Redefinition of label\n")
                            sys.exit(52)
                        self.labels.update({child.text : int(self.root[i].attrib['order'])})
        except:
            sys.stderr.write("Invalid XML file\n")
            sys.exit(32)

    # checks whether integer value is really integer
    def check_number(self, number):
        for i in range(0, len(number)):
            if(number[i] != '-' and not str.isdigit(number[i])):
                sys.stderr.write("Value is not integer\n")
                sys.exit(32)
        return int(number)

    # formats the value 
    def format_value(self, value, value_type):
        if(value_type == "int"):    # integer
            return self.check_number(value)
        elif(value_type == "bool"): # bool
            if(value == "true"):
                return True
            elif(value == "false"):
                return False
            else:
                sys.stderr.write("Value is not bool\n")
                sys.exit(32)
        elif(value_type == "string"):   # normal string
            if(isinstance(value_type, str)):
                return value
            else:
                sys.stderr.write("Value is not string\n")
                sys.exit(32)
        elif(value_type == "label"):
            return value
        elif(value_type == "type"):
            return value
        elif(value_type == "nil"):
            return value
        else:                           # error
            sys.stderr.write("Invalid value type\n")
            sys.exit(52)

    # gets value of argument
    def get_argument_value(self, argument):
        if(argument.type == "var"): # variable is checked according to the frames
            if(argument.frame == "GF"): # global frame
                try:
                    value = self.global_frame[argument.name]
                except:
                    sys.stderr.write("Variable in given frame doesn't exist\n")
                    sys.exit(54)
            elif(argument.frame == "LF"):   # local frame
                if(len(self.local_frames) == 0):    # check how many local frames we have
                    sys.stderr.write("Frame that doesn't exist\n")
                    sys.exit(55)
                try:
                    value = self.local_frames[len(self.local_frames)-1][argument.name]
                except:
                    sys.stderr.write("Variable in given frame doesn't exist\n")
                    sys.exit(54)
            elif(argument.frame == "TF"):   # temporary frame
                try:
                    self.temporary_frame
                except:
                    sys.stderr.write("Frame doesn't exist\n")
                    sys.exit(55)

                if(argument.name not in self.temporary_frame.keys()):
                    sys.stderr.write("Variable doesn't exist\n")
                    sys.exit(54)
                else:
                        value = self.temporary_frame[argument.name]
            else:
                sys.stderr.write("Inalid frame type")
                sys.exit(32)

            if(self.can_miss_value):
                if(value == None):
                    sys.stderr.write("Missing value\n")
                    sys.exit(56)
            return value
        else:                               # return the formatted value
            return self.format_value(argument.value, argument.type)

    
    # insert value to given frame
    def insert_to_frame(self, name, target_frame, value):
        if(target_frame == "GF"):   # check for target frame
            if(name in self.global_frame.keys()):
                self.global_frame[name] = value
            else:
                self.global_frame.update({name : value})
        elif(target_frame == "LF"): # check for target frame
            if(len(self.local_frames) == 0):
                sys.stderr.write("Missing frame\n")
                sys.exit(55)
            else:
                if(name in self.local_frames[len(self.local_frames) - 1].keys()):
                    self.local_frames[len(self.local_frames) - 1][name] = value
                else:
                    self.local_frames[len(self.local_frames) - 1].update({name : value})
        elif(target_frame == "TF"): # check for target frame
            try:
                if(name in self.temporary_frame.keys()):
                    self.temporary_frame[name] = value
                else:
                    self.temporary_frame.update({name : value})
            except:
                sys.exit(55)
        else:   # this is not a frame
            sys.stderr.write("Invalid frame\n")
            sys.exit(32)

    # TODO DELELTE
    def debug_print(self):
        print("")
        print(self.counter)
        print("Data stack " + str(self.data_stack))
        print("Global " + str(self.global_frame))
        print("Local " + str(self.local_frames))
        try:
            print("Temporary " + str(self.temporary_frame))
        except:
            pass
        print("")

    # starts with interpreting
    def start(self):
        self.counter = 1
        self.order = {}
        
        # prepare xml correct order
        cnt = 0
        for i in self.root:
            num = int(i.attrib['order'])
            if(num in self.order.keys()):
                sys.stderr.write("Multiple instruction order number\n")
                sys.exit(32)
            self.order.update({num : cnt})
            cnt = cnt + 1

        #print("These are my variables")
        #print(self.order)
        #print(self.labels)
        #print("")

        # execute instruction
        while self.counter < (len(self.root) + 1):
            try:
                current_instruction = self.order[self.counter]
            except:
                sys.stderr.write("Invalid instruction order number\n")
                sys.exit(32)
            #print("I will execute instruction with op_num " + str(current_instruction))
            self.execute_instruction(current_instruction)

        # close the files
        if(self.arg.input):
            self.arg.i_f.close()

        if(self.arg.source):
            self.arg.s_f.close()

        # output the statistics if needed
        if(self.arg.stats):
            stat_file = open(self.arg.stats_file, "w")
            if(len(self.arg.stats_arg) == 1):
                if("--insts" == self.arg.stats_arg[0]): # we have only insts
                    stat_file.write(str(self.insts) + '\n')
                else:                                   # we have only vars
                    stat_file.write(str(self.vars) + '\n')
            else:
                if("--insts" == self.arg.stats_arg[0]): # first is insts
                    stat_file.write(str(self.insts) + '\n')
                    stat_file.write(str(self.vars) + '\n')
                else:                                   # first is vars
                    stat_file.write(str(self.vars) + '\n')
                    stat_file.write(str(self.insts) + '\n')

            stat_file.close()

    # checks existence of variable
    def check_variable_existence(self, arg):
        if(arg.frame == "GF"):                             # check for existence of variable
            if(arg.name not in self.global_frame):
                sys.stderr.write("Variable doesn't exist\n")
                sys.exit(54)
        elif(arg.frame == "TF"):
            try:
                self.temporary_frame
            except:
                sys.stderr.write("Frame doesn't exist\n")
                sys.exit(55)
            if(arg.name not in self.temporary_frame.keys()):
                sys.stderr.write("Variable doesn't exist\n")
                sys.exit(54)
        elif(arg.frame == "LF"):
            if(len(self.local_frames) == 0):
                sys.stderr.write("Missing frame\n")
                sys.exit(55)
            else:
                if(arg.name not in self.local_frames[len(self.local_frames) - 1].keys()):
                    sys.stderr.write("Variable doesn't exist\n")
                    sys.exit(54)


    # executes each instruction
    def execute_instruction(self, op_num):
        # get the current opcode
        try:
            current_opcode = self.root[op_num].attrib['opcode']
            current_opcode = current_opcode.upper()
        except:
            sys.stderr.write("Invalid XML format\n")
            sys.exit(32)

        #print("This is opcode no " + str(self.counter) + " instruction: " + current_opcode)
        #print("Call stack is " + str(self.call_stack))

        # prepare args #
        if(current_opcode in non_arg):
            # too many arguments
            if(len(self.root[op_num].findall("arg1")) != 0):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
        # one argument
        elif(current_opcode in one_arg):
            try:
                # get arguments
                first_arg = self.root[op_num].findall("arg1")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            # too many arguments
            if(len(self.root[op_num].findall("arg1")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            arg1 = Operand(first_arg)
        # two arguments
        elif(current_opcode in two_arg):
            try:
                # get arguments
                first_arg = self.root[op_num].findall("arg1")[0]
                second_arg = self.root[op_num].findall("arg2")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            # too many arguments
            if(len(self.root[op_num].findall("arg1")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            if(len(self.root[op_num].findall("arg2")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            arg1 = Operand(first_arg)
            arg2 = Operand(second_arg)
        # three arguments
        elif(current_opcode in three_arg):
            try:
                # get arguments
                first_arg = self.root[op_num].findall("arg1")[0]
                second_arg = self.root[op_num].findall("arg2")[0]
                third_arg = self.root[op_num].findall("arg3")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            # too many arguments
            if(len(self.root[op_num].findall("arg1")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            if(len(self.root[op_num].findall("arg2")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            if(len(self.root[op_num].findall("arg3")) != 1):
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(32)
            arg1 = Operand(first_arg)
            arg2 = Operand(second_arg)
            arg3 = Operand(third_arg)
        else:
            sys.exit(32)

        # CREATEFRAME
        if(current_opcode == "CREATEFRAME"):    # creates frame and increments counter
            self.temporary_frame = {}
            self.counter = self.counter + 1
        # PUSHFRAME
        elif(current_opcode == "PUSHFRAME"):    # tries to push frame if exists, if not, error
            try:
                self.local_frames.append(self.temporary_frame)
                del self.temporary_frame
            except:
                sys.stderr.write("Temporary frame doesn't exist\n")
                sys.exit(55)
            self.counter = self.counter + 1
        # POPFRAME
        elif(current_opcode == "POPFRAME"):     # pops frame from the local frame stack if it exists
            if(len(self.local_frames) == 0):
                sys.stderr.write("No frame to pop\n")
                sys.exit(55)
            else:   # delete top part
                self.temporary_frame = (self.local_frames[len(self.local_frames) - 1]).copy()
                del self.local_frames[len(self.local_frames) - 1]
            self.counter = self.counter + 1
        # DEFVAR <var>
        elif(current_opcode == "DEFVAR"):
            self.insert_to_frame(arg1.name, arg1.frame, None)   # define variable
            self.counter = self.counter + 1
        # MOVE <var> <symb>
        elif(current_opcode == "MOVE"):
            if(arg2.type == "label"):   # cannot move label
                sys.stderr.write("Label cannot be moved into variable\n")
                sys.exit(32)
            self.check_variable_existence(arg1)
            if(arg2.type == "var"):
                self.check_variable_existence(arg2)

            value = self.get_argument_value(arg2)               # copy value
            if(arg2.type == "var"):
                self.check_variable_existence(arg2)
            self.insert_to_frame(arg1.name, arg1.frame, value)
            self.counter = self.counter + 1
        # PUSHS <symb>
        elif(current_opcode == "PUSHS"):
            if(arg1.type == "label"):   # cannot move label
                sys.stderr.write("Label cannot be pushed into variable\n")
                sys.exit(32)
            value = self.get_argument_value(arg1)               # push value to data sack
            self.data_stack.append(value)
            self.counter = self.counter + 1
        # POPS <var>
        elif(current_opcode == "POPS"):                         # pops value from stack if it can and saves it to variables
            if(len(self.data_stack) == 0):
                sys.stderr.write("Missing value on data stack\n")
                sys.exit(56)
            value = self.data_stack[len(self.data_stack) - 1]
            del self.data_stack[len(self.data_stack) - 1]
            self.check_variable_existence(arg1)
            self.insert_to_frame(arg1.name, arg1.frame, value)
            self.counter = self.counter + 1
        # ADD <var> <symb> <symb>
        elif(current_opcode == "ADD"):                          # adds 2 operands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):  # we can only add 2 integers
                result = int(value_1 + value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result) # save the result
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # SUB <var> <symb> <symb>
        elif(current_opcode == "SUB"):                      # subtracts 2 operands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):  # we can only subtract 2 integers
                result = int(value_1 - value_2)                     # save the result
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # MUL <var> <symb> <symb>
        elif(current_opcode == "MUL"):                      # multiplies 2 oeprands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):  # it can only be 2 integers
                result = int(value_1 * value_2)                     # save the result
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # IDIV <var> <symb> <symb>
        elif(current_opcode == "IDIV"):                                 # we divide one operand by the other
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):  # it can only be 2 integers
                if(value_2 == 0):
                    sys.stderr.write("Zero division\n")
                    sys.exit(57)
                result = int(int(value_1) / int(value_2))                 # save and round the result
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # LT <var> <symb> <symb>
        elif(current_opcode == "LT"):                       # carries out 'less than' operation for 2 operands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(type(value_1) != type(value_2)):
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1<value_2                    # save the result
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # GT <var> <symb> <symb>
        elif(current_opcode == "GT"):                       # carries out 'greater than' operation for 2 operands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(type(value_1) != type(value_2)):
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1>value_2                    # save the result
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # EQ <var> <symb> <symb>
        elif(current_opcode == "EQ"):                       # carries out 'equal' operation for 2 operands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(value_1 != "nil" and value_2 != "nil"):
                if(type(value_1) != type(value_2)):             # we can only compare 2 same types
                    sys.stderr.write("Invalid operand types\n")
                    sys.exit(53)
            else:
                if(value_1 == "nil"):
                    value_1 = None
                if(value_2 == "nil"):
                    value_2 = None

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str) or value_1 == None):
                result = value_1 == value_2
            else:
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # INT2CHAR <var> <symb>
        elif(current_opcode == "INT2CHAR"):                 # converts unicode (integer) to char
            value_1 = self.get_argument_value(arg2)
            self.check_variable_existence(arg1)

            if(arg2.type == "var"):                         # either variable with int
                if(type(value_1) != int):
                    sys.stderr.write("Invalid operand types\n")
                    sys.exit(53)
            elif(arg2.type != "int"):                       # or explicitly int
                sys.stderr.write("Invalid operand types\n")
                sys.exit(53)

            try:
                new_char = chr(value_1)
            except:
                sys.stderr.write("Invalid work with string\n")
                sys.exit(58)
            self.insert_to_frame(arg1.name, arg1.frame, new_char)
            self.counter = self.counter + 1
        # STRI2INT <var> <symb> <symb>
        elif(current_opcode == "STRI2INT"):                 # get ordinal unicode (integer) number of a character from string at certain index
            string_value = self.get_argument_value(arg2)
            index = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(isinstance(string_value, str) and isinstance(index, int)):   # first must be string, second one integer
                try:
                    value = ord(string_value[index])
                except:
                    sys.stderr.write("Invalid work with string\n")
                    sys.exit(58)
                self.insert_to_frame(arg1.name, arg1.frame, value)
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # CONCAT <var> <symb> <symb>
        elif(current_opcode == "CONCAT"):                   # concatenates 2 strings
            self.can_miss_value = False
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.can_miss_value = True
            self.check_variable_existence(arg1)

            if(arg2.type == "var"):
                self.check_variable_existence(arg2)
                if(value_1 == None):
                    sys.stderr.write("Invalid work with strings\n")
                    sys.exit(56)

            if(arg3.type == "var"):
                self.check_variable_existence(arg3)
                if(value_2 == None):
                    sys.stderr.write("Invalid work with strings\n")
                    sys.exit(56)

            if(isinstance(value_1, str) and isinstance(value_2, str)):  # both must be string to begin with
                new_string = value_1 + value_2
            elif(value_1 == None and isinstance(value_2, str)):         # it can also be empty
                new_string = value_2
            elif(value_2 == None and isinstance(value_1, str)):
                new_string = value_1
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, new_string)
            self.counter = self.counter + 1
        # STRLEN <var> <symb>
        elif(current_opcode == "STRLEN"):                   # get length of the string and saves it into a variable
            string = self.get_argument_value(arg2)
            self.check_variable_existence(arg1)

            if(isinstance(string, str)):                    # it must be string
                string = self.replace_decimal_escapes(string)
                length = len(string)
            elif(string == None):
                length = 0
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, length)
            self.counter = self.counter + 1
        # GETCHAR <var> <symb> <symb>
        elif(current_opcode == "GETCHAR"):                  # get character from specific index of a string
            string = self.get_argument_value(arg2)
            index = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(isinstance(string, str) and isinstance(index, int)): # one must be string, the other one is integer
                try:
                    char = string[index]
                except:
                    sys.stderr.write("Invalid work with string\n")
                    sys.exit(58)
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, char)
            self.counter = self.counter + 1
        # SETCHAR <var> <symb> <symb>
        elif(current_opcode == "SETCHAR"):              # sets certain character of a string to given character
            self.check_variable_existence(arg1)
            self.can_miss_value = False
            string = self.get_argument_value(arg1)
            index = self.get_argument_value(arg2)
            char = self.get_argument_value(arg3)
            self.can_miss_value = True

            if(string == None or index == None or char == None):
                sys.stderr.write("Invalid work with string\n")
                sys.exit(58)

            if(type(index) != int):                     # index must be a number
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)

            if(isinstance(string, str) and string != None):     # check for correct types and their values
                if(isinstance(char, str) and char != ""):
                    try:
                        char = char[0]
                        string = list(string)
                        string[index] = char
                        string = "".join(string)
                    except:
                        sys.stderr.write("Invalid work with string\n")
                        sys.exit(58)
                else:
                    sys.stderr.write("Mismatch of types\n")
                    sys.exit(53)
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, string)
            self.counter = self.counter + 1
        # TYPE <var> <symb>
        elif(current_opcode == "TYPE"):                 # gets type of a variables or constant and saves it to variable
            self.check_variable_existence(arg1)
            variable = self.get_argument_value(arg2)
            if(type(variable) is int):
                self.insert_to_frame(arg1.name, arg1.frame, "int")
            elif(type(variable) is str):
                if(variable == "nil"):
                    self.insert_to_frame(arg1.name, arg1.frame, "nil")
                else:
                    self.insert_to_frame(arg1.name, arg1.frame, "string")
            elif(type(variable) is bool):
                self.insert_to_frame(arg1.name, arg1.frame, "bool")
            elif(variable == None):
                self.insert_to_frame(arg1.name, arg1.frame, "nil")
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # DPRINT <symb>
        elif(current_opcode == "DPRINT"):           # debug print
            exit_code = self.get_argument_value(arg1)
            sys.stderr.write(exit_code)
        # BREAK
        elif(current_opcode == "BREAK"):            # writes current information 
            sys.stderr.write("Currently carrying out " + str(op_num) + ". instruction\n")
            sys.stderr.write("Global frame contains " + str(self.global_frame) + "\n")
            sys.stderr.write("There is/are " + str(len(self.local_frames)) + " local frames\n")
            if(len(self.local_frames) != 0):
                sys.stderr.write("Top local frame contains " + str(self.local_frames[len(self.local_frames) - 1]) + "\n")
            try:
                sys.stderr.write("Temporary frame contains " + str(self.temporary_frame) + "\n")
            except:
                sys.stderr.write("Temporary frame doesn't exist\n")
            self.counter = self.counter + 1
        # EXIT <symb>
        elif(current_opcode == "EXIT"):         # exits with given exit code
            exit_code = int(self.get_argument_value(arg1))
            if(arg1.type == "int" or arg1.type == "var"):             # type must be integer
                if(exit_code >=0 and exit_code <= 49):
                    sys.exit(exit_code)
                else:
                    sys.stderr.write("Invalid exit code\n")
                    sys.exit(57)
            else:
                sys.stderr.write("Invalid type of exit code\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # JUMP <label>
        elif(current_opcode == "JUMP"):         # gets jump destination and changes counter to it
            label = self.get_argument_value(arg1)
            try:
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            except:
                sys.stderr.write("Invalid jump destination\n")
                sys.exit(52)

        # LABEL <label>
        elif(current_opcode == "LABEL"):
            self.counter = self.counter + 1 # just changes the counter because the labels are already saved
        # JUMPIFEQ <label> <symb> <symb>
        elif(current_opcode == "JUMPIFEQ"):
            label = self.get_argument_value(arg1)
            self.can_miss_value = False
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.can_miss_value = True

            if(value_1 != "nil" and value_2 != "nil"):
                if(type(value_1) != type(value_2)): # must be the same type
                    sys.stderr.write("Mismatch of types\n")
                    sys.exit(53)
            else:
                if(value_1 == "nil"):
                    value_1 = None
                if(value_2 == "nil"):
                    value_2 = None
            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str) or value_1 == None):
                if(value_1 == value_2):             # must be the same value to jump
                    jump_destination = self.labels[label]
                    self.counter = int(jump_destination)
                else:
                    self.counter = self.counter + 1
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
        # JUMPIFNEQ <label> <symb> <symb>
        elif(current_opcode == "JUMPIFNEQ"):
            label = self.get_argument_value(arg1)
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)): # must be the same type
                sys.exit(53)

            if(value_1 != value_2):             # must be different value to jump
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1
        # WRITE <symb>
        elif(current_opcode == "WRITE"):
            value = self.get_argument_value(arg1)
            if(type(value) == bool):
                if(value == True):
                    value = "true"
                else:
                    value = "false"
            value = str(value)              # replaces string escapes and prints it out
            value = self.replace_decimal_escapes(value)
            print(value, end='', flush=True)
            self.counter = self.counter + 1
        # CALL <label>
        elif(current_opcode == "CALL"):         # calls certain value
            label = self.get_argument_value(arg1)
            if(type(label) == int):
                sys.stderr.write("Invalid call type\n")
                sys.exit(32)
            try:
                jump_destination = self.labels[label]
                self.call_stack.append(self.counter + 1)  # when you come back, jump right after label
                #print("My jump destination is " + str(jump_destination))
                self.counter = jump_destination
                
            except:
                sys.stderr.write("Invalid call\n")
                sys.exit(52)
        # RETURN
        elif(current_opcode == "RETURN"):
            try:
                self.counter = self.call_stack[len(self.call_stack) - 1]    # gets new destination where to return
                del self.call_stack[-1]
            except:
                sys.stderr.write("Missing return destination\n")
                sys.exit(56)
        # AND <var> <symb> <symb>
        elif(current_opcode == "AND"):          # carries out operation AND for 2 oeprands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(type(value_1) == bool and type(value_2) == bool):
                result = (value_1 and value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # OR <var> <symb> <symb>
        elif(current_opcode == "OR"):           # carries out operation OR for 2 oeprands
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            self.check_variable_existence(arg1)

            if(type(value_1) == bool and type(value_2) == bool):
                result = (value_1 or value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # NOT <var> <symb>
        elif(current_opcode == "NOT"):      # carries out operation NOT for 1 operand
            value_1 = self.get_argument_value(arg2)
            self.check_variable_existence(arg1)

            if(type(value_1) == bool):
                result = not value_1
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # READ <var> <type>
        elif(current_opcode == "READ"):
            self.check_variable_existence(arg1)
            
            if(self.arg.input):         # gets input from file
                line = self.arg.i_f.readline()
                try:
                    if(line[len(line) - 1] == '\n'):
                        line = line[:-1]
                    if(arg2.value == "bool"):
                        line = line.lower()
                        if(line == "true"):
                            line = True
                        elif(line == "false"):
                            line = False
                        else:
                            line = False
                    elif(arg2.value == "int"):
                        line = self.check_number(line)
                    elif(arg2.value == "string"):
                        if(isinstance(line, str)):
                            pass
                        else:
                            line = ""
                    elif(arg2.value == "nil"):
                        sys.stderr.write("Invalid XML file\n")
                        sys.exit(32)
                    else:
                        sys.stderr.write("Invalid operand types\n")
                        sys.exit(53)
                except:
                    if(arg2.value == "bool"):
                        line = False
                    elif(arg2.value == "int"):
                        line = 0
                    elif(arg2.value == "string"):
                        line = ""
                    elif(arg2.value == "nil"):
                        sys.stderr.write("Invalid XML file\n")
                        sys.exit(32)
                    else:
                        sys.stderr.write("Invalid operand types\n")
                        sys.exit(53)
            else:                   # gets input form the user
                line = input()
                if(arg2.value == "bool"):
                    line = line.lower()
                    if(line == "true"):
                        line = True
                    elif(line == "false"):
                        line = False
                    else:
                        line = False
                elif(arg2.value == "int"):
                    if(line.isdigit()):
                        line = int(line)
                    else:
                        line = 0
                elif(arg2.value == "string"):
                    if(isinstance(line, str)):
                        pass
                    else:
                        line = ""
                elif(arg2.value == "nil"):
                    sys.stderr.write("Invalid XML file\n")
                    sys.exit(32)
                else:
                    sys.stderr.write("Invalid operand types\n")
                    sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, line)
            self.counter = self.counter + 1
        #
        #       STACK FUNCTIONS
        # 
        # CLEARS
        elif(current_opcode == "CLEARS"):
            self.data_stack = []            # clears the data stack
            self.counter = self.counter + 1
        # ADDS
        elif(current_opcode == "ADDS"):     # adds 2 integers from data stack
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]

            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            addition = first_op + second_op
            self.remove_from_stack(2)
            self.data_stack.append(addition)    # push it to data stack
            self.counter = self.counter + 1
        # SUBS
        elif(current_opcode == "SUBS"):     # subtracts 2 integers from data stack
            self.chceck_available_data_stack(2)
            second_op = self.data_stack[len(self.data_stack) - 1]
            first_op = self.data_stack[len(self.data_stack) - 2]
            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            subtraction = first_op - second_op
            self.remove_from_stack(2)
            self.data_stack.append(subtraction) # push it to data stack
            self.counter = self.counter + 1
        # MULS
        elif(current_opcode == "MULS"):     # multiply 2 integers from data stack
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            if(type(first_op) == bool or type(second_op) == bool):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            multiplication = first_op * second_op
            self.remove_from_stack(2)
            self.data_stack.append(multiplication)  # push it to data stack
            self.counter = self.counter + 1
        # IDIVS
        elif(current_opcode == "IDIVS"):    # divides 2 integers from data stack
            self.chceck_available_data_stack(2)
            second_op = self.data_stack[len(self.data_stack) - 1]
            first_op = self.data_stack[len(self.data_stack) - 2]
            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            if(second_op == 0):             # check for zero division
                sys.stderr.write("Zero division\n")
                sys.exit(57)
            division = int(first_op / second_op)
            self.remove_from_stack(2)
            self.data_stack.append(division)    # push it to data stack
            self.counter = self.counter + 1
        # LTS
        elif(current_opcode == "LTS"):  # carries out 'less than' operation for 2 operands on data stack
            self.chceck_available_data_stack(2)
            second_op = self.data_stack[len(self.data_stack) - 1]
            first_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str)):
                self.data_stack.append(first_op < second_op)    # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # GTS
        elif(current_opcode == "GTS"):  # carries out 'greater than' operation for 2 operands on data stack
            self.chceck_available_data_stack(2)
            second_op = self.data_stack[len(self.data_stack) - 1]
            first_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str)):
                self.data_stack.append(first_op > second_op)    # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # EQS
        elif(current_opcode == "EQS"):  # carries out 'equal' operation for 2 operands on data stack
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)

            if(first_op != "nil" and second_op != "nil"):
                if(type(first_op) != type(second_op)):
                    sys.stderr.write("Invalid operand types\n")
                    sys.exit(53)
            else:
                if(first_op == "nil"):
                    first_op = None
                if(second_op == "nil"):
                    second_op = None

            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str) or first_op == None):
                self.data_stack.append(first_op == second_op)   # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # ANDS
        elif(current_opcode == "ANDS"): # carries out 'equal' operation for 2 operands on data stack
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) == bool and type(second_op) == bool):
                self.data_stack.append(first_op and second_op)  # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # ORS
        elif(current_opcode == "ORS"): # carries out 'or' operation for 2 operands on data stack
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) == bool and type(second_op) == bool):
                self.data_stack.append(first_op or second_op)   # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # NOTS
        elif(current_opcode == "NOTS"): # carries out 'or' operation for 1 operand on data stack
            self.chceck_available_data_stack(1)
            first_op = self.data_stack[len(self.data_stack) - 1]
            self.remove_from_stack(1)
            if(type(first_op) == bool):
                self.data_stack.append(not first_op)    # push it to data stack
            else:
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            self.counter = self.counter + 1
        # INT2CHARS
        elif(current_opcode == "INT2CHARS"):    # convert integer to character on data stack
            self.chceck_available_data_stack(1)
            first_op = self.data_stack[len(self.data_stack) - 1]
            self.remove_from_stack(1)
            try:
                self.data_stack.append(chr(first_op))
            except:
                sys.stderr.write("Invalid types\n")
                sys.exit(58)
            self.counter = self.counter + 1
        # STRI2INTS
        elif(current_opcode == "STRI2INTS"):    # converts character of string at certain index to integer
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(isinstance(second_op, str) and isinstance(first_op, int)):
                try:
                    self.data_stack.append(ord(second_op[first_op]))
                except:
                    sys.stderr.write("Index out of bounds\n")
                    sys.exit(58)
            else:
                sys.stderr.write("Type mismatch\n")
                sys.exit(53)

            self.counter = self.counter + 1
        # JUMPIFEQS
        elif(current_opcode == "JUMPIFEQS"):    # jumps to given label if 2 top values at data stack are equal
            label = self.get_argument_value(arg1)
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)

            if(first_op != "nil" and second_op != "nil"):
                if(type(first_op) != type(second_op)):
                    sys.stderr.write("Invalid types\n")
                    sys.exit(53)
            else:
                if(first_op == "nil"):
                    first_op = None
                if(second_op == "nil"):
                    second_op = None

            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str) or first_op == None):
                if(first_op == second_op):
                    jump_destination = self.labels[label]       # choose the jump destination
                    self.counter = int(jump_destination)
                else:
                    self.counter = self.counter + 1
            else:
                sys.stderr.write("Mismatch of types\n")
                sys.exit(53)
        # JUMPIFNEQS
        elif(current_opcode == "JUMPIFNEQS"):   # jumps to given label if 2 top values at data stack are not equal
            label = self.get_argument_value(arg1)
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            if(first_op != second_op):
                jump_destination = self.labels[label]       # choose the jump destination
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1

        # statistics for instructions that were carried out
        if(self.arg.stats and "--insts" in self.arg.stats_arg):
            self.insts = self.insts + 1

        # statistics for total number of defined variables
        if(self.arg.stats and "--vars" in self.arg.stats_arg):
            self.calculate_defined_variables()
        #self.debug_print()

    # calculates the maximum number of defined variables
    def calculate_defined_variables(self):
        total_sum = 0

        # look in global frames
        for key in self.global_frame:
            if(self.global_frame[key] != None):
                total_sum = total_sum + 1

        # look in global frames
        for i in range(0, len(self.local_frames)):
            for key in self.local_frames[i]:
                if(self.local_frames[i][key] != None):
                    total_sum = total_sum + 1

        # look in temporary frames
        try:
            for key in self.temporary_frame:
                if(self.temporary_frame[key] != None):
                    total_sum = total_sum + 1
        except:
            pass

        if(total_sum > self.vars):
            self.vars = total_sum

    # checks whether there is enough arguments pushed onto stack
    def chceck_available_data_stack(self, number):
        if(len(self.data_stack) < number):
            sys.stderr.write("Not enough data on data stack\n")
            sys.exit(56)

    # removes given number of parameters from stack
    def remove_from_stack(self, number):
        for dummy in range(0, number):
            del self.data_stack[len(self.data_stack) - 1]

    # replaces decimal escape sequences
    def replace_decimal_escapes(self, s):
        return re.sub(
        r"\\(\d\d\d)",
        lambda x: chr(int(x.group(1), 10)), 
        s
    )
            
# starts interpret, prepares labels
def main():  
    my_interpret = Interpret()
    my_interpret.prepare_labels()
    my_interpret.start()
    

# calls the main function
if __name__ == '__main__':
    main()
