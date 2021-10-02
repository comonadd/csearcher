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
    def cls(cls, config: Config, f: pathlib.Path, pattern, index=None):
        if index is not None:
            tree = index
        else:
            with open(f, "r") as pyf:
                source = pyf.read()
            tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                name = node.name
                line = node.lineno
                match = re.search(pattern, name)
                if not match:
                    continue
                entry = Entry(
                    line=line, name=name, kind=EntryKind.Class, match=match.span()
                )
                yield entry

    @classmethod
    def index_file(cls, f: pathlib.Path):
        with open(f, "r") as pyf:
            source = pyf.read()
        tree = ast.parse(source)
        return tree

    @classmethod
    def fun(cls, config: Config, f: pathlib.Path, pattern, index=None):
        if index is not None:
            tree = index
        else:
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
                entry = Entry(
                    line=line, name=name, kind=EntryKind.Function, match=match.span()
                )
                yield entry
        return []
