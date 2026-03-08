"""Tests for yc_common helpers."""

import base64
from unittest.mock import MagicMock

import pytest
import yc_common
from conftest import SA_KEY_B64


class TestSdkFromKeyB64:
    def test_valid_key(self, mocker):
        mocker.patch("yandexcloud.SDK", return_value=MagicMock())
        sdk = yc_common._sdk_from_key_b64(SA_KEY_B64)
        assert sdk is not None

    def test_invalid_base64(self):
        with pytest.raises(SystemExit):
            yc_common._sdk_from_key_b64("not-valid-base64!!!")

    def test_invalid_json(self):
        bad = base64.b64encode(b"not-json").decode()
        with pytest.raises(SystemExit):
            yc_common._sdk_from_key_b64(bad)


class TestLoadSdkFromStorage:
    def test_missing_env_exits(self, monkeypatch):
        monkeypatch.delenv("RD_CONFIG_YC_SA_KEY", raising=False)
        with pytest.raises(SystemExit):
            yc_common.load_sdk_from_storage()

    def test_valid_env(self, monkeypatch, mocker):
        monkeypatch.setenv("RD_CONFIG_YC_SA_KEY", SA_KEY_B64)
        mocker.patch("yandexcloud.SDK", return_value=MagicMock())
        sdk = yc_common.load_sdk_from_storage()
        assert sdk is not None


class TestWaitForOperation:
    def test_success(self, mock_sdk):
        op = MagicMock(done=True)
        op.HasField.return_value = False
        mock_sdk.client.return_value.Get.return_value = op

        yc_common.wait_for_operation(mock_sdk, "op-id")

    def test_operation_failure(self, mock_sdk):
        op = MagicMock(done=True)
        op.HasField.return_value = True
        op.error.message = "internal error"
        mock_sdk.client.return_value.Get.return_value = op

        with pytest.raises(RuntimeError, match="operation failed"):
            yc_common.wait_for_operation(mock_sdk, "op-id")

    def test_timeout(self, mock_sdk, mocker):
        op = MagicMock(done=False)
        mock_sdk.client.return_value.Get.return_value = op
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="timed out"):
            yc_common.wait_for_operation(mock_sdk, "op-id", timeout=0)
