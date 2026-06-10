from .client import get_driver


def what_does_function_call(function_name: str) -> list[dict]:
    query = """
    MATCH (caller:Function {name: $name})-[:CALLS]->(callee:Function)
    RETURN callee.name AS name,
           callee.file_path AS file_path,
           callee.start_line AS line
    ORDER BY callee.name
    """

    with get_driver().session() as session:
        result = session.run(query, name=function_name)
        return [dict(r) for r in result]
    

def what_calls_function(function_name: str) -> list[dict]:
    query = """
    MATCH (caller:Function)-[:CALLS]->(callee:Function {name: $name})
    RETURN caller.name AS name,
           caller.file_path AS file_path,
           caller.start_line AS line
    ORDER BY caller.name
    """

    with get_driver().session() as session:
        result = session.run(query, name=function_name)
        return [dict(r) for r in result]
    

def full_call_chain(function_name: str, max_depth: int=5) -> list[dict]:
    """
    Every function reachable FROM this one through any call chain.
    This is the query that answers 'what does changing X affect?'
    """

    query = """
    MATCH path = (start:Function {name: $name})-[:CALLS*1..$depth]->(end:Function)
    RETURN DISTINCT end.name AS name,
                    end.file_path AS file_path,
                    length(path) AS hops
    ORDER BY hops, end.name
    """

    with get_driver().session() as session:
        result = session.run(query, name=function_name, depth=max_depth)
        return [dict(r) for r in result]
    

def what_imports_module(module_name: str) -> list[dict]:
    query="""
    MATCH (f:File)-[:IMPORTS]->(m:Module)
    WHERE m.name CONTAINS $name
    RETURN f.path AS file_path, m.name AS module
    ORDER BY f.path
    """

    with get_driver().session() as session:
        result = session.run(query, name=module_name)
        return [dict(r) for r in result]
    

def most_complex_functions(limit: int = 10) -> list[dict]:
    query = """
    MATCH (f:Function)
    RETURN f.name AS name,
           f.file_path AS file_path,
           f.complexity AS complexity,
           f.start_line AS line
    ORDER BY f.complexity DESC
    LIMIT $limit
    """

    with get_driver().session() as session:
        result = session.run(query, limit=limit)
        return [dict(r) for r in result]
    


def most_called_functions(limit: int = 10) -> list[dict]:
    query = """
    MATCH (caller:Function)-[:CALLS]->(callee:Function)
    RETURN callee.name AS name,
           callee.file_path AS file_path,
           count(caller) AS call_count
    ORDER BY call_count DESC
    LIMIT $limit
    """

    with get_driver().session() as session:
        result = session.run(query, limit=limit)
        return [dict(r) for r in result]
    


def graph_stats() -> dict:
    with get_driver().session() as session:
        counts = session.run("""
            MATCH (f:File) WITH count(f) AS files
            MATCH (fn:Function) WITH files, count(fn) AS functions
            MATCH (m:Module) WITH files, functions, count(m) AS modules
            MATCH ()-[c:CALLS]->() WITH files, functions, modules, count(c) AS calls
            MATCH ()-[i:IMPORTS]->()
            RETURN files, functions, modules, calls, count(i) AS imports
        """).single()
        return dict(counts) if counts is not None else {}

