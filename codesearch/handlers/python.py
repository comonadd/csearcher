import sys, inspect
import re
import os
import pathlib
from codesearch.config import Config
from codesearch.entry import Entry, EntryKind
from pydoc import importfile
import ast
from codesearch.logger import logger


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
    def ref(cls, config: Config, f: pathlib.Path, symname, index=None):
        if index is not None:
            tree = index
        else:
            with open(f, "r") as pyf:
                source = pyf.read()
            tree = ast.parse(source)
        refs_found = []

        def determine_name_of_call_node(node):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id
            elif node.value.func.value.id == symname:
                return node.value.func.value.id
            else:
                logger.warn("Unrecognized call node")
                logger.warn(node)
                return None

        def find_refs_in(body):
            for node in body:
                if isinstance(node, ast.FunctionDef):
                    find_refs_in(node.body)
                elif isinstance(node, ast.Expr):
                    if isinstance(node.value, ast.Call):
                        name = determine_name_of_call_node(node)
                        if name is None:
                            continue
                        if name != symname:
                            continue
                        refs_found.append(
                            Entry(line=node.lineno, kind=EntryKind.Call, name=name)
                        )

        find_refs_in(tree.body)
        return refs_found
        # if isinstance(node, ast.ClassDef):
        #     name = node.name
        #     line = node.lineno
        #     match = re.search(pattern, name)
        #     if not match:
        #         continue
        #     entry = Entry(
        #         line=line, name=name, kind=EntryKind.Class, match=match.span()
        #     )
        #     yield entry

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
