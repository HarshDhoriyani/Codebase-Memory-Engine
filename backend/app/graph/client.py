from neo4j import GraphDatabase, Driver
from functools import lru_cache
import os

@lru_cache(maxsize=1)
def get_driver() -> Driver:
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password123")
    return GraphDatabase.driver(uri, auth=(user, password))


def close_driver():
    get_driver().close()

def is_connected() -> bool:
    try:
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False