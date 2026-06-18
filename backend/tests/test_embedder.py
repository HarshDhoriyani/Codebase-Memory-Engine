from app.embedder.embedder import build_function_text, embed_query
from app.embedder.qdrant_store import _stable_id


def test_build_function_text_includes_name():
    fn = {
        "name": "validate_email",
        "file_path": "app/utils.py",
        "params": ["email: str"],
        "return_type": "bool",
        "docstring": "Validates email format",
        "body": "def validate_email(email):\n   return '@' in email",
    }
    text = build_function_text(fn)
    assert "validate_email" in text
    assert "app/utils.py" in text

def test_build_function_text_includes_docstring():
    fn = {
        "name": "foo",
        "file_path": "app/foo.py",
        "params": [],
        "return_type": None,
        "docstring": "This is the docstring",
        "body": "def foo():\n   pass",
    }
    text = build_function_text(fn)
    assert "docstring" in text.lower() or "This is the docstring" in text


def test_build_function_text_no_crash_on_empty():
    fn = {
        "name": "empty",
        "file_path": "app/empty.py",
        "params": [],
        "return_type": None,
        "docstring": "",
        "body": "",
    }
    text = build_function_text(fn)
    assert "empty" in text



def test_stable_id_is_integer():
    fid = "app/utils.py::validate::10"
    assert isinstance(_stable_id(fid), int)


def test_stable_id_is_deterministic():
    fid = "app/utils.py::validate::10"
    assert _stable_id(fid) == _stable_id(fid)


def test_stable_id_different_for_different_inputs():
    assert _stable_id("file_a::foo::1") != _stable_id("file_b::bar::2")


def test_embed_query_returns_vector():
    vec = embed_query("find functions that validate email")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(v, float) for v in vec)