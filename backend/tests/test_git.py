from app.git.classifier import (
    classify_commit,
    classify_commits,
    primary_category,
)
from app.git.archaeologist import _parse_changed_lines, _function_was_touched
from app.parser.models import FunctionNode


def test_classifies_bugfix():
    assert classify_commit("fix crash in auth handler") == "bugfix"

def test_classifies_feature():
    assert classify_commit("add support for OAuth2") == "feature"

def test_classifies_refactor():
    assert classify_commit("refactor routing module") == "refactor"

def test_classifies_docs():
    assert classify_commit("update docstring for validate()") == "docs"

def test_classifies_test():
    assert classify_commit("add test coverage for parser") == "test"

def test_classifies_perf():
    assert classify_commit("optimize query performance") == "performance"


def test_primary_category_most_frequent():
    messages = [
        "fix crash",
        "fix null pointer",
        "add feature",
        "fix memory leak",
    ]

    assert primary_category(messages) == "bugfix"

def test_primary_category_empty():
    assert primary_category([]) == "unknown"

def test_classify_commits_counts():
    messages = ["fix bug", "fix crash", "add feature"]
    counts = classify_commits(messages)
    assert counts["bugfix"] == 2
    assert counts["feature"] == 1


SAMPLE_DIFF = """
@@ -10,6 +10,7 @@
    def foo():
+       new_line = True
        existing = 1
-       old_line = 2
        return existing
@@ -25,4 +26,4 @@
    def bar():
-       pass
+       return None    
"""

def test_parses_added_lines():
    lines = _parse_changed_lines(SAMPLE_DIFF)
    assert len(lines) > 0

def test_changed_lines_are_integers():
    lines = _parse_changed_lines(SAMPLE_DIFF)
    assert all(isinstance(l, int) for l in lines)


def make_fn(start: int, end: int) -> FunctionNode:
    return FunctionNode(
        name="test_fn", file_path="test.py",
        language="python", start_line=start,
        end_line=end, params=[], body="", complexity=1,
    )

def test_function_touched_when_lines_overlap():
    fn = make_fn(10, 20)
    changed = {15, 16}
    assert _function_was_touched(fn, changed) is True

def test_function_not_touched_when_no_overlap():
    fn = make_fn(10, 20)
    changed = {25, 30}
    assert _function_was_touched(fn, changed) is False


def test_function_touched_at_boundary():
    fn = make_fn(10, 20)
    assert _function_was_touched(fn, {10}) is True
    assert _function_was_touched(fn, {20}) is True
    assert _function_was_touched(fn, {21}) is False