import sys
import glob
import os
import re
import pathlib
import json
from pydoc import importfile
from dataclasses import dataclass
from typing import List, Set
from collections import defaultdict
from codesearch.handlers import handler_for_file_type
from codesearch.config import Config, load_config, merge_configs

COL_PINK = '\033[95m'
COL_OKBLUE = '\033[94m'
COL_OKGREEN = '\033[92m'
COL_WARNING = '\033[93m'
COL_FAIL = '\033[91m'
COL_ENDC = '\033[0m'

def cmd_colgen(col: str):
    def cmd_out(text):
        return f"{col}{text}{COL_ENDC}"
    return cmd_out
cmd_green = cmd_colgen(COL_OKGREEN)

def is_excluded(config: Config, fname: str):
    for r in config.exclude:
        if re.search(r, fname):
            return True
    return False

def determine_included_files(config: Config, dir: str):
    all_files = glob.glob(f"{dir}/**", recursive=True)
    excluded_files = set([])
    for pattern in config.exclude:
        subpatterns = [
            glob.glob(f"{dir}/**/{pattern}", recursive=True),
            glob.glob(f"{dir}/{pattern}/**/*", recursive=True),
        ]
        for sp in subpatterns:
            for f in sp:
                excluded_files.add(f)
    filtered_files = [f for f in all_files if f not in excluded_files]
    return filtered_files


class CodeSearch:
    def __init__(self, dir=".", source=None):
        self.dir = dir
        sys.path.append(dir)
        self.config = load_config(dir)
        if self.config.source is not None:
            self.config.source = source
        self.files = determine_included_files(self.config, dir)

    def cls(self, classname):
        cl_pattern = re.compile(classname)
        entries = defaultdict(list)
        for f in self.files:
            handler = handler_for_file_type(f)
            if handler is not None:
                for entry in handler.cls(self.config, f, cl_pattern):
                    print(f"\tClass [{entry['line']}:{entry['col']}]: {entry['class']}")
                    if 'source' in entry:
                        print(entry['source'])

    def fun(self, funname):
        pattern = re.compile(funname)
        entries = defaultdict(list)
        found = False
        for f in self.files:
            handler = handler_for_file_type(f)
            if handler is not None:
                fentries = list(handler.fun(self.config, f, pattern))
                if len(fentries) == 0:
                    continue
                found = True
                print(cmd_green(f))
                for entry in fentries:
                    print(f"\tFunction [{entry['line']}:{entry['col']}]: {entry['class']}")
                    if 'source' in entry:
                        print(entry['source'])
        if not found:
            print("Nothing found")
