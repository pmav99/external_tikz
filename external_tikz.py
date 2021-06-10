#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

file : external_tikz.py
Python version : 3
author : Panagiotis Mavrogiorgos (gmail.com pmav99)
Licence : MIT

Short Description
-----------
This script automates the external compilation of tikz source files (TSF).

Long Description
----------------
The script searches for TSFs within its folder and in all the subfolders.
MASTER_FILE's preamble is used for the compilation of all the TSFs.
The used compiler is specified by the COMPILER variable.

The first time the script runs, all the TSFs are (re)compiled.
Each compilation happens at the same folder as the TSF.
The produced pdfs have the same name as the TSFs.
All the auxiliary files are removed after the compilation.

After the compilation of all the TSFs has finished, the names and the
modification time of the TSFs are stored in a pickled dictionary.

On subsequent runs, if there are new TSFs or if the old TSFs have been modified
since last time the script was called, they are recompiled.

Notes
-----
1. Basic command line arguments (see options with -h). In order to change the
   settings you should edit the script.
2. The script must be placed on the same folder as the MASTER_FILE.
3. The pickled dictionary is stored in a file whose name is specified
   by the PICKLE_FILE variable. It is stored in the same folder as the
   MASTER_FILE.
4. All the TSF must have the extension specified by the EXT variable.
5. If in order to compile the TSF you must use packages/options that
   are not included in the preamble of the main file, then you can
   specify them in the PREVIEW variable (e.g. the `preview` package).
6. The MASTER_FILE cannot input/import other tex files!
7. If there are major changes in the main tex files preamble (font
   changes etc) then in order to recompile all the TSF, just erase
   the PICKLE_FILE.


Licence (MIT)
-------------

Copyright (c) 2011, Panagiotis Mavrogiorgos.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
import os
import os.path
import pickle
import subprocess
import argparse

PICKLE_FILE = "external_tikz.pickle"
MASTER_FILE = "preamble_tikz.tex"
EXT = "tikz"
COMPILER = "xelatex"
COMPILER_OPTIONS = []
COMPILATION_EXTENSIONS = ["aux", "log", "tex", "out", "bcf", "run.xml"]
PREVIEW = r"""
\usepackage[xetex,active,displaymath,tightpage]{preview}
\PreviewEnvironment[]{tikzpicture}
\PreviewEnvironment[]{pgfpicture}
"""

def read_preamble(main_dir, preview):
    """
    Read the preamble of the main tex file.
    """
    preamble = ""
    with open(os.path.join(main_dir, MASTER_FILE), "r") as f:
        for line in f:
            if line == "\\begin{document}\n":
                break
            preamble += line
        preamble += preview
        preamble += "\\begin{document}\n"
    return preamble

def read_source_files(cwd, ext):
    """
    Read the tikz source filenames and their modification time.
    Return a dictionary.
    """
    new ={}
    for (path, dirs, files) in os.walk(cwd):
        for f in files:
            if f.endswith(ext):
                full_path = os.path.join(path,f)
                new[full_path] = os.path.getmtime(full_path)
    return new

def read_stored_data(cwd, pickle_file):
    """
    Check if the stored data (pickled) exist. If they exist read them.
    Return a dictionary.
    """
    if pickle_file not in os.listdir(cwd):
        old = {}
    else:
        with open(pickle_file, "rb") as f:
            old = pickle.load(f)
    return old

def create_tex_file(main_path, preview, tsf_path):
    """
    Create the source file and write it to disk at the same folder as the tsf.
    """
    tex_source = read_preamble(main_path, preview)

    with open(tsf_path, "r") as f:
        tex_source += f.read()
    tex_source += "\n\\end{document}"

    tex_path = tsf_path[:-len(EXT)] + "tex"

    with open(tex_path, "w") as f:
        f.write(tex_source)

def create_pdf(compiler, tsf_dir, tsf_name):
    """
    Run XeLaTeX to the source file and copy the pdf to the same folder as the
    tikz source code. If the main file  and the TSF exist in the same folder
    it is not moved.
    """
    os.chdir(tsf_dir)              # Change working directory

    name = tsf_name[:-len(EXT)]
    pdf_name = name + "pdf"
    tex_name = name + "tex"

    try: # old file removal
        os.remove(pdf_name)
    except OSError:
        print("File doesn't exists. Creating for the first time.")

    # Formulate compiler string
    compiler_string = '%s' % compiler
    for option in COMPILER_OPTIONS:
        compiler_string += " ".join(option)
    compiler_string += ' %s' % tex_name

    subprocess.call('%s' % (compiler_string), shell=True)

    for ext in COMPILATION_EXTENSIONS:
        f = name + ext
        try:
            os.remove(f)
        except:
            pass

def main():
    main_dir = os.path.abspath(os.curdir)
    main_path = os.path.join(main_dir, MASTER_FILE)

    parser = argparse.ArgumentParser(description='Auto-compiles tikz source files.')

    parser.add_argument('-f', '--files', dest='files', metavar = None,
                       help='Input a tikz file list to be compiled.')

    parser.add_argument('-a', '--recompile-all', dest='recompile_all',
                       help='Recompiles all the tikz files.', action = 'store_true')

    args = parser.parse_args()

    # if the -a flag has been passed, erase the pickle file.
    if args.recompile_all is True:
        try:
            os.remove(os.path.join(os.path.dirname(main_path), PICKLE_FILE))
        except:
            pass

    # Read and compare the new and the old dicts
    # if the entries have been modified since last time or if there is a new entry
    # create a temporary file and compile it with xelatex
    # then move the newly created pdf to the same folder as the tikz source file.
    old = read_stored_data(main_dir, PICKLE_FILE)
    new = read_source_files(main_dir, EXT)
    for (tsf_path, mod_time) in new.items():
        if tsf_path not in old or mod_time != old[tsf_path]:

            tsf_name = os.path.basename(tsf_path)
            tsf_dir = os.path.dirname(tsf_path)

            create_tex_file(main_dir, PREVIEW, tsf_path)

            create_pdf(COMPILER, tsf_dir, tsf_name)
            #----------------------------------------------------------------------
            # clean up code
            # The created extensions depend on the packages used in the preamble
            # If leftover, files are found, then just add more entires in the
            # following tuple.

    #-------------------------------------------------------------------------------
    # pickle the new data
    os.chdir(main_dir)
    with open(PICKLE_FILE, "w") as f:
        pickle.dump(new, f)

if __name__ == "__main__":
    main()




