#!/usr/bin/env python3
"""
Start a Yandex Cloud resource.

Execution context:
  Runs INSIDE the Rundeck container as the yc-start NodeStep plugin.
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
from yandex.cloud.compute.v1 import instance_service_pb2, instance_service_pb2_grpc
from yandex.cloud.k8s.v1 import cluster_service_pb2 as k8s_cluster_service_pb2
from yandex.cloud.k8s.v1 import cluster_service_pb2_grpc as k8s_cluster_service_pb2_grpc
from yandex.cloud.loadbalancer.v1 import (
    network_load_balancer_service_pb2,
    network_load_balancer_service_pb2_grpc,
)
from yandex.cloud.mdb.postgresql.v1 import cluster_service_pb2, cluster_service_pb2_grpc
from yc_common import (
    COMPUTE_RUNNING,
    COMPUTE_STOPPED,
    COMPUTE_STOPPING,
    K8S_RUNNING,
    K8S_STOPPED,
    K8S_STOPPING,
    NLB_ACTIVE,
    NLB_STOPPED,
    NLB_STOPPING,
    PG_RUNNING,
    PG_STOPPED,
    PG_STOPPING,
    load_sdk_from_storage,
    wait_for_operation,
)


def start_compute_instance(sdk: yandexcloud.SDK, instance_id: str) -> None:
    svc = sdk.client(instance_service_pb2_grpc.InstanceServiceStub)

    try:
        instance = svc.Get(instance_service_pb2.GetInstanceRequest(instance_id=instance_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Instance {instance_id} not found, skipping.")
            return
        raise
    status = instance.status

    if status == COMPUTE_RUNNING:
        print(f"Instance {instance_id} is already running.")
        return
    if status not in (COMPUTE_STOPPED, COMPUTE_STOPPING):
        print(f"Instance {instance_id} is in status {status}, skipping.")
        return

    print(f"Starting compute instance {instance_id}...")
    op = svc.Start(instance_service_pb2.StartInstanceRequest(instance_id=instance_id))
    wait_for_operation(sdk, op.id)
    print(f"Instance {instance_id} started.")


def start_pg_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == PG_RUNNING:
        print(f"Cluster {cluster_id} is already running.")
        return
    if status not in (PG_STOPPED, PG_STOPPING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Starting managed-postgresql cluster {cluster_id}...")
    op = svc.Start(cluster_service_pb2.StartClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id)
    print(f"Cluster {cluster_id} started.")


def start_k8s_cluster(sdk: yandexcloud.SDK, cluster_id: str) -> None:
    svc = sdk.client(k8s_cluster_service_pb2_grpc.ClusterServiceStub)

    try:
        cluster = svc.Get(k8s_cluster_service_pb2.GetClusterRequest(cluster_id=cluster_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Cluster {cluster_id} not found, skipping.")
            return
        raise
    status = cluster.status

    if status == K8S_RUNNING:
        print(f"Cluster {cluster_id} is already running.")
        return
    if status not in (K8S_STOPPED, K8S_STOPPING):
        print(f"Cluster {cluster_id} is in status {status}, skipping.")
        return

    print(f"Starting managed-kubernetes cluster {cluster_id}...")
    op = svc.Start(k8s_cluster_service_pb2.StartClusterRequest(cluster_id=cluster_id))
    wait_for_operation(sdk, op.id, timeout=900)
    print(f"Cluster {cluster_id} started.")


def start_nlb(sdk: yandexcloud.SDK, nlb_id: str) -> None:
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

    if status == NLB_ACTIVE:
        print(f"Network load balancer {nlb_id} is already active.")
        return
    if status not in (NLB_STOPPED, NLB_STOPPING):
        print(f"Network load balancer {nlb_id} is in status {status}, skipping.")
        return

    print(f"Starting network load balancer {nlb_id}...")
    op = svc.Start(
        network_load_balancer_service_pb2.StartNetworkLoadBalancerRequest(
            network_load_balancer_id=nlb_id
        )
    )
    wait_for_operation(sdk, op.id)
    print(f"Network load balancer {nlb_id} started.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, help="Resource type (e.g. compute-instance)")
    parser.add_argument("--id", required=True, help="Resource ID")
    args = parser.parse_args()

    sdk = load_sdk_from_storage()

    try:
        match args.type:
            case "compute-instance":
                start_compute_instance(sdk, args.id)
            case "managed-postgresql":
                start_pg_cluster(sdk, args.id)
            case "managed-kubernetes":
                start_k8s_cluster(sdk, args.id)
            case "network-load-balancer":
                start_nlb(sdk, args.id)
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
