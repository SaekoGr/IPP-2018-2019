#!/usr/bin/env python3

import sys
import re
import xml.etree.ElementTree as ET
from enum import Enum
from unidecode import unidecode
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

        self.source = False
        self.input = False
        self.stats = False
        self.stats_arg = []

        for arg in arguments:
            if("--source=" in arg):
                self.source = True
                self.source_file = self.parse_path(arg)
            elif("--input=" in arg):
                self.input = True
                self.input_file = self.parse_path(arg)
            elif("--stats=" in arg):
                self.stats = True
                self.stats_file = self.parse_path(arg)
            elif("--insts" == arg or "--vars" == arg):
                self.stats_arg.append(arg)
            else:
                sys.stderr.write("Invalid arguments\n")
                sys.exit(10)

        if(self.source == False and self.input == False):
            sys.stderr.write("At least one file is needed\n")
            sys.exit(10)

        if(self.stats == False and len(self.stats_arg) != 0):
            sys.stderr.write("File for stats is required\n")
            sys.exit(10)

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
        
        try:
            self.type = instruction.attrib['type']
        except:
            sys.stderr.write("Missing type attribute\n")
            sys.exit(52)

        
        if(self.type == "var"):
            try:
                if("@" in instruction.text):
                    self.frame = self.get_frame(instruction.text)
                    self.name = self.get_name(instruction.text)
                    self.check_variable_name(self.name)
                    self.value = None
                else:
                    sys.stderr.write("Missing @ in variable name\n")
                    sys.exit(52)
            except:
                sys.stderr.write("Invalid variable\n")
                sys.exit(52)
        else:
            try:
                self.value = instruction.text
                self.frame = None
                self.name = None
            except:
                sys.exit(52)

    #
    def get_frame(self, name):  # TODO - try excep - both
        nam = re.search(r'.*(?=@)', name)
        return nam.group(0)

    #
    def get_name(self, name):
        frame = re.search(r'(?<=@).*', name)
        return frame.group(0)
    
    #
    def check_variable_name(self, name):
        i = 0
        possible_chars = ["_", "-", "$", "&", "%", "*", "!", "?"]
        for char in name:
            if(char.isalpha()):
                i = i + 1
                continue
            elif(char.isdigit()):
                if(i == 0):
                    sys.stderr.write("Variable name cannot start with number\n")
                    sys.exit(32)
                i = i + 1
                continue
            elif(char in possible_chars):
                i = i + 1
                continue
            else:
                sys.stderr.write("Invalid variable name\n")
                sys.exit(32)
                

