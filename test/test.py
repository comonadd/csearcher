import pytest
import os
import pathlib
from codesearch import *


def test_invalid_dir():
    with pytest.raises(InvalidDirectoryPath):
        c = CodeSearch(dir="./invalid-dir")

tests_root = os.path.dirname(os.path.realpath(__file__))

def test_python_functions():
    pytree = pathlib.Path(tests_root, "python-tree")
    c = CodeSearch(dir=pytree)
    entries = c.fun("some")
    k = f"{pytree}/main.py"
    assert k in entries
    expected_entries = set([
        Entry(line=1, col=0, name="some_fun", kind=EntryKind.Function),
        Entry(line=7, col=0, name="hello_some", kind=EntryKind.Function),
    ])
    assert set(entries[k]) == expected_entries


def test_python_classes():
    pytree = pathlib.Path(tests_root, "python-tree")
    c = CodeSearch(dir=pytree)
    entries = c.cls("Manager")
    k = f"{pytree}/main.py"
    assert k in entries
    expected_entries = set([
        Entry(line=19, col=0, name="CatManager", kind=EntryKind.Class),
        Entry(line=22, col=0, name="CatManagerManager", kind=EntryKind.Class),
        Entry(line=16, col=0, name="Manager", kind=EntryKind.Class),
    ])
    assert set(entries[k]) == expected_entries


def test_js_functions():
    tree = pathlib.Path(tests_root, "js-tree")
    c = CodeSearch(dir=tree)
    entries = c.fun("other")
    k = f"{tree}/es6.js"
    assert k in entries
    expected_entries = set([
        Entry(line=11, col=6, name="anotherFunction", kind=EntryKind.Function),
        Entry(line=18, col=9, name="otherFun", kind=EntryKind.Function),
    ])
    assert set(entries[k]) == expected_entries


def test_js_classes():
    tree = pathlib.Path(tests_root, "js-tree")
    c = CodeSearch(dir=tree)
    entries = c.cls("Hello")
    k = f"{tree}/es6.js"
    assert k in entries
    expected_entries = set([
        Entry(line=15, col=6, name="HelloWorld", kind=EntryKind.Class),
        Entry(line=1, col=6, name="Hello", kind=EntryKind.Class),
    ])
    assert set(entries[k]) == expected_entries
