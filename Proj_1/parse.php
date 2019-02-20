#!/usr/bin/env php
<?php


### TODO - COMMENTS
### SYMB
### EVALUATE RETURN CODE

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

# 
function has_comment($line){
    if(strpos($line, '#') !== false){
        return true;
    }
    else{
        return false;
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

# it gets the type in front of the '@' 
function get_type($arg){
    $type_regex = "/.*(?=@)/";
    preg_match($type_regex, $arg, $match);
    if(!$match){
        return "error";
    }
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

# gets everything after '@'
function after_at($arg){
    if(has_at($arg)){
        $after_regex = "/(?<=@).*/";
        preg_match($after_regex, $arg, $match);
        return $match[0];
    }
    else{
        exit(23);
    }
}

# evaluates arguments, opcodes, sorts it into the xml format
function evaluate_arg($arg, $arg_type, $arg_num){
    if($arg_type == "symb"){
        $arg_type = get_type($arg);
        if($arg_type == "error"){
            exit(23);
        }
    }
    switch($arg_type){
        case "string":
            $current_string = after_at($arg);
            if($current_string == 23){
                exit(23);
            }
            else{
                write_arg($arg_type, $arg_num, $current_string);
            }
            break;
        case "label":   # no
        case "type":
            if(has_at($arg)){
                exit(23);
            }
            else{
                write_arg($arg_type, $arg_num, $arg);
            }
            break;
        case "bool":
            $bool_value = after_at($arg);
            if(strcmp($bool_value, "true") == 0){
                write_arg($arg_type, $arg_num, $bool_value);
            }
            elseif(strcmp($bool_value, "false") == 0){
                write_arg($arg_type, $arg_num, $bool_value);
            }
            else{
                exit(23);
            }
            break;
        case "int":
        case "nil":
            $after_at = after_at($arg);
            write_arg($arg_type, $arg_num, $after_at);
            break;
        case "var":
            write_arg($arg_type, $arg_num, $arg);
            break;
        default:
            exit(23);
    }
}



function remove_comment_new($word){
    if(has_comment($word)){
        $before_comment = "/.*(?=#)/";
        preg_match($before_comment, $word, $match);
        return $match[0];
    }
    else{
        return $word;
    }
}

#
function remove_whitespaces($word){
    $tmp_word = "";
    for($i = 0; $i < strlen($word); $i++){
        if($word[$i] == "\s" or $word[$i] == "\t" or $word[$i] == " " or is_one_line_comment($word)){
            continue;
        }
        $tmp_word = $tmp_word . $word[$i];
    }
    return $tmp_word;
}



# instruction has no arguments
function zero_args($opcode, $line){
    if(get_next_arg($opcode, $line) == ""){
        write_instruction_header($opcode);
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        exit(23);
    }
}

#
function get_next_arg($word, $line){
    $arg_regex = "/(?<=$word\s).*?(?=\s)/";
    preg_match($arg_regex, $line, $match);
    print_r($match);
    if(!$match or empty($match)){
        return "";
    }
    else{
        return remove_whitespaces($match[0]);
    }
}

#
function one_arg($opcode, $line, $arg1_type){
    $arg1 = remove_comment_new(get_next_arg($opcode, $line));

    if(get_next_arg($arg1, $line) == ""){
        write_instruction_header($opcode);
        evaluate_arg($arg1, $arg1_type, "arg1");
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        exit(23);
    }
}

#
function two_args($opcode, $line, $arg1_type, $arg2_type){
    $tmp_state = "";
    $arg1 = get_next_arg($opcode, $line);
    $tmp_state = get_current_state($opcode, $arg1, $line);
    $arg2 = remove_comment_new(get_next_arg($arg1, $line));
    $tmp_state = get_current_state($tmp_state, $arg2, $line);

    if(get_next_arg($tmp_state, $line) == ""){
        write_instruction_header($opcode);
        evaluate_arg($arg1, $arg1_type, "arg1");
        evaluate_arg($arg2, $arg2_type, "arg2");
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        exit(23);
    }
}



#
function get_current_state($word_1, $word_2, $line){
    $basic_regex = "/$word_1\s*$word_2/";
    preg_match($basic_regex, $line, $match);
    print("tu ešte som\n");
    print_r($match);
    if(!$match or empty($match)){
        exit(23);
    }
    else{
        return $match[0];
    }
}

# 
function three_args($opcode, $line, $arg1_type, $arg2_type, $arg3_type){
    $tmp_state = "";
    $arg1 = get_next_arg($opcode, $line);
    $tmp_state = get_current_state($opcode, $arg1, $line);
    $arg2 = get_next_arg($tmp_state, $line);
    $tmp_state = get_current_state($tmp_state, $arg2, $line);
    $arg3 = remove_comment_new(get_next_arg($tmp_state, $line));
    $tmp_state = get_current_state($tmp_state, $arg3, $line);

    if(get_next_arg($tmp_state, $line) == ""){
            write_instruction_header($opcode);
            evaluate_arg($arg1, $arg1_type, "arg1");
            evaluate_arg($arg2, $arg2_type, "arg2");
            evaluate_arg($arg3, $arg3_type, "arg3");
            xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        exit(23);
    }
}

#
function compare_opcode($opcode, $line){
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
        return two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "INT2CHAR")){       # 2
        return two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "READ")){           # 2
        return two_args($opcode, $line, "var", "type");
    }
    elseif(!strcasecmp($opcode, "STRLEN")){         # 2
        return two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "TYPE")){           # 2
        return two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "ADD")){            # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "SUB")){            # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "MUL")){            # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "IDIV")){           # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "LT")){             # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "GT")){             # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "EQ")){             # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "AND")){            # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "OR")){             # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "NOT")){            # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "STRI2INT")){       # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "CONCAT")){         # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "GETCHAR")){        # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "SETCHAR")){        # 3
        return three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "JUMPIFEQ")){       # 3
        return three_args($opcode, $line, "label", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "JUMPIFNEQ")){      # 3
        return three_args($opcode, $line, "label", "symb", "symb");
    }
    else{
        print("Zly opcode\n");
        exit(22);
    }
    return 0;
}

