from neo4j import Session
from .client import get_driver
from ..parser.models import DependencyGraph, ParseResult

BATCH_SIZE = 500


def _run_batch(session: Session, query: str, batch: list[dict]):
    session.run(query, {"batch": batch})


def insert_files(session: Session, parse_results: list[ParseResult]):
    query = """
    UNWIND $batch AS row
    MERGE (f:File {path: row.path})
    SET f.language = row.language,
        f.total_lines = row.total_lines
    """

    batch = [
        {
            "path": r.file_path,
            "language": r.language,
            "total_lines": r.total_lines,
        }
        for r in parse_results
        if r.language != "unsupported"
    ]
    for i in range(0, len(batch), BATCH_SIZE):
        _run_batch(session, query, batch[i:i + BATCH_SIZE])
    print(f" Inserted {len(batch)} File nodes")


def insert_functions(session: Session, parse_results: list[ParseResult]):
    query = """
    UNWIND $batch AS row
    MERGE (fn:Function {id: row.id})
    SET fn.name        = row.name,
        fn.file_path   = row.file_path,
        fn.language    = row.language,
        fn.start_line  = row.start_line,
        fn.end_line    = row.end_line,
        fn.complexity  = row.complexity,
        fn.return_type = row.return_type,
        fn.docstring   = row.docstring,
        fn.params      = row.params
    WITH fn, row
    MATCH (f:File {path: row.file_path})
    MERGE (f)-[:DEFINES]->(fn)
    """

    batch = []
    for r in parse_results:
        for fn in r.functions:
            batch.append({
                "id"          : f"{fn.file_path}::{fn.name}::{fn.start_line}",
                "name"        : fn.name,
                "file_path"   : fn.file_path,
                "language"    : fn.language,
                "start_line"  : fn.start_line,
                "end_line"    : fn.end_line,
                "complexity"  : fn.complexity,
                "return_type" : fn.return_type or "",
                "docstring"   : fn.docstring or "",
                "params"      : fn.params,    
            })

    for i in range(0, len(batch), BATCH_SIZE):
        _run_batch(session, query, batch[i:i + BATCH_SIZE])
    print(f" Inserted {len(batch)} Function nodes")



def insert_call_edges(session: Session, graph: DependencyGraph):
    query = """
    UNWIND $batch AS row
    MATCH (caller:Function {name: row.caller_name, file_path: row.caller_file})
    MATCH (callee:Function {name: row.callee_name})
    MERGE (caller)-[:CALLS {line: row.call_line}]->(callee)
    """

    batch = [
        {
            "caller_name": e.caller_name,
            "caller_file": e.caller_file,
            "callee_name": e.callee_name,
            "call_line": e.call_line,
        }
        for e in graph.edges
    ]

    for i in range(0, len(batch), BATCH_SIZE):
        _run_batch(session, query, batch[i:i + BATCH_SIZE])
    print(f" Inserted {len(batch)} CALLS edges")


def insert_imports(session: Session, graph: DependencyGraph):
    query = """
    UNWIND $batch AS row
    MERGE (m:Module {name: row.module})
    WITH m, row
    MATCH (f:File {path: row.path_file})
    MERGE (f)-[:IMPORTS]->(m)
    """

    batch = []
    for file_path, modules in graph.import_map.items():
        for module in modules:
            if module:
                batch.append({
                    "file_path": file_path,
                    "module": module,
                })
    
    for i in range(0, len(batch), BATCH_SIZE):
        _run_batch(session, query, batch[i:i + BATCH_SIZE])
    print(f" Inserted {len(batch)} IMPORTS edges")


def store_graph(parse_results: list[ParseResult], graph: DependencyGraph):
    print("Storing graph in Neo4j...")
    driver = get_driver()
    with driver.session() as session:
        insert_files(session, parse_results)
        insert_functions(session, parse_results)
        insert_call_edges(session, graph)
        insert_imports(session, graph)
    print("Graph stored successfully")
    return {
        "files": graph.total_files,
        "functions": graph.total_functions,
        "edges": graph.total_edges,
    }