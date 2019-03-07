#!/usr/bin/env php
<?php

# array for all the types
define('types', array(
    'int',
    'bool',
    'string',
    'nil',
    'label',
    'type',
    'var'
));

# looks for substring in an array, used for stats
function substr_in_array($needle, array $haystack){
    foreach($haystack as $item){
        if(false !== strpos($item, $needle)){
            return true;
        }
    }
    return false;
}

# prepares xml document, sets indentaion
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

# checks whether line contains comment
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
        exit(23);
    }
    $type = $match[0];
    if($type == "GF" or $type == "LF" or $type == "TF"){
        return "var";
    }
    else{
        for($i = 0; $i < count(types); $i++){
            if($type == types[$i]){
                return "$type";
            }
        }
        exit(23);
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
function after_at($arg, $arg_type){
    if(has_at($arg)){
        switch($arg_type){
            case "string":
                if(strpos($arg, '\\') !== false){
                    $arg = str_replace('\\', '\\\\', $arg);
                }
                break;
            default:
                if(strpos($arg, '\\') !== false){
                    exit(23);
                }
                break;
        }
        
        $after_regex = "/(?<=@).*/";
        preg_match($after_regex, $arg, $match);

        $match[0] = str_replace('\\\\', '\\', $match[0]);
        return $match[0];
    }
    else{
        exit(23);
    }
}

# check whether the frame is correctly written
function check_frame($arg){
    if(has_at($arg)){
        $before_at = "/.*(?=@)/";
        preg_match($before_at, $arg, $match);

        if(!$match){
            fwrite(STDERR, "Invalid variable operand\n");
            exit(23);
        }
        if($match[0] == "GF" || $match[0] == "TF" || $match[0] == "LF"){
            ;
        }
        else{
            fwrite(STDERR, "Invalid variable operand\n");
            exit(23);
        }
    }
    else{
        fwrite(STDERR, "Invalid variable operand\n");
        exit(23);
    }
}

# checks for correct variable name
function check_variable_name($name){
    for($i = 0; $i < strlen($name); $i++){
        if(ctype_alpha($name[$i])){
            continue;
        }
        elseif(is_numeric($name[$i])){
            if($i == 0){
                fwrite(STDERR, "Variable name starts with number\n");
                exit(23);
            }
            continue;
        }
        switch($name[$i]){
            case "-":
            case "_":
            case "$":
            case "&":
            case "%":
            case "*":
            case "!":
            case "?":
                break;
            default:
                fwrite(STDERR, "Invalid variable name\n");
                exit(23);

        }
    }
}

# checks for correct escape sequence
function check_escape($string){
    $tmp_string = "";
    $state = 0;
    for($i = 0; $i < strlen($string); $i++){

        if($string[$i] == '\\'){
            $state = 1;
            if($i == (strlen($string) - 1)){    # not enough numbers
                fwrite(STDERR, "Invalid escape sequence\n");
                exit(23);
            }
            continue;
        }

        switch($state){
            case 1:
                $state = $state + 1;
                if($i == (strlen($string) - 1)){    # not enough numbers
                    fwrite(STDERR, "Invalid escape sequence\n");
                    exit(23);
                }
                $tmp_string = $tmp_string . $string[$i];
                break;
            case 2:
                $state = $state + 1;
                if($i == (strlen($string) - 1)){    # not enough numbers
                    fwrite(STDERR, "Invalid escape sequence\n");
                    exit(23);
                }
                $tmp_string = $tmp_string . $string[$i];
                break;
            case 3:
                $state = $state + 1;
                $tmp_string = $tmp_string . $string[$i];
                if(!is_numeric($tmp_string)){
                    fwrite("Invalid escape sequence\n");
                    exit(23);
                }
                break;
            case 4:
                if(is_numeric($string[$i])){
                    fwrite(STDERR, "Invalid escape sequence\n");
                    exit(23);
                }
                elseif($string[$i] == '\\'){
                    $state = 1;
                    $tmp_state = "";
                }
                else{
                    $state = $state + 1;
                }
                break;
            default:
                $tmp_string = "";
                break;
        }
    }
}

# evaluates arguments, opcodes, sorts it into the xml format
function evaluate_arg($arg, $arg_type, $arg_num){
    # look at what type it is when it can be variable or constant
    if($arg_type == "symb"){
        $arg_type = get_type($arg);
    }

    # check all possible types
    switch($arg_type){
        case "string":  # we check correct escape sequences
            $current_string = after_at($arg, $arg_type);
            check_escape($current_string);
            write_arg($arg_type, $arg_num, $current_string);
            break;
        case "label":   # no @
            if(has_at($arg)){
                exit(23);
            }
            else{
                write_arg($arg_type, $arg_num, $arg);
            }
            break;
        case "type":    # type can only has following types
            if(has_at($arg)){
                exit(23);
            }
            else{
                switch($arg){
                    case("bool"):
                    case("string"):
                    case("int"):
                    case("nil"):
                        write_arg($arg_type, $arg_num, $arg);
                        break;
                    default:
                        exit(23);
                }  
            }
            break;
        case "bool":
            $bool_value = after_at($arg, $arg_type);
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
        case "int": # checks for correctly written integer value
            $after_at = after_at($arg, $arg_type);
            if(is_numeric($after_at)){
                write_arg($arg_type, $arg_num, $after_at);
            }
            else{
                fwrite(STDERR, "Invalid integer value\n");
                exit(23);
            }
            break;
        case "nil":
            $after_at = after_at($arg, $arg_type);
            write_arg($arg_type, $arg_num, $after_at);
            break;
        case "var":
            check_frame($arg);
            $dummy = after_at($arg, $arg_type);
            if(empty($dummy)){  # check
                fwrite(STDERR, "Undefined variable name\n"); 
                exit(23);
            }
            check_variable_name($dummy);
            write_arg($arg_type, $arg_num, $arg);
            break;
        default:
            exit(23);
    }
}

# if string contains comment, it removes it
function remove_comment($word){
    if(has_comment($word)){
        $before_comment = "/.*(?=#)/";
        preg_match($before_comment, $word, $match);
        return $match[0];
    }
    else{
        return $word;
    }
}

# function removes all unnecessary whitespaces that regex could have picked up
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
    # check for too many arguments
    if(get_next_arg($opcode, $line) == ""){
        write_instruction_header($opcode);
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        fwrite(STDERR, "Too many operands for current opcode\n");
        exit(23);
    }
}

