import os
import re
import os.path
import clang.cindex
from clang.cindex import TokenKind, CursorKind
from codesearch.config import Config


# check if the cursor's type is a template
def is_template(node):
    return hasattr(node, 'type') and node.type.get_num_template_arguments() != -1


class CppHandler:
    idx = clang.cindex.Index.create()
    
    @classmethod
    def cls(cls, config: Config, f: str, pattern):
        tu = cls.idx.parse(f, args=['-std=c++20'], options=0)
        for t in tu.cursor.walk_preorder():
            if t.spelling == '' or is_template(t):
                continue
            if t.kind != CursorKind.CLASS_DECL and t.kind != CursorKind.CLASS_TEMPLATE and t.kind != CursorKind.STRUCT_DECL:
                #print(t.kind)
                continue
            #print(t.location.file.name, f)
            if t.location.file.name != f:
                # skip symbols defined in other files
                continue
            #print(t.spelling)
            line = t.location.line
            column = t.location.column
            if re.search(pattern, t.spelling):
                entry = Entry(line=line, col=column, name=t.spelling, kind=EntryKind.Class)
                yield entry

    @classmethod
    def fun(cls, config: Config, f: str, pattern):
        tu = cls.idx.parse(f, args=['-std=c++20'], options=0)
        for t in tu.cursor.walk_preorder():
            if t.spelling == '' or is_template(t):
                continue
            if t.kind != CursorKind.FUNCTION_DECL:
                continue
            if t.location.file.name != f:
                # skip symbols defined in other files
                continue
            line = t.location.line
            column = t.location.column
            if re.search(pattern, t.spelling):
                entry = Entry(line=line, col=column, name=t.spelling, kind=EntryKind.Function)
                yield entry
