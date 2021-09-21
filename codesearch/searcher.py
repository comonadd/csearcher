import sys
import glob
import os
import re
import pathlib
import json
from dataclasses import dataclass, field
from typing import List, Set, Dict
from collections import defaultdict
from codesearch.handlers import handler_for_file_type
from codesearch.config import Config, load_config, merge_configs
from codesearch.entry import Entry
from timeit import timeit
import cProfile
import fnmatch

COL_PINK = "\033[95m"
COL_OKBLUE = "\033[94m"
COL_OKGREEN = "\033[92m"
COL_WARNING = "\033[93m"
COL_FAIL = "\033[91m"
COL_ENDC = "\033[0m"


def cmd_colgen(col: str):
    def cmd_out(text):
        return f"{col}{text}{COL_ENDC}"

    return cmd_out


cmd_green = cmd_colgen(COL_OKGREEN)
cmd_yellow = cmd_colgen(COL_WARNING)


Entries = Dict[pathlib.Path, List[Entry]]


def determine_included_files(config: Config, dir: str):
    files = []

    def iter(d):
        for f in os.listdir(d):
            skip = any([fnmatch.fnmatch(f, p) for p in config.exclude])
            fp = pathlib.Path(d, f)
            if skip:
                continue
            if os.path.isdir(fp):
                if fp in config.exclude:
                    continue
                iter(fp)
            else:
                files.append(fp)

    iter(dir)
    return files


class InvalidDirectoryPath(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'Invalid directory path specified: "{self.path}"'


class CodeSearch:
    def __init__(self, dir=".", source=None):
        if not os.path.exists(dir):
            raise InvalidDirectoryPath(dir)
        self.dir = dir
        sys.path.append(dir)
        self.config = load_config(dir)
        if self.config.source is not None:
            self.config.source = source
        self.files = determine_included_files(self.config, dir)

    def for_all_files_execute_handler(self, handler_key: str, search_pattern: str):
        pattern = re.compile(search_pattern)
        entries = defaultdict(dict)
        for f in self.files:
            handler = handler_for_file_type(f)
            if handler is not None:
                fun = handler.__dict__[handler_key].__func__
                fentries = list(fun(handler, self.config, f, pattern))
                entries[f] = fentries
        return entries

    def cls(self, classname):
        return self.for_all_files_execute_handler("cls", classname)

    def fun(self, funname):
        return self.for_all_files_execute_handler("fun", funname)


def print_search_results(entries: Entries):
    found_something = False
    for f, fentries in entries.items():
        nothing_in_file = len(fentries) == 0
        if nothing_in_file:
            continue
        print(cmd_green(f))
        for entry in fentries:
            found_something = True
            pt = f"\t{entry.kind} [{entry.line}:{entry.col}]: "
            if entry.match is None:
                start, end = 0, 0
            elif isinstance(entry.match, tuple):
                start, end = entry.match
            elif isinstance(entry.match, re.Match):
                start, end = entry.match.span()
            t = entry.name
            pt += t[:start]
            pt += cmd_yellow(t[start:end])
            pt += t[end:]
            print(pt)
    if not found_something:
        print("Nothing found")
        return


class CodeSearchCLI:
    def __init__(self, dir=".", source=None):
        self.searcher = CodeSearch(dir, source)

    def cls(self, classname):
        print_search_results(self.searcher.cls(classname))

    def fun(self, funname):
        print_search_results(self.searcher.fun(funname))
