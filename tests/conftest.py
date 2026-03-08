"""Shared fixtures for unit tests."""

import base64
import json
from unittest.mock import MagicMock

import grpc
import pytest


SA_KEY = {"id": "key-id", "service_account_id": "sa-id", "private_key": "private-key-data"}
SA_KEY_B64 = base64.b64encode(json.dumps(SA_KEY).encode()).decode()


class FakeRpcError(grpc.RpcError):
    """Minimal grpc.RpcError for testing."""

    def __init__(self, code: grpc.StatusCode, details: str = "test error") -> None:
        self._code = code
        self._details = details

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._details


def rpc_error(code: grpc.StatusCode = grpc.StatusCode.NOT_FOUND) -> FakeRpcError:
    return FakeRpcError(code)


@pytest.fixture
def mock_sdk() -> MagicMock:
    return MagicMock()
