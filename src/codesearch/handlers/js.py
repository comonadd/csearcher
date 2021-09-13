import re
import os
from codesearch.config import Config
from codesearch.entry import Entry, EntryKind
import esprima


class JSHandler:
    @staticmethod
    def cls(config: Config, f: str, pattern):
        with open(f, "r") as source:
            program = source.read()
        parsed = esprima.parseScript(program, { "loc": True })
        for item in parsed.body:
            if item.type == "ClassDeclaration":
                loc = item.id.loc
                name = item.id.name
            else:
                continue
            if not pattern.search(name):
                continue
            line = loc.start.line
            col = loc.start.column
            yield Entry(line=line, col=col, name=name, kind=EntryKind.Class)
        return []

    @staticmethod
    def fun(config: Config, f: str, pattern):
        with open(f, "r") as source:
            program = source.read()
        parsed = esprima.parseScript(program, { "loc": True })
        for item in parsed.body:
            if item.type == "VariableDeclaration" and item.declarations[0].init.type == "ArrowFunctionExpression":
                # arrow functions
                loc = item.declarations[0].id.loc
                name = item.declarations[0].id.name
            elif item.type == "FunctionDeclaration":
                # regular function declarations
                loc = item.id.loc
                name = item.id.name
            else:
                continue
            if not pattern.search(name):
                continue
            line = loc.start.line
            col = loc.start.column
            yield Entry(line=line, col=col, name=name, kind=EntryKind.Function)
        return []
