#!/usr/bin/env python3

import sys
import re
import xml.etree.ElementTree as ET
from enum import Enum


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

class Operand:
    def __init__(self, instruction):
        try:
            self.type = instruction.attrib['type']
        except:
            exit(32)

        if(self.type == "var"):
            if("@" in instruction.text):
                self.frame = self.get_frame(instruction.text)
                self.name = self.get_name(instruction.text)
                self.value = None
            else:
                sys.exit(32)
        else:
            self.value = instruction.text
            self.frame = None
            self.name = None

    def get_frame(self, name):
        nam = re.search(r'.*(?=@)', name)
        return nam.group(0)

    def get_name(self, name):
        frame = re.search(r'(?<=@).*', name)
        return frame.group(0)

        

#
class Interpret:
    #
    def __init__(self, root):
        self.global_frame = {}
        self.local_frames = []
        self.data_stack = []
        self.labels = {}
        self.root = root

    #
    def prepare_labels(self, root):
        try:
            for i in range(0, len(root)):
                #print(root[i].attrib['opcode'])
                if(root[i].attrib['opcode'] == "LABEL"):
                    for child in root[i]:
                        if(child.text in self.labels):
                            exit(52)    ## TODO --- check this return code
                        self.labels.update({child.text : root[i].attrib['order']})
        except:
            sys.exit(32)

    #
    def get_argument_value(self, argument):
        if(argument.type == "var"):
            if(argument.frame == "GF"):
                try:
                    value = self.global_frame[self.name]
                except:
                    sys.exit(54)
            elif(argument.frame == "LF"):
                try:
                    value = self.local_frames[len(self.local_frames)-1][self.name]
                except:
                    sys.exit(55)
            elif(argument.frame == "TF"):
                try:
                    value = self.temporary_frame[self.name]
                except:
                    sys.exit(55)
            else:
                sys.exit(32)

            if(value == "None"):
                sys.exit(56)
            return value
        else:
            return argument.value

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

    #
    def execute_instruction(self, op_num):
        try:
            current_opcode = self.root[op_num].attrib['opcode']
        except:
            sys.exit(32)

        # CREATEFRAME
        if(current_opcode == "CREATEFRAME"):
            self.temporary_frame = {}
        # PUSHFRAME
        elif(current_opcode == "PUSHFRAME"):
            try:
                self.local_frames.append(self.temporary_frame)
                del self.temporary_frame
            except:
                sys.exit(55)
        # POPFRAME
        elif(current_opcode == "POPFRAME"):
            if(len(self.local_frames) == 0):
                sys.exit(55)
            else:
                self.temporary_frame = (self.local_frames[len(self.local_frames) - 1]).copy()
                del self.local_frames[len(self.local_frames) - 1]
        # DEFVAR <var>
        elif(current_opcode == "DEFVAR"):
            arg1 = Operand(self.root[op_num][0])
            self.insert_to_frame(arg1.name, arg1.frame, "None")
        # MOVE <var> <symb>
        elif(current_opcode == "MOVE"):
            arg1 = Operand(self.root[op_num][0])
            arg2 = Operand(self.root[op_num][1])
            value = self.get_argument_value(arg2)
            self.insert_to_frame(arg1.name, arg1.frame, value)
        # PUSHS <symb>
        elif(current_opcode == "PUSHS"):
            arg1 = Operand(self.root[op_num][0])
            value = self.get_argument_value(arg1)
            self.data_stack.append(value)
        # POPS <var>
        elif(current_opcode == "POPS"):
            arg1 = Operand(self.root[op_num][0])
            if(len(self.data_stack) == 0):
                sys.exit(56)
            value = self.data_stack[len(self.data_stack) - 1]
            del self.data_stack[len(self.data_stack) - 1]
            self.insert_to_frame(arg1.name, arg1.frame, value)




        self.debug_print()



#
def main():
    if(len(sys.argv) == 1 or len(sys.argv) > 4):
        sys.stderr.write("Invalid arguments\n")
        sys.exit(10)

    # parse arguments
    arg = Arguments(sys.argv[1:])

    try:
        tree = ET.parse(arg.source_file)
    except:
        exit(31)

    try:
        root = tree.getroot()
        if(root.attrib['language'] != "IPPcode19"):
            exit(32)
    except:
        exit(31)
    
    my_interpret = Interpret(root)
    my_interpret.prepare_labels(root)

    for x in range(0, len(root), 1):
        my_interpret.execute_instruction(x)

if __name__ == '__main__':
    main()