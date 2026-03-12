#!/usr/bin/env python3
"""
Stop a Yandex Cloud resource.

Execution context:
  Runs INSIDE the Rundeck container as the yc-stop NodeStep plugin.
  Invoked per node by Rundeck during job dispatch.
  Arguments --type and --id are substituted by Rundeck from node attributes.
  The SA key is injected automatically from Key Storage via plugin config.

Environment:
  RD_CONFIG_YC_SA_KEY  — base64-encoded Service Account JSON key,
                         injected automatically by Rundeck from Key Storage
                         via valueConversion: STORAGE_PATH_AUTOMATIC_READ.
"""

import argparse
import os
import sys

# Suppress gRPC shutdown timeout noise
os.environ.setdefault("GRPC_VERBOSITY", "NONE")

import grpc
import yandexcloud
from yandex.cloud.apploadbalancer.v1 import (
    load_balancer_service_pb2 as alb_service_pb2,
)
from yandex.cloud.apploadbalancer.v1 import (
    load_balancer_service_pb2_grpc as alb_service_pb2_grpc,
)
from yandex.cloud.compute.v1 import instance_service_pb2, instance_service_pb2_grpc
from yandex.cloud.k8s.v1 import cluster_service_pb2 as k8s_cluster_service_pb2
from yandex.cloud.k8s.v1 import cluster_service_pb2_grpc as k8s_cluster_service_pb2_grpc
from yandex.cloud.loadbalancer.v1 import (
    network_load_balancer_service_pb2,
    network_load_balancer_service_pb2_grpc,
)
from yandex.cloud.mdb.clickhouse.v1 import cluster_service_pb2 as ch_cluster_service_pb2
from yandex.cloud.mdb.clickhouse.v1 import cluster_service_pb2_grpc as ch_cluster_service_pb2_grpc
from yandex.cloud.mdb.kafka.v1 import cluster_service_pb2 as kafka_cluster_service_pb2
from yandex.cloud.mdb.kafka.v1 import cluster_service_pb2_grpc as kafka_cluster_service_pb2_grpc
from yandex.cloud.mdb.mysql.v1 import cluster_service_pb2 as mysql_cluster_service_pb2
from yandex.cloud.mdb.mysql.v1 import cluster_service_pb2_grpc as mysql_cluster_service_pb2_grpc
from yandex.cloud.mdb.postgresql.v1 import cluster_service_pb2, cluster_service_pb2_grpc
from yandex.cloud.mdb.redis.v1 import cluster_service_pb2 as redis_cluster_service_pb2
from yandex.cloud.mdb.redis.v1 import cluster_service_pb2_grpc as redis_cluster_service_pb2_grpc
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
    K8S_STARTING,
    K8S_STOPPED,
    KAFKA_RUNNING,
    KAFKA_STARTING,
    KAFKA_STOPPED,
    MYSQL_RUNNING,
    MYSQL_STARTING,
    MYSQL_STOPPED,
    NLB_ACTIVE,
    NLB_STARTING,
    NLB_STOPPED,
    PG_RUNNING,
    PG_STARTING,
    PG_STOPPED,
    REDIS_RUNNING,
    REDIS_STARTING,
    REDIS_STOPPED,
    load_sdk_from_storage,
    wait_for_operation,
)


