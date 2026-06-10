from unittest.mock import MagicMock, patch
from app.graph.queries import (
    what_does_function_call,
    most_complex_functions,
)


def make_mock_record(data: dict):
    record = MagicMock()
    record.keys.return_value = data.keys()
    record.__getitem__ = lambda self, k: data[k]
    record.data.return_value = data
    record.items.return_value = data.items()
    return record


def test_what_does_function_call_returns_list():
    mock_result = [
        make_mock_record({"name": "validate", "file_path": "app/utils.py", "line": 10}),
        make_mock_record({"name": "send", "file_path": "app/email.py", "line": 20}),
    ]

    with patch("app.graph.queries.get_driver") as mock_driver:
        mock_session = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__ = lambda s, *a: mock_session
        mock_driver.return_value.session.return_value.__exit__ = MagicMock(return_value=False)
        result = what_does_function_call("send_email")
        assert isinstance(result, list)

def test_most_complex_functions_returns_list():
    with patch("app.graph.queries.get_driver") as mock_driver:
        mock_session = MagicMock()
        mock_session.run.return_value = []
        mock_driver.return_value.session.return_value.__enter__ = lambda s, *a: mock_session
        mock_driver.return_value.session.return_value.__exit__ = MagicMock(return_value=False)
        result = most_complex_functions(5)
        assert isinstance(result, list)