# function looks at what we already have a give us the next possible argument
# implemented, so that there can be multiple arguments that are the same
function get_next_arg($word, $line){
    if(strpos($word, '\\') !== false){
        $word = str_replace('\\', '\\\\', $word);
    }
    if(strpos($word, "?") !== false){
        $word = str_replace("?", '\?', $word);
    }
    if(strpos($word, "$") !== false){
        $word = str_replace("$", '\$', $word);
    }
    if(strpos($word, "<") !== false){
        $word = str_replace("<", '\<', $word);
    }
    if(strpos($word, ">") !== false){
        $word = str_replace(">", '\>', $word);
    }
    if(strpos($word, "/") !== false){
        $word = str_replace("/", '\/', $word);
    }

    $arg_regex = "/(?<=$word\s).*?(?=\s)/";
    preg_match($arg_regex, $line, $match);
    if(!$match or empty($match)){
        return "";
    }
    else{
        $match[0] = str_replace('\\\\', '\\', $match[0]);
        $match[0] = str_replace('\?', "?", $match[0]);
        $match[0] = str_replace('\$', "$", $match[0]);
        $match[0] = str_replace('\<', "<", $match[0]);
        $match[0] = str_replace('\>', ">", $match[0]);
        $match[0] = str_replace('\/', "/", $match[0]);
        return remove_whitespaces($match[0]);
    }
}

# function that works with one arguments
function one_arg($opcode, $line, $arg1_type){
    # obtain 1 argument
    $arg1 = remove_comment(get_next_arg($opcode, $line));

    # check whether it exists
    if($arg1 == ""){
        fwrite(STDERR, "Too few operands for current opcode\n");
        exit(23);
    }

    # counters for statistics
    if(!strcasecmp($opcode, "JUMP") and $GLOBALS['stats'] and $GLOBALS['jumps']){
        $GLOBALS['jump_counter']++;
    }
    if(!strcasecmp($opcode, "LABEL") and $GLOBALS['stats'] and $GLOBALS['jumps']){
        if(!in_array($arg1, $GLOBALS['label_array'])){
            array_push($GLOBALS['label_array'], $arg1);
            $GLOBALS['label_counter']++;
        }
    }
    
    # check for too many arguments
    if(get_next_arg($arg1, $line) == ""){
        # we can write it to xml
        write_instruction_header($opcode);
        evaluate_arg($arg1, $arg1_type, "arg1");
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        fwrite(STDERR, "Too many operands for current opcode\n");
        exit(23);
    }
}

