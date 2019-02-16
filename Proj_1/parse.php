#!/usr/bin/env php
<?php


### TODO - COMMENTS
### SYMB

define('types', array(
    'int',
    'bool',
    'string',
    'nil',
    'label',
    'type',
    'var'
));

# prepares xml document
function prepare_document($xml){
    xmlwriter_set_indent($xml, 1);
    $res = xmlwriter_set_indent_string($xml, '    ');
    xmlwriter_start_document($xml, '1.0', 'UTF-8');
    xmlwriter_start_element($xml, "program");
    xmlwriter_start_attribute($xml, 'language');
    xmlwriter_text($xml, "IPPcode19");
    xmlwriter_end_attribute($xml);
    return $xml;
}

# writes header for instruction
function write_instruction_header($opcode){
    xmlwriter_start_element($GLOBALS['xml'], "instruction");
    xmlwriter_start_attribute($GLOBALS['xml'], "order");
    xmlwriter_text($GLOBALS['xml'], $GLOBALS['instruction_counter']);
    $GLOBALS['instruction_counter']++;
    xmlwriter_start_attribute($GLOBALS['xml'], "opcode");
    xmlwriter_text($GLOBALS['xml'], strtoupper($opcode));
}

# instruction has no arguments
function zero_args($opcode, $line){
    if("$opcode\n" == $line or "$opcode" == $line){
        write_instruction_header($opcode);
        xmlwriter_end_element($GLOBALS['xml']);
        return 0;
    }
    else{
        return 23;
    }
}

# writes argument
function write_arg($type, $arg_num, $arg){
    xmlwriter_start_element($GLOBALS['xml'], $arg_num);
    xmlwriter_start_attribute($GLOBALS['xml'], "type");
    xmlwriter_text($GLOBALS['xml'], $type);
    xmlwriter_end_attribute($GLOBALS['xml']);
    xmlwriter_text($GLOBALS['xml'], $arg);
    xmlwriter_end_element($GLOBALS['xml']);
}

# 
function get_type($arg){
    $type_regex = "/.*(?=@)/";
    preg_match($type_regex, $arg, $match);
    $type = $match[0];

    if($type == "GF" or $type == "LF" or $type == "TF"){
        return "var";
    }
    else{
        for($i = 0; $i < count(types); $i++){
            if(!strcmp($type, types[$i])){
                return "$type";
            }
        }
        return "error";
    }
}

# checks whether it contains '@'
function has_at($arg){
    if(strpos($arg, '@') !== false){
        return true;
    }
    else{
        return false;
    }
}

#
function after_at($arg){
    if(has_at($arg)){
        $after_regex = "/(?<=@).*/";
        preg_match($after_regex, $arg, $match);
        return $match[0];
    }
    else{
        return 23;
    }
}

#
function evaluate_arg($opcode, $arg, $arg_type, $arg_num){
    write_instruction_header($opcode);
    if($arg_type == "symb"){
        $arg_type = get_type($arg);
        if($arg_type == "error"){
            return 23;
        }
    }
    switch($arg_type){
        case "string":
            $current_string = after_at($arg);
            if($current_string == 23){
                return 23;
            }
            else{
                write_arg($arg_type, $arg_num, $current_string);
                xmlwriter_end_element($GLOBALS['xml']);
                return 0;
            }
        case "label":   # no
        case "type":
            if(has_at($arg)){
                return 23;
            }
            else{
                write_arg($arg_type, $arg_num, $arg);
                xmlwriter_end_element($GLOBALS['xml']);
            }
            break;
        case "var":
        case "bool":
        case "int":
        case "nil":
            write_arg($arg_type, $arg_num, $arg);
            xmlwriter_end_element($GLOBALS['xml']);
            return 0;
            break;
        default:
            return 23;
    }
}

#
function one_arg($opcode, $line, $arg1_type){
    $arg1_regex = "/(?<=$opcode ).*/";
    preg_match($arg1_regex, $line, $match);
    if(!$match){
        return 23;
    }
    $arg1 = $match[0];
    $is_ok = False;

    if("$opcode $arg1\n" != $line and "$opcode $arg1" == $line){
        return 23;
    }

    evaluate_arg($opcode, $arg1, $arg1_type, "arg1");

}

