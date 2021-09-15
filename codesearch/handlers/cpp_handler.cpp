#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <clang-c/Index.h>  // This is libclang.

#include <filesystem>
#include <functional>
#include <iostream>
#include <regex>
#include <set>
#include <utility>

using namespace std;
namespace fs = std::filesystem;

template <typename Function>
struct function_traits;

template <typename Ret, typename... Args>
struct function_traits<Ret(Args...)> {
  typedef Ret (*ptr)(Args...);
};

template <typename Ret, typename... Args>
struct function_traits<Ret (*const)(Args...)> : function_traits<Ret(Args...)> {
};

template <typename Cls, typename Ret, typename... Args>
struct function_traits<Ret (Cls::*)(Args...) const>
    : function_traits<Ret(Args...)> {};

using voidfun = void (*)();

template <typename F>
voidfun lambda_to_void_function(F lambda) {
  static auto lambda_copy = lambda;

  return []() { lambda_copy(); };
}

// requires C++20
template <typename F>
auto lambda_to_pointer(F lambda) ->
    typename function_traits<decltype(&F::operator())>::ptr {
  static auto lambda_copy = lambda;

  return []<typename... Args>(Args... args) { return lambda_copy(args...); };
}

using u32 = unsigned int;
using i32 = int;

struct Entry {
  const char* name;
  u32 line;
  u32 col;
};

using CursorKinds = std::set<CXCursorKind>;

std::vector<Entry> process_file(CXIndex index,
                                const CursorKinds& predicate_kinds,
                                char const* filename, char const* pattern_s) {
  std::regex pattern(pattern_s, std::regex_constants::ECMAScript |
                                    std::regex_constants::icase);
  CXTranslationUnit unit = clang_parseTranslationUnit(
      index, filename, nullptr, 0, nullptr, 0, CXTranslationUnit_None);
  if (unit == nullptr) {
    cerr << "Unable to parse translation unit: " << filename << endl;
    return {};
  }
  CXCursor cursor = clang_getTranslationUnitCursor(unit);
  std::vector<Entry> entries;
  auto abspath = fs::absolute(filename);
  const char* abspath_cstr = abspath.c_str();
  auto visitor = lambda_to_pointer(
      [&](CXCursor c, CXCursor parent, CXClientData client_data) {
        auto kind = clang_getCursorKind(c);
        if (predicate_kinds.find(kind) != predicate_kinds.end()) {
          auto loc = clang_getCursorLocation(c);
          CXFile file;
          unsigned line = 0;
          unsigned col = 0;
          clang_getSpellingLocation(loc, &file, &line, &col, NULL);
          auto sym_fname = clang_File_tryGetRealPathName(file);
          auto sym_fname_cstr = reinterpret_cast<const char*>(sym_fname.data);
          // skip if symbol defined in another file
          auto clang_str = clang_getCursorSpelling(c);
          auto c_str = reinterpret_cast<const char*>(clang_str.data);
          if (!fs::equivalent(sym_fname_cstr, abspath_cstr)) {
            return CXChildVisit_Recurse;
          }
          if (std::regex_search(c_str, pattern)) {
            entries.push_back(Entry{.name = c_str, .line = line, .col = col});
          }
        }
        return CXChildVisit_Recurse;
      });
  clang_visitChildren(cursor, visitor, nullptr);
  clang_disposeTranslationUnit(unit);
  return entries;
}

static CXIndex _index;

std::set FUNCTION_CURSOR_KINDS = {CXCursor_FunctionDecl};
std::set CLASS_CURSOR_KINDS = {CXCursor_ClassDecl, CXCursor_ClassTemplate,
                               CXCursor_StructDecl};

static PyObject* py_handler_for(PyObject* self, PyObject* args,
                                CursorKinds kinds) {
  const char* filename;
  const char* pattern;
  if (!PyArg_ParseTuple(args, "ss", &filename, &pattern)) {
    return NULL;
  }
  auto entries = process_file(_index, kinds, filename, pattern);
  auto* py_entries = PyList_New(0);
  for (auto& entry : entries) {
    auto* py_entry = PyDict_New();
    PyObject* entry_name = PyUnicode_FromString(entry.name);
    PyDict_SetItemString(py_entry, "name", entry_name);
    PyObject* entry_line = PyLong_FromLong(entry.line);
    PyObject* entry_col = PyLong_FromLong(entry.col);
    PyDict_SetItemString(py_entry, "line", entry_line);
    PyDict_SetItemString(py_entry, "col", entry_col);
    PyList_Append(py_entries, py_entry);
  }
  return py_entries;
}

// find all functions inside of a given file
static PyObject* file_fun(PyObject* self, PyObject* args) {
  return py_handler_for(self, args, FUNCTION_CURSOR_KINDS);
}

static PyObject* file_cls(PyObject* self, PyObject* args) {
  return py_handler_for(self, args, CLASS_CURSOR_KINDS);
}

static PyMethodDef cppHandlerMethods[] = {
    {"file_fun", file_fun, METH_VARARGS, "File functions"},
    {"file_cls", file_cls, METH_VARARGS, "File class declarations"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef cppHandlerModule = {
    PyModuleDef_HEAD_INIT, "cpp_handler", /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,   /* size of per-interpreter state of the module,
             or -1 if the module keeps state in global variables. */
    cppHandlerMethods};

PyMODINIT_FUNC PyInit_cpp_handler(void) {
  // initialize clang index
  _index = clang_createIndex(0, 0);
  return PyModule_Create(&cppHandlerModule);
}

int main(int argc, char* argv[]) {
  wchar_t* program = Py_DecodeLocale(argv[0], NULL);
  if (program == NULL) {
    fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
    exit(1);
  }

  /* Add a built-in module, before Py_Initialize */
  if (PyImport_AppendInittab("cpp_handler", PyInit_cpp_handler) == -1) {
    fprintf(stderr, "Error: could not extend in-built modules table\n");
    exit(1);
  }

  /* Pass argv[0] to the Python interpreter */
  Py_SetProgramName(program);

  /* Initialize the Python interpreter.  Required.
     If this step fails, it will be a fatal error. */
  Py_Initialize();

  /* Optionally import the module; alternatively,
     import can be deferred until the embedded script
     imports it. */
  PyObject* pmodule = PyImport_ImportModule("cpp_handler");
  if (!pmodule) {
    PyErr_Print();
    fprintf(stderr, "Error: could not import module 'spam'\n");
  }

  PyMem_RawFree(program);
  return 0;
}

