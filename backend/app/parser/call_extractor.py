from tree_sitter import Node
from .models import CallEdge, FunctionNode


def _get_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _extract_callee_name(node: Node, source: bytes) -> str | None:
    if node.type == "identifier":
        return _get_text(node, source)
    if node.type == "attribute":
        attr = node.child_by_field_name("attribute")
        if attr:
            return _get_text(attr, source)
    return None


def _get_containing_function(
    line: int,
    functions: list[FunctionNode]
) -> FunctionNode | None:
    """Return whichever function contains this line number."""
    for fn in functions:
        if fn.start_line <= line <= fn.end_line:
            return fn
    return None


def extract_calls(
    tree,
    source: bytes,
    file_path: str,
    functions: list[FunctionNode],
) -> list[CallEdge]:
    known_functions = {fn.name for fn in functions}
    edges = []
    seen = set()  # deduplicate (caller, callee, line)

    def walk(node: Node):
        if node.type == "call":
            call_line = node.start_point[0] + 1
            caller_fn = _get_containing_function(call_line, functions)

            if caller_fn:
                func_node = node.child_by_field_name("function")
                if func_node:
                    callee = _extract_callee_name(func_node, source)
                    key = (caller_fn.name, callee, call_line)

                    if (
                        callee
                        and callee in known_functions
                        and callee != caller_fn.name   # skip recursion
                        and key not in seen
                    ):
                        seen.add(key)
                        edges.append(CallEdge(
                            caller_name=caller_fn.name,
                            caller_file=file_path,
                            callee_name=callee,
                            call_line=call_line,
                        ))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return edges