def stop_compute_instance(sdk: yandexcloud.SDK, instance_id: str) -> None:
    svc = sdk.client(instance_service_pb2_grpc.InstanceServiceStub)

    try:
        instance = svc.Get(instance_service_pb2.GetInstanceRequest(instance_id=instance_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Instance {instance_id} not found, skipping.")
            return
        raise
    status = instance.status

    if status == COMPUTE_STOPPED:
        print(f"Instance {instance_id} is already stopped.")
        return
    if status not in (COMPUTE_RUNNING, COMPUTE_STARTING):
        print(f"Instance {instance_id} is in status {status}, skipping.")
        return

    print(f"Stopping compute instance {instance_id}...")
    op = svc.Stop(instance_service_pb2.StopInstanceRequest(instance_id=instance_id))
    wait_for_operation(sdk, op.id)
    print(f"Instance {instance_id} stopped.")


def stop_clickhouse_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(ch_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(ch_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == CLICKHOUSE_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (CLICKHOUSE_RUNNING, CLICKHOUSE_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-clickhouse cluster {cluster_id}...")
    op = svc.Stop(ch_cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} stopped.")


def stop_pg_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == PG_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (PG_RUNNING, PG_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-postgresql cluster {cluster_id}...")
    op = svc.Stop(cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} stopped.")


def stop_k8s_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(k8s_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(k8s_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == K8S_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (K8S_RUNNING, K8S_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-kubernetes cluster {cluster_id}...")
    op = svc.Stop(k8s_cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id, timeout=900)
    print(f"Cluster {cluster_id} stopped.")


def stop_kafka_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(kafka_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(kafka_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == KAFKA_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (KAFKA_RUNNING, KAFKA_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-kafka cluster {cluster_id}...")
    op = svc.Stop(kafka_cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} stopped.")


def stop_mysql_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(mysql_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(mysql_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == MYSQL_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (MYSQL_RUNNING, MYSQL_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-mysql cluster {cluster_id}...")
    op = svc.Stop(mysql_cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} stopped.")


def stop_redis_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(redis_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(redis_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == REDIS_STOPPED:
        print(f"Cluster {cluster_id} is already stopped.")
        return
    if status not in (REDIS_RUNNING, REDIS_STARTING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Stopping managed-redis cluster {cluster_id}...")
    op = svc.Stop(redis_cluster_service_pb2.StopClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} stopped.")


def stop_nlb(sdk: yandexcloud.SDK, nlb_id: str) -> None:
    svc = sdk.client(network_load_balancer_service_pb2_grpc.NetworkLoadBalancerServiceStub)

    try:
        balancer = svc.Get(
            network_load_balancer_service_pb2.GetNetworkLoadBalancerRequest(
                network_load_balancer_id=nlb_id
            )
        )
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Network load balancer {nlb_id} not found, skipping.")
            return
        raise
    status = balancer.status

    if status == NLB_STOPPED:
        print(f"Network load balancer {nlb_id} is already stopped.")
        return
    if status not in (NLB_ACTIVE, NLB_STARTING):
        print(f"Network load balancer {nlb_id} is in status {status}, skipping.")
        return

    print(f"Stopping network load balancer {nlb_id}...")
    op = svc.Stop(
        network_load_balancer_service_pb2.StopNetworkLoadBalancerRequest(
            network_load_balancer_id=nlb_id
        )
    )
    wait_for_operation(sdk, op.id)
    print(f"Network load balancer {nlb_id} stopped.")


def stop_alb(sdk: yandexcloud.SDK, alb_id: str) -> None:
    svc = sdk.client(alb_service_pb2_grpc.LoadBalancerServiceStub)

    try:
        balancer = svc.Get(alb_service_pb2.GetLoadBalancerRequest(load_balancer_id=alb_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Application load balancer {alb_id} not found, skipping.")
            return
        raise
    status = balancer.status

    if status == ALB_STOPPED:
        print(f"Application load balancer {alb_id} is already stopped.")
        return
    if status not in (ALB_ACTIVE, ALB_STARTING):
        print(f"Application load balancer {alb_id} is in status {status}, skipping.")
        return

    print(f"Stopping application load balancer {alb_id}...")
    op = svc.Stop(alb_service_pb2.StopLoadBalancerRequest(load_balancer_id=alb_id))
    wait_for_operation(sdk, op.id)
    print(f"Application load balancer {alb_id} stopped.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, help="Resource type (e.g. compute-instance)")
    parser.add_argument("--id", required=True, help="Resource ID")
    args = parser.parse_args()

    sdk = load_sdk_from_storage()

    try:
        match args.type:
            case "compute-instance":
                stop_compute_instance(sdk, args.id)
            case "managed-postgresql":
                stop_pg_cluster(sdk, args.id)
            case "managed-kubernetes":
                stop_k8s_cluster(sdk, args.id)
            case "managed-kafka":
                stop_kafka_cluster(sdk, args.id)
            case "managed-clickhouse":
                stop_clickhouse_cluster(sdk, args.id)
            case "managed-mysql":
                stop_mysql_cluster(sdk, args.id)
            case "managed-redis":
                stop_redis_cluster(sdk, args.id)
            case "network-load-balancer":
                stop_nlb(sdk, args.id)
            case "application-load-balancer":
                stop_alb(sdk, args.id)
            case _:
                print(f"ERROR: unsupported resource type: {args.type}", file=sys.stderr)
                sys.exit(1)
    except grpc.RpcError as exc:
        print(f"ERROR: gRPC {exc.code()}: {exc.details()}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
