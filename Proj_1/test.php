#!/usr/bin/env php
<?php

# checks for substring in an array
function substr_in_array($needle, array $haystack){
    foreach($haystack as $item){
        if(false !== strpos($item, $needle)){
            return false;
        }
    }
    return true;
}

# gets full path
function get_path($full_string){
    $path_regex = "/(?<==).*/";
    preg_match($path_regex, $full_string, $match);
    return $match[0];
}

# prints out help
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

# generates html head
function generate_html_head(){
    echo "<!DOCTYPE html>\n";
    echo "<html>\n";

    echo "    <head>\n";
    echo "        <meta charset=\"UTF-8\">\n";
    echo "        <title>IPP Projekt</title>\n";
    echo "        <style>\n";

    echo "            body{\n";
    echo "                background-color:rgb(255, 175, 231);\n";
    echo "                font-family: \"Times New Roman\", Times, serif;\n";
    echo "            }\n";

    echo "            h1{\n";
    echo "                font-size: 42px;\n";
    echo "                text-align: center;\n";
    echo "                padding: 5px;\n";
    echo "                margin-bottom: 5%;\n";
    echo "            }\n";

    echo "            h3{\n";
    echo "                margin-bottom: 1.5%;\n";
    echo "                line-height: 0%;\n";
    echo "            }\n";

    echo "            table, td, tr{\n";
    echo "                border-collapse: collapse;\n";
    echo "                width: 800px;\n";
    echo "            }\n";

    echo "            td, tr{\n";
    echo "                text-align: left;\n";
    echo "            }\n";
    echo "        </style>\n";

    echo "    </head>\n";

    echo "        <h1>Tests for IPP Project 2018/2019</h1>\n";

    $real_input = $GLOBALS['argv'];
    echo "        <h3>Tests were run with these parameters:";
    if(count($real_input) == 1){
        echo " None";
    }
    for($i = 1; $i < count($real_input); $i++){
        if($real_input[$i] == true){
            echo " $real_input[$i]";
        }
    }
    echo "</h3><br>\n";
    echo "        <h3>Script run these tests:</h3>\n";
    echo "        <table>\n";
    echo "            <tr>\n";
    echo "                <th>No.</th>\n";
    echo "                <th>Path</th>\n";
    echo "                <th>Filename</th>\n";
    echo "                <th>Status</th>\n";
    echo "            </tr>\n";
}

# adds the html tail
function generate_html_tail(){
    $all_tests = $GLOBALS['total_counter'];
    $ok_tests = $GLOBALS['passed_counter'];
    $fail = $GLOBALS['failed_counter'];

    if($all_tests > 0){
        $success_rate = ($ok_tests / $all_tests)* 100;
    }
    else{
        $success_rate = 0;
    }

    echo "        </table><br>\n";
    echo "        <h3>Summary:</h3>\n";
    echo "        <table style=\"width: 300px\">\n";
    echo "            <tr>\n";
    echo "                <td>Number of tests</td>\n";
    echo "                <td>$all_tests</td>\n";
    echo "            </tr>\n";
    echo "            <tr>\n";
    echo "                <td>Successful tests</td>\n";
    echo "                <td>$ok_tests</td>\n";
    echo "            </tr>\n";
    echo "            <tr>\n";
    echo "                <td>Failed tests</td>\n";
    echo "                <td>$fail</td>\n";
    echo "            </tr>\n";
    echo "            <tr>\n";
    echo "                <td>Success rate</td>\n";
    echo "                <td>$success_rate%</td>\n";
    echo "            </tr>\n";
    echo "        </table>\n";
    echo "    </body>\n";
    echo "</html>\n";
}

# generates all the output
function prepare_html(){
    generate_html_head();
    Tests::run_tests($GLOBALS['directory_path']);
    generate_html_tail();
}


#                           #
#           MAIN            #
#                           #

# array of all possible arguments
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

