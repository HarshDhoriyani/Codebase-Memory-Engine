from app.parser.models import FunctionNode
from app.parser.call_extractor import extract_calls
from app.parser.import_extractor import extract_imports
from app.parser.graph_builder import build_dependency_graph, _detect_cycles
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())

def parse(source: str):
    parser = Parser(PY_LANGUAGE)
    source_bytes = source.encode("utf-8")
    return parser.parse(source_bytes), source_bytes



IMPORT_SAMPLE = """
import os
import sys
from fastapi import APIRouter, Depends
from . import utils
from ..models import User
"""


def test_extracts_simple_imports():
    tree, src = parse(IMPORT_SAMPLE)
    imports = extract_imports(tree, src, "app/routes.py")
    modules = [i.imported_module for i in imports]
    assert "os" in modules
    assert "sys" in modules

def test_extracts_from_imports():
    tree, src = parse(IMPORT_SAMPLE)
    imports = extract_imports(tree, src, "app/routes.py")
    fastapi_import = next(i for i in imports if "fastapi" in i.imported_module)
    assert "APIRouter" in fastapi_import.imported_names
    assert "Depends" in fastapi_import.imported_names

def test_detects_relative_imports():
    tree, src = parse(IMPORT_SAMPLE)
    imports = extract_imports(tree, src, "app/routes.py")
    relative = [i for i in imports if i.is_relative]
    assert len(relative) >= 1


CALL_SAMPLE = """
def validate(email):
    return "@" in email

def send_email(email):
    if validate(email):
        print("sending")

def process(email):
    send_email(email)
    validate(email)
"""

def make_functions(names_lines):
    return [
        FunctionNode(
            name=n, file_path="test.py", language="python",
            start_line=s, end_line=e,
            params=[], body="", complexity=1
        )
        for n, s, e in names_lines
    ]

def test_detects_direct_calls():
    tree, src = parse(CALL_SAMPLE)
    fns = make_functions([
        ("validate", 2, 3),
        ("send_email", 5, 7),
        ("process", 9, 11),
    ])
    edges = extract_calls(tree, src, "test.py", fns)
    callers = [(e.caller_name, e.callee_name) for e in edges]
    assert ("send_email", "validate") in callers
    assert ("process", "send_email") in callers
    assert ("process", "validate") in callers

def test_no_self_loops():
    source = "def foo():\n  foo()\n"
    tree, src = parse(source)
    fns = make_functions([("foo", 1, 2)])
    edges = extract_calls(tree, src, "test.py", fns)
    assert all(e.caller_name != e.callee_name for e in edges)

def test_detects_circular_dependency():
    import_map = {
        "a.py": ["b.py"],
        "b.py": ["c.py"],
        "c.py": ["a.py"],
    }

    cycles = _detect_cycles(import_map)
    assert len(cycles) > 0

def test_no_false_positive_cycles():
    import_map = {
        "a.py": ["b.py"],
        "b.py": ["c.py"],
        "c.py": [],
    }
    cycles = _detect_cycles(import_map)
    assert len(cycles) == 0