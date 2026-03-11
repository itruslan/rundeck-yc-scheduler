"""Tests for stop.py resource stop functions."""

from unittest.mock import MagicMock

import grpc
import pytest
import stop
from conftest import rpc_error
from yc_common import (
    ALB_ACTIVE,
    ALB_STARTING,
    ALB_STOPPED,
    CLICKHOUSE_RUNNING,
    CLICKHOUSE_STARTING,
    CLICKHOUSE_STOPPED,
    COMPUTE_RUNNING,
    COMPUTE_STARTING,
    COMPUTE_STOPPED,
    K8S_RUNNING,
    K8S_STOPPED,
    KAFKA_RUNNING,
    KAFKA_STARTING,
    KAFKA_STOPPED,
    MYSQL_RUNNING,
    MYSQL_STARTING,
    MYSQL_STOPPED,
    NLB_ACTIVE,
    NLB_STOPPED,
    PG_RUNNING,
    PG_STOPPED,
    REDIS_RUNNING,
    REDIS_STARTING,
    REDIS_STOPPED,
)


class TestStopComputeInstance:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_compute_instance(mock_sdk, "inst-id")

        svc.Stop.assert_not_called()

    def test_stops_running_instance(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_compute_instance(mock_sdk, "inst-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_instance(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=COMPUTE_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_compute_instance(mock_sdk, "inst-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_compute_instance(mock_sdk, "inst-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_compute_instance(mock_sdk, "inst-id")

    def test_unknown_status_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=99)
        mock_sdk.client.return_value = svc

        stop.stop_compute_instance(mock_sdk, "inst-id")

        svc.Stop.assert_not_called()


class TestStopPgCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=PG_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_pg_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=PG_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_pg_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_pg_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_pg_cluster(mock_sdk, "cluster-id")


class TestStopK8sCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=K8S_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_k8s_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=K8S_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_k8s_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1", timeout=900)

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_k8s_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_k8s_cluster(mock_sdk, "cluster-id")


class TestStopKafkaCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=KAFKA_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_kafka_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=KAFKA_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_kafka_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=KAFKA_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_kafka_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_kafka_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_kafka_cluster(mock_sdk, "cluster-id")


class TestStopNlb:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=NLB_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_nlb(mock_sdk, "nlb-id")

        svc.Stop.assert_not_called()

    def test_stops_active_nlb(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=NLB_ACTIVE)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_nlb(mock_sdk, "nlb-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_nlb(mock_sdk, "nlb-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_nlb(mock_sdk, "nlb-id")


class TestStopAlb:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=ALB_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_alb(mock_sdk, "alb-id")

        svc.Stop.assert_not_called()

    def test_stops_active_alb(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=ALB_ACTIVE)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_alb(mock_sdk, "alb-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_alb(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=ALB_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_alb(mock_sdk, "alb-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_alb(mock_sdk, "alb-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_alb(mock_sdk, "alb-id")

    def test_unknown_status_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=99)
        mock_sdk.client.return_value = svc

        stop.stop_alb(mock_sdk, "alb-id")

        svc.Stop.assert_not_called()


class TestStopClickhouseCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=CLICKHOUSE_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_clickhouse_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=CLICKHOUSE_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_clickhouse_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=CLICKHOUSE_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_clickhouse_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_clickhouse_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_clickhouse_cluster(mock_sdk, "cluster-id")


class TestStopRedisCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=REDIS_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_redis_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=REDIS_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_redis_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=REDIS_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_redis_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_redis_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_redis_cluster(mock_sdk, "cluster-id")


class TestStopMysqlCluster:
    def test_already_stopped_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=MYSQL_STOPPED)
        mock_sdk.client.return_value = svc

        stop.stop_mysql_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_stops_running_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=MYSQL_RUNNING)
        svc.Stop.return_value = MagicMock(id="op-1")
        mock_sdk.client.return_value = svc
        mock_wait = mocker.patch("stop.wait_for_operation")

        stop.stop_mysql_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()
        mock_wait.assert_called_once_with(mock_sdk, "op-1")

    def test_stops_starting_cluster(self, mock_sdk, mocker):
        svc = MagicMock()
        svc.Get.return_value = MagicMock(status=MYSQL_STARTING)
        svc.Stop.return_value = MagicMock(id="op-2")
        mock_sdk.client.return_value = svc
        mocker.patch("stop.wait_for_operation")

        stop.stop_mysql_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_called_once()

    def test_not_found_skips(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.NOT_FOUND)
        mock_sdk.client.return_value = svc

        stop.stop_mysql_cluster(mock_sdk, "cluster-id")

        svc.Stop.assert_not_called()

    def test_other_rpc_error_raises(self, mock_sdk):
        svc = MagicMock()
        svc.Get.side_effect = rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_sdk.client.return_value = svc

        with pytest.raises(grpc.RpcError):
            stop.stop_mysql_cluster(mock_sdk, "cluster-id")