# look whether the line is comment
function is_one_line_comment($line){
    $comment_regex = "/[ \t]*#.*/";
    preg_match($comment_regex, $line, $match);
    if(!$match){
        return false;
    }
    elseif("$match[0]" == "$line" or "$match[0]\n" == "$line"){
        return true;
    }
    else{
        return false;
    }
}

#
function check_whitespaces($line){
    $size_line = strlen($line);
    for($i = 0; $i < $size_line; $i++){
        switch($line[$i]){
            case "\t":
            case "\s":
            case "\n":
                break;
            default:
                return false;
        }
    }
    return true;
}

# processes each line
function process_line($line){
    # check for one line comment
    if(is_one_line_comment($line)){
        return 0;
    }
    if($line == "\n" or $line == "\s" or $line == "\t"){
        return 0;
    }
    if(check_whitespaces($line)){
        return 0;
    }

    $opcode_regex = "/^[\s]*([a-zA-Z]*)/";
    preg_match($opcode_regex, $line, $match);
    
    $opcode = $match[count($match)-1];
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
        #fwrite(STDERR, "Error opening file\n");
    }
}
elseif($argv[1] === "--help"){   # help argument
    if($argc != 2)  
        exit(10);
    else
        exit(print_help());
}
else{
    #fwrite(STDERR, "Invalid arguments\n");
    exit(10);
}

# check the header
$fh = fgets($f);
if($fh == ".IPPcode19\n"){
    ;
}
else{
    fwrite(STDERR, "Header is missing or incorrect\n");
    exit(21);
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
        exit($ret_code);
    }
    elseif($ret_code == 23){
        fwrite(STDERR, "Lexical or syntactical error\n");
        exit($ret_code);
    }
}

# close xml document
xmlwriter_end_element($xml);
xmlwriter_end_document($xml);
echo xmlwriter_output_memory($xml);
exit(0);

?>