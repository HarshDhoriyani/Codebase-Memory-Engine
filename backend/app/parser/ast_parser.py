import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Node
from pathlib import Path
from .models import FunctionNode, ParseResult

LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "typescript": Language(tstypescript.language_typescript()),
}

EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

def detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    return EXTENSIONS.get(ext)

def _get_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

def _extract_docstring_python(node: Node, source: bytes) -> str | None:
    body = next((c for c in node.children if c.type == "block"), None)
    if not body:
        return None
    first = next((c for c in body.children if c.type == "expression_statement"), None)
    if not first:
        return None
    string_node = next((c for c in first.children if c.type == "string"), None)
    if not string_node:
        return None
    raw = _get_text(string_node, source).strip("\"' \n")
    return raw if raw else None

def _count_complexity(node: Node) -> int:
    BRANCH_TYPES = {
        "if_statement", "elif_clause", "for_statement", "while_statement", "except_clause", "boolean_operator"
    }
    count = 1

    def walk(n):
        nonlocal count
        if n.type in BRANCH_TYPES:
            count += 1
        for child in n.children:
            walk(child)

    walk(node)
    return count

def extract_functions_python(tree, source: bytes, file_path: str) -> list[FunctionNode]:
    functions = []

    def walk(node: Node):
        if node.type in ("function_definition", "async_function_definition"):
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            return_node = node.child_by_field_name("return_type")

            params = []
            if params_node:
                for p in params_node.children:
                    if p.type in ("identifier", "typed_parameter", "default_parameter"):
                        params.append(_get_text(p, source))

            functions.append(FunctionNode(
                name=_get_text(name_node, source) if name_node else "unknown",
                file_path=file_path,
                language="python",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                params=params,
                return_type=_get_text(return_node, source) if return_node else None,
                docstring=_extract_docstring_python(node, source),
                body=_get_text(node, source),
                complexity=_count_complexity(node),
            ))

        for child in node.children:
            walk(child)
    
    walk(tree.root_node)
    return functions


def parse_file(file_path: str, source_code: str) -> ParseResult:
    language = detect_language(file_path)

    if not language or language not in LANGUAGES:
        return ParseResult(
            file_path=file_path,
            language="unsupported",
            functions=[],
            imports=[],
            total_lines=source_code.count("\n"),
            parse_errors=[f"Unsupported language for {file_path}"]
        )
    
    parser = Parser(LANGUAGES[language])
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    functions = []
    errors = []

    if language == "python":
        functions = extract_functions_python(tree, source_bytes, file_path)

    def find_errors(node):
        if node.type == "ERROR":
            errors.append(f"Parse error at line {node.start_point[0] + 1}")
        for c in node.children:
            find_errors(c)

    find_errors(tree.root_node)

    return ParseResult(
        file_path=file_path,
        language=language,
        functions=functions,
        imports=[],
        total_lines=source_code.count("\n"),
        parse_errors=errors,
    )