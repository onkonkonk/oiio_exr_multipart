#!/usr/bin/python
 
import os
import shutil
import sys
import pathlib
import subprocess
from itertools import groupby

import OpenImageIO as oiio
from OpenImageIO import ImageOutput, ImageBuf, ImageBufAlgo




def get_inputs(default_dir_in):
    global dir_in
    inp_in = str(input("Enter input directory (default: " + str(default_dir_in) + "):")).strip()
    if inp_in == '' :
        dir_in = default_dir_in
        return dir_in
    elif os.path.exists(inp_in) :
        dir_in = inp_in
        return dir_in
    else :
        raise Exception('Input directory does not exist.')


def get_outputs(default_dir_out): 
    global dir_out
    inp_out = str(input("Enter output directory (default: " + str(default_dir_out) + "):")).strip()
    if inp_out == '' :
        dir_out = default_dir_out
        return dir_out
    else :
        if not os.path.exists(inp_out) :
            os.mkdir(inp_out)
        dir_out = inp_out
        return dir_out

###################################

def main():
    
    get_inputs("./in/")
    get_outputs("./out/")

    all_files = []

    for f in os.listdir(dir_in):
        if not f.startswith('.') or not f.startswith('_'):
            files.append(f)

    print(all_files)


if __name__ == "__main__" :

    main()
    sys.exit()