#
class Interpret:
    #
    def __init__(self):
        # parse arguments
        self.arg = Arguments(sys.argv[1:])

        if(self.arg.input):
            self.arg.i_f = open(self.arg.input_file, "r")
        else:
            self.arg.i_f = sys.stdin
            

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

        try:
            root = tree.getroot()
            if(root.attrib['language'] != "IPPcode19"):
                sys.stderr.write("Invalid language\n")
                sys.exit(52)
        except:
            sys.exit(31)

        self.global_frame = {}
        self.local_frames = []
        self.data_stack = []
        self.labels = {}
        self.root = root
        self.call_stack = []
        # statistics variables
        self.insts = 0
        self.vars = 0
        

    #
    def prepare_labels(self):
        try:
            for i in range(0, len(self.root)):
                if(self.root[i].attrib['opcode'] == "LABEL"):
                    for child in self.root[i]:
                        if(child.text in self.labels):
                            sys.exit(52)
                        self.labels.update({child.text : self.root[i].attrib['order']})
        except:
            sys.exit(32)

    #
    def format_value(self, value, value_type):
        if(value_type == "int"):
            if(str.isdigit(value)):
                return int(value)
            else:
                sys.exit(32)
        elif(value_type == "bool"):
            if(value == "true"):
                return True
            elif(value == "false"):
                return False
            else:
                sys.exit(32)
        elif(value_type == "string"):
            if(isinstance(value_type, str)):
                return value
            else:
                sys.exit(32)
        elif(value_type == "label"):
            return value
        elif(value_type == "type"):
            return value
        elif(value_type == "nil"):
            return value
        else:
            sys.stderr.write("Invalid value type\n")
            sys.exit(52)

    #
    def get_argument_value(self, argument):
        if(argument.type == "var"):
            if(argument.frame == "GF"):
                try:
                    value = self.global_frame[argument.name]
                except:
                    sys.exit(54)
            elif(argument.frame == "LF"):
                try:
                    value = self.local_frames[len(self.local_frames)-1][argument.name]
                except:
                    sys.exit(55)
            elif(argument.frame == "TF"):
                try:
                    value = self.temporary_frame[argument.name]
                except:
                    sys.exit(55)
            else:
                sys.exit(32)

            if(value == None):
                sys.exit(56)
            return value
        else:
            return self.format_value(argument.value, argument.type)

    
    # insert value to given frame
    def insert_to_frame(self, name, target_frame, value):
        if(target_frame == "GF"):
            if(name in self.global_frame.keys()):
                self.global_frame[name] = value
            else:
                self.global_frame.update({name : value})
        elif(target_frame == "LF"):
            if(len(self.local_frames) == 0):
                sys.exit(55)
            else:
                if(name in self.local_frames[len(self.local_frames) - 1].keys()):
                    self.local_frames[len(self.local_frames) - 1][name] = value
                else:
                    self.local_frames[len(self.local_frames) - 1].update({name : value})
        elif(target_frame == "TF"):
            try:
                if(name in self.temporary_frame.keys()):
                    self.temporary_frame[name] = value
                else:
                    self.temporary_frame.update({name : value})
            except:
                sys.exit(55)
        else:
            sys.stderr.write("Invalid frame\n")
            sys.exit(23)

    #
    def debug_print(self):
        print("")
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

        # execute instruction
        while self.counter < (len(self.root) + 1):
            try:
                current_instruction = self.order[self.counter]
            except:
                sys.stderr.write("Invalid instruction order number\n")
                sys.exit(32)
            self.execute_instruction(current_instruction)

        # close the files
        if(self.arg.input):
            self.arg.i_f.close()

        if(self.arg.source):
            self.arg.s_f.close()

        if(self.arg.stats):
            stat_file = open(self.arg.stats_file, "w")
            if(len(self.arg.stats_arg) == 1):
                if("--insts" == self.arg.stats_arg[0]):
                    stat_file.write(str(self.insts) + '\n')
                else:
                    stat_file.write(str(self.vars) + '\n')
            else:
                if("--insts" == self.arg.stats_arg[0]):
                    stat_file.write(str(self.insts) + '\n')
                    stat_file.write(str(self.vars) + '\n')
                else:
                    stat_file.write(str(self.vars) + '\n')
                    stat_file.write(str(self.insts) + '\n')

            stat_file.close()



    # executes each instruction
    def execute_instruction(self, op_num):
        try:
            current_opcode = self.root[op_num].attrib['opcode']
        except:
            sys.exit(32)

        # prepare args #
        if(current_opcode in non_arg):
            pass
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
        if(current_opcode == "CREATEFRAME"):
            self.temporary_frame = {}
            self.counter = self.counter + 1
        # PUSHFRAME
        elif(current_opcode == "PUSHFRAME"):
            try:
                self.local_frames.append(self.temporary_frame)
                del self.temporary_frame
            except:
                sys.exit(55)
            self.counter = self.counter + 1
        # POPFRAME
        elif(current_opcode == "POPFRAME"):
            if(len(self.local_frames) == 0):
                sys.exit(55)
            else:
                self.temporary_frame = (self.local_frames[len(self.local_frames) - 1]).copy()
                del self.local_frames[len(self.local_frames) - 1]
            self.counter = self.counter + 1
        # DEFVAR <var>
        elif(current_opcode == "DEFVAR"):
            self.insert_to_frame(arg1.name, arg1.frame, None)
            self.counter = self.counter + 1
        # MOVE <var> <symb>
        elif(current_opcode == "MOVE"):
            value = self.get_argument_value(arg2)
            self.insert_to_frame(arg1.name, arg1.frame, value)
            self.counter = self.counter + 1
        # PUSHS <symb>
        elif(current_opcode == "PUSHS"):
            value = self.get_argument_value(arg1)
            self.data_stack.append(value)
            self.counter = self.counter + 1
        # POPS <var>
        elif(current_opcode == "POPS"):
            if(len(self.data_stack) == 0):
                sys.exit(56)
            value = self.data_stack[len(self.data_stack) - 1]
            del self.data_stack[len(self.data_stack) - 1]
            self.insert_to_frame(arg1.name, arg1.frame, value)
            self.counter = self.counter + 1
        # ADD <var> <symb> <symb>
        elif(current_opcode == "ADD"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):
                result = int(value_1 + value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # SUB <var> <symb> <symb>
        elif(current_opcode == "SUB"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):
                result = int(value_1 - value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # MUL <var> <symb> <symb>
        elif(current_opcode == "MUL"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):
                result = int(value_1 * value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # IDIV <var> <symb> <symb>
        elif(current_opcode == "IDIV"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(isinstance(value_1, bool) or isinstance(value_2, bool)):
                sys.exit(53)

            if(isinstance(value_1, int) and isinstance(value_2, int)):
                if(value_2 == 0):
                    sys.exit(57)
                result = int(value_1 / value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # LT <var> <symb> <symb>
        elif(current_opcode == "LT"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                sys.exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1<value_2
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # GT <var> <symb> <symb>
        elif(current_opcode == "GT"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                sys.exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1>value_2
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # EQ <var> <symb> <symb>
        elif(current_opcode == "EQ"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                sys.exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str) or isinstance(value_1, None)):
                result = value_1 == value_2
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # INT2CHAR <var> <symb>
        elif(current_opcode == "INT2CHAR"):
            value_1 = self.get_argument_value(arg2)
            try:
                new_char = chr(value_1)
            except:
                sys.exit(58)
            self.insert_to_frame(arg1.name, arg1.frame, new_char)
            self.counter = self.counter + 1
        # STRI2INT <var> <symb> <symb>
        elif(current_opcode == "STRI2INT"):
            string_value = self.get_argument_value(arg2)
            index = self.get_argument_value(arg3)
            if(isinstance(string_value, str) and isinstance(index, int)):
                try:
                    value = ord(string_value[index])
                except:
                    sys.exit(58)
                self.insert_to_frame(arg1.name, arg1.frame, value)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # CONCAT <var> <symb> <symb>
        elif(current_opcode == "CONCAT"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            print(value_1, value_2)
            if(isinstance(value_1, str) and isinstance(value_2, str)):
                new_string = value_1 + value_2
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, new_string)
            self.counter = self.counter + 1
        # STRLEN <var> <symb>
        elif(current_opcode == "STRLEN"):
            string = self.get_argument_value(arg2)
            if(isinstance(string, str)):
                length = len(string)
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, length)
            self.counter = self.counter + 1
        # GETCHAR <var> <symb> <symb>
        elif(current_opcode == "GETCHAR"):
            string = self.get_argument_value(arg2)
            index = self.get_argument_value(arg3)
            if(isinstance(string, str) and isinstance(index, int)):
                try:
                    char = string[index]
                except:
                    sys.exit(58)
            else:
                sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, char)
            self.counter = self.counter + 1
        # SETCHAR <var> <symb> <symb>
        elif(current_opcode == "SETCHAR"):
            string = self.get_argument_value(arg1)
            index = self.get_argument_value(arg2)
            char = self.get_argument_value(arg3)
            if(isinstance(string, str) and string != None):
                if(isinstance(char, str) and char != ""):
                    try:
                        char = char[0]
                        string = list(string)
                        string[index] = char
                        string = "".join(string)
                    except:
                        sys.exit(58)
                else:
                    sys.exit(58)
            else:
                sys.exit(58)
            self.insert_to_frame(arg1.name, arg1.frame, string)
            self.counter = self.counter + 1
        # TYPE <var> <symb>
        elif(current_opcode == "TYPE"):
            variable = self.get_argument_value(arg2)
            if(type(variable) is int):
                self.insert_to_frame(arg1.name, arg1.frame, "int")
            elif(type(variable) is str):
                self.insert_to_frame(arg1.name, arg1.frame, "string")
            elif(type(variable) is bool):
                self.insert_to_frame(arg1.name, arg1.frame, "bool")
            elif(variable == None):
                self.insert_to_frame(arg1.name, arg1.frame, "nil")
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # DPRINT <symb>
        elif(current_opcode == "DPRINT"):
            exit_code = self.get_argument_value(arg1)
            sys.stderr.write(exit_code)
        # BREAK
        elif(current_opcode == "BREAK"):
            sys.stderr.write("Currently carrying out " + str(op_num + 1) + ". instruction\n")
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
        elif(current_opcode == "EXIT"):
            exit_code = self.get_argument_value(arg1)
            if(exit_code >=0 and exit_code <= 49):
                sys.exit(exit_code)
            else:
                sys.exit(57)
            self.counter = self.counter + 1
        # JUMP <label>
        elif(current_opcode == "JUMP"):
            label = self.get_argument_value(arg1)
            try:
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            except:
                sys.exit(52)

        # LABEL <label>
        elif(current_opcode == "LABEL"):
            self.counter = self.counter + 1
        # JUMPIFEQ <label> <symb> <symb>
        elif(current_opcode == "JUMPIFEQ"):
            label = self.get_argument_value(arg1)
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                sys.exit(53)

            if(value_1 == value_2):
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1
        # JUMPIFNEQ <label> <symb> <symb>
        elif(current_opcode == "JUMPIFNEQ"):
            label = self.get_argument_value(arg1)
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                sys.exit(53)

            if(value_1 != value_2):
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1
        # WRITE <symb>
        elif(current_opcode == "WRITE"):
            value = self.get_argument_value(arg1)
            if(type(value) == bool):
                pass            # TODO
            else:
                value = str(value)
                try:
                    value = self.replace_decimal_escapes(value)
                except:
                    pass
                print(value, end='', flush=True)
            self.counter = self.counter + 1
        # CALL <label>
        elif(current_opcode == "CALL"):
            label = self.get_argument_value(arg1)
            try:
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
                self.call_stack.append(op_num + 1)
            except:
                sys.exit(52)
        # RETURN
        elif(current_opcode == "RETURN"):
            try:
                self.counter = self.call_stack[len(self.call_stack) - 1]
                del self.call_stack[-1]
            except:
                sys.exit(56)
        # AND <var> <symb> <symb>
        elif(current_opcode == "AND"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(type(value_1) == bool and type(value_2) == bool):
                result = (value_1 and value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # OR <var> <symb> <symb>
        elif(current_opcode == "OR"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)
            if(type(value_1) == bool and type(value_2) == bool):
                result = (value_1 or value_2)
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # NOT <var> <symb>
        elif(current_opcode == "NOT"):
            value_1 = self.get_argument_value(arg2)
            if(type(value_1) == bool):
                result = not value_1
                self.insert_to_frame(arg1.name, arg1.frame, result)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # READ <var> <type>
        elif(current_opcode == "READ"):
            if(self.arg.input):
                line = self.arg.i_f.readline()
                try:
                    if(line[len(line) - 1] == '\n'):
                        line = line[:-1]
                    line = input()
                    if(arg2.value == "bool"):
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
                    else:
                        sys.exit(53)
                except:
                    if(arg2.value == "bool"):
                        line = False
                    elif(arg2.value == "int"):
                        line = 0
                    elif(arg2.value == "string"):
                        line = ""
                    else:
                        sys.exit(53)
            else:
                line = input()
                if(arg2.value == "bool"):
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
                else:
                    sys.exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, line)
            self.counter = self.counter + 1
        #
        #       STACK FUNCTIONS
        # 
        # CLEARS
        elif(current_opcode == "CLEARS"):
            self.data_stack = []
            self.counter = self.counter + 1
        # ADDS
        elif(current_opcode == "ADDS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]

            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            addition = first_op + second_op
            self.remove_from_stack(2)
            self.data_stack.append(addition)
            self.counter = self.counter + 1
        # SUBS
        elif(current_opcode == "SUBS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)

            subtraction = first_op - second_op
            self.remove_from_stack(2)
            self.data_stack.append(subtraction)
            self.counter = self.counter + 1
        # MULS
        elif(current_opcode == "MULS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            multiplication = first_op * second_op
            self.remove_from_stack(2)
            self.data_stack.append(multiplication)
            self.counter = self.counter + 1
        # IDIVS
        elif(current_opcode == "IDIVS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            if((not isinstance(first_op, int)) or (not isinstance(second_op, int))):
                sys.stderr.write("Invalid types\n")
                sys.exit(53)
            
            if(second_op == 0):
                sys.stderr.write("Zero division\n")
                sys.exit(57)
            division = int(first_op / second_op)
            self.remove_from_stack(2)
            self.data_stack.append(division)
            self.counter = self.counter + 1
        # LTS
        elif(current_opcode == "LTS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str)):
                self.data_stack.append(first_op < second_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # GTS
        elif(current_opcode == "GTS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str)):
                self.data_stack.append(first_op > second_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # EQS
        elif(current_opcode == "EQS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(isinstance(first_op, int) or isinstance(first_op, bool) or isinstance(first_op, str) or isinstance(first_op, None)):
                self.data_stack.append(first_op == second_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # ANDS
        elif(current_opcode == "ANDS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) == bool and type(second_op) == bool):
                self.data_stack.append(first_op and second_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # ORS
        elif(current_opcode == "ORS"):
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) == bool and type(second_op) == bool):
                self.data_stack.append(first_op or second_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # NOTS
        elif(current_opcode == "NOTS"):
            self.chceck_available_data_stack(1)
            first_op = self.data_stack[len(self.data_stack) - 1]
            self.remove_from_stack(1)
            if(type(first_op) == bool):
                self.data_stack.append(not first_op)
            else:
                sys.exit(53)
            self.counter = self.counter + 1
        # INT2CHARS
        elif(current_opcode == "INT2CHARS"):
            self.chceck_available_data_stack(1)
            first_op = self.data_stack[len(self.data_stack) - 1]
            self.remove_from_stack(1)
            try:
                self.data_stack.append(chr(first_op))
            except:
                sys.exit(58)
            self.counter = self.counter + 1
        # STRI2INTS
        elif(current_opcode == "STRI2INTS"):
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
        elif(current_opcode == "JUMPIFEQS"):
            label = self.get_argument_value(arg1)
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(first_op == second_op):
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1
        # JUMPIFNEQS
        elif(current_opcode == "JUMPIFNEQS"):
            label = self.get_argument_value(arg1)
            self.chceck_available_data_stack(2)
            first_op = self.data_stack[len(self.data_stack) - 1]
            second_op = self.data_stack[len(self.data_stack) - 2]
            self.remove_from_stack(2)
            if(type(first_op) != type(second_op)):
                sys.exit(53)
            if(first_op != second_op):
                jump_destination = self.labels[label]
                self.counter = int(jump_destination)
            else:
                self.counter = self.counter + 1

        
        if(self.arg.stats and "--insts" in self.arg.stats_arg):
            self.insts = self.insts + 1

        if(self.arg.stats and "--vars" in self.arg.stats_arg):
            self.calculate_defined_variables()
        #self.debug_print()

    #
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

    #
    def chceck_available_data_stack(self, number):
        if(len(self.data_stack) < number):
            sys.stderr.write("Not enough data on data stack\n")
            sys.exit(56)

    #
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
    

if __name__ == '__main__':
    main()