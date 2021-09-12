import sys, inspect
import re
import os
from codesearch.config import Config
from pydoc import importfile


class PythonHandler:
    @staticmethod
    def cls(config: Config, f: str, cl_pattern):
        fname = os.path.basename(f)
        mod = importfile(f)
        classes = inspect.getmembers(mod, inspect.isclass)
        # filter out all imported classes
        classes = [cl for cl in classes if cl[1].__module__ == mod.__name__]
        # filter out all that don't match the provided pattern
        classes = [cl for cl in classes if re.search(cl_pattern, cl[0])]
        for cname, cl in classes:
            entry = { "line": 0, "col": 0, "class": cname }
            if config.source:
                entry["source"] = inspect.getsource(cl)
            yield entry

    @staticmethod
    def fun(config: Config, f: str, pattern):
        fname = os.path.basename(f)
        mod = importfile(f)
        items = inspect.getmembers(mod, inspect.isfunction)
        # filter out all imported functions
        items = [sym for sym in items if sym[1].__module__ == mod.__name__]
        # filter out all that don't match the provided pattern
        items = [sym for sym in items if re.search(pattern, sym[0])]
        for name, sym in items:
            entry = { "line": 0, "col": 0, "class": name }
            if config.source:
                entry["source"] = inspect.getsource(cl)
            yield entry
