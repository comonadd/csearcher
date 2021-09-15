import os
from codesearch.handlers.cpp import CppHandler
from codesearch.handlers.python import PythonHandler
from codesearch.handlers.js import JSHandler


handlers = {
    ".py": PythonHandler,
    ".cpp": CppHandler,
    ".hpp": CppHandler,
    ".cc": CppHandler,
    ".h": CppHandler,
    ".cxx": CppHandler,
    ".js": JSHandler,
}

def handler_for_file_type(f: str):
    _, ext = os.path.splitext(f)
    handler = handlers.get(ext, None)
    return handler
