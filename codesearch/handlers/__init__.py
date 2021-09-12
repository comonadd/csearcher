import os
from codesearch.handlers.cpp import CppHandler
from codesearch.handlers.python import PythonHandler


handlers = {
    ".py": PythonHandler,
    ".cpp": CppHandler,
    ".hpp": CppHandler,
    ".cc": CppHandler,
    ".h": CppHandler,
    ".cxx": CppHandler,
}

def handler_for_file_type(f: str):
    _, ext = os.path.splitext(f)
    handler = handlers.get(ext, None)
    return handler