# function that works with two arguments
function two_args($opcode, $line, $arg1_type, $arg2_type){
    # obtain 2 arguments
    $tmp_state = "";
    $arg1 = get_next_arg($opcode, $line);
    $tmp_state = get_current_state($opcode, $arg1, $line);
    $arg2 = remove_comment(get_next_arg($arg1, $line));
    $tmp_state = get_current_state($tmp_state, $arg2, $line);

    # check whether both exist
    if($arg1 == "" or $arg2 == ""){
        fwrite(STDERR, "Too few operands for current opcode\n");
        exit(23);
    }

    # special check for read function
    if(!strcasecmp($opcode, "READ")){           # 2
        if($arg2 != "string" && $arg2 != "int" && $arg2 != "bool"){
            fwrite(STDERR, "Invalid read type\n");
            exit(23);
        }
    }

    # check for too many arguments
    if(get_next_arg($tmp_state, $line) == ""){
        # we can write it to our xml
        write_instruction_header($opcode);
        evaluate_arg($arg1, $arg1_type, "arg1");
        evaluate_arg($arg2, $arg2_type, "arg2");
        xmlwriter_end_element($GLOBALS['xml']);
    }
    else{
        fwrite(STDERR, "Too many operands for current opcode\n");
        exit(23);
    }
}

# function return tmp_string, that is used in order
# to prevent bad matching with regex
# when there are multiple arguments, that are the same
function get_current_state($word_1, $word_2, $line){
    # if word contains backslash, we duplicate it, then remove it
    # so that regex would work correctly
    if(strpos($word_1, '\\') !== false){
        $word_1 = str_replace('\\', '\\\\', $word_1);
    }
    if(strpos($word_2, '\\') !== false){
        $word_2 = str_replace('\\', '\\\\', $word_2);
    }
    if(strpos($word_1, "?") !== false){
        $word_1 = str_replace("?", '\?', $word_1);
    }
    if(strpos($word_2, "?") !== false){
        $word_2 = str_replace("?", '\?', $word_2);
    }
    if(strpos($word_1, "$") !== false){
        $word_1 = str_replace("$", '\$', $word_1);
    }
    if(strpos($word_2, "$") !== false){
        $word_2 = str_replace("$", '\$', $word_2);
    }
    if(strpos($word_1, "<") !== false){
        $word_1 = str_replace("<", '\<', $word_1);
    }
    if(strpos($word_2, "<") !== false){
        $word_2 = str_replace("<", '\<', $word_2);
    }
    if(strpos($word_1, ">") !== false){
        $word_1 = str_replace(">", '\>', $word_1);
    }
    if(strpos($word_2, ">") !== false){
        $word_2 = str_replace(">", '\>', $word_2);
    }
    if(strpos($word_1, "/") !== false){
        $word_1 = str_replace("/", '\/', $word_1);
    }
    if(strpos($word_2, "/") !== false){
        $word_2 = str_replace("/", '\/', $word_2);
    }

    $basic_regex = "/$word_1\s*$word_2/";
    preg_match($basic_regex, $line, $match);
    if(!$match or empty($match)){
        exit(23);
    }
    else{
        $match[0] = str_replace('\\\\', '\\', $match[0]);
        $match[0] = str_replace('\?', "?", $match[0]);
        $match[0] = str_replace('\$', "$", $match[0]);
        $match[0] = str_replace('\<', "<", $match[0]);
        $match[0] = str_replace('\>', ">", $match[0]);
        $match[0] = str_replace('\/', "/", $match[0]);
        return $match[0];
    }
}

# function that works with 3 arguments
function three_args($opcode, $line, $arg1_type, $arg2_type, $arg3_type){
    # obtain 3 arguments
    $tmp_state = "";
    $arg1 = get_next_arg($opcode, $line);
    $tmp_state = get_current_state($opcode, $arg1, $line);
    $arg2 = get_next_arg($tmp_state, $line);
    $tmp_state = get_current_state($tmp_state, $arg2, $line);
    $arg3 = remove_comment(get_next_arg($tmp_state, $line));
    $tmp_state = get_current_state($tmp_state, $arg3, $line);


    # check whether they exist
    if($arg1 == "" or $arg2 == "" or $arg3 == ""){
        fwrite(STDERR, "Too few operands for current opcode\n");
        exit(23);
    }

    # counters for statistics
    if(!strcasecmp($opcode, "JUMPIFEQ") and $GLOBALS['stats'] and $GLOBALS['jumps']){
        $GLOBALS['jump_counter']++;
    }
    if(!strcasecmp($opcode, "JUMPIFNEQ") and $GLOBALS['stats'] and $GLOBALS['jumps']){
        $GLOBALS['jump_counter']++;
    }

    # check if there are not too many arguments
    if(get_next_arg($tmp_state, $line) == ""){
            # all is correct, we can write it to our xml
            write_instruction_header($opcode);
            evaluate_arg($arg1, $arg1_type, "arg1");
            evaluate_arg($arg2, $arg2_type, "arg2");
            evaluate_arg($arg3, $arg3_type, "arg3");
            xmlwriter_end_element($GLOBALS['xml']);
    }
    else{   # too many operands, error
        fwrite(STDERR, "Too many operands for current opcode\n");
        exit(23);
    }
}

