import pytest
from app.parser.ast_parser import parse_file

SAMPLE_PYTHON = '''
def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

def greet(name: str):
    print(f"Hello, {name}")

async def fetch_data(url: str, timeout: int = 30):
    """Fetch data from a URL asynchronously."""
    pass
    
def complex_func(a, b, c):
    if a > 0:
        if b > 0:
            return a + b
        elif c > 0:
            return a + c
    for i in range(10):
        print(i)
    return 0
'''

def text_extracts_correct_count():
    result = parse_file("test.py", SAMPLE_PYTHON)
    assert len(result.functions) == 4

def test_function_names():
    result = parse_file("test.py", SAMPLE_PYTHON)
    names = [f.name for f in result.functions]
    assert "add" in names
    assert "greet" in names
    assert "fetch_data" in names
    assert "complex_func" in names

def test_return_type_extracted():
    result = parse_file("test.py", SAMPLE_PYTHON)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert add_fn.return_type == "int"

def test_docstring_extracted():
    result = parse_file("test.py", SAMPLE_PYTHON)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert add_fn.docstring is not None
    assert "Add two numbers" in add_fn.docstring

def test_params_extracted():
    result = parse_file("test.py", SAMPLE_PYTHON)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert len(add_fn.params) == 2

def test_complexity_increases_with_branches():
    result = parse_file("test.py", SAMPLE_PYTHON)
    simple = next(f for f in result.functions if f.name == "greet")
    complex_ = next(f for f in result.functions if f.name == "complex_func")
    assert complex_.complexity > simple.complexity

def test_language_detected():
    result = parse_file("test.py", SAMPLE_PYTHON)
    assert result.language == "python"

def test_unsupported_extension():
    result = parse_file("test.rb", "def foo; end")
    assert result.language == "unsupported"
    assert len(result.parse_errors) > 0

def test_line_numbers_correct():
    result = parse_file("test.py", SAMPLE_PYTHON)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert add_fn.start_line > 0
    assert add_fn.end_line >= add_fn.start_line