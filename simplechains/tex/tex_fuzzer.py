#!/usr/bin/env python3

import subprocess
import os
import re
from stateless.status import *

def validate_tex(input_str, min_input_len, trace):
    """ return:
        rv: "complete", "incomplete" or "wrong",
        n: the index of the character -1 if not applicable
        c: the character where error happened  "" if not applicable
    """
    try:
        # Construct the command using an f-string for better readability
        cmd = f"echo '{input_str}' | sudo tee test.tex > /dev/null 2>&1 && sed -i -e 's/(backslash)/\\\/g' test.tex && echo 'test.tex \\\end' | tex > test.log"
        
        # Execute the command using subprocess.run
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        excode = result.returncode

        # Read the output from test.log
        file_out = ''
        try:
            with open('test.log', 'r') as file:
                Lines = file.readlines()
                file_out = ' '.join([line.strip() for line in Lines])
        except FileNotFoundError:
            # If test.log does not exist, treat it as an error or handle accordingly
            Lines = []
            file_out = ''

        nout = len(Lines)
        input_len = len(input_str)

        if excode != 0 and excode != 1:
            print("\n++++++++++++++++ Crash or Bug found! ++++++++++++++++")
            print("Exit code:", excode)
            print("String:", input_str)
            save_crash(input_str, str(excode))

        if nout == 4: # Valid input
            if input_len > min_input_len:
                if min_input_len != -1: # -1 means we are inside a recursion and we are testing if input is incomplete. Hence don't save input.
                    save_valid_input(input_str)
                return Status.Complete, -1, ""
            else:
                return Status.Incomplete, -1, "" # Append more

        elif "Missing $ inserted." in file_out:
            if 'a$' in trace:
                input_str = close_string(input_str, trace)
                rv, n, x = validate_tex(input_str, -1, [])
                if rv == Status.Complete:
                    return Status.Incomplete, -1, "" # Append more
                else:
                    return Status.Incorrect, -1, ""
            else:
                return Status.Incorrect, -1, ""

        elif ("Runaway argument?" in file_out or
              "Runaway text?" in file_out or
              "Missing } inserted." in file_out or
              "Missing { inserted." in file_out or
              "(\end occurred inside a group at level" in file_out):
            if not trace:
                return Status.Incorrect, -1, ""
            input_str = close_string(input_str, trace)
            rv, n, x = validate_tex(input_str, -1, [])
            if rv == Status.Complete:
                return Status.Incomplete, -1, "" # Append more
            else:
                return Status.Incorrect, -1, ""

        else:
            return Status.Incorrect, -1, ""

    except subprocess.TimeoutExpired:
        print("Command timed out.")
        return Status.Incorrect, -1, ""
    except Exception as e:
        print(f"Exception occurred: {e}")
        return Status.Incorrect, -1, ""


def close_string(curr_input, trace):
    # Assuming 'trace' is a list of characters to append
    return curr_input + ''.join(trace)


def save_valid_input(created_string):
    with open("valid_inputs.txt", "a") as myfile:
        var = repr(created_string) + "\n"
        myfile.write(var)


def save_crash(created_string, code):
    with open("crashes.txt", "a") as myfile:
        var = f"Exit code: {code} Input: {repr(created_string)}\n"
        myfile.write(var)
