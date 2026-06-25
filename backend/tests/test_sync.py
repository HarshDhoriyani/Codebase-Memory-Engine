from app.sync.differ import hash_file, find_changed_files


def test_hash_file_returns_string():
    result = hash_file("def foo(): pass")
    assert isinstance(result, str)
    assert len(result) == 32   # MD5 hex length


def test_hash_file_deterministic():
    content = "def foo(): pass"
    assert hash_file(content) == hash_file(content)


def test_hash_file_different_for_different_content():
    assert hash_file("def foo(): pass") != hash_file("def bar(): pass")


def test_find_changed_files_detects_new():
    old = {"a.py": "hash1"}
    new = {"a.py": "hash1", "b.py": "hash2"}
    changed, deleted = find_changed_files(old, new)
    assert "b.py" in changed
    assert len(deleted) == 0


def test_find_changed_files_detects_modified():
    old = {"a.py": "hash1"}
    new = {"a.py": "hash2"}   # same file, different hash
    changed, deleted = find_changed_files(old, new)
    assert "a.py" in changed


def test_find_changed_files_detects_deleted():
    old = {"a.py": "hash1", "b.py": "hash2"}
    new = {"a.py": "hash1"}   # b.py removed
    changed, deleted = find_changed_files(old, new)
    assert "b.py" in deleted


def test_find_changed_files_no_changes():
    hashes = {"a.py": "hash1", "b.py": "hash2"}
    changed, deleted = find_changed_files(hashes, hashes)
    assert len(changed) == 0
    assert len(deleted) == 0


def test_find_changed_files_empty():
    changed, deleted = find_changed_files({}, {})
    assert len(changed) == 0
    assert len(deleted) == 0