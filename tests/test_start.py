"""Tests for start.py resource start functions."""

from unittest.mock import MagicMock

import grpc
import pytest
import start
from conftest import rpc_error
from yc_common import (
    COMPUTE_RUNNING,
    COMPUTE_STOPPED,
    COMPUTE_STOPPING,
    K8S_RUNNING,
    K8S_STOPPED,
    NLB_ACTIVE,
    NLB_STOPPED,
    PG_RUNNING,
    PG_STOPPED,
)


class TestStartComputeInstance:
    def test_already_running_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_RUNNING)
        mock_sdk.client.return_value = svc

        start.start_compute_instance(mock_sdk, "inst-id")

        svc.Start.assert_not_called()

    def test_starts_stopped_instance(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_STOPPED)
        svc.Start.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("start.wait_for_operation")

        start.start_compute_instance(mock_sdk, "inst-id")

        svc.Start.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_starts_stopping_instance(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_STOPPING)
        svc.Start.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("start.wait_for_operation")

        start.start_compute_instance(mock_sdk, "inst-id")

        svc.Start.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        start.start_compute_instance(mock_sdk, "inst-id")

        svc.Start.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            start.start_compute_instance(mock_sdk, "inst-id")

    def test_unknown_status_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=99)
        mock_sdk.client.return_value = svc

        start.start_compute_instance(mock_sdk, "inst-id")

        svc.Start.assert_not_called()


class TestStartPgCluster:
    def test_already_running_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=PG_RUNNING)
        mock_sdk.client.return_value = svc

        start.start_pg_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_not_called()

    def test_starts_stopped_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=PG_STOPPED)
        svc.Start.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("start.wait_for_operation")

        start.start_pg_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        start.start_pg_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            start.start_pg_cluster(mock_sdk, "cluster-id")


class TestStartK8sCluster:
    def test_already_running_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=K8S_RUNNING)
        mock_sdk.client.return_value = svc

        start.start_k8s_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_not_called()

    def test_starts_stopped_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=K8S_STOPPED)
        svc.Start.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("start.wait_for_operation")

        start.start_k8s_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        start.start_k8s_cluster(mock_sdk, "cluster-id")

        svc.Start.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            start.start_k8s_cluster(mock_sdk, "cluster-id")


class TestStartNlb:
    def test_already_active_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=NLB_ACTIVE)
        mock_sdk.client.return_value = svc

        start.start_nlb(mock_sdk, "nlb-id")

        svc.Start.assert_not_called()

    def test_starts_stopped_nlb(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=NLB_STOPPED)
        svc.Start.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("start.wait_for_operation")

        start.start_nlb(mock_sdk, "nlb-id")

        svc.Start.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        start.start_nlb(mock_sdk, "nlb-id")

        svc.Start.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            start.start_nlb(mock_sdk, "nlb-id")