# all paths
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
        if(strpos($key, "--int-script=") !== false){
            $int_script = get_path($key);
            $arguments["int-script="] = true;
        }
        if(strpos($key, "--parse-script=") !== false){
            $parse_script = get_path($key);
            $arguments["parse-script="] = true;
        }
        if(strpos($key, "--directory=") !== false){
            $directory_path = get_path($key);
            $arguments["--directory="] = true;
        }

        $arguments[$key] = true;
    }
    else{
        fwrite(STDERR, "Invalid argument\n");
        exit(10);
    }
}

# checks for forbidden combination
if($arguments["--parse-only"] == true and $arguments["--int-only"] == true){
    fwrite(STDERR, "Combination of --parse-only and --int-only is not allowed\n");
    exit(10);
}

# check for help and correct number of arguments
if($arguments["--help"] == true){
    if($argc != 2){
        fwrite(STDERR, "--help cannot be combined with other arguments\n");
        exit(10);
    }
    else{
        print_help();
        exit(0);
    }
}

#set directories if empty
if(empty($directory_path)){
    $directory_path = getcwd();
}

if(empty($parse_script)){
    $parse_script = getcwd() . "/parse.php";
}

if(empty($int_script)){
    $int_script = getcwd() . "/interpret.py";
}


# check their existence
if(!file_exists($directory_path)){
    fwrite(STDERR, "$directory_path doesn't exist\n");
    exit(11);
}

if(!file_exists($parse_script)){
    fwrite(STDERR, "$parse_script doesn't exist\n");
    exit(11);
}

if(!file_exists($int_script)){
    fwrite(STDERR, "$int_script doesn't exist\n");
    exit(11);
}

# prepares the top part of html and css
prepare_html();

# class for all the tests
class Tests{
    # runs tests for the current directory
    public static function run_tests($directory_path){
        $arguments = $GLOBALS['arguments'];
        # open particular directory
        $dir_handle = opendir($directory_path);
        
        # reads file from the current directory
        while($current_file = readdir($dir_handle)){
            # just skip the . and .. files
            if($current_file == "." or $current_file == ".."){
                continue;
            }
            
            # check whether it is directory, if yes, check for the recursive parameter
            if(is_dir("$directory_path" . "/" . "$current_file") and $arguments['--recursive']){
                self::run_tests("$directory_path" . "/" . "$current_file"); # resursiveley call this function
            }   # we found a file
            elseif(is_file("$directory_path" . "/" . "$current_file")){
                $full_path = "$directory_path" . "/" . "$current_file";
                $extension = pathinfo($full_path, PATHINFO_EXTENSION);
                if($extension == "src"){    # our file has the appropriate extension
                    self::prepare_files(pathinfo($full_path, PATHINFO_FILENAME), $directory_path);
                    self::run_test($directory_path, pathinfo($full_path, PATHINFO_FILENAME), $arguments['--parse-only'], $arguments['--int-only']);
                }
            }
        }
    }

    # checks for existence of all the other files, if not, generate new
    public static function prepare_files($file_name, $directory_path){
        if(!file_exists("$directory_path" . "/" . "$file_name" . ".in")){ # .in file
            touch("$directory_path" . "/" . "$file_name" . ".in");
        }
        if(!file_exists("$directory_path" . "/" . "$file_name" . ".out")){
            touch("$directory_path" . "/" . "$file_name" . ".out");
        }
        if(!file_exists("$directory_path" . "/" . "$file_name" . ".rc")){
            touch("$directory_path" . "/" . "$file_name" . ".rc");
            exec('echo "0" >' . "$directory_path" . "/" . "$file_name" . ".rc");
        }
    }

