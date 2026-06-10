from pydantic import BaseModel
from typing import Optional

class FunctionNode(BaseModel):
    name: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    params: list[str]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    body: str
    complexity: int = 0

class ParseResult(BaseModel):
    file_path: str
    language: str
    functions: list[FunctionNode]
    imports: list[str]
    total_lines: int
    parse_errors: list[str] = []

class ImportInfo(BaseModel):
    source_file: str
    imported_module: str
    imported_names: list[str] = []
    is_relative: bool = False

class CallEdge(BaseModel):
    caller_name: str
    caller_file: str
    callee_name: str
    call_line: int

class GraphNode(BaseModel):
    function: FunctionNode
    calls: list[str] = []
    called_by: list[str] = []
    imports: list[str] = []

class DependencyGraph(BaseModel):
    total_files: int
    total_functions: int
    total_edges: int
    nodes: list[GraphNode]
    edges: list[CallEdge]
    import_map: dict[str, list[str]]
    circular_dependencies: list[list[str]] = []