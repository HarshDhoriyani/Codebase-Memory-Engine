from tree_sitter import Node
from .models import ImportInfo

def _get_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def extract_imports(tree, source: bytes, file_path: str) -> list[ImportInfo]:
    imports = []

    def walk(node: Node):
        if node.type == "import_statement":
            for child in node.children:
                if child.type in ("dotted_name", "aliased_import"):
                    module_name = _get_text(child, source).split(" as ")[0].strip()
                    imports.append(ImportInfo(
                        source_file=file_path,
                        imported_module=module_name,
                        imported_names=[],
                        is_relative=False,
                    ))

        elif node.type == "import_from_statement":
            module_node = node.child_by_field_name("module_name")
            module_name = _get_text(module_node, source) if module_node else ""

            is_relative = module_name.startswith(".")

            imported_names = []
            for child in node.children:
                if child.type == "import":
                    continue
                if child.type in ("dotted_name", "identifier"):
                    name = _get_text(child, source)
                    if name != module_name:
                        imported_names.append(name)
                elif child.type == "aliased_import":
                    original = child.child_by_field_name("name")
                    if original:
                        imported_names.append(_get_text(original, source))
            

            imports.append(ImportInfo(
                source_file=file_path,
                imported_module=module_name,
                imported_names=imported_names,
                is_relative=is_relative,
            ))
        

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return imports