    # runs that particular code
    public static function run_test($directory_path, $file, $parse_only, $int_only){
        $GLOBALS['total_counter']++;
        $test_num = $GLOBALS['total_counter'];
        $exit_array = "";
        $exit_code = -1;

        # get expected return code
        $f = fopen($directory_path . "/" . $file . ".rc", 'r');
        $expected_rc = fgets($f);
        fclose($f);

        if($parse_only){    # we test only parser
            exec('php7.3 ' . $GLOBALS['parse_script'] . ' < ' . $directory_path . '/' . $file . '.src > tmp_output_test', $exit_array, $exit_code); ### !!!!!!!!!!!! PHPHP VERSION
            if($exit_code == $expected_rc){
                if($exit_code == 0){    # also check the output
                    exec('xmldiff tmp_output_test ' . $directory_path . "/" . $file . ".out > tmp_xml_test");
                    if("\n" == file_get_contents("tmp_xml_test")){
                        $GLOBALS['passed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                    }
                    else{
                        $GLOBALS['failed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, false);
                    }
                    exec('rm -f tmp_xml_test');
                } # don't check the output
                else{
                    $GLOBALS['passed_counter']++;
                    self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                }
            }   # even the return codes didn't match
            else{
                $GLOBALS['failed_counter']++;
                self::test_result($test_num, $directory_path . "/" . $file, $file, false);
            }
            exec('rm -f tmp_output_test');
        }
        elseif($int_only){  # we test only interpreter
            exec('python3.6 ' . $GLOBALS['int_script'] . '--source=' . $file . '.src input=' . $file . '.in > tmp_output_test', $exit_array, $exit_code); #### PYTHON VERSION
            if($exit_code == $expected_rc){
                if($exit_code == 0){    # also check the output
                    exec('diff tmp_output_test ' . $directory_path . "/" . $file . ".out > tmp_diff_output");
                    if(0 == filesize("tmp_diff_output")){
                        $GLOBALS['passed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                    }
                    else{
                        $GLOBALS['failed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, false);
                    }
                    exec('rm -f tmp_diff_output');
                }   # don't check the output
                else{
                    $GLOBALS['passed_counter']++;
                    self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                }
            }
            else{   # the return codes didn't match at all
                $GLOBALS['failed_counter']++;
                self::test_result($test_num, $directory_path . "/" . $file, $file, false);
            }
            exec('rm -f tmp_output_test');
        }
        else{               # testing both
            exec('php7.3 ' . $GLOBALS['parse_script'] . ' < ' . $directory_path . '/' . $file . '.src > tmp_output_test_php', $exit_array, $exit_code); ### !!!!!!!!!!!! PHPHP VERSION
            exec('python3.6 ' . $GLOBALS['int_script'] . ' --source=tmp_output_test_php input=' . $file . '.in > tmp_output_test', $exit_array, $exit_code); #### PYTHON VERSION
            if($exit_code == $expected_rc){
                if($exit_code == 0){ # also check the output
                    exec('diff tmp_output_test ' . $directory_path . "/" . $file . ".out > tmp_diff_output");
                    if(0 == filesize("tmp_diff_output")){
                        $GLOBALS['passed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                    }
                    else{
                        $GLOBALS['failed_counter']++;
                        self::test_result($test_num, $directory_path . "/" . $file, $file, false);
                    }
                    exec('rm -f tmp_diff_output');
                }   # don't check the output
                else{
                    $GLOBALS['passed_counter']++;
                    self::test_result($test_num, $directory_path . "/" . $file, $file, true);
                }
            }   # the return codes didn't even match
            else{
                $GLOBALS['failed_counter']++;
                self::test_result($test_num, $directory_path . "/" . $file, $file, false);
            }
            exec("tmp_output_test");
        }
    }

    # function for concatenating the test result to our html
    public static function test_result($num, $path, $file, $result){
        echo "            <tr>\n";
        echo "                <td>$num</td>\n";
        echo "                <td>$path</td>\n";
        echo "                <td>$file</td>\n";
        if($result){    # success
            echo "                <td style=\"color:green\">pass</td>\n";
        }
        else{           # fail
            echo "                <td style=\"color:red\">fail</td>\n";
        }
        echo "            </tr>\n";
    }
}
?>
