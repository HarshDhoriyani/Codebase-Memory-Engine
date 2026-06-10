from .models import ParseResult, GraphNode, CallEdge, ImportInfo, DependencyGraph
from .import_extractor import extract_imports
from .call_extractor import extract_calls
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())


def _reparse(source_code: str):
    parser = Parser(PY_LANGUAGE)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    return tree, source_bytes


def _detect_cycles(import_map: dict) -> list:
    visited = set()
    cycles = []

    def dfs(node, path, in_stack):
        if node in in_stack:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        path.append(node)
        for neighbour in import_map.get(node, []):
            dfs(neighbour, path, in_stack)
        path.pop()
        in_stack.discard(node)

    for node in import_map:
        if node not in visited:
            dfs(node, [], set())

    return cycles


def build_dependency_graph(parse_results: list, source_map: dict) -> DependencyGraph:
    all_edges = []
    all_imports = []
    import_map = {}

    # pass 1 — extract imports + call edges from every file
    for result in parse_results:
        if result.language != "python":
            continue
        source = source_map.get(result.file_path)
        if not source:
            continue

        tree, source_bytes = _reparse(source)

        file_imports = extract_imports(tree, source_bytes, result.file_path)
        all_imports.extend(file_imports)
        import_map[result.file_path] = [i.imported_module for i in file_imports]

        if result.functions:
            file_edges = extract_calls(
                tree, source_bytes, result.file_path, result.functions
            )
            all_edges.extend(file_edges)

    # pass 2 — build GraphNodes
    calls_map = {}
    called_by_map = {}

    for edge in all_edges:
        calls_map.setdefault(edge.caller_name, []).append(edge.callee_name)
        called_by_map.setdefault(edge.callee_name, []).append(edge.caller_name)

    graph_nodes = []
    for result in parse_results:
        file_import_modules = import_map.get(result.file_path, [])
        for fn in result.functions:
            graph_nodes.append(GraphNode(
                function=fn,
                calls=list(set(calls_map.get(fn.name, []))),
                called_by=list(set(called_by_map.get(fn.name, []))),
                imports=file_import_modules,
            ))

    # pass 3 — detect circular dependencies
    cycles = _detect_cycles(import_map)

    total_files = len(parse_results)
    total_functions = sum(len(r.functions) for r in parse_results)
    total_edges = len(all_edges)

    return DependencyGraph(
        nodes=graph_nodes,
        edges=all_edges,
        import_map=import_map,
        circular_dependencies=cycles,
        total_files=total_files,
        total_functions=total_functions,
        total_edges=total_edges,
    )