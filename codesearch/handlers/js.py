import re
import os
from codesearch.config import Config
from codesearch.entry import Entry, EntryKind
import esprima


class JSHandler:
    @classmethod
    def parse_file(cls, f: str):
        with open(f, "r") as source:
            program = source.read()
            is_typescript = str(f).endswith(".ts")
            is_jsx = str(f).endswith(".jsx")
            tree = esprima.parse(
                program,
                {
                    "loc": True,
                    "sourceType": "module",
                    "jsx": is_jsx,
                    "typescript": is_typescript,
                },
            )
            return tree

    @classmethod
    def index_file(cls, f: str):
        return cls.parse_file(f)

    @classmethod
    def cls(cls, config: Config, f: str, pattern, index=None):
        if index is None:
            tree = JSHandler.parse_file(f)
        else:
            tree = index
        for item in tree.body:
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

    @classmethod
    def fun(cls, config: Config, f: str, pattern, index=None):
        if index is None:
            tree = JSHandler.parse_file(f)
        else:
            tree = index
        for item in tree.body:
            if (
                item.type == "VariableDeclaration"
                and item.declarations[0].init.type == "ArrowFunctionExpression"
            ):
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