# compares the opcode and calls appropriate function
function compare_opcode($opcode, $line){
    if(!strcasecmp($opcode, "CREATEFRAME")){        # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "PUSHFRAME")){      # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "POPFRAME")){       # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "RETURN")){         # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "BREAK")){          # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "CLEARS")){         # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "ADDS")){           # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "SUBS")){           # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "MULS")){           # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "IDIVS")){          # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "LTS")){            # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "GTS")){            # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "EQS")){            # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "ANDS")){           # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "ORS")){            # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "NOTS")){           # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "INT2CHARS")){      # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "STRI2INTS")){      # 0
        zero_args($opcode, $line);
    }
    elseif(!strcasecmp($opcode, "JUMPIFEQS")){      # 1
        one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "JUMPIFNEQS")){     # 1
        one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "DEFVAR")){         # 1
        one_arg($opcode, $line, "var");
    }
    elseif(!strcasecmp($opcode, "CALL")){           # 1
        one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "PUSHS")){          # 1
        one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "POPS")){           # 1
        one_arg($opcode, $line, "var");
    }
    elseif(!strcasecmp($opcode, "EXIT")){           # 1
        one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "DPRINT")){         # 1
        one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "LABEL")){          # 1
        one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "JUMP")){           # 1
        one_arg($opcode, $line, "label");
    }
    elseif(!strcasecmp($opcode, "WRITE")){          # 1
        one_arg($opcode, $line, "symb");
    }
    elseif(!strcasecmp($opcode, "MOVE")){           # 2
        two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "INT2CHAR")){       # 2
        two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "READ")){           # 2
        two_args($opcode, $line, "var", "type");
    }
    elseif(!strcasecmp($opcode, "STRLEN")){         # 2
        two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "TYPE")){           # 2
        two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "NOT")){            # 2
        two_args($opcode, $line, "var", "symb");
    }
    elseif(!strcasecmp($opcode, "ADD")){            # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "SUB")){            # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "MUL")){            # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "IDIV")){           # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "LT")){             # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "GT")){             # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "EQ")){             # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "AND")){            # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "OR")){             # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "STRI2INT")){       # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "CONCAT")){         # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "GETCHAR")){        # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "SETCHAR")){        # 3
        three_args($opcode, $line, "var", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "JUMPIFEQ")){       # 3
        three_args($opcode, $line, "label", "symb", "symb");
    }
    elseif(!strcasecmp($opcode, "JUMPIFNEQ")){      # 3
        three_args($opcode, $line, "label", "symb", "symb");
    }
    else{
        fwrite(STDERR, "Unknown opcode\n");
        exit(22);
    }
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