#
function compare_opcode($opcode, $line){
    $found = False;
    if(!strcasecmp($opcode, "CREATEFRAME")){        # 0
        return zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "PUSHFRAME")){      # 0
        return zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "POPFRAME")){       # 0
        return zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "RETURN")){         # 0
        return zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "BREAK")){          # 0
        return zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "DEFVAR")){         # 1
        return one_arg($opcode, $line, "var");
    }
    elseif(!strcasecmp($opcode, "CALL")){           # 1
        return one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "PUSHS")){          # 1
        return one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "POPS")){           # 1
        return one_arg($opcode, $line, "var");
    }
    elseif(!strcasecmp($opcode, "EXIT")){           # 1
        return one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "DPRINT")){         # 1
        return one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "LABEL")){          # 1
        return one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "JUMP")){           # 1
        return one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "WRITE")){          # 1
        return one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "MOVE")){           # 2
        
    }
    elseif(!strcasecmp($opcode, "INT2CHAR")){       # 2
        
    }
    elseif(!strcasecmp($opcode, "READ")){           # 2
        
    }
    elseif(!strcasecmp($opcode, "STRLEN")){         # 2
        
    }
    elseif(!strcasecmp($opcode, "TYPE")){           # 2
        
    }
    elseif(!strcasecmp($opcode, "ADD")){            # 3
        
    }
    elseif(!strcasecmp($opcode, "SUB")){            # 3
        
    }
    elseif(!strcasecmp($opcode, "MUL")){            # 3
        
    }
    elseif(!strcasecmp($opcode, "IDIV")){           # 3
        
    }
    elseif(!strcasecmp($opcode, "LT")){             # 3
        
    }
    elseif(!strcasecmp($opcode, "GT")){             # 3
        
    }
    elseif(!strcasecmp($opcode, "EQ")){             # 3
        
    }
    elseif(!strcasecmp($opcode, "AND")){            # 3
        
    }
    elseif(!strcasecmp($opcode, "OR")){             # 3
        
    }
    elseif(!strcasecmp($opcode, "NOT")){            # 3
        
    }
    elseif(!strcasecmp($opcode, "STRI2INT")){       # 3
        
    }
    elseif(!strcasecmp($opcode, "CONCAT")){         # 3
        
    }
    elseif(!strcasecmp($opcode, "GETCHAR")){        # 3
        
    }
    elseif(!strcasecmp($opcode, "SETCHAR")){        # 3
        
    }
    elseif(!strcasecmp($opcode, "JUMPIFEQ")){       # 3
        
    }
    elseif(!strcasecmp($opcode, "JUMPIFNEQ")){      # 3
        
    }
    else{
        return 22;
    }
    return 0;
}

# processes each line
function process_line($line){
    $opcode_regex = "/^[a-zA-Z]*/";
    preg_match($opcode_regex, $line, $match);
    $opcode = $match[0];
    return compare_opcode($opcode, $line);
}

# functions for help
function print_help(){
    fwrite(STDOUT, "Usage: php7.3 parse.php < file\n");
    return 0;
}

#                           #
#           MAIN            #
#                           #

# parsing the input arguments
if($argc == 1){                 # no arguments, wait for stdin
    $f = fopen('php://stdin', 'r');
    if(!$f){
        fwrite(STDERR, "Error opening file\n");
    }
}
elseif($argv[1] === "--help"){   # help argument
    if($argc != 2)  
        return 10;
    else
        return print_help();
}
else{
    fwrite(STDERR, "Invalid arguments\n");
    return 10;
}

# check the header
$fh = fgets($f);
if($fh == ".IPPcode19\n"){
    ;
}
else{
    fwrite(STDERR, "Header is missing or incorrect\n");
    return 21;
}

# prepare xml document
$xml = xmlwriter_open_memory();
$xml = prepare_document($xml);
$instruction_counter = 1;

# reading line by line and processing it
while(($line = fgets($f)) != false){
    $ret_code = process_line($line);
    if($ret_code == 22){
        fwrite(STDERR, "Incorrect or uknown opcode\n");
        return $ret_code;
    }
    elseif($ret_code == 23){
        fwrite(STDERR, "Lexical or syntactical error\n");
        return $ret_code;
    }
}

# close xml document
xmlwriter_end_element($xml);
xmlwriter_end_document($xml);
echo xmlwriter_output_memory($xml);

?>