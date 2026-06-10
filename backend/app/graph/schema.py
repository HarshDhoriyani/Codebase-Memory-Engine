from .client import get_driver


CONSTRAINTS = [
    "CREATE CONSTRAINT file_path IF NOT EXISTS "
    "FOR (f:File) REQUIRE f.path IS UNIQUE",

    "CREATE CONSTRAINT function_id IF NOT EXISTS "
    "FOR (f:Function) REQUIRE f.id IS UNIQUE",

    "CREATE CONSTRAINT module_name IF NOT EXISTS "
    "FOR (m:Module) REQUIRE m.name IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX function_name IF NOT EXISTS "
    "FOR (f:Function) ON (f.name)",

    "CREATE INDEX function_file IF NOT EXISTS "
    "FOR (f:Function) ON (f.file_path)",

    "CREATE INDEX function_complexity IF NOT EXISTS "
    "FOR (f:Function) ON (f.complexity)",
]



def setup_schema():
    driver = get_driver()
    with driver.session() as session:
        for constraint in CONSTRAINTS:
            session.run(constraint)
        for index in INDEXES:
            session.run(index)

    print("Neo4j schema ready")

def clear_graph():
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Graph cleared")