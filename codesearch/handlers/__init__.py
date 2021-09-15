import os


def import_python_handler():
    from codesearch.handlers.python import PythonHandler

    return PythonHandler


def import_cpp_handler():
    from codesearch.handlers.cpp import CppHandler

    return CppHandler


def import_js_handler():
    from codesearch.handlers.js import JSHandler

    return JSHandler


handlers = {
    ".py": import_python_handler,
    ".cpp": import_cpp_handler,
    ".hpp": import_cpp_handler,
    ".cc": import_cpp_handler,
    ".h": import_cpp_handler,
    ".cxx": import_cpp_handler,
    ".js": import_js_handler,
}


def handler_for_file_type(f: str):
    _, ext = os.path.splitext(f)
    handler_importer = handlers.get(ext, None)
    if handler_importer is None:
        return None
    handler = handler_importer()
    return handler
