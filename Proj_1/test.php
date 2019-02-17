#!/usr/bin/env php
<?php

#
function substr_in_array($needle, array $haystack){
    foreach($haystack as $item){
        if(false !== strpos($item, $needle)){
            return false;
        }
    }
    return true;
}

#
function get_path($full_string){
    $path_regex = "/(?<==).*/";
    preg_match($path_regex, $full_string, $match);
    return $match[0];
}

#
function set_current_directory(){
    return getcwd();
}

#
function print_help(){
    fwrite(STDOUT, "Script is run as: php test.php\n");
    fwrite(STDOUT, "With optional parameters:\n");
    fwrite(STDOUT, "--help : outputs help\n");
    fwrite(STDOUT, "--directory=path : directory, where the tests are located (if no path is given, default directory is current working directory\n");
    fwrite(STDOUT, "--recursive : tests from all subdirectories will be run\n");
    fwrite(STDOUT, "--parse-script=file : name of the parser file; if no file is given, it will take parse.php from current working directory\n");
    fwrite(STDOUT, "--int-script=file : name of interpreter file; if no file is given, it will take interpret.py from current working directory\n");
    fwrite(STDOUT, "--parse-only : only tests parser; cannot be combined with --int-only\n");
    fwrite(STDOUT, "--int-only : only tests iterpreter; cannot be combined with --parse-only\n");
}

function prepare_html(){
    
}

#
$arguments = array(
    "test.php" => false,
    "--help" => false,
    "--directory=" => false,
    "--recursive" => false,
    "--parse-script=" => false,
    "--int-script=" => false,
    "--parse-only" => false,
    "--int-only" => false,
);

#
$directory_path = "";
$parse_script = "";
$int_script = "";

# test counter
$total_counter = 0;
$passed_counter = 0;
$failed_counter = 0;

# set my arguments
foreach($argv as $key){
    if(substr_in_array($key, $arguments)){
        $arguments[$key] = true;
        if(strpos($key, "--int-script=") !== false){
            $int_script = get_path($key);
        }
        elseif(strpos($key, "--parse-script=") !== false){
            $parse_script = get_path($key);
        }
        elseif(strpos($key, "--directory") !== false){
            $directory_path = get_path($key);
        }
    }
    else{
        fwrite(STDERR, "Invalid argument\n");
        return 10;
    }
}

# checks for forbidden combination
if($arguments["--parse-only"] == true and $arguments["--int-only"] == true){
    fwrite(STDERR, "Combination of --parse-only and --int-only is not allowed\n");
    return 10;
}

if($arguments["--help"] == true){
    if($argc != 2){
        fwrite(STDERR, "--help cannot be combined with other arguments\n");
        return 10;
    }
    else{
        print_help();
        return 0;
    }
}


#set directories if empty
if(empty($directory_path)){
    $directory_path = set_current_directory();
}

if(empty($parse_script)){
    $parse_script = set_current_directory() . "/parse.php";
}

if(empty($int_script)){
    $int_script = set_current_directory() . "/interpret.py";
}

# check their existence
if(!file_exists($directory_path)){
    fwrite(STDERR, "$directory_path doesn't exist\n");
    return 11;
}

if(!file_exists($parse_script)){
    fwrite(STDERR, "$parse_script doesn't exist\n");
    return 11;
}

if(!file_exists($int_script)){
    fwrite(STDERR, "$int_script doesn't exist\n");
    return 11;
}

#var_dump($arguments);
#echo "Directory path is $directory_path\n";
#echo "Parse script is $parse_script\n";
#echo "Int script is $int_script\n";



?>