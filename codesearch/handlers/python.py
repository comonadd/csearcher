import sys, inspect
import re
import os
import pathlib
from codesearch.config import Config
from codesearch.entry import Entry, EntryKind
from pydoc import importfile
import ast


class PythonHandler:
    @classmethod
    def cls(cls, config: Config, f: pathlib.Path, pattern):
        mod = importfile(str(f))
        classes = inspect.getmembers(mod, inspect.isclass)
        # filter out all imported classes
        classes = [cl for cl in classes if cl[1].__module__ == mod.__name__]
        # filter out all that don't match the provided pattern
        for name, sym in classes:
            match = re.search(pattern, name)
            if not match:
                continue
            # TODO: this is kind of slow, use something else?
            line = inspect.findsource(sym)[1] + 1
            entry = Entry(line=line, name=name, kind=EntryKind.Class, match=match)
            if config.source:
                entry["source"] = inspect.getsource(sym)
            yield entry

    @classmethod
    def fun(cls, config: Config, f: pathlib.Path, pattern):
        with open(f, "r") as pyf:
            source = pyf.read()
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                line = node.lineno
                name = node.name
                match = re.search(pattern, name)
                if not match:
                    continue
                entry = Entry(line=line, name=name, kind=EntryKind.Function, match=match)
                yield entry
        return []
