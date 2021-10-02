import os
import re
import os.path
import pathlib
import cpp_handler
from codesearch.config import Config
from codesearch.entry import Entry, EntryKind


class CppHandler:
    @classmethod
    def cls(cls, config: Config, f: pathlib.Path, pattern, index=None):
        entries = cpp_handler.file_cls(str(f), pattern.pattern, bool(index))
        entries = [Entry(kind=EntryKind.Class, **entry) for entry in entries]
        for e in entries:
            yield e

    @classmethod
    def index_file(cls, f: pathlib.Path):
        index = cpp_handler.index_file(str(f))
        return index

    @classmethod
    def fun(cls, config: Config, f: pathlib.Path, pattern: re.Pattern, index=None):
        entries = cpp_handler.file_fun(str(f), pattern.pattern, bool(index))
        entries = [Entry(kind=EntryKind.Function, **entry) for entry in entries]
        for e in entries:
            yield e