# checks, whether line contains only 1 whitespace and nothing else
function check_whitespaces($line){
    $size_line = strlen($line);
    for($i = 0; $i < $size_line; $i++){
        switch($line[$i]){
            case "\t":
            case "\s":
            case "\n":
            case " ":
            case ' ':
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
        return;
    }
    if($line == "\n" or $line == "\s" or $line == "\t"){
        return;
    }
    if(check_whitespaces($line)){
        return;
    }

    # uses regex to extract the opcode
    $opcode_regex = "/^[\s]*([a-zA-Z2]*)/";
    preg_match($opcode_regex, $line, $match);
    $opcode = $match[count($match)-1];
    compare_opcode($opcode, $line);
}

# functions for help
function print_help(){
    fwrite(STDOUT, "Usage: php7.3 parse.php\n");
    fwrite(STDOUT, "Input can be given as file to stdin or written directly to stdin\n");
    fwrite(STDOUT, "Arguments for statistics: --stats=file [--comments --labels --jumps --loc] and at least one parameter must be given\n");
    exit(0);
}

# help function for getting the path to a file
function get_path($full_string){
    $path_regex = "/(?<==).*/";
    preg_match($path_regex, $full_string, $match);
    return $match[0];
}


#                           #
#           MAIN            #
#                           #
# variables for stats
$stats = false;
$loc = false;
$comments = false;
$labels = false;
$jumps = false;
$stats_path = "";
# stats counters
$loc_counter = 0;
$comment_counter = 0;
$label_counter = 0;
$jump_counter = 0;
$stats_array = [];
$label_array = [];


if($argc != 1){   # tries to find substring in the input arguments
    if($argv[1] === "--help"){   # help argument
        if($argc != 2){  # there was help called but also other arguments = error
            fwrite(STDERR, "Help cannot be combined with any other arguments\n");
            exit(10);
        }
        else{
            exit(print_help()); # normally prints out help
        }
    }

    if(substr_in_array("--stats=", $argv)){ # we require stats as well
        foreach($argv as $item){            # creates the appropriate string
            if(strpos($item, "--stats=") !== false){
                if($stats == true){         # check for duplicates
                    fwrite(STDERR, "Same argument was entered twice\n");
                    exit(10);
                }
                $stats = true;
                $stats_path = get_path($item);
            }
            elseif(strpos($item, "--loc") !== false){
                if($loc == true){           # check for duplicates
                    fwrite(STDERR, "Same argument was entered twice\n");
                    exit(10);
                }
                array_push($stats_array, "--loc");
                $loc = true;
            }
            elseif(strpos($item, "--comments") !== false){
                if($comments == true){      # check for duplicates
                    fwrite(STDERR, "Same argument was entered twice\n");
                    exit(10);
                }
                array_push($stats_array, "--comments");
                $comments = true;
            }
            elseif(strpos($item, "--labels") !== false){
                if($labels == true){        # check for duplicates
                    fwrite(STDERR, "Same argument was entered twice\n");
                    exit(10);
                }
                array_push($stats_array, "--labels");
                $labels = true;
            }
            elseif(strpos($item, "--jumps") !== false){
                if($jumps == true){         # check for duplicates
                    fwrite(STDERR, "Same argument was entered twice\n");
                    exit(10);
                }
                array_push($stats_array, "--jumps");
                $jumps = true;
            }
            elseif(strpos($item, "parse.php") !== false){
                continue;
            }
            else{
                fwrite(STDERR, "Invalid input arguments\n");
                exit(10);
            }
        }
    }
    else{   # arguments were not even stats, error
        fwrite(STDERR, "Invalid arguments\n");
        exit(10);
    }
}
# input file
$f = fopen('php://stdin', 'r');

# check the header
$fh = fgets($f);
# comment counter
if(has_comment($fh)){
    if($GLOBALS['stats'] and $GLOBALS['comments']){ # stats
        $GLOBALS['comment_counter']++;
    }
}
$fh = remove_comment($fh);
$fh = remove_whitespaces($fh);
$fh = strtolower($fh);

if($fh != ".ippcode19\n" && $fh != ".ippcode19"){
    fwrite(STDERR, "Header is missing or incorrect\n");
    exit(21);
}

# prepare xml document
$xml = xmlwriter_open_memory();
$xml = prepare_document($xml);
$instruction_counter = 1;

# reading line by line and processing it
while(((($line = fgets($f)) != false)) and !feof($f)){
    # comment counter
    if(has_comment($line)){
        if($GLOBALS['stats'] and $GLOBALS['comments']){ # stats
            $GLOBALS['comment_counter']++;
        }
    }
    process_line($line);
}

# outputs the stats
if($stats){
    # creates the file if it doesn't exist
    if(!file_exists($stats_path)){
        exec('touch ' . $stats_path);
    }

    $st = fopen($stats_path, 'w');
    
    # output the appropriate statistics
    foreach($stats_array as $item){
        if(strpos($item, "--loc") !== false){
            $loc_counter = ($instruction_counter - 1);
            fwrite($st, $GLOBALS['loc_counter'] . "\n");
        }
        elseif(strpos($item, "--comments") !== false){
            fwrite($st, $GLOBALS['comment_counter'] . "\n");
        }
        elseif(strpos($item, "--labels") !== false){
            fwrite($st, $GLOBALS['label_counter'] . "\n");
        }
        elseif(strpos($item, "--jumps") !== false){
            fwrite($st, $GLOBALS['jump_counter']. "\n");
        }
    }
    fclose($st);
}

# close xml document
xmlwriter_end_element($xml);
xmlwriter_end_document($xml);
echo xmlwriter_output_memory($xml);
exit(0);
?>