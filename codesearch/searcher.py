import json
import os
import pathlib
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional

from util import cmd_green, cmd_yellow

from codesearch.config import (
    Config,
    determine_included_files,
    load_config,
    merge_configs,
)
from codesearch.entry import Entries, Entry
from codesearch.handlers import handler_for_file_type
from codesearch.logger import configure_loggers, logger


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
            elif isinstance(entry.match, list):
                [start, end] = entry.match
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


class InvalidDirectoryPath(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'Invalid directory path specified: "{self.path}"'


@dataclass
class CodeSearchIndex:
    by_file: Dict[pathlib.Path, Any] = field(default_factory=dict)


class CodeSearch:
    index: CodeSearchIndex

    def __init__(self, dir=".", source=None, use_index=False):
        if not os.path.exists(dir):
            raise InvalidDirectoryPath(dir)
        configure_loggers(daemon=False)
        self.dir = dir
        sys.path.append(dir)
        self.config = load_config(dir)
        if self.config.source is not None:
            self.config.source = source
        self.files = determine_included_files(self.config, dir)
        self.use_index = use_index
        if use_index:
            self.index = CodeSearchIndex()
            self.build_index()

    def build_index(self):
        logger.info("Building index")
        for f in self.files:
            handler = handler_for_file_type(f)
            if handler is not None:
                idx = handler.index_file(f)
                self.index.by_file[f] = idx
        logger.info("Done")

    def for_all_files_execute_handler(
        self, handler_key: str, search_pattern: str
    ) -> Entries:
        pattern = re.compile(search_pattern)
        entries: Any = defaultdict(dict)
        for f in self.files:
            idx = self.index.by_file.get(f, None) if self.use_index else None
            handler = handler_for_file_type(f)
            if handler is None:
                # Just skip this file since we don't know how to handle it
                continue
            fun = handler.__dict__.get(handler_key)
            if fun is None:
                logger.warn(
                    f'Couldn\'t find action handler "{handler_key}" for file "{f}"',
                )
                continue
            fun = fun.__func__
            fentries = list(fun(handler, self.config, f, pattern, index=idx))
            entries[str(f)] = fentries
        return entries

    def cls(self, classname):
        return self.for_all_files_execute_handler("cls", classname)

    def fun(self, funname):
        return self.for_all_files_execute_handler("fun", funname)

    def ref(self, symname):
        return self.for_all_files_execute_handler("ref", symname)
