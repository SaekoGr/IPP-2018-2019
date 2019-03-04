#!/usr/bin/env python3

import sys
import re
import xml.etree.ElementTree as ET
from enum import Enum
from unidecode import unidecode
import codecs

non_arg = ["CREATEFRAME", "PUSHFRAME", "POPFRAME" , "RETURN", "BREAK"]
one_arg = ["DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT"]
two_arg = ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT"]
three_arg = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]

#
class Arguments:
    #
    def __init__(self, arguments):
        # help argument
        if("--help" in arguments):
            if(len(arguments) == 1):
                self.print_help()
            else:
                exit(10)

        self.source = False
        self.input = False

        for arg in arguments:
            if("--source=" in arg):
                self.source = True
                self.source_file = self.parse_path(arg)
            elif("--input" in arg):
                self.input = True
                self.input_file = self.parse_path(arg)
            else:
                exit(10)

        if(self.source == False and self.input == False):
            exit(10)


    # 
    def parse_path(self, path):
        new_path = re.search(r'(?<==).*', path)
        return new_path.group(0)

    #
    def print_help(self):
        sys.stdout.write("Script is run as: python3.6 interpret.py\n")
        sys.stdout.write("With possible arguments:\n")
        sys.stdout.write("--help : prints help\n")
        sys.stdout.write("--source=file : sets the path to the XML representation of source file\n")
        sys.stdout.write("--input=file : sets path to the file that contains input for interpretation\n")
        sys.stdout.write("At least one file must be given\n")

#
class Operand:
    #
    def __init__(self, instruction):
        
        try:
            self.type = instruction.attrib['type']
        except:
            sys.stderr.write("Missing type attribute\n")
            exit(52)

        
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
                    sys.exit(52)
                i = i + 1
                continue
            elif(char in possible_chars):
                i = i + 1
                continue
            else:
                sys.stderr.write("Invalid variable name\n")
                sys.exit(52)
                

        

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
                exit(31)
        else:
            try:
                tree = ET.parse(sys.stdin)
            except:
                exit(31)

        try:
            root = tree.getroot()
            if(root.attrib['language'] != "IPPcode19"):
                exit(52)
        except:
            exit(31)

        self.global_frame = {}
        self.local_frames = []
        self.data_stack = []
        self.labels = {}
        self.root = root
        self.call_stack = []

    #
    def prepare_labels(self):
        try:
            for i in range(0, len(self.root)):
                if(self.root[i].attrib['opcode'] == "LABEL"):
                    for child in self.root[i]:
                        if(child.text in self.labels):
                            exit(52)
                        self.labels.update({child.text : self.root[i].attrib['order']})
        except:
            sys.exit(32)

    #
    def format_value(self, value, value_type):
        if(value_type == "int"):
            if(str.isdigit(value)):
                return int(value)
            else:
                exit(32)
        elif(value_type == "bool"):
            if(value == "true"):
                return True
            elif(value == "false"):
                return False
            else:
                exit(32)
        elif(value_type == "string"):
            if(isinstance(value_type, str)):
                return value
            else:
                exit(32)
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

    

    # also updates
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
            exit(23)

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

    def start(self):
        self.counter = 1
        self.order = {}

        # prepare xml correct order
        cnt = 0
        for i in self.root:
            num = int(i.attrib['order'])
            if(num in self.order.keys()):
                sys.stderr.write("Multiple instruction order number\n")
                sys.exit(52)
            self.order.update({num : cnt})
            cnt = cnt + 1

        # execute instruction
        while self.counter < (len(self.root) + 1):
            try:
                current_instruction = self.order[self.counter]
            except:
                sys.stderr.write("Invalid instruction order number\n")
                sys.exit(52)
            self.execute_instruction(current_instruction)

        # close the files
        if(self.arg.input):
            self.arg.i_f.close()

        if(self.arg.source):
            self.arg.s_f.close()


    #
    def execute_instruction(self, op_num):
        try:
            current_opcode = self.root[op_num].attrib['opcode']
        except:
            sys.exit(52)

        # prepare args #
        if(current_opcode in non_arg):
            pass
        elif(current_opcode in one_arg):
            try:
                first_arg = self.root[op_num].findall("arg1")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(52)
            arg1 = Operand(first_arg)
        elif(current_opcode in two_arg):
            try:
                first_arg = self.root[op_num].findall("arg1")[0]
                second_arg = self.root[op_num].findall("arg2")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(52)
            arg1 = Operand(first_arg)
            arg2 = Operand(second_arg)
        elif(current_opcode in three_arg):
            try:
                first_arg = self.root[op_num].findall("arg1")[0]
                second_arg = self.root[op_num].findall("arg2")[0]
                third_arg = self.root[op_num].findall("arg3")[0]
            except:
                sys.stderr.write("Invalid arguments in xml file\n")
                sys.exit(52)
            arg1 = Operand(first_arg)
            arg2 = Operand(second_arg)
            arg3 = Operand(third_arg)
        else:
            exit(52)

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
                exit(53)

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
                exit(53)

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
                exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1<value_2
            else:
                exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # GT <var> <symb> <symb>
        elif(current_opcode == "GT"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str)):
                result = value_1>value_2
            else:
                exit(53)
            self.insert_to_frame(arg1.name, arg1.frame, result)
            self.counter = self.counter + 1
        # EQ <var> <symb> <symb>
        elif(current_opcode == "EQ"):
            value_1 = self.get_argument_value(arg2)
            value_2 = self.get_argument_value(arg3)

            if(type(value_1) != type(value_2)):
                exit(53)

            if(isinstance(value_1, int) or isinstance(value_1, bool) or isinstance(value_1, str) or isinstance(value_1, None)):
                result = value_1 == value_2
            else:
                exit(53)
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
                self.counter = int(jump_destination) - 1
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
                self.counter = int(jump_destination) - 1
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
                self.counter = int(jump_destination) - 1
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
                self.counter = int(jump_destination) - 1
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

        self.debug_print()


    def replace_decimal_escapes(self, s):
        return re.sub(
        r"\\(\d\d\d)",
        lambda x: chr(int(x.group(1), 10)), 
        s
    )
            
        
#
def main():
    if(len(sys.argv) == 1 or len(sys.argv) > 4):
        sys.stderr.write("Invalid arguments\n")
        sys.exit(10)

    my_interpret = Interpret()
    my_interpret.prepare_labels()
    my_interpret.start()
    

if __name__ == '__main__':